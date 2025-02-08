import os
import google.generativeai as genai
from flask import Flask, request, jsonify
from flask_cors import CORS  # Import CORS from flask_cors

# Initialize the Flask app
app = Flask(__name__)

# Enable CORS for all domains
CORS(app)  # This will allow all origins to make requests to your API

# Configure the Gemini API key
genai.configure(api_key="AIzaSyB4GgtY8Tkf6KeCx9CbkDykvSviN_bkmAg")

# Set up the generation configuration
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

# Create the generative model
model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    generation_config=generation_config,
    system_instruction="I am a blind person. When I upload an image, please describe it as though you are guiding me through the scene in a natural, detailed way. Your description should give me a sense of the scene’s layout, including approximate distances between objects or people, spatial arrangements, and any other details that would help me understand the image. Focus on providing vivid, sensory-rich information without needing to say 'let me explain.' Just describe the image directly, from sounds to textures, colors, and distances between elements, so I can visualize it as if I were experiencing it myself",
)

# Helper function to upload the image to Gemini
def upload_to_gemini(path, mime_type=None):
    """Uploads the given file to Gemini."""
    file = genai.upload_file(path, mime_type=mime_type)
    return file

@app.route('/upload-image', methods=['POST'])
def upload_image():
    # Check if an image file is part of the request
    if 'image' not in request.files:
        return jsonify({"error": "No image file part in the request."}), 400

    image_file = request.files['image']
    
    if image_file.filename == '':
        return jsonify({"error": "No selected file."}), 400

    # Save the image temporarily to the file system
    temp_path = f"./temp_{image_file.filename}"
    image_file.save(temp_path)

    try:
        # Upload the image to Gemini
        file = upload_to_gemini(temp_path, mime_type=image_file.content_type)

        # Start the chat session with the uploaded image
        chat_session = model.start_chat(
            history=[
                {
                    "role": "user",
                    "parts": [file],
                },
            ]
        )

        # Send the request for a description
        response = chat_session.send_message("Describe the image for me.")

        # Return the description as a JSON response
        description = response.text

        # Clean up the temporary file from the server
        os.remove(temp_path)

        # Return the description to the user
        return jsonify({"description": description})

    except Exception as e:
        # Clean up the temporary file in case of error
        if os.path.exists(temp_path):
            os.remove(temp_path)

        return jsonify({"error": str(e)}), 500

# Run the Flask server
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
