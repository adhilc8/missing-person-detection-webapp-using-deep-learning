#import libraries
import numpy as np
from flask import Flask, request, render_template, redirect, url_for, session, Response, jsonify
import sqlite3
import os
import cv2
import mediapipe as mp
import numpy as np
import time
import requests
from datetime import datetime
from werkzeug.utils import secure_filename




############## Flask app Initiate#####################################################
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-only-change-me")


################### DB and Directroy Details ########################################
DB_NAME = "users.db"
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)



################################   Function to initialize the database ##################
def init_db():
    if not os.path.exists(DB_NAME):
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT NOT NULL,
                    contact TEXT NOT NULL,
                    address TEXT NOT NULL,
                    missing_person_name TEXT NOT NULL,
                    relation TEXT NOT NULL,
                    missing_since TEXT NOT NULL,
                    upload_date TEXT NOT NULL,
                    current_status TEXT NOT NULL,
                    path TEXT NOT NULL,
                    password TEXT NOT NULL,
                    image TEXT NOT NULL,
                    terms_accepted BOOLEAN NOT NULL
                )
            ''')
            conn.commit()


def get_user_details(username):
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()
            
            if user:
                return {
                    "id": user[0],
                    "username": user[1],
                    "email": user[2],
                    "contact": user[3],
                    "address" : user[4],
                    "missing_person_name": user[5],
                    "relation": user[6],  
                    "missing_since": user[7],
                    "upload_date":user[8],
                    "current_status": user[9],
                    "path":user[10],
                    "password": user[11],
                    "image": user[12],
                    "terms_accepted": user[13]
                }
            else:
                return "User not found"
    except sqlite3.Error as e:
        return f"Database error: {e}"



################### Initialize the database when the app starts  ###############################
init_db()





################################### route functions ###############################################
@app.route('/')
def landing():
    return render_template('home.html')

@app.route('/login')
def login():
    error = request.args.get("error")  # Capture error message
    return render_template('login.html', error=error)


@app.route('/signup')
def signup():
    error = request.args.get("error")  # Capture error message
    return render_template('signup.html', error=error)

@app.route('/signupsuccess', methods=['POST'])
def signupsuccess():
    if request.method == 'POST':
        username = request.form.get("username")
        email = request.form.get("email")
        contact = request.form.get("contact")
        address = request.form.get("address")
        missing_person_name = request.form.get("missing_person_name")
        relation = request.form.get("relation")
        missing_since = request.form.get("missing_since")
        upload_date = datetime.today().strftime('%Y-%m-%d')
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        image = 'general/general.png'
        current_status = 'still searching...'
        path = 'general/general.png'
        terms_accepted = request.form.get("terms") is not None



        if not username:
            return redirect(url_for("signup", error="Username cannot be empty."))

        if password != confirm_password:
            return redirect(url_for("signup", error="Passwords do not match."))

        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            existing_user = cursor.fetchone()

            if existing_user:
                return redirect(url_for("signup", error="Username already exists. Please choose a different one."))

            cursor.execute('''
                INSERT INTO users (username, email, contact, address, missing_person_name, relation, missing_since, upload_date, current_status, path, password, image, terms_accepted) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (username, email, contact, address, missing_person_name, relation, missing_since, upload_date, current_status, path, password, image, terms_accepted))
            conn.commit()

        session["username"] = username
        session["email"] = email

        return render_template('login.html', error="Signup successful!")






@app.route('/home', methods=['POST'])
def home():
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")

        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()

            if not user:
                return redirect(url_for('login', error="Username does not exist."))

            # You may also add password verification here
            if user[11] != password:  # Assuming password is at index 5
                return redirect(url_for('login', error="Incorrect password."))
        session["username"] = username
        return render_template('home2.html', user=username)



@app.route('/home2')
def home2():
    username = session["username"]
    return render_template('home2.html', user=username)


@app.route('/home3')
def home3():
    username = session["username"]
    return render_template('home.html', user=username)


@app.route('/profile')
def profile():
    user_details = get_user_details(session["username"])
    username = user_details['username']
    email = user_details['email']
    contact = user_details['contact']
    missing_person_name = user_details['missing_person_name']
    relation = user_details['relation']
    date_since = user_details['missing_since']
    address = user_details['address']
    date = user_details['upload_date']
    status = user_details['current_status']
    path = user_details['path']
    image = user_details['image']


    return render_template('profile.html', user = username, address = address, date = date, path = path, status = status, date_since = date_since, missing_person_name = missing_person_name, relation = relation, contact = contact, email = email, image_name = image)





def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

################# Update missing person image when upload ###########################################

def update_user_image(username, image_filename):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users SET image = ? WHERE username = ?
        ''', (image_filename, username))
        conn.commit()




@app.route('/upload_image', methods=['POST'])
def upload_image():
    print("FILES:", request.files)          # Check if file is coming through
    print("FORM:", request.form)            # Check form data

    if 'image' not in request.files:
        print("ERROR: No 'image' key in request.files")
        return 'No file part', 400
    
    file = request.files['image']
    print("FILENAME:", file.filename)       # Check filename

    if file.filename == '':
        print("ERROR: Empty filename")
        return 'No file selected', 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        print("SAVING TO:", save_path)      # Check save path
        file.save(save_path)
        print("SAVE SUCCESSFUL")
        username = session["username"]
        print('U', username)
        print('F', filename)
        update_user_image(username, filename)
        return redirect(url_for('profile'))
    
    print("ERROR: File type not allowed:", file.filename)
    return 'Invalid file type', 400






if __name__ == "__main__":
    app.run(debug=True)
