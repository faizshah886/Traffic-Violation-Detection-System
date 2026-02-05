# 🚦 AI-Powered Traffic Violation Detection System

An automated traffic violation detection system powered by **Flask** and **YOLOv8** (You Only Look Once). This system detects helmet violations, triple riding, and red light crossings from video footage, extracts vehicle numbers using **OCR**, and automatically generates PDF challans.

## 🌟 Key Features

*   **Automated Detection**:
    *   ⛑️ **Helmet Violation**: Detects riders without helmets.
    *   🏍️ **Triple Riding**: Detects more than two people on a two-wheeler.
    *   🚦 **Red Light Violation**: Detects vehicles crossing a user-defined stop line during a red light.
*   **License Plate Recognition (ANPR)**: Automatic Number Plate Recognition using OCR to extract vehicle numbers.
*   **Challan Generation**: Automatically generates official-looking PDF challans with evidence images and QR codes.
*   **Web Dashboard**:
    *   User-friendly interface for video uploads.
    *   Interactive canvas to draw stop-lines on video frames.
    *   Dashboard to view, filter, and download generated challans.
*   **Background Processing**: Efficiently processes videos in the background using threading.

## 🛠️ Technology Stack

*   **Backend**: Python, Flask, SQLite
*   **AI/ML**: YOLOv8 (Ultralytics), OpenCV
*   **OCR**: EasyOCR
*   **Frontend**: HTML5, Bootstrap 5, Javascript
*   **Utilities**: ReportLab (PDF), Qrcode

## 🚀 Installation & Setup

### Prerequisites
*   Python 3.8 or higher
*   Git

### 1. Clone the Repository
```bash
git clone <repository-url>
cd traffic
```

### 2. Install Dependencies
**Windows:**
```bash
setup.bat
```

**Linux / macOS:**
```bash
chmod +x setup.sh
./setup.sh
```

**Manual Installation:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python app/database.py    # Initialize database
```

### 3. Run the Application
```bash
python app/main.py
```
The application will start at `http://localhost:5000`.

## 📖 How to Use

1.  **Upload Video**: Navigate to the homepage and upload a traffic surveillance video (MP4, AVI, etc.).
2.  **Configure Stop Line**:
    *   Upon upload, you will be prompted to draw a stop line on a video frame.
    *   This line is used to detect red light violations.
3.  **Processing**: The system will process the video in the background. You can track progress on the dashboard.
4.  **View Challans**: Go to the **Challans** page to view detected violations.
5.  **Download**: Click on a challan to view details and download the official PDF citation.

## 📂 Project Structure

```
traffic/
├── app/
│   ├── main.py            # Flask application entry point
│   ├── detector.py        # YOLOv8 detection logic
│   ├── anpr.py            # OCR / Number plate recognition
│   ├── chalgen.py         # PDF Challan generator
│   ├── database.py        # Database models & initialization
│   ├── worker.py          # Background processing worker
│   ├── models.py          # Data models
│   ├── static/            # CSS, JS, images
│   └── templates/         # HTML templates
├── yolo/                  # YOLO models
├── requirements.txt       # Project dependencies
├── setup.bat              # Windows setup script
├── setup.sh               # Linux/macOS setup script
└── README.md              # Project documentation
```

## 🔌 API Endpoints

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/` | GET | Application Homepage |
| `/upload` | POST | Upload video for processing |
| `/challans` | GET | View all generated challans |
| `/challan/<id>/pdf` | GET | Download Challan PDF |
| `/api/status` | GET | Check system status |

## 🛡️ License

This project is open-source and available under the [MIT License](LICENSE).
