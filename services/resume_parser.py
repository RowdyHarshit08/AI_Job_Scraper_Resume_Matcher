import os, re, fitz
from docx import Document

SKILLS = ["python","java","c++","sql","html","css","javascript","django","mongodb",
          "machine learning","ai","data structures","algorithms","git","flask",
          "pandas","numpy","tensorflow","pytorch","excel","statistics"]

def extract_pdf_text(path, use_ocr=False):
    text = ""
    try:
        doc = fitz.open(path)
        for page in doc:
            text += page.get_text("text") + "\n"
        doc.close()
    except Exception as e:
        return "", f"PDF error: {str(e)}"

    text = text.strip()
    if text:
        return text, ""
    if not use_ocr:
        return "", "No readable text found in PDF."
    return "", "OCR not supported in this deployment."

def extract_docx_text(path):
    try:
        doc = Document(path)
        return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
    except Exception:
        return ""

def extract_txt_text(path):
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception:
        return ""

def detect_skills(text):
    lower = text.lower()
    return sorted([s for s in SKILLS if s in lower])

def extract_resume(path):
    if not os.path.exists(path):
        return "", {"error": "File not found"}

    ext = os.path.splitext(path)[1].lower()
    text, error = "", ""

    if ext == ".pdf":
        text, error = extract_pdf_text(path)
    elif ext == ".docx":
        text = extract_docx_text(path)
    elif ext == ".txt":
        text = extract_txt_text(path)
    else:
        return "", {"error": "Unsupported file type"}

    text = text.strip()
    if not text:
        return "", {"error": error or "No readable text"}

    lines = [l for l in text.splitlines() if l.strip()]
    name = lines[0][:100] if lines else "Candidate"

    email_match = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", text)
    email = email_match.group(0) if email_match else None

    skills = detect_skills(text)

    return text, {"name": name, "email": email, "skills": skills}
