import os
import cv2
import csv
import time
from datetime import datetime
from flask import Flask, render_template, Response, request, jsonify, session, redirect, url_for
import pandas as pd
import numpy as np

app = Flask(__name__)
app.secret_key = 'super_secret_key_for_attendance'

# Basic Config
DATASET_PATH = 'dataset'
TRAINER_PATH = 'trainer/trainer.yml'
ATTENDANCE_PATH = 'attendance'

for path in [DATASET_PATH, 'trainer', ATTENDANCE_PATH]:
    if not os.path.exists(path):
        os.makedirs(path)

students_file = 'students.csv'
if not os.path.exists(students_file):
    with open(students_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Id', 'Name', 'Email'])

# OpenCV setup
face_detector = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
recognizer = cv2.face.LBPHFaceRecognizer_create()

if os.path.exists(TRAINER_PATH):
    recognizer.read(TRAINER_PATH)

# Global State
class ScannerState:
    def __init__(self):
        self.mode = 'idle' # idle, register, attendance
        self.user_id = ''
        self.user_name = ''
        self.user_email = ''
        self.sample_num = 0
        self.total_samples = 50
        self.registration_complete = False
        self.last_attendance_mark = {}
        self.current_class = 'General'
        
state = ScannerState()
video_capture = None

# Hardcoded Users
USERS = {
    'prof@mits.gwl': {'password': '1234', 'role': 'professor', 'name': 'Professor', 'id': 1},
    'CS24@mits.gwl': {'password': '1234', 'role': 'student', 'name': 'Student CS24', 'id': 24},
    'CS23@mits.gwl': {'password': '5678', 'role': 'student', 'name': 'Student CS23', 'id': 23}
}

def get_student_name(target_id):
    if not os.path.exists(students_file):
        return "Unknown"
    df = pd.read_csv(students_file)
    student = df[df['Id'] == int(target_id)]
    if not student.empty:
        return student.iloc[0]['Name']
    
    # Check current hardcoded memory fallback
    for email, info in USERS.items():
        if info['id'] == target_id:
            return info['name']
            
    return "Unknown"

def mark_attendance(student_id, student_name):
    # check if marked already today
    date_str = datetime.now().strftime("%Y-%m-%d")
    time_str = datetime.now().strftime("%H:%M:%S")
    file_path = os.path.join(ATTENDANCE_PATH, f"Attendance_{state.current_class}_{date_str}.csv")
    
    if not os.path.exists(file_path):
        with open(file_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Id', 'Name', 'Date', 'Time', 'Class'])
            
    df = pd.read_csv(file_path)
    if student_id not in df['Id'].values:
        with open(file_path, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([student_id, student_name, date_str, time_str, state.current_class])
        return True, "Attendance marked successfully"
    return False, "Already marked today"

def do_training():
    image_paths = [os.path.join(DATASET_PATH, f) for f in os.listdir(DATASET_PATH)]
    faces = []
    ids = []
    if not image_paths:
        return
    for image_path in image_paths:
        try:
            face_img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            id_val = int(os.path.split(image_path)[-1].split(".")[1])
            faces.append(face_img)
            ids.append(id_val)
        except Exception:
            continue
    if faces and ids:
        recognizer.train(faces, np.array(ids))
        recognizer.write(TRAINER_PATH)

def generate_frames():
    global video_capture
    if video_capture is None:
        video_capture = cv2.VideoCapture(0)
        
    while True:
        success, img = video_capture.read()
        if not success:
            break
        img = cv2.flip(img, 1)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_detector.detectMultiScale(gray, 1.3, 5)

        for (x,y,w,h) in faces:
            cv2.rectangle(img, (x,y), (x+w,y+h), (0, 255, 200), 2)
            
            if state.mode == 'register':
                state.sample_num += 1
                face_img = gray[y:y+h, x:x+w]
                cv2.imwrite(f"{DATASET_PATH}/User.{state.user_id}.{state.sample_num}.jpg", face_img)
                cv2.putText(img, f"Capturing: {state.sample_num}/{state.total_samples}", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                
                if state.sample_num >= state.total_samples:
                    state.mode = 'idle'
                    state.registration_complete = True
                    # Auto train
                    do_training()

            elif state.mode == 'attendance':
                ids, conf = recognizer.predict(gray[y:y+h, x:x+w])
                if conf < 60:
                    name = get_student_name(ids)
                    status_text = name
                    color = (0, 255, 0)
                    now = time.time()
                    if ids not in state.last_attendance_mark or (now - state.last_attendance_mark[ids] > 10):
                        marked, msg = mark_attendance(ids, name)
                        if marked:
                            state.last_attendance_mark[ids] = now
                            status_text += " (Marked)"
                        else:
                            status_text += " (Already Marked)"
                    else:
                        status_text += " (Already Marked)"
                else:
                    name = "Unknown"
                    status_text = "Unknown Person"
                    color = (0, 0, 255)
                    
                cv2.putText(img, status_text, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

        ret, buffer = cv2.imencode('.jpg', img)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


# --- Routes --- #

def require_login(role=None):
    def wrapper(f):
        def decorated(*args, **kwargs):
            if 'email' not in session:
                return redirect(url_for('login'))
            if role and session.get('role') != role:
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        decorated.__name__ = f.__name__
        return decorated
    return wrapper

@app.route('/')
def landing():
    return render_template('landing.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if email in USERS and USERS[email]['password'] == password:
            session['email'] = email
            session['role'] = USERS[email]['role']
            session['name'] = USERS[email]['name']
            session['id'] = USERS[email]['id']
            
            if session['role'] == 'professor':
                return redirect(url_for('professor_dashboard'))
            else:
                return redirect(url_for('student_dashboard'))
        else:
            error = 'Invalid credentials. Please try again.'
            
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('landing'))

@app.route('/student_dashboard')
@require_login('student')
def student_dashboard():
    return render_template('student_dashboard.html', user=session)

@app.route('/professor_dashboard')
@require_login('professor')
def professor_dashboard():
    return render_template('professor_dashboard.html', user=session)

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/start_register', methods=['POST'])
def start_register():
    if session.get('role') != 'student':
        return jsonify({'error': 'Unauthorized'}), 403
        
    s_id = session.get('id')
    s_name = session.get('name')
    s_email = session.get('email')
        
    # Append to CSV
    df = pd.read_csv(students_file)
    if int(s_id) not in df['Id'].values:
        with open(students_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([s_id, s_name, s_email])
    else:
        df.loc[df['Id'] == int(s_id), 'Name'] = s_name
        df.to_csv(students_file, index=False)
        
    state.user_id = str(s_id)
    state.user_name = s_name
    state.sample_num = 0
    state.registration_complete = False
    state.mode = 'register'
    
    return jsonify({'message': 'Started capturing faces... Please look at the camera.'})

@app.route('/registration_status')
def registration_status():
    if state.registration_complete:
        state.registration_complete = False # reset
        return jsonify({'complete': True, 'message': 'Face registration complete! Model trained automatically.'})
    return jsonify({'complete': False, 'progress': state.sample_num, 'total': state.total_samples})

@app.route('/start_attendance', methods=['POST'])
def start_attendance():
    if session.get('role') != 'professor':
        return jsonify({'error': 'Unauthorized'}), 403
        
    data = request.json or {}
    class_name = data.get('class_name', 'General')
    state.current_class = class_name
        
    if not os.path.exists(TRAINER_PATH):
        return jsonify({'error': 'Model not trained yet! Please register a student first.'}), 400
        
    recognizer.read(TRAINER_PATH)
    state.mode = 'attendance'
    state.last_attendance_mark = {}
    return jsonify({'message': f'Attendance mode activated for {class_name}.'})

@app.route('/stop_camera', methods=['POST'])
def stop_camera():
    global video_capture
    state.mode = 'idle'
    if video_capture is not None:
        video_capture.release()
        video_capture = None
    return jsonify({'message': 'Camera stopped.'})

@app.route('/get_attendance', methods=['GET'])
def get_attendance():
    date_str = request.args.get('date', datetime.now().strftime("%Y-%m-%d"))
    class_name = request.args.get('class_name', 'General')
    
    file_path = os.path.join(ATTENDANCE_PATH, f"Attendance_{class_name}_{date_str}.csv")
    
    if not os.path.exists(file_path):
        return jsonify({'records': []})
        
    df = pd.read_csv(file_path)
    records = df.to_dict('records')
    return jsonify({'records': records})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
