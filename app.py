import os
import sqlite3
from datetime import datetime

from flask import Flask, render_template, request
from services.resume_parser import extract_resume
from services.matcher import match_resume_to_job
from services.ai_analyzer import analyze_job_with_ai


app = Flask(__name__)

app.secret_key = "ai-job-scraper-secret-key"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024


def get_db_connection():
    db_path = os.path.join(BASE_DIR, "database.db")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    return conn


def initialize_database():

    conn = get_db_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            location TEXT,
            description TEXT,
            skills TEXT,
            experience TEXT,
            url TEXT,
            source TEXT,
            created_at TEXT,
            UNIQUE(title, company, location)
        )
    """)

    jobs = [
        (
            "Python + Django Intern",
            "AppNest Demo",
            "Remote",
            "Create web features using Django, Python, databases and frontend technologies.",
            "Python, Django, SQL, HTML, CSS, Git",
            "0-1 years",
            "https://example.com/jobs/django-intern",
            "Dataset"
        ),
        (
            "Junior Data Scientist",
            "InsightWorks Demo",
            "Mumbai, India",
            "Prepare data, build predictive models and communicate findings using Python and machine learning.",
            "Python, Pandas, Scikit-learn, SQL, Machine Learning",
            "0-1 years",
            "https://example.com/jobs/junior-data-scientist",
            "Dataset"
        ),
        (
            "Full Stack Developer Intern",
            "WebForge Demo",
            "Remote",
            "Build responsive web applications with HTML, CSS, JavaScript and Python backend frameworks.",
            "HTML, CSS, JavaScript, Python, Django, MongoDB",
            "0-1 years",
            "https://example.com/jobs/full-stack-intern",
            "Dataset"
        ),
        (
            "Cloud Data Engineer Trainee",
            "CloudCore Demo",
            "Hyderabad, India",
            "Assist with ETL pipelines, SQL, data processing and cloud data engineering workflows.",
            "SQL, Python, ETL, Cloud, Data Engineering",
            "0-1 years",
            "https://example.com/jobs/cloud-data-engineer",
            "Dataset"
        ),
        (
            "Software Engineer Intern",
            "DevSphere Demo",
            "Gurugram, India",
            "Work on software features, debugging, data structures and algorithms using Java or Python.",
            "Java, Python, DSA, Git, SQL",
            "0-1 years",
            "https://example.com/jobs/software-engineer-intern",
            "Dataset"
        ),
        (
            "Backend Developer Intern",
            "CodeCraft Demo",
            "Pune, India",
            "Develop backend applications using Python, Flask/Django, databases and REST APIs.",
            "Python, Flask, Django, SQL, REST API",
            "0-1 years",
            "https://example.com/jobs/backend-intern",
            "Dataset"
        ),
        (
            "AI/ML Intern",
            "NeuralLab Demo",
            "Remote",
            "Support AI prototypes using Python, machine learning concepts, NLP and model evaluation.",
            "Python, AI, Machine Learning, NLP, Git",
            "0-1 years",
            "https://example.com/jobs/ai-ml-intern",
            "Dataset"
        ),
        (
            "Machine Learning Intern",
            "AIWorks Demo",
            "Bengaluru, India",
            "Assist with machine learning experiments, data preprocessing, model evaluation and Python development.",
            "Python, Machine Learning, Pandas, Scikit-learn, Statistics",
            "0-1 years",
            "https://example.com/jobs/ml-intern",
            "Dataset"
        ),
        (
            "Data Analyst Intern",
            "DataBridge Demo",
            "Noida, India",
            "Analyze datasets using Python, Pandas and SQL. Create reports and dashboards and communicate insights.",
            "Python, Pandas, SQL, Excel, Data Analysis",
            "0-1 years",
            "https://example.com/jobs/data-analyst-intern",
            "Dataset"
        ),
        (
            "Python Developer Intern",
            "TechNova Demo",
            "Remote",
            "Build Python services and APIs. Work with SQL, Git, REST APIs and basic testing.",
            "Python, SQL, REST API, Git",
            "0-1 years",
            "https://example.com/jobs/python-developer-intern",
            "Dataset"
        )
    ]

    for job in jobs:
        conn.execute("""
            INSERT OR IGNORE INTO jobs
            (
                title,
                company,
                location,
                description,
                skills,
                experience,
                url,
                source,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (*job, datetime.now().isoformat()))

    conn.commit()
    conn.close()


