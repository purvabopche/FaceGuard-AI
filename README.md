# FaceCheck AI - Smart Attendance System

FaceCheck AI is a modern, full-stack Face Recognition Attendance System designed for rapid deployment in educational institutions. Using state-of-the-art LBPH (Local Binary Patterns Histograms) face recognition under the hood, and a beautifully designed glassmorphism dashboard, FaceCheck AI completely digitizes and automates the classroom attendance tracking process.

## 🌟 Key Features

*   **Role-based Dashboards:** Dedicated experiences for Students and Professors.
*   **Automated Face Training:** Students simply click to scan their face, and the neural model trains automatically in the background without any manual interaction!
*   **Live Attendance Tracking:** Professors create custom classes (e.g. `CS101`) and start the tracking session. Attendance is captured automatically and instantly logs to organized CSV spreadsheets.
*   **Premium UI/UX:** Stunning, responsive interface crafted with Vanilla CSS featuring authentic glassmorphism panels, robust transitions, and Phosphor icon integrations.
*   **Localized Data Security:** All biometric datasets, neural models, and attendance sheets are saved logically to local directories, ensuring total data privacy.

## 👥 Pre-configured Users

For testing the platform, use these hardcoded credentials:

### Professor Profile
*   **Email:** `prof@mits.gwl`
*   **Password:** `1234`
*   _Capabilities: Initializing classes, running live tracking feeds, viewing specific date/class attendance records._

### Student Profiles
*   **Email:** `CS24@mits.gwl`
*   **Password:** `1234`
*   _Capabilities: Secure authentication, submitting biometric facial data._

*   **Email:** `CS23@mits.gwl`
*   **Password:** `5678`

## 🚀 Installation & Setup

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/anikettagor2/attendace-.git
    cd attendace-
    ```

2.  **Create a Virtual Environment (Optional but recommended)**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the Flask Application**
    ```bash
    python app.py
    ```

5.  **Access the Platform**
    Open your browser and navigate to `http://127.0.0.1:5000`

## 📁 Project Structure

```
├── app.py                     # Main Backend & Routing Engine
├── requirements.txt           # Python Environment Requirements
├── students.csv               # Automatically updated list of registered students
├── dataset/                   # Directory where raw face captures are securely saved
├── trainer/                   # Directory holding the trained LBPH model (`.yml`)
├── attendance/                # Output directory for daily class attendance sheets
├── static/
│   ├── css/
│   │   └── style.css          # Core Styling Tokens (Glassmorphism UI)
└── templates/
    ├── landing.html           # Project Information & Login Portal
    ├── login.html             # Role-based Authentication Interface
    ├── student_dashboard.html # Biometric Enrolment Interface
    └── professor_dashboard.html # Live Tracker & Records Viewer
```

## 🛠 Tech Stack

*   **Backend:** Python 3, Flask, Pandas, NumPy
*   **AI/Computer Vision:** OpenCV (cv2), Haar Cascades, LBPH Face Recognizer
*   **Frontend:** HTML5, CSS3 (Vanilla), JavaScript
*   **Icons:** Phosphor Web

---

*Engineered for speed, accuracy, and beauty.*
