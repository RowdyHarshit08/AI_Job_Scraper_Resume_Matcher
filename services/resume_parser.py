import os
import re
import gc

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
    "javascript",
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
    "excel",
    "statistics",
    "data analysis",
    "etl",
    "cloud",
    "data engineering",
    "rest api",
]


# -------------------------------------------------
# PDF TEXT EXTRACTION
# -------------------------------------------------

def extract_pdf_text(path):

    text = ""

    try:

        doc = fitz.open(path)

        if doc.needs_pass:

            print("Password protected PDF detected.")

            doc.close()

            return ""

        for page in doc:

            try:

                page_text = page.get_text("text")

                if page_text:

                    text += page_text + "\n"

            except Exception as e:

                print(
                    "PDF page text error:",
                    e
                )

        doc.close()

    except Exception as e:

        print(
            "PDF extraction error:",
            e
        )

    return text.strip()


# -------------------------------------------------
# OCR FOR SCANNED PDF
# -------------------------------------------------

def ocr_pdf(path):

    text = ""

    try:

        import pytesseract
        from PIL import Image

    except Exception as e:

        print(
            "OCR libraries unavailable:",
            e
        )

        return ""

    try:

        doc = fitz.open(path)

        if doc.needs_pass:

            print(
                "Password protected PDF cannot be OCR processed."
            )

            doc.close()

            return ""

        total_pages = len(doc)

        print(
            f"Starting OCR for {total_pages} pages..."
        )

        for page_number in range(total_pages):

            try:

                page = doc[page_number]

                print(
                    f"OCR page "
                    f"{page_number + 1}/{total_pages}"
                )

                # Low resolution keeps RAM usage low
                matrix = fitz.Matrix(
                    1.25,
                    1.25
                )

                pix = page.get_pixmap(
                    matrix=matrix,
                    colorspace=fitz.csRGB,
                    alpha=False
                )

                image = Image.frombytes(
                    "RGB",
                    [pix.width, pix.height],
                    pix.samples
                )

                try:

                    page_text = pytesseract.image_to_string(
                        image,
                        lang="eng",
                        config="--psm 6",
                        timeout=12
                    )

                    if page_text:

                        text += (
                            page_text +
                            "\n"
                        )

                except Exception as e:

                    print(
                        f"OCR failed on page "
                        f"{page_number + 1}:",
                        e
                    )

                # Free memory immediately
                image.close()

                del image
                del pix

                gc.collect()

            except Exception as e:

                print(
                    f"Could not process OCR page "
                    f"{page_number + 1}:",
                    e
                )

                gc.collect()

        doc.close()

    except Exception as e:

        print(
            "OCR PDF error:",
            e
        )

    return text.strip()


# -------------------------------------------------
# DOCX EXTRACTION
# -------------------------------------------------

def extract_docx_text(path):

    text = ""

    try:

        doc = Document(path)

        for paragraph in doc.paragraphs:

            if paragraph.text:

                text += (
                    paragraph.text +
                    "\n"
                )

        for table in doc.tables:

            for row in table.rows:

                for cell in row.cells:

                    if cell.text:

                        text += (
                            cell.text +
                            " "
                        )

    except Exception as e:

        print(
            "DOCX extraction error:",
            e
        )

    return text.strip()


# -------------------------------------------------
# SKILL DETECTION
# -------------------------------------------------

def detect_skills(text):

    text_lower = text.lower()

    found = []

    for skill in SKILLS:

        if skill.lower() in text_lower:

            found.append(skill)

    return sorted(
        set(found)
    )


# -------------------------------------------------
# EMAIL
# -------------------------------------------------

def extract_email(text):

    match = re.search(
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
        text
    )

    if match:

        return match.group(0)

    return ""


# -------------------------------------------------
# PHONE
# -------------------------------------------------

def extract_phone(text):

    match = re.search(
        r"(?:\+91[\s-]?)?[6-9]\d{9}",
        text
    )

    if match:

        return match.group(0)

    return ""


# -------------------------------------------------
# NAME
# -------------------------------------------------

def extract_name(text):

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    if not lines:

        return ""

    blocked = [
        "resume",
        "curriculum",
        "email",
        "phone",
        "mobile",
        "objective",
        "developer",
        "engineer",
        "education",
        "skills",
        "experience",
        "contact"
    ]

    for line in lines[:15]:

        clean = re.sub(
            r"[^A-Za-z .'-]",
            "",
            line
        ).strip()

        words = clean.split()

        if 2 <= len(words) <= 4:

            if not any(
                word in clean.lower()
                for word in blocked
            ):

                return clean

    return lines[0]


# -------------------------------------------------
# MAIN RESUME FUNCTION
# -------------------------------------------------

def extract_resume(path):

    extension = os.path.splitext(
        path
    )[1].lower()

    text = ""

    # ---------------------------------------------
    # PDF
    # ---------------------------------------------

    if extension == ".pdf":

        print(
            "Trying normal PDF text extraction..."
        )

        text = extract_pdf_text(
            path
        )

        # Normal PDF contains little/no text
        # → automatically use OCR
        if len(text.strip()) < 50:

            print(
                "Normal PDF text not sufficient."
            )

            print(
                "Trying OCR for scanned/image PDF..."
            )

            ocr_text = ocr_pdf(
                path
            )

            if ocr_text:

                text = ocr_text

    # ---------------------------------------------
    # DOCX
    # ---------------------------------------------

    elif extension == ".docx":

        print(
            "Extracting DOCX text..."
        )

        text = extract_docx_text(
            path
        )

    # ---------------------------------------------
    # TXT
    # ---------------------------------------------

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

            print(
                "TXT extraction error:",
                e
            )

    # ---------------------------------------------
    # UNSUPPORTED
    # ---------------------------------------------

    else:

        return "", {
            "error": (
                "Unsupported file format. "
                "Please upload PDF, DOCX or TXT."
            )
        }

    # ---------------------------------------------
    # FINAL VALIDATION
    # ---------------------------------------------

    text = text.strip()

    if not text:

        return "", {
            "error": (
                "Unable to extract readable text "
                "from this file. The PDF may be "
                "corrupted, password protected, "
                "or contain an unsupported image format."
            )
        }

    # ---------------------------------------------
    # RESUME INFORMATION
    # ---------------------------------------------

    info = {

        "name": extract_name(
            text
        ),

        "email": extract_email(
            text
        ),

        "phone": extract_phone(
            text
        ),

        "skills": detect_skills(
            text
        ),

    }

    return text, info