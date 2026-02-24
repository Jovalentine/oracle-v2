import os
import uuid, traceback, tempfile
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory, send_file
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from core.db import MongoDB
from core.gemini_pipeline import GeminiForensicPipeline
from core.pdf_generator import generate_case_pdf


# Initialize Environment & Flask
load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "fallback_dev_key")

# Setup Directories
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/tmp/uploads")
REPORT_DIR = os.getenv("REPORT_DIR", "/tmp/reports")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)

# Initialize Database
db = MongoDB()

# Initialize AI Engine
try:
    ai_engine = GeminiForensicPipeline()
    print("✅ Gemini AI Engine Initialized")
except Exception as e:
    print("\n" + "="*50)
    print("🚨 AI ENGINE FAILED TO START 🚨")
    print("="*50)
    traceback.print_exc()
    print("="*50 + "\n")
    ai_engine = None

# -----------------------------------
# AUTHENTICATION ROUTES
# -----------------------------------

@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    if "user" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        u = request.form.get("username")
        p = request.form.get("password")

        if db.get_user(u, p):
            session["user"] = u
            return redirect(url_for("dashboard"))

        flash("Invalid credentials.", "error")

    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if "user" in session:
        return redirect(url_for("dashboard"))
        
    if request.method == "POST":
        u = request.form.get("username")
        p = request.form.get("password")
        confirm_p = request.form.get("confirm_password")

        if p != confirm_p:
            flash("Passwords do not match.", "error")
            return redirect(url_for("register"))
            
        if db.users.find_one({"username": u}):
            flash("Username already exists.", "error")
        else:
            db.create_user(u, p)
            flash("Registered successfully! Please login.", "success")
            return redirect(url_for("login"))
            
    return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# -----------------------------------
# CORE APPLICATION ROUTES
# -----------------------------------

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        flash("Please log in to view your dashboard.", "error")
        return redirect(url_for("login"))
    
    # Fetch real cases from MongoDB sorted by newest first
    user_cases = db.get_cases_by_user(session["user"])
    return render_template("dashboard.html", username=session["user"], cases=user_cases)

@app.route("/new", methods=["GET", "POST"])
def new_case():
    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        if 'image' not in request.files:
            flash("No file part", "error")
            return redirect(request.url)
            
        file = request.files['image']
        if file.filename == '':
            flash("No selected file", "error")
            return redirect(request.url)

        if file:
            # 1. Save File securely
            filename = secure_filename(f"{uuid.uuid4().hex[:8]}_{file.filename}")
            filepath = os.path.join(UPLOAD_DIR, filename)
            file.save(filepath)

            # 2. Run Gemini AI Analysis
            try:
                print(f"🕵️ Analyzing {filename} with Gemini...")
                analysis_result = ai_engine.analyze_image(filepath)
                
                # 3. Save to MongoDB
                case_id = uuid.uuid4().hex[:8]
                case_data = {
                    "case_id": case_id,
                    "user": session["user"],
                    "type": "image",
                    "filename": filename,
                    "analysis": analysis_result 
                }
                db.save_case(case_data)
                
                flash("Forensic analysis complete.", "success")
                return redirect(url_for("view_case", case_id=case_id)) 

            except Exception as e:
                print(f"Analysis Failed: {e}")
                flash(f"AI Analysis Failed: {str(e)}", "error")
                return redirect(request.url)

    return render_template("new_case.html")

# -----------------------------------
# REPORT & ASSET ROUTES
# -----------------------------------

@app.route("/case/<case_id>")
def view_case(case_id):
    if "user" not in session:
        return redirect(url_for("login"))
    
    case_data = db.get_case(case_id, session["user"])
    if not case_data:
        flash("Case not found or access denied.", "error")
        return redirect(url_for("dashboard"))
        
    return render_template("report.html", case=case_data)

@app.route("/export/<case_id>")
def export_pdf(case_id):
    if "user" not in session:
        return redirect(url_for("login"))
    
    case_data = db.get_case(case_id, session["user"])
    if not case_data:
        flash("Case not found.", "error")
        return redirect(url_for("dashboard"))
    
    # Generate PDF
    pdf_path = generate_case_pdf(case_data, UPLOAD_DIR, REPORT_DIR)
    
    # Send to user to download
    return send_file(pdf_path, as_attachment=True)

# -----------------------------------
# VIDEO ANALYSIS ROUTE 
# -----------------------------------

# Add this near the top of app.py to help with security
ALLOWED_VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv'}

def allowed_video(filename):
    return os.path.splitext(filename.lower())[1] in ALLOWED_VIDEO_EXTENSIONS

# ...

@app.route("/new-video", methods=["GET", "POST"])
def new_video_case():
    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        if 'video' not in request.files:
            flash("No file part", "error")
            return redirect(request.url)
            
        file = request.files['video']
        if file.filename == '' or not allowed_video(file.filename):
            flash("Invalid or missing video file", "error")
            return redirect(request.url)

        if file:
            # 1. Save Video
            filename = secure_filename(f"{uuid.uuid4().hex[:8]}_{file.filename}")
            filepath = os.path.join(UPLOAD_DIR, filename)
            file.save(filepath)

            # 2. Run Gemini Video Analysis
            try:
                print(f"🕵️ Analyzing Video {filename} with Gemini...")
                analysis_result = ai_engine.analyze_video(filepath)
                
                # 3. Save to MongoDB
                case_id = uuid.uuid4().hex[:8]
                case_data = {
                    "case_id": case_id,
                    "user": session["user"],
                    "type": "video",  # Marking this as a video case
                    "filename": filename,
                    "analysis": analysis_result 
                }
                db.save_case(case_data)
                
                flash("Video forensic analysis complete.", "success")
                return redirect(url_for("view_case", case_id=case_id)) 

            except Exception as e:
                print(f"Video Analysis Failed: {e}")
                flash(f"AI Analysis Failed: {str(e)}", "error")
                return redirect(request.url)

    return render_template("new_video_case.html")
@app.route("/delete/<case_id>", methods=["POST"])
def delete_case(case_id):
    if "user" not in session:
        return redirect(url_for("login"))
    
    # 1. Get the case to find the filename
    case_data = db.get_case(case_id, session["user"])
    
    if case_data:
        # 2. Delete the physical file from the uploads folder
        file_path = os.path.join(UPLOAD_DIR, case_data.get("filename", ""))
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError as e:
                print(f"Error deleting file: {e}")
                
        # 3. Delete the record from MongoDB
        db.cases.delete_one({"case_id": case_id, "user": session["user"]})
        flash("Evidence and case file permanently deleted.", "success")
    else:
        flash("Case not found or unauthorized.", "error")
        
    return redirect(url_for("dashboard"))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    # Route to serve the raw images for the frontend to display
    return send_from_directory(UPLOAD_DIR, filename)

if __name__ == "__main__":
    app.run(port=5001, debug=True)