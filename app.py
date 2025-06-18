from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, session
import cv2
import base64
import pickle
import numpy as np
import face_recognition
from datetime import datetime
import os
from utils import send_email_alert, recognize

app = Flask(__name__)

# Configuration
app.secret_key = "admin"  # Required for session management
ADMIN_PASSWORD = "admin"  # Replace with your secure password
ENCODING_FILE = 'EncodeFile.p'
DB_DIR = './DB'
log_path = './log.txt'
log_dir = './log'
EMAIL_SUBJECT = "Unknown Alert"
EMAIL_MESSAGE_IN = "Alert: Unknown Person is trying to login"
EMAIL_MESSAGE_OUT = "Alert: Unknown Person is trying to logout"

# Load the encoding file
if os.path.exists(ENCODING_FILE):
    # print("Loading Encode File ...")
    with open(ENCODING_FILE, 'rb') as file:
        encodeListKnownWithIds = pickle.load(file)
    encodeListKnown, studentIds = encodeListKnownWithIds
    # print("Encode File Loaded")
else:
    encodeListKnown, studentIds = [], []
    print("Encoding file not found. Starting fresh.")

# Route for homepage
@app.route('/')
def index():
    session.pop("authenticated", None)  # Remove authentication session
    return render_template('index.html')

#Password verification for admin
@app.route('/', methods=['POST'])
def check_admin():
    try:
        data = request.json
        password = data.get('password', ' ').strip()
        if password != ADMIN_PASSWORD:
            print("Incorrect Pin.")
            return jsonify({"status": "fail", "message": "Incorrect Pin."})
        if password == ADMIN_PASSWORD:
            # Store authentication flag in session
            session["authenticated"] = True
            return jsonify({"status": "success", "message": "Correct Pin."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

# Route for login
@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.json['image']
        img_data = base64.b64decode(data.split(',')[1])
        np_arr = np.frombuffer(img_data, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        name = recognize(frame, DB_DIR)        
        try:
            with open(log_path, 'r') as log_file:
                lines = log_file.readlines()
        except FileNotFoundError:
            lines = []

        last_entry = None

        if lines:
            # Reverse iterate to find the most recent log entry for the user
            for line in reversed(lines):
                if name in line.split(',')[0]:  # Match only the ID (name)
                    last_entry = line.strip()
                    break

        latest_time = None
        status = None
        seconds_elapsed = None

        if last_entry:
            try:
                user, timestamp, status = last_entry.split(',')
                latest_time = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S.%f")
            except Exception as e:
                print("Error parsing log entry:", e)

        if latest_time:
            seconds_elapsed = (datetime.now() - latest_time).total_seconds()
            # print(f"Seconds elapsed since last login for {name}: {seconds_elapsed:.2f}")

        if status == 'in' and seconds_elapsed is not None and seconds_elapsed < 20:
            return jsonify({"status": "fail", "message": "You are already logged in."})
        else:
             # label = test(
             # image=self.most_recent_capture_arr,
             # model_dir='C:/Users/Admin/Downloads/FaceRecognition/face-attendance-system-master/Silent-Face-Anti-Spoofing-master/resources/anti_spoof_models',
             # device_id=0
             # )

            label = 1  

            if label == 1:
                if name == 'no_person_found':
                    return jsonify({"status": "fail", "message": "No face detected. Please try again."})
                elif name == 'unknown_person':
                    # Save the intruder's image to the log directory
                    cv2.imwrite(os.path.join(log_dir, 'Unknown_login.jpg'), frame)
                    send_email_alert(EMAIL_SUBJECT, EMAIL_MESSAGE_IN)
                    print(f"Email sent for Unknown Person.")
                    return jsonify({"status": "fail", "message": "Unknown face detected."})
                else:
                    # Save the user's image to the log directory 
                    cv2.imwrite(os.path.join(log_dir, '{}_in.jpg'.format(name)), frame)
                    #self.alert_sent = False
                    ##print("No unknown detected.")
                    try:
                        with open(log_path, 'a') as log_file:
                            log_file.write(f'{name},{datetime.now()},in\n')
                    except Exception as e:
                        print("Error writing to log file:", e)
                    return jsonify({"status": "success", "message": f"Welcome, {name}!"})      
            else:
                return jsonify({"status": "fail", "message": "It is a spoof"})
            
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})
        

# Route for logout
@app.route('/logout', methods=['POST'])
def logout():
    try:
        data = request.json['image']
        img_data = base64.b64decode(data.split(',')[1])
        np_arr = np.frombuffer(img_data, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        name = recognize(frame, DB_DIR)        
        try:
            with open(log_path, 'r') as log_file:
                lines = log_file.readlines()
        except FileNotFoundError:
            lines = []

        last_entry = None

        if lines:
            # Reverse iterate to find the most recent log entry for the user
            for line in reversed(lines):
                if name in line.split(',')[0]:  # Match only the ID (name)
                    last_entry = line.strip()
                    break

        latest_time = None
        status = None
        seconds_elapsed = None

        if last_entry:
            try:
                user, timestamp, status = last_entry.split(',')
                latest_time = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S.%f")
            except Exception as e:
                print("Error parsing log entry:", e)

        if latest_time:
            seconds_elapsed = (datetime.now() - latest_time).total_seconds()
            #print(f"Seconds elapsed since last login for {name}: {seconds_elapsed:.2f}")

        if status == 'out' and seconds_elapsed is not None and seconds_elapsed < 20:
            return jsonify({"status": "fail", "message": "You are already logged out, Please login."})
        else:
             # label = test(
             # image=self.most_recent_capture_arr,
             # model_dir='C:/Users/Admin/Downloads/FaceRecognition/face-attendance-system-master/Silent-Face-Anti-Spoofing-master/resources/anti_spoof_models',
             # device_id=0
             # )

            label = 1  

            if label == 1:
                if name == 'no_person_found':
                    return jsonify({"status": "fail", "message": "No face detected. Please try again."})
                elif name == 'unknown_person':
                    # Save the intruder's image to the log directory
                    cv2.imwrite(os.path.join(log_dir, 'Unknown_logout.jpg'), frame)
                    send_email_alert(EMAIL_SUBJECT, EMAIL_MESSAGE_OUT)
                    print(f"Email sent for Unknown Person.")
                    return jsonify({"status": "fail", "message": "Unknown face detected."})
                else:
                    # Save the user's image to the log directory 
                    cv2.imwrite(os.path.join(log_dir, '{}_out.jpg'.format(name)), frame)
                    #self.alert_sent = False
                    ##print("No unknown detected.")
                    try:
                        with open(log_path, 'a') as log_file:
                            log_file.write(f'{name},{datetime.now()},out\n')
                    except Exception as e:
                        print("Error writing to log file:", e)
                    return jsonify({"status": "success", "message": f"{name} you have been successfully logged out."})      
            else:
                return jsonify({"status": "fail", "message": "It is a spoof"})
            
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

# Route for add-user page
@app.route('/add-user')
def add_user_page():
    if not session.get("authenticated"):  
        return redirect(url_for("index"))  # Redirect to home if not authenticated
    return render_template('add_user.html')

# Route for registering a new user
@app.route('/add-user', methods=['POST'])
def add_user():
    try:
        data = request.json
        image = data.get('image')
        username = data.get('username', ' ').strip()

        if not username:
            return jsonify({"status": "fail", "message": "Username cannot be empty."})

        img_data = base64.b64decode(image.split(',')[1])
        np_arr = np.frombuffer(img_data, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        name = recognize(frame, DB_DIR)
        if name == 'no_person_found':
            return jsonify({"status": "fail", "message": "No face detected. Please try again."})
        elif name == 'unknown_person':
            if not os.path.exists(DB_DIR):
                os.mkdir(DB_DIR)

            user_image_path = os.path.join(DB_DIR, f"{username}.jpg")
            cv2.imwrite(user_image_path, frame)

            img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            encoding = face_recognition.face_encodings(img)[0]

            encodeListKnown.append(encoding)
            studentIds.append(username)

            with open(ENCODING_FILE, 'wb') as file:
                pickle.dump([encodeListKnown, studentIds], file)

            return jsonify({"status": "success", "message": f"User '{username}' registered successfully!"})
        else:
            return jsonify({"status": "fail", "message": "You are already registered."})
    # except IndexError:
    #     return jsonify({"status": "fail", "message": "No face detected. Please try again."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

# Route for downloading logs
@app.route('/download-log')
def download_log():
    log_path = './log.txt'
    if os.path.exists(log_path):
        return send_file(log_path, as_attachment=True, download_name='log.txt') #remove download_name if gives any erroe
    else:
        return jsonify({"status": "fail", "message": "Log file not found."}), 404

if __name__ == '__main__':
    app.run(debug=True)