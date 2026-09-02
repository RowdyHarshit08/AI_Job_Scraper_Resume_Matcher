import os
import re

import fitz
from docx import Document


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
        print("PDF extraction error:", e)

    return text.strip()


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

    except Exception as e:
        print("DOCX extraction error:", e)

    return text.strip()


def detect_skills(text):
    text_lower = text.lower()

    found = []

    for skill in SKILLS:
        if skill.lower() in text_lower:
            found.append(skill)

    return sorted(set(found))


def extract_email(text):
    match = re.search(
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
        text
    )

    return match.group(0) if match else ""


def extract_phone(text):
    match = re.search(
        r"(?:\+91[\s-]?)?[6-9]\d{9}",
        text
    )

    return match.group(0) if match else ""


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

            blocked = [
                "resume",
                "curriculum",
                "email",
                "phone",
                "mobile",
                "objective",
                "developer",
                "engineer"
            ]

            if not any(
                word in clean.lower()
                for word in blocked
            ):
                return clean

    return lines[0]


def extract_resume(path):

    extension = os.path.splitext(path)[1].lower()

    text = ""

    if extension == ".pdf":

        print("Trying normal PDF text extraction...")

        text = extract_pdf_text(path)

        if not text or len(text.strip()) < 50:

            print("Scanned/image PDF detected.")

            return "", {
                "error": (
                    "This PDF appears to be scanned or image-based. "
                    "Please upload a text-based PDF or DOCX resume."
                )
            }

    elif extension == ".docx":

        print("Extracting DOCX text...")

        text = extract_docx_text(path)

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

    else:

        return "", {
            "error": (
                "Unsupported file format. "
                "Please upload PDF, DOCX or TXT."
            )
        }

    text = text.strip()

    if not text:

        return "", {
            "error": "No readable text found in the uploaded file."
        }

    info = {
        "name": extract_name(text),
        "email": extract_email(text),
        "phone": extract_phone(text),
        "skills": detect_skills(text),
    }

    return text, info