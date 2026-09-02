import os
import re
import shutil

import fitz  # PyMuPDF
import pytesseract
from PIL import Image
from docx import Document


# -----------------------------
# TESSERACT SETUP
# -----------------------------
tesseract_path = shutil.which("tesseract")

if tesseract_path:
    pytesseract.pytesseract.tesseract_cmd = tesseract_path
else:
    windows_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ]

    for path in windows_paths:
        if os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path
            break


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
# LIGHTWEIGHT OCR
# -----------------------------
def ocr_pdf(path):
    text = ""

    try:
        doc = fitz.open(path)

        # Only process first 3 pages to avoid excessive memory usage
        max_pages = min(len(doc), 3)

        for page_number in range(max_pages):

            page = doc.load_page(page_number)

            # LOW DPI = much lower memory usage
            pix = page.get_pixmap(
                matrix=fitz.Matrix(1.0, 1.0),
                colorspace=fitz.csRGB,
                alpha=False
            )

            image = Image.frombytes(
                "RGB",
                [pix.width, pix.height],
                pix.samples
            )

            # Resize large images if necessary
            max_width = 1600

            if image.width > max_width:
                ratio = max_width / image.width
                new_height = int(image.height * ratio)

                image = image.resize(
                    (max_width, new_height)
                )

            try:
                page_text = pytesseract.image_to_string(
                    image,
                    config="--psm 6",
                    timeout=35
                )

                text += page_text + "\n"

            except Exception as ocr_error:
                print(
                    f"OCR failed on page {page_number + 1}:",
                    ocr_error
                )

            # Explicitly release memory
            image.close()
            del pix

        doc.close()

    except Exception as e:
        print("OCR error:", e)

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
# EMAIL
# -----------------------------
def extract_email(text):
    match = re.search(
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
        text
    )

    return match.group(0) if match else ""


# -----------------------------
# PHONE
# -----------------------------
def extract_phone(text):
    match = re.search(
        r"(?:\+91[\s-]?)?[6-9]\d{9}",
        text
    )

    return match.group(0) if match else ""


# -----------------------------
# NAME
# -----------------------------
def extract_name(text):
    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    if not lines:
        return ""

    # Try first meaningful line
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
# MAIN FUNCTION
# -----------------------------
def extract_resume(path):

    extension = os.path.splitext(path)[1].lower()

    text = ""

    # PDF
    if extension == ".pdf":

        print("Trying normal PDF text extraction...")

        text = extract_pdf_text(path)

        if text and len(text.strip()) >= 50:

            print("Normal PDF text found.")

        else:

            print("Normal PDF text not found.")
            print("Trying lightweight OCR...")

            text = ocr_pdf(path)

    # DOCX
    elif extension == ".docx":

        print("Extracting DOCX text...")
        text = extract_docx_text(path)

    # TXT
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

    # Unsupported
    else:
        text = ""

    text = text.strip()

    if not text:
        return "", {
            "error": "Readable text not found."
        }

    info = {
        "name": extract_name(text),
        "email": extract_email(text),
        "phone": extract_phone(text),
        "skills": detect_skills(text),
    }

    return text, info