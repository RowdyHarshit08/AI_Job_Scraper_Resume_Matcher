import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

from services.resume_parser import extract_resume
from services.matcher import match_resume_to_job
from services.ai_analyzer import ai_analyze

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-me")
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
UPLOAD_DIR = os.path.join(app.root_path, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
DB_PATH = os.path.join(app.root_path, "database.db")
ALLOWED = {"pdf", "docx"}

DEMO_JOBS = [
    ("Python Developer Intern", "TechNova Demo", "Remote", "Build Python services and APIs. Work with SQL, Git, REST APIs and basic testing.", "Python, SQL, REST API, Git", "0-1 years", "https://example.com/jobs/python-developer-intern"),
    ("Data Analyst Intern", "DataBridge Demo", "Noida, India", "Analyze datasets using Python, Pandas and SQL. Create reports and dashboards and communicate insights.", "Python, Pandas, SQL, Excel, Data Analysis", "0-1 years", "https://example.com/jobs/data-analyst-intern"),
    ("Machine Learning Intern", "AIWorks Demo", "Bengaluru, India", "Assist with machine learning experiments, data preprocessing, model evaluation and Python development.", "Python, Machine Learning, Pandas, Scikit-learn, Statistics", "0-1 years", "https://example.com/jobs/ml-intern"),
    ("AI/ML Intern", "NeuralLab Demo", "Remote", "Support AI prototypes using Python, machine learning concepts, NLP and model evaluation.", "Python, AI, Machine Learning, NLP, Git", "0-1 years", "https://example.com/jobs/ai-ml-intern"),
    ("Backend Developer Intern", "CodeCraft Demo", "Pune, India", "Develop backend applications using Python, Flask/Django, databases and REST APIs.", "Python, Flask, Django, SQL, REST API", "0-1 years", "https://example.com/jobs/backend-intern"),
    ("Software Engineer Intern", "DevSphere Demo", "Gurugram, India", "Work on software features, debugging, data structures and algorithms using Java or Python.", "Java, Python, DSA, Git, SQL", "0-1 years", "https://example.com/jobs/software-engineer-intern"),
    ("Cloud Data Engineer Trainee", "CloudCore Demo", "Hyderabad, India", "Assist with ETL pipelines, SQL, data processing and cloud data engineering workflows.", "SQL, Python, ETL, Cloud, Data Engineering", "0-1 years", "https://example.com/jobs/cloud-data-engineer"),
    ("Full Stack Developer Intern", "WebForge Demo", "Remote", "Build responsive web applications with HTML, CSS, JavaScript and Python backend frameworks.", "HTML, CSS, JavaScript, Python, Django, MongoDB", "0-1 years", "https://example.com/jobs/full-stack-intern"),
    ("Junior Data Scientist", "InsightWorks Demo", "Mumbai, India", "Prepare data, build predictive models and communicate findings using Python and machine learning.", "Python, Pandas, Scikit-learn, SQL, Machine Learning", "0-1 years", "https://example.com/jobs/junior-data-scientist"),
    ("Python + Django Intern", "AppNest Demo", "Remote", "Create web features using Django, Python, databases and frontend technologies.", "Python, Django, SQL, HTML, CSS, Git", "0-1 years", "https://example.com/jobs/django-intern"),
]

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, company TEXT NOT NULL,
        location TEXT, description TEXT, skills TEXT, experience TEXT, url TEXT,
        source TEXT, created_at TEXT, UNIQUE(title, company, location))""")
    conn.execute("""CREATE TABLE IF NOT EXISTS resumes (
        id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT, text TEXT, skills TEXT,
        uploaded_at TEXT)""")
    conn.commit()
    count = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    if count == 0:
        now = datetime.now().isoformat(timespec="seconds")
        conn.executemany("""INSERT OR IGNORE INTO jobs
            (title, company, location, description, skills, experience, url, source, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'Demo Dataset', ?)""",
            [(a,b,c,d,e,f,g,now) for a,b,c,d,e,f,g in DEMO_JOBS])
        conn.commit()
    conn.close()

@app.route("/")
def index():
    conn = get_db()
    job_count = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    conn.close()
    return render_template("index.html", job_count=job_count)

@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "GET":
        return render_template("upload.html")
    file = request.files.get("resume")
    if not file or not file.filename:
        flash("Please select a PDF or DOCX resume.", "danger")
        return redirect(url_for("upload"))
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED:
        flash("Only PDF and DOCX files are supported.", "danger")
        return redirect(url_for("upload"))
    filename = secure_filename(file.filename)
    path = os.path.join(UPLOAD_DIR, filename)
    file.save(path)
    try:
        text, info = extract_resume(path)
    except Exception as e:
        flash("Resume could not be processed. Please try another PDF/DOCX.", "danger")
        return redirect(url_for("upload"))
    if not text.strip():
        flash("Readable text not found. Please upload a text-based PDF/DOCX. Scanned/image PDFs need OCR.", "warning")
        return redirect(url_for("upload"))
    conn = get_db()
    cur = conn.execute("INSERT INTO resumes(filename,text,skills,uploaded_at) VALUES(?,?,?,?)",
                       (filename, text, ", ".join(info["skills"]), datetime.now().isoformat(timespec="seconds")))
    resume_id = cur.lastrowid
    conn.commit()
    conn.close()
    return redirect(url_for("jobs", resume_id=resume_id))

@app.route("/jobs")
def jobs():
    resume_id = request.args.get("resume_id", type=int)
    q = request.args.get("q", "").strip()
    location = request.args.get("location", "").strip()
    conn = get_db()
    resume = conn.execute("SELECT * FROM resumes WHERE id=?", (resume_id,)).fetchone() if resume_id else conn.execute("SELECT * FROM resumes ORDER BY id DESC LIMIT 1").fetchone()
    sql = "SELECT * FROM jobs WHERE 1=1"
    params=[]
    if q:
        sql += " AND (title LIKE ? OR company LIKE ? OR description LIKE ? OR skills LIKE ?)"
        params += [f"%{q}%"]*4
    if location:
        sql += " AND location LIKE ?"
        params.append(f"%{location}%")
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    results=[]
    for job in rows:
        score_data = match_resume_to_job(resume["text"], dict(job)) if resume else {"score":0,"matching_skills":[],"missing_skills":[],"similarity":0}
        item=dict(job); item.update(score_data); results.append(item)
    results.sort(key=lambda x:x["score"], reverse=True)
    return render_template("jobs.html", jobs=results, resume=resume, q=q, location=location)

@app.route("/job/<int:job_id>")
def job_details(job_id):
    resume_id=request.args.get("resume_id", type=int)
    conn=get_db()
    job=conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    resume=conn.execute("SELECT * FROM resumes WHERE id=?", (resume_id,)).fetchone() if resume_id else conn.execute("SELECT * FROM resumes ORDER BY id DESC LIMIT 1").fetchone()
    conn.close()
    if not job: return "Job not found",404
    data=match_resume_to_job(resume["text"],dict(job)) if resume else {"score":0,"matching_skills":[],"missing_skills":[],"similarity":0}
    ai=ai_analyze(resume["text"], dict(job), data) if resume else {"summary":"Upload a resume to get personalized analysis.","strengths":[],"recommendations":[],"matching_skills":data["matching_skills"],"missing_skills":data["missing_skills"],"score":data["score"],"source":"local"}
    return render_template("job_details.html", job=dict(job), resume=resume, match=data, ai=ai)

@app.route("/api/match/<int:job_id>")
def api_match(job_id):
    conn=get_db()
    job=conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    resume=conn.execute("SELECT * FROM resumes ORDER BY id DESC LIMIT 1").fetchone()
    conn.close()
    if not job or not resume: return jsonify({"error":"Upload a resume first."}),400
    data=match_resume_to_job(resume["text"],dict(job))
    return jsonify(data)

@app.errorhandler(413)
def too_large(_):
    flash("File is too large. Maximum size is 5 MB.", "danger")
    return redirect(url_for("upload"))

init_db()
if __name__ == "__main__":
    app.run(debug=True)
