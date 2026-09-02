import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash

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


@app.route("/")
def index():

    return render_template(
        "index.html"
    )


@app.route("/upload", methods=["POST"])
def upload():

    if "resume" not in request.files:

        return render_template(
            "index.html",
            error="Please select a resume file."
        )

    file = request.files["resume"]

    if file.filename == "":

        return render_template(
            "index.html",
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
            "index.html",
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
            "index.html",
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
            "index.html",
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

    return render_template(
        "jobs.html",
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
        error="File is too large. Maximum size is 10 MB."
    ), 413


@app.errorhandler(500)
def internal_error(error):

    print("Internal server error:", error)

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