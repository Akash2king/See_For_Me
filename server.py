from flask import Flask, request, jsonify, send_from_directory, render_template
import logging
import os
import requests
import json
import base64

app = Flask(__name__)

logging.basicConfig(level=logging.DEBUG)  # for better debugging, we will log out every request with headers and body.

@app.before_request
def log_request_info():
    logging.info('Headers: %s', request.headers)
    logging.info('Body: %s', request.get_data())

@app.route("/upload-image", methods=["POST"])
def upload_image():
    try:
        image_raw_bytes = request.get_data()  # get the whole body
        
        # Create static directory if it doesn't exist
        static_dir = os.path.join(app.root_path, "static")
        os.makedirs(static_dir, exist_ok=True)
        
        save_location = os.path.join(static_dir, "test.jpg")  # save location
        
        with open(save_location, 'wb') as f:  # wb for write byte data in the file instead of string
            f.write(image_raw_bytes)  # write the bytes from the request body to the file
        
        logging.info("Image saved to %s", save_location)
        
        # Upload the image to Gemini API
        gemini_response = upload_to_gemini(save_location)
        
        # Delete the image after the response is generated
        os.remove(save_location)
        logging.info("Image deleted from %s", save_location)

        # Return response and render the webpage
        return render_template("response.html", response=gemini_response)
    except Exception as e:
        logging.error("Error processing upload: %s", str(e))
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route("/status", methods=["GET"])
def status():
    return jsonify({
        "status": "online",
        "message": "API server is running"
    })

@app.route("/webpage", methods=["GET"])
def serve_webpage():
    try:
        return send_from_directory(os.path.join(app.root_path, 'static'), 'index.html')
    except Exception as e:
        logging.error("Error serving webpage: %s", str(e))
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route("/speakout", methods=["GET"])
def speak_out():
    return render_template("response.html", response="Click the button to speak out the response.")


def upload_to_gemini(image_path):
    try:
        api_key = "AIzaSyAk-WvOxFs38u391lWOhLAf0an-DT4QGxg"
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-pro-vision:generateContent?key={api_key}"
        with open(image_path, "rb") as image_file:
            image_bytes = image_file.read()
            base64_encoded_image = base64.b64encode(image_bytes).decode('utf-8')
        payload = {
            "contents": [{
                "parts": [
                    {"text": "Describe this image in detail."},
                    {"inline_data": {
                        "mime_type": "image/jpeg",
                        "data": base64_encoded_image
                    }}
                ]
            }],
            "generationConfig": {
                "temperature": 0.4,
                "topK": 32,
                "topP": 1,
                "maxOutputTokens": 4096
            }
        }
        headers = {'Content-Type': 'application/json'}
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        if response.status_code == 200:
            result = response.json()
            if 'candidates' in result and len(result['candidates']) > 0:
                return result['candidates'][0]['content']
            return json.dumps(result)
        else:
            logging.error("Gemini API error: %s, %s", response.status_code, response.text)
            return f"Error from Gemini API: {response.status_code}, {response.text}"
    except Exception as e:
        logging.error("Error in upload_to_gemini: %s", str(e))
        return f"Error processing image with Gemini: {str(e)}"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
