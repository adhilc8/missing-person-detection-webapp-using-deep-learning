import cv2
import numpy as np
import os
from mtcnn import MTCNN
from keras_facenet import FaceNet
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
import smtplib
import ssl
from email.message import EmailMessage
import imghdr 


# ─────────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────────
DB_NAME  = "users.db"
DB_PATH  = "static/uploads"

cameras = {
    0: "8.5241° N, 76.9366° E",
    1: "9.9312° N, 76.2673° E",
    2: "9.4981° N, 76.3388° E"
}
CAMERA_ID   = 1
camera_name = cameras.get(CAMERA_ID, f"Camera {CAMERA_ID}")

# ─────────────────────────────────────────────
#  INIT MODELS
# ─────────────────────────────────────────────
detector = MTCNN()
embedder = FaceNet()

# Known faces dictionary {filename: embedding}
known_faces = {}

# ─────────────────────────────────────────────
#  DATABASE FUNCTIONS
# ─────────────────────────────────────────────
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
                    "id":                  user[0],
                    "username":            user[1],
                    "email":               user[2],
                    "contact":             user[3],
                    "address":             user[4],
                    "missing_person_name": user[5],
                    "relation":            user[6],
                    "missing_since":       user[7],
                    "upload_date":         user[8],
                    "current_status":      user[9],
                    "path":                user[10],
                    "password":            user[11],
                    "image":               user[12],
                    "terms_accepted":      user[13]
                }
            else:
                return "User not found"
    except sqlite3.Error as e:
        return f"Database error: {e}"


def get_details_by_image(image_filename):
    """Fetch missing person details from DB using image filename."""
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT username, email, contact, address, missing_person_name, relation, missing_since, upload_date, current_status, path, password, image, terms_accepted FROM users WHERE image = ?",
                (image_filename,)
            )
            result = cursor.fetchone()
            if result:
                return result
            else:
                return None
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None


# ─────────────────────────────────────────────
#  FACE RECOGNITION FUNCTIONS
# ─────────────────────────────────────────────
def preprocess_face(img):
    """Resize and preprocess face for FaceNet."""
    face = cv2.resize(img, (160, 160))
    return face


def build_database():
    """Load all images from DB_PATH and compute embeddings."""
    for filename in os.listdir(DB_PATH):
        if filename.lower().endswith((".jpg", ".jpeg", ".png")):
            path = os.path.join(DB_PATH, filename)
            img  = cv2.imread(path)
            if img is None:
                continue
            results = detector.detect_faces(img)
            if results:
                x, y, w, h = results[0]['box']
                face        = img[y:y+h, x:x+w]
                face        = preprocess_face(face)
                embedding   = embedder.embeddings([face])[0]
                known_faces[filename] = embedding
                print(f"[INFO] Added {filename} to database")
            else:
                print(f"[WARNING] No face detected in {filename}, skipping.")


def match_face(frame, box, threshold=0.9):
    """Match detected face against database embeddings."""
    x, y, w, h = box
    face        = frame[y:y+h, x:x+w]
    face        = preprocess_face(face)
    embedding   = embedder.embeddings([face])[0]

    best_match = None
    best_score = float("inf")

    for name, known_embedding in known_faces.items():
        score = np.linalg.norm(embedding - known_embedding)
        if score < best_score:
            best_score = score
            best_match = name

    if best_score < threshold:
        return best_match, best_score, True
    else:
        return "Unknown", best_score, False



def update_user_path(username, image_filename):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users SET path = ? WHERE username = ?
        ''', (image_filename, username))
        conn.commit()

def update_current_status(username, status):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users SET current_status = ? WHERE username = ?
        ''', (status, username))
        conn.commit()



# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────
if __name__ == "__main__":
    init_db()
    build_database()

    if not known_faces:
        print("[ERROR] No faces loaded into database. Exiting.")
        exit()

    cap = cv2.VideoCapture(CAMERA_ID)
    print(f"[INFO] Starting {camera_name} | Press 'q' to quit.")

    match_found = False  # Flag to break out of while loop

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[ERROR] Failed to grab frame.")
            break

        # Persistent camera location on frame
        cv2.putText(frame, f"[ {camera_name} ]", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

        results = detector.detect_faces(frame)

        for res in results:
            x, y, w, h = res['box']
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

            cv2.putText(frame, "Face Matching...", (x, y-60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            name, score, matched = match_face(frame, (x, y, w, h))

            if matched:
                user_details        = get_details_by_image(name)
                username            = user_details[0]
                email               = user_details[1]
                contact             = user_details[2]
                address             = user_details[3]
                missing_person_name = user_details[4]
                relation            = user_details[5]
                missing_since       = user_details[6]
                upload_date         = user_details[7]
                current_status      = user_details[8]
                path                = user_details[9]
                password            = user_details[10]
                image               = user_details[11]
                terms_accepted      = user_details[12]

                # Terminal output
                print(f"\n{'='*40}")
                print(f"[MATCH FOUND]")
                print(f"  Missing Person : {missing_person_name}")
                print(f"  Image File     : {name}")
                print(f"  Score          : {score:.2f}")
                print(f"  Location         : {camera_name}")
                print(f"  Reported By    : {username}")
                print(f"  Contact        : {contact}")
                print(f"  Missing Since  : {missing_since}")
                print(f"{'='*40}\n")

                # On-frame display
                cv2.putText(frame, f"MATCH: {missing_person_name} ({score:.2f})", (x, y-40),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                cv2.putText(frame, f"Location: {camera_name}", (x, y-5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

                # Save the matched frame
                timestamp     = datetime.now().strftime("%Y%m%d_%H%M%S")
                save_filename = f"match_{missing_person_name}_{timestamp}.jpg"
                save_dir      = os.path.join("static", "detections")
                #os.makedirs(save_dir, exist_ok=True)
                save_path = os.path.join(save_dir, save_filename)
                cv2.imwrite(save_path, frame)
                print(f"[INFO] Match frame saved to: {save_path}")

                update_user_path(username, save_filename)
                status = 'Found at: ' + str(camera_name)
                update_current_status(username, status)

########################################################### Send email ##############################################
                sender = os.environ.get("SMTP_SENDER", "adhilc8848@gmail.com")
                receiver = email
                password = os.environ.get("SMTP_APP_PASSWORD")
                image_path = save_path

                if not sender or not password:
                    print("[WARN] Email alerts are disabled; set SMTP_SENDER and SMTP_APP_PASSWORD.")
                else:
                    # --- Message ---
                    msg = EmailMessage()
                    msg["Subject"] = "Person Named " + str(missing_person_name) + " has been Found!"
                    msg["From"] = sender
                    msg["To"] = receiver
                    msg.set_content("Hi " + str(username)+ ", The person you reported missing has been found at location: " + str(camera_name) + ". \nPlease find the attached image and reachout to PersonTrack.AI as soon as possible. \n\n\n Team PersonTrack.AI")

                    with open(image_path, 'rb') as f:
                        file_data = f.read()
                        image_type = imghdr.what(f.name) # Detect image type
                        msg.add_attachment(
                            file_data,
                            maintype='image',
                            subtype=image_type,
                            filename=image_path
                            )
                    context = ssl.create_default_context()
                    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
                        server.login(sender, password)
                        server.send_message(msg)




                # Show the frame for 2 seconds then close
                cv2.imshow("FaceNet + MTCNN (Missing Person DB)", frame)
                cv2.waitKey(2000)

                match_found = True  # Set flag to exit while loop
                break               # Break out of for loop

            else:
                cv2.putText(frame, f"No Match ({score:.2f})", (x, y-10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

        if match_found:
            break  # Break out of while loop

        cv2.imshow("FaceNet + MTCNN (Missing Person DB)", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("[INFO] Streaming stopped.")
