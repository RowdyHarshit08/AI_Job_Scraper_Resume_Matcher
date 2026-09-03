import os
import sqlite3

from flask import Flask, render_template, request

from services.resume_parser import extract_resume
from services.matcher import match_resume_to_job
from services.ai_analyzer import analyze_job_with_ai


app = Flask(__name__)

BASE = os.path.dirname(__file__)
UPLOAD_FOLDER = os.path.join(BASE, "uploads")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024


# ---------------------------------------------------------
# DEMO JOB DATASET
# ---------------------------------------------------------

JOBS = [
    (
        "Python Django Intern",
        "AppNest Demo",
        "Remote",
        "Python,Django,SQL,HTML,CSS,Git"
    ),
    (
        "Junior Data Scientist",
        "InsightWorks Demo",
        "Mumbai",
        "Python,Pandas,Scikit-learn,SQL,Machine Learning"
    ),
    (
        "Full Stack Developer Intern",
        "WebForge Demo",
        "Remote",
        "HTML,CSS,JavaScript,Python,Django,MongoDB"
    ),
    (
        "Cloud Data Engineer Trainee",
        "CloudCore Demo",
        "Hyderabad",
        "SQL,Python,ETL,Cloud,Data Engineering"
    ),
    (
        "Software Engineer Intern",
        "DevSphere Demo",
        "Gurugram",
        "Java,Python,DSA,Git,SQL"
    ),
    (
        "AI/ML Intern",
        "NeuralLab Demo",
        "Remote",
        "Python,AI,Machine Learning,NLP,Git"
    ),
    (
        "Machine Learning Intern",
        "AIWorks Demo",
        "Bengaluru",
        "Python,Machine Learning,Pandas,Scikit-learn,Statistics"
    ),
    (
        "Data Analyst Intern",
        "DataBridge Demo",
        "Noida",
        "Python,Pandas,SQL,Excel,Data Analysis"
    ),
]


# ---------------------------------------------------------
# DATABASE
# ---------------------------------------------------------

def get_db():
    connection = sqlite3.connect(
        os.path.join(BASE, "database.db")
    )

    connection.row_factory = sqlite3.Row

    return connection


def init_database():

    connection = get_db()

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY,
            title TEXT,
            company TEXT,
            location TEXT,
            description TEXT,
            skills TEXT
        )
        """
    )

    for title, company, location, skills in JOBS:

        connection.execute(
            """
            INSERT OR IGNORE INTO jobs
            (title, company, location, description, skills)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                title,
                company,
                location,
                "Build and work on modern technology projects.",
                skills
            )
        )

    connection.commit()
    connection.close()


init_database()


# ---------------------------------------------------------
# HOME
# ---------------------------------------------------------

@app.route("/")
def home():

    return render_template("index.html")


# ---------------------------------------------------------
# UPLOAD RESUME
# ---------------------------------------------------------

@app.route("/upload", methods=["GET", "POST"])
def upload():

    # Show upload page
    if request.method == "GET":

        return render_template("upload.html")


    # Get uploaded file
    resume_file = request.files.get("resume")


    if not resume_file or not resume_file.filename:

        return render_template(
            "upload.html",
            error="Please select a resume file."
        )


    filename = os.path.basename(resume_file.filename)

    extension = os.path.splitext(filename)[1].lower()


    # Supported formats
    if extension not in [".pdf", ".docx", ".txt"]:

        return render_template(
            "upload.html",
            error="Only PDF, DOCX and TXT files are supported."
        )


    # Save uploaded resume
    file_path = os.path.join(
        UPLOAD_FOLDER,
        filename
    )


    try:

        resume_file.save(file_path)

    except Exception as e:

        return render_template(
            "upload.html",
            error=f"Could not save the resume: {str(e)}"
        )


    # -----------------------------------------------------
    # EXTRACT RESUME
    # -----------------------------------------------------

    try:

        resume_text, resume_info = extract_resume(
            file_path
        )

    except Exception as e:

        return render_template(
            "upload.html",
            error=f"Could not process this resume: {str(e)}"
        )


    # Extraction failed
    if not resume_text:

        error_message = resume_info.get(
            "error",
            "No readable text was found in this resume."
        )

        return render_template(
            "upload.html",
            error=error_message
        )


    # -----------------------------------------------------
    # GET JOBS
    # -----------------------------------------------------

    connection = get_db()

    jobs = connection.execute(
        "SELECT * FROM jobs"
    ).fetchall()

    connection.close()


    # -----------------------------------------------------
    # SHOW JOBS
    # -----------------------------------------------------

    return render_template(
        "jobs.html",
        jobs=jobs,
        resume_text=resume_text,
        resume_skills=resume_info.get("skills", []),
        candidate_name=resume_info.get(
            "name",
            "Candidate"
        ),
        candidate_email=resume_info.get(
            "email",
            ""
        ),
        candidate_phone=resume_info.get(
            "phone",
            ""
        )
    )


# ---------------------------------------------------------
# ALL JOBS
# ---------------------------------------------------------

@app.route("/jobs")
def jobs():

    connection = get_db()

    job_list = connection.execute(
        "SELECT * FROM jobs"
    ).fetchall()

    connection.close()

    return render_template(
        "jobs.html",
        jobs=job_list
    )


# ---------------------------------------------------------
# MATCH RESUME WITH JOB
# ---------------------------------------------------------

@app.route("/match/<int:job_id>")
def match(job_id):

    resume_skills_string = request.args.get(
        "resume_skills",
        ""
    )

    resume_skills = [
        skill.strip()
        for skill in resume_skills_string.split(",")
        if skill.strip()
    ]


    connection = get_db()

    job = connection.execute(
        "SELECT * FROM jobs WHERE id = ?",
        (job_id,)
    ).fetchone()

    connection.close()


    if not job:

        return render_template(
            "index.html",
            error="Job not found."
        )


    match_result = match_resume_to_job(
        resume_skills,
        dict(job)
    )


    return render_template(
        "job_details.html",
        job=job,
        match=match_result,
        resume_text=request.args.get(
            "resume_text",
            ""
        )
    )


# ---------------------------------------------------------
# AI ANALYSIS
# ---------------------------------------------------------

@app.route("/analyze/<int:job_id>")
def analyze(job_id):

    connection = get_db()

    job = connection.execute(
        "SELECT * FROM jobs WHERE id = ?",
        (job_id,)
    ).fetchone()

    connection.close()


    if not job:

        return render_template(
            "index.html",
            error="Job not found."
        )


    resume_skills_string = request.args.get(
        "resume_skills",
        ""
    )


    resume_skills = [
        skill.strip()
        for skill in resume_skills_string.split(",")
        if skill.strip()
    ]


    resume_text = request.args.get(
        "resume_text",
        ""
    )


    match_result = match_resume_to_job(
        resume_skills,
        dict(job)
    )


    analysis = analyze_job_with_ai(
        dict(job),
        resume_text,
        match_result
    )


    return render_template(
        "job_details.html",
        job=job,
        match=match_result,
        analysis=analysis,
        resume_text=resume_text
    )


# ---------------------------------------------------------
# RUN APPLICATION
# ---------------------------------------------------------

if __name__ == "__main__":

    port = int(
        os.getenv("PORT", 5000)
    )

    app.run(
        host="0.0.0.0",
        port=port
    )
