Markdown
# 👁️ Oracle Forensic System v2.0

An AI-powered digital forensic investigation portal designed to analyze traffic accident scenes using dashcam/CCTV footage and static images. Built with Python, Flask, MongoDB, and Google's advanced Gemini 2.5 Flash multimodal AI.

## 🚀 Project Overview
Oracle Forensic is a full-stack web application built to assist digital forensic investigators. By uploading visual evidence of a traffic collision, the system utilizes generative AI to reconstruct the scene, allocate fault percentages, detect pedestrians, and generate a chronological event timeline. 

This project transitions complex, multi-model pipelines into a lightning-fast, single-engine architecture using Native Multimodal Sequence Processing.

## ✨ Key Features
* **Multimodal Evidence Processing:** Natively supports both static crash images (`.jpg`, `.png`) and video footage (`.mp4`, `.mov`) via OpenCV temporal keyframe extraction.
* **AI Reconstruction Engine:** Powered by `gemini-2.5-flash` with custom-tuned safety thresholds for forensic analysis.
* **Official PDF Dossiers:** Dynamically generates professional, branded PDF reports containing evidence thumbnails, telemetry tables, and investigative narratives using `ReportLab`.
* **Resilient Investigator Dashboard:** A glassmorphic UI that safely handles asynchronous data, categorizes cases, and features an animated multi-color fault allocation UI.
* **Dynamic Theming:** Seamless, zero-reload toggling between Dark Mode and Light Mode with `localStorage` preference saving.
* **Secure Architecture:** Built-in user authentication, encrypted session management, and persistent MongoDB storage.

## 🛠️ Technology Stack
* **Backend:** Python 3, Flask, Werkzeug
* **Database:** MongoDB (PyMongo)
* **AI / ML:** Google GenAI SDK (`gemini-2.5-flash`), OpenCV (Computer Vision)
* **Document Generation:** ReportLab
* **Frontend:** HTML5, CSS3 (CSS Variables, Flexbox/Grid), Vanilla JavaScript

## ⚙️ Local Installation & Setup

**1. Clone the repository**

```bash
git clone https://github.com/yourusername/oracle-forensic.git
cd oracle-forensic
2. Create a virtual environment

Bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
3. Install dependencies

Bash
pip install -r requirements.txt
4. Environment Variables

Create a .env file in the root directory and add your credentials:

Ini, TOML
SECRET_KEY=your_super_secret_flask_key
MONGO_URI=mongodb+srv://<username>:<password>@cluster.mongodb.net/oracle_forensic
GEMINI_API_KEY=your_google_gemini_api_key
UPLOAD_DIR=/tmp/uploads
REPORT_DIR=/tmp/reports
5. Run the Application

Bash
python app.py
The application will be live at http://127.0.0.1:5001.

👨‍💻 Author
Francis Johan M. Final Year Engineering Project (2026)