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

prompt = '''
        "I am a blind individual, and I would like you to assist me in understanding images by providing detailed, vivid, and sensory-rich descriptions. When I upload an image, please describe it as though you are guiding me through the scene in a natural and immersive way. Your description should include:

        1. **Spatial Layout**: Describe the arrangement of objects, people, or elements in the scene, including approximate distances between them (e.g., 'a table is about three feet in front of you, with a chair to its left, two feet away').
        2. **Visual Details**: Mention colors, shapes, sizes, and textures (e.g., 'a smooth, round red apple on a wooden table').
        3. **Sensory Cues**: Include any implied sounds, smells, or tactile sensations that might be associated with the scene (e.g., 'the sound of leaves rustling in the wind' or 'the warm glow of sunlight filtering through a window').
        4. **Context and Atmosphere**: Provide context about the setting, mood, or activity taking place (e.g., 'a bustling city street with people walking briskly and cars honking in the distance').
        5. **Key Focal Points**: Highlight the most important or prominent elements in the image and their relationships to one another.

        Your goal is to help me visualize the scene as if I were experiencing it myself, with a focus on clarity, detail, and natural flow. Avoid phrases like 'let me explain' or 'in the image'; simply describe the scene directly and vividly."
        '''

# Create the generative model
model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    generation_config=generation_config,
    system_instruction=prompt
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