# Initialize database when application starts
initialize_database()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["GET", "POST"])
def upload():

    # GET request -> show upload page
    if request.method == "GET":
        return render_template("upload.html")

    if "resume" not in request.files:
        return render_template(
            "upload.html",
            error="Please select a resume file."
        )

    file = request.files["resume"]

    if file.filename == "":
        return render_template(
            "upload.html",
            error="Please select a resume file."
        )

    allowed_extensions = {
        ".pdf",
        ".docx",
        ".txt"
    }

    extension = os.path.splitext(
        file.filename
    )[1].lower()

    if extension not in allowed_extensions:
        return render_template(
            "upload.html",
            error=(
                "Unsupported file format. "
                "Please upload PDF, DOCX or TXT."
            )
        )

    filename = file.filename

    filepath = os.path.join(
        app.config["UPLOAD_FOLDER"],
        filename
    )

    file.save(filepath)

    try:

        text, info = extract_resume(filepath)

    except Exception as e:

        print("Resume extraction error:", e)

        return render_template(
            "upload.html",
            error=(
                "Unable to process the resume. "
                "Please upload a valid PDF or DOCX file."
            )
        )

    if not text:

        error_message = info.get(
            "error",
            "Unable to read the uploaded resume."
        )

        return render_template(
            "upload.html",
            error=error_message
        )

    skills = info.get(
        "skills",
        []
    )

    name = info.get(
        "name",
        ""
    )

    email = info.get(
        "email",
        ""
    )

    phone = info.get(
        "phone",
        ""
    )

    conn = get_db_connection()

    jobs_data = conn.execute(
        "SELECT * FROM jobs"
    ).fetchall()

    conn.close()

    return render_template(
        "jobs.html",
        jobs=jobs_data,
        resume_text=text,
        resume_name=filename,
        candidate_name=name,
        candidate_email=email,
        candidate_phone=phone,
        resume_skills=skills
    )


@app.route("/jobs")
def jobs():

    conn = get_db_connection()

    jobs_data = conn.execute(
        "SELECT * FROM jobs"
    ).fetchall()

    conn.close()

    return render_template(
        "jobs.html",
        jobs=jobs_data
    )


@app.route("/search")
def search():

    role = request.args.get(
        "role",
        ""
    ).strip()

    company = request.args.get(
        "company",
        ""
    ).strip()

    skill = request.args.get(
        "skill",
        ""
    ).strip()

    location = request.args.get(
        "location",
        ""
    ).strip()

    conn = get_db_connection()

    query = "SELECT * FROM jobs WHERE 1=1"

    parameters = []

    if role:

        query += " AND title LIKE ?"

        parameters.append(
            f"%{role}%"
        )

    if company:

        query += " AND company LIKE ?"

        parameters.append(
            f"%{company}%"
        )

    if skill:

        query += " AND skills LIKE ?"

        parameters.append(
            f"%{skill}%"
        )

    if location:

        query += " AND location LIKE ?"

        parameters.append(
            f"%{location}%"
        )

    jobs_data = conn.execute(
        query,
        parameters
    ).fetchall()

    conn.close()

    return render_template(
        "jobs.html",
        jobs=jobs_data
    )


@app.route("/match/<int:job_id>")
def match_job(job_id):

    resume_text = request.args.get(
        "resume_text",
        ""
    )

    resume_skills = request.args.get(
        "resume_skills",
        ""
    )

    resume_skills = [
        skill.strip()
        for skill in resume_skills.split(",")
        if skill.strip()
    ]

    conn = get_db_connection()

    job = conn.execute(
        "SELECT * FROM jobs WHERE id = ?",
        (job_id,)
    ).fetchone()

    conn.close()

    if not job:

        return render_template(
            "index.html",
            error="Job not found."
        )

    try:

        result = match_resume_to_job(
            resume_skills,
            dict(job)
        )

    except Exception as e:

        print("Matching error:", e)

        result = {
            "score": 0,
            "matching_skills": [],
            "missing_skills": []
        }

    return render_template(
        "job_details.html",
        job=job,
        match=result,
        resume_text=resume_text
    )


@app.route("/analyze/<int:job_id>")
def analyze(job_id):

    conn = get_db_connection()

    job = conn.execute(
        "SELECT * FROM jobs WHERE id = ?",
        (job_id,)
    ).fetchone()

    conn.close()

    if not job:

        return render_template(
            "index.html",
            error="Job not found."
        )

    try:

        analysis = analyze_job_with_ai(
            dict(job)
        )

    except Exception as e:

        print("AI analysis error:", e)

        analysis = {
            "error": (
                "AI analysis is currently unavailable."
            )
        }

    return render_template(
        "job_details.html",
        job=job,
        analysis=analysis
    )


@app.errorhandler(413)
def file_too_large(error):

    return render_template(
        "index.html",
        error=(
            "File is too large. "
            "Maximum size is 10 MB."
        )
    ), 413


@app.errorhandler(500)
def internal_error(error):

    print(
        "Internal server error:",
        error
    )

    return render_template(
        "index.html",
        error=(
            "Something went wrong while processing "
            "the request. Please try again."
        )
    ), 500


if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=True
    )