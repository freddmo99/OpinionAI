from flask import flash, redirect, render_template, request, session, url_for
import pyrebase

# Initialize Firebase here if needed or pass it as a parameter
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

# Initialize Firebase
firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()

def register():
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        password = request.form['password']

        try:
            # Attempt to create the user
            user = auth.create_user_with_email_and_password(email, password)
            session['user'] = email  # Store email in session
            
            # Redirect to the login page after successful registration
            return redirect(url_for('login_route'))

        except Exception as e:
            error_message = str(e)
            
            print(f"Error during registration: {error_message}")

            if "EMAIL_EXISTS" in error_message:
                flash("This email is already registered. Please use a different email or log in.", "error")
            elif "WEAK_PASSWORD" in error_message:
                flash("The password is too weak. Please use at least 6 characters.", "error")
            elif "INVALID_EMAIL" in error_message:
                flash("Invalid email format. Please provide a valid email address.", "error")
            elif "MISSING_PASSWORD" in error_message:
                flash("Password is required. Please enter a password.", "error")
            else:
                flash("An error occurred during registration. Please try again.", "error")

    return render_template('register_page.html')


def login():
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        password = request.form['password']
        try:
            # Sign in the user and get the token
            user = auth.sign_in_with_email_and_password(email, password)
            session['user'] = email  # Store email in session
            session['idToken'] = user['idToken']  # Store the Firebase token in session

            # Redirect to the home page after successful login
            return redirect(url_for('home'))
        
        except Exception as e:
            error_message = str(e)

            # Handle specific error cases
            if "INVALID_LOGIN_CREDENTIALS" in error_message:
                flash("Invalid email or password. Please try again.", "error")
            else:
                flash("An error occurred during login. Please try again.", "error")

            return render_template('login_page.html')
    
    return render_template('login_page.html')


def logout():
    session.pop('user', None)
    return redirect(url_for('login_route'))
