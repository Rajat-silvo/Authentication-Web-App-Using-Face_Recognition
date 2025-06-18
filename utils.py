import smtplib
from email.message import EmailMessage
import face_recognition
import cv2
import pickle
import numpy as np

SENDER_EMAIL= "xyz@gmail.com"  # Replace with sender's email address
ALERT_EMAIL = "abc@gmail.com"  # Replace with receiver's email address
EMAIL_PASSWORD = 'yourAppPassword'#create app password by going to google account settings and by searching app password


def send_email_alert(subject, body):
    """Sends an email alert."""
    try:
        msg = EmailMessage()
        msg.set_content(body)
        msg['Subject'] = subject
        msg['From'] = SENDER_EMAIL
        msg['To'] = ALERT_EMAIL

        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(SENDER_EMAIL, EMAIL_PASSWORD)
            server.send_message(msg)
        print("Email alert sent.")
    except Exception as e:
        print(f"Failed to send email: {e}")

def recognize(frame, db_path):
    embeddings_unknown = face_recognition.face_encodings(frame)
    if len(embeddings_unknown) == 0:
        return 'no_person_found'                  
    else: 
        # Load the encoding file
        #print("Loading Encode File ...")
        file = open('EncodeFile.p', 'rb')
        encodeListKnownWithIds = pickle.load(file)
        file.close()
        encodeListKnown, studentIds = encodeListKnownWithIds
        # print(studentIds)
        #print("Encode File Loaded")

        imgS = cv2.resize(frame, (0, 0), None, 0.25, 0.25)
        imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

        faceCurFrame = face_recognition.face_locations(imgS)
        encodeCurFrame = face_recognition.face_encodings(imgS, faceCurFrame)

        if faceCurFrame:
            for encodeFace, faceLoc in zip(encodeCurFrame, faceCurFrame):
                matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
                faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)
                matchIndex = np.argmin(faceDis)
                try:
                    if matches[matchIndex]:
                        if faceDis[matchIndex]<=0.5:
                            return studentIds[matchIndex]
                        else:
                            return 'unknown_person'
                    else:
                        return 'unknown_person'
                except Exception as e:
                    return 'no_person_found'

                # if faceDis[matchIndex]<=0.5:
                # #if matches[matchIndex]:
                #     return studentIds[matchIndex]
                # else:
                #     return 'unknown_person'