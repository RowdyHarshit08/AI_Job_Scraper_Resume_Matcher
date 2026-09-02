import os
import re
import shutil


SKILLS = [
    "python", "java", "c++", "c", "sql", "oracle",
    "mongodb", "html", "css", "javascript", "django",
    "flask", "machine learning", "deep learning",
    "artificial intelligence", "ai", "data structures",
    "algorithms", "pandas", "numpy", "scikit-learn",
    "tensorflow", "pytorch", "git", "github",
    "rest api", "api", "etl", "data analysis",
    "data science", "statistics", "aws", "azure",
    "gcp", "cloud", "excel", "nlp", "power bi"
]


def clean_text(text):
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_pdf_text(path):
    import fitz

    document = fitz.open(path)

    try:
        text = ""

        for page in document:
            text += page.get_text("text") + "\n"

        return text

    finally:
        document.close()


def find_tesseract():

    locations = [
        shutil.which("tesseract"),
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"
    ]

    for location in locations:

        if location and os.path.exists(location):
            return location

    return None


def ocr_pdf(path):

    try:
        import fitz
        import pytesseract
        from PIL import Image

    except Exception:
        return ""

    tesseract = find_tesseract()

    if not tesseract:
        return ""

    pytesseract.pytesseract.tesseract_cmd = tesseract

    document = fitz.open(path)

    pages_text = []

    try:

        for page in document:

            pix = page.get_pixmap(
                dpi=220,
                alpha=False
            )

            image = Image.frombytes(
                "RGB",
                [pix.width, pix.height],
                pix.samples
            )

            text = pytesseract.image_to_string(
                image,
                config="--psm 6"
            )

            pages_text.append(text)

    finally:
        document.close()

    return "\n".join(pages_text)


def extract_docx_text(path):

    from docx import Document

    document = Document(path)

    text_parts = []

    for paragraph in document.paragraphs:
        text_parts.append(paragraph.text)

    for table in document.tables:

        for row in table.rows:

            text_parts.append(
                " | ".join(
                    cell.text for cell in row.cells
                )
            )

    return "\n".join(text_parts)


def extract_resume(path):

    extension = os.path.splitext(path)[1].lower()

    if extension == ".pdf":

        # First try normal PDF text extraction
        text = clean_text(
            extract_pdf_text(path)
        )

        # If PDF has no readable text,
        # automatically try OCR
        if len(re.sub(r"\s+", "", text)) < 30:

            print("Normal PDF text not found.")
            print("Trying OCR...")

            text = clean_text(
                ocr_pdf(path)
            )

    elif extension == ".docx":

        text = clean_text(
            extract_docx_text(path)
        )

    else:

        raise ValueError(
            "Only PDF and DOCX files are supported."
        )

    lower_text = text.lower()

    detected_skills = []

    for skill in SKILLS:

        if skill.lower() in lower_text:
            detected_skills.append(skill)

    emails = re.findall(
        r"[\w.+-]+@[\w-]+\.[\w.-]+",
        text
    )

    phones = re.findall(
        r"(?:\+91[\s-]?)?[6-9]\d{9}",
        text
    )

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    name = lines[0] if lines else ""

    return text, {
        "name": name,
        "email": emails[0] if emails else "",
        "phone": phones[0] if phones else "",
        "skills": sorted(set(detected_skills))
    }