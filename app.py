import os
import cv2
import mediapipe as mp
import numpy as np
from flask import Flask, render_template, Response, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from dotenv import load_dotenv
from models import db, User
import time
import requests  # For sending messages via Telegram
import pygame
import threading

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Initialize MediaPipe Face Mesh
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# Constants for eye landmarks
LEFT_EYE = [362, 385, 387, 263, 373, 380]
RIGHT_EYE = [33, 160, 158, 133, 153, 144]

# Constants
EYE_AR_THRESH = float(os.getenv('EYE_AR_THRESH', 0.30))  # Lowered for easier detection
EYE_AR_CONSEC_FRAMES = int(os.getenv('EYE_AR_CONSEC_FRAMES', 60))  # About 2 seconds at 30 fps
COUNTER = 0
ALARM_ON = False
last_alert_time = 0
ALERT_COOLDOWN = 60  # Cooldown period between alerts (seconds)

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '7853720483:AAGZe2hS0VlOoYnuUZiqX6B2qMEY6fEGdJI')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '7014613370')
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

# Alarm sound setup
ALARM_SOUND_PATH = os.path.join(os.path.dirname(__file__), 'alarm.mp3')

def play_alarm():
    try:
        pygame.mixer.init()
        pygame.mixer.music.load(ALARM_SOUND_PATH)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pass
    except Exception as e:
        print(f'Error playing alarm sound: {e}')

def eye_aspect_ratio(landmarks, eye_indices):
    # Extract the 6 eye points in the correct order
    points = np.array([[landmarks[i].x, landmarks[i].y] for i in eye_indices])
    # For debugging: print the points
    print(f"Eye points ({eye_indices}):", points)
    # Compute distances
    A = np.linalg.norm(points[1] - points[5])  # vertical
    B = np.linalg.norm(points[2] - points[4])  # vertical
    C = np.linalg.norm(points[0] - points[3])  # horizontal
    ear = (A + B) / (2.0 * C)
    return ear

def send_alert():
    global last_alert_time
    current_time = time.time()
    if current_time - last_alert_time >= ALERT_COOLDOWN:
        try:
            print("Sending Telegram alert...")
            message = "ALERT: Driver drowsiness detected! The driver appears to be drowsy or falling asleep."
            response = requests.post(TELEGRAM_API_URL, data={
                'chat_id': TELEGRAM_CHAT_ID,
                'text': message
            })
            print("Telegram response:", response.status_code, response.text)
            if response.status_code == 200:
                print("Alert sent successfully to Telegram!")
                last_alert_time = current_time
            else:
                print(f"Failed to send alert. Status code: {response.status_code}")
                print(f"Error: {response.text}")
        except Exception as e:
            print(f"Error sending alert: {str(e)}")
            print("Please check your Telegram bot configuration.")

def send_alert_and_alarm():
    # Send Telegram alert
    send_alert()
    # Play alarm sound in a separate thread so it doesn't block
    threading.Thread(target=play_alarm, daemon=True).start()

def detect_drowsiness(frame):
    global COUNTER, ALARM_ON
    
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb_frame)
    
    if results.multi_face_landmarks:
        print("Face detected!")
        for face_landmarks in results.multi_face_landmarks:
            left_ear = eye_aspect_ratio(face_landmarks.landmark, LEFT_EYE)
            right_ear = eye_aspect_ratio(face_landmarks.landmark, RIGHT_EYE)
            ear = (left_ear + right_ear) / 2.0
            print(f"Left EAR: {left_ear:.3f}, Right EAR: {right_ear:.3f}, Avg EAR: {ear:.3f}, COUNTER: {COUNTER}, ALARM_ON: {ALARM_ON}")
            
            height, width = frame.shape[:2]
            for eye in [LEFT_EYE, RIGHT_EYE]:
                points = []
                for i in eye:
                    x = int(face_landmarks.landmark[i].x * width)
                    y = int(face_landmarks.landmark[i].y * height)
                    points.append([x, y])
                points = np.array(points, dtype=np.int32)
                cv2.polylines(frame, [points], True, (0, 255, 0), 1)
            
            if ear < EYE_AR_THRESH:
                COUNTER += 1
                print(f"EAR below threshold! Counter: {COUNTER}")
                if COUNTER >= EYE_AR_CONSEC_FRAMES and not ALARM_ON:
                    print("Drowsiness detected! Triggering alert and alarm.")
                    ALARM_ON = True
                    send_alert_and_alarm()
                    cv2.putText(frame, "DROWSINESS ALERT!", (10, 30),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            else:
                if COUNTER != 0:
                    print("EAR above threshold, resetting counter and alarm.")
                COUNTER = 0
                ALARM_ON = False
                
            # Display counter when eyes are closed
            if COUNTER > 0:
                seconds = COUNTER / 30  # Assuming 30 fps
                cv2.putText(frame, f"Eyes Closed: {seconds:.1f}s", (10, 60),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    else:
        print("No face detected!")
    
    return frame

def gen_frames():
    cap = cv2.VideoCapture(0)
    while True:
        success, frame = cap.read()
        if not success:
            break
        else:
            frame = detect_drowsiness(frame)
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    if current_user.is_authenticated:
        return render_template('dashboard.html')
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        emergency_contact = request.form.get('emergency_contact')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))
        
        user = User(username=username, emergency_contact=emergency_contact)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/video_feed')
@login_required
def video_feed():
    return Response(gen_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/update_contact', methods=['POST'])
@login_required
def update_contact():
    emergency_contact = request.form.get('emergency_contact')
    if emergency_contact:
        current_user.emergency_contact = emergency_contact
        db.session.commit()
        flash('Emergency contact updated successfully')
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
