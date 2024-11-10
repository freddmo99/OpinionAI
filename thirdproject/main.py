from flask import Flask, flash, redirect, render_template, request, session, url_for
import pyrebase
from Procedures.Login import register, login, logout  # Import login-related functions
from Procedures.Storage import (
    upload_file,
    get_image_list,
    serve_image,
    get_image_metadata,
    add_db_entry,
    get_image_list_with_metadata,
    upload_text_file
)  # Import storage-related functions
from google.cloud import storage
from google.cloud import datastore
import google.generativeai as genai  
import os
from Procedures.AI import upload_to_gemini
from Settings import GEMINI_API_KEY 

app = Flask(__name__)
app.secret_key = 'FAMG_Secret_key'

# Firebase configuration
firebaseConfig = {
    "apiKey": "AIzaSyCBpLDybaPgH2NIcbd0IMqtOboCWFAMd0w",
    "authDomain": "test01project-7b8a9.firebaseapp.com",
    "projectId": "test01project-7b8a9",
    "storageBucket": "test01project-7b8a9.appspot.com",
    "messagingSenderId": "364438740852",
    "appId": "1:364438740852:web:67bda0d6c81bcff39e9621",
    "measurementId": "G-65QKHZEJLB",
    "databaseURL": "https://console.firebase.google.com/project/test01project-7b8a9/database/test01project-7b8a9-default-rtdb/data/~2F"
}

firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()

# Google Cloud Storage configuration
bucketname = 'cloudnativebucket'
storage_client = storage.Client()
datastore_client = datastore.Client()
# Routes

#AI

# Google Generative AI API configuration

#Set up API Key
genai.configure(api_key=GEMINI_API_KEY) 
#Set up AI config
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}


#Create Gemini Model
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
)

PROMPT = 'give a title to the image and describe the image'

@app.get("/")
def home():
    if 'idToken' in session:
        email = session.get('user')
        id_token = session.get('idToken')
        # Debugging information to verify session details
        print(f"Session info - Email: {email}, ID Token: {id_token}")

        try:
            # Verify the token
            user = auth.get_account_info(session['idToken'])
            print(f"Firebase returned user info: {user}")
            image_list = get_image_list(bucketname)
            

            print(f"Images list: {image_list}")  
            return render_template('home_page.html', email=email, images=image_list)
        except Exception as e:
            session.pop('user', None)
            session.pop('idToken', None)
            flash("Your session has expired. Please log in again.", "warning")
            return redirect(url_for('login_route'))
    return render_template('login_page.html')


# Login-related routes
@app.route('/register', methods=['GET', 'POST'])
def register_route():
    return register()

@app.route('/login', methods=['GET', 'POST'])
def login_route():
    return login()

@app.route('/logout', methods=['GET', 'POST'])
def logout_route():
    return logout()


@app.route('/upload', methods=['POST'])
def upload_image():
    file = request.files['file_name']
    filename = file.filename
    
    # Step 1: Upload the image to your bucket
    upload_file(bucketname, filename, file)

    # Get metadata for the uploaded image
    metadata = get_image_metadata(filename)
    
    # Step 2: Add user information to metadata
    email = session.get('user')  # Get the email of the logged-in user
    metadata['uploaded_by'] = email  # Add the user's email to the metadata
    add_db_entry(metadata)

    # AI part----------------------

    # Step 3: AI part - Call the AI API to get the caption and description
    img = upload_to_gemini(filename, mime_type="image/jpeg")
    parts = [img, PROMPT]
    response = model.generate_content(parts)
    generated_text = response._result.candidates[0].content.parts[0].text

    # Step 4: Save the description as a .txt file inside the bucket
    txt_filename = filename.rsplit('.', 1)[0] + '.txt'  # Create a .txt filename based on the original image filename
    upload_text_file(bucketname, txt_filename, generated_text)  # Upload the generated description as a .txt file

    return redirect(url_for('home'))




@app.route('/images')
def list_images():
    image_list = get_image_list(bucketname)
    print(f"Images list: {image_list}")  # Debug print
    return render_template('home_page.html', images=image_list)

@app.route('/image/<filename>')
def serve_image_route(filename):
    return serve_image(bucketname, filename)


if __name__ == "__main__":
    app.run(host="localhost", port=8080, debug=True)
