import os
import re
import shutil

import fitz
from docx import Document


# -----------------------------
# TESSERACT SETUP
# -----------------------------
# OCR is intentionally not used on Render Free.
# This keeps the live application stable.


# -----------------------------
# SKILLS
# -----------------------------
SKILLS = [
    "python",
    "java",
    "c",
    "c++",
    "sql",
    "oracle",
    "html",
    "css",
    "django",
    "mongodb",
    "machine learning",
    "artificial intelligence",
    "ai",
    "data structures",
    "algorithms",
    "nlp",
    "git",
    "github",
    "flask",
    "pandas",
    "numpy",
    "scikit-learn",
    "tensorflow",
    "pytorch",
]


# -----------------------------
# PDF TEXT EXTRACTION
# -----------------------------
def extract_pdf_text(path):
    text = ""

    try:
        doc = fitz.open(path)

        for page in doc:
            page_text = page.get_text("text")

            if page_text:
                text += page_text + "\n"

        doc.close()

    except Exception as e:
        print("PDF text extraction error:", e)

    return text.strip()


# -----------------------------
# DOCX EXTRACTION
# -----------------------------
def extract_docx_text(path):
    text = ""

    try:
        doc = Document(path)

        for paragraph in doc.paragraphs:
            if paragraph.text:
                text += paragraph.text + "\n"

        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    if cell.text:
                        text += cell.text + " "

        return text.strip()

    except Exception as e:
        print("DOCX extraction error:", e)
        return ""


# -----------------------------
# SKILL DETECTION
# -----------------------------
def detect_skills(text):
    text_lower = text.lower()

    found = []

    for skill in SKILLS:
        if skill.lower() in text_lower:
            found.append(skill)

    return sorted(set(found))


# -----------------------------
# EMAIL EXTRACTION
# -----------------------------
def extract_email(text):
    match = re.search(
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
        text
    )

    return match.group(0) if match else ""


# -----------------------------
# PHONE EXTRACTION
# -----------------------------
def extract_phone(text):
    match = re.search(
        r"(?:\+91[\s-]?)?[6-9]\d{9}",
        text
    )

    return match.group(0) if match else ""


# -----------------------------
# NAME EXTRACTION
# -----------------------------
def extract_name(text):
    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    if not lines:
        return ""

    for line in lines[:8]:

        clean = re.sub(
            r"[^A-Za-z .'-]",
            "",
            line
        ).strip()

        words = clean.split()

        if 2 <= len(words) <= 4:

            if not any(
                keyword in clean.lower()
                for keyword in [
                    "resume",
                    "curriculum",
                    "email",
                    "phone",
                    "mobile",
                    "objective",
                    "developer",
                    "engineer"
                ]
            ):
                return clean

    return lines[0]


# -----------------------------
# MAIN RESUME FUNCTION
# -----------------------------
def extract_resume(path):

    extension = os.path.splitext(path)[1].lower()

    text = ""

    # -------------------------
    # PDF
    # -------------------------
    if extension == ".pdf":

        print("Trying normal PDF text extraction...")

        text = extract_pdf_text(path)

        if text and len(text.strip()) >= 50:

            print("Normal PDF text found.")

        else:

            print("Scanned/image PDF detected.")

            return "", {
                "error": (
                    "Scanned PDF detected. "
                    "Please upload a text-based PDF or DOCX."
                )
            }

    # -------------------------
    # DOCX
    # -------------------------
    elif extension == ".docx":

        print("Extracting DOCX text...")

        text = extract_docx_text(path)

    # -------------------------
    # TXT
    # -------------------------
    elif extension == ".txt":

        try:

            with open(
                path,
                "r",
                encoding="utf-8",
                errors="ignore"
            ) as file:

                text = file.read()

        except Exception as e:

            print("TXT extraction error:", e)
            text = ""

    # -------------------------
    # UNSUPPORTED FILE
    # -------------------------
    else:

        return "", {
            "error": (
                "Unsupported file format. "
                "Please upload PDF, DOCX or TXT."
            )
        }

    # -------------------------
    # EMPTY TEXT
    # -------------------------
    text = text.strip()

    if not text:

        return "", {
            "error": "Readable text not found."
        }

    # -------------------------
    # RESUME INFORMATION
    # -------------------------
    info = {
        "name": extract_name(text),
        "email": extract_email(text),
        "phone": extract_phone(text),
        "skills": detect_skills(text),
    }

    return text, info