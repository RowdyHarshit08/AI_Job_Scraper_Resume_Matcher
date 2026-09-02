# AI Job Scraper & Resume Matcher

A Flask-based educational project that uploads PDF/DOCX resumes, extracts text and skills, ranks demo job listings, and generates explainable resume-to-job match scores.

## Features
- PDF and DOCX resume upload
- Text extraction with PyMuPDF/python-docx
- Basic skill extraction
- SQLite job/resume storage
- 10 demo jobs
- TF-IDF + cosine similarity matching
- Matching and missing skills
- Optional OpenAI analysis
- Local NLP fallback when OpenAI is unavailable
- Responsive Bootstrap UI
- Error handling for unsupported/large/unreadable files

## Windows Setup

Open Command Prompt/PowerShell inside this folder.

```text
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python app.py
```

Then open `http://127.0.0.1:5000`.

### OpenAI (optional)
Open `.env` and set:

```text
OPENAI_API_KEY=your_real_key_here
```

The application still works without an API key. It automatically uses the local matching/analysis fallback.

## Important note about scraping
The included dataset is intentionally a safe demo dataset using example.com URLs. Live job-site scraping varies by site and must respect each site's robots.txt, terms, rate limits, and access restrictions. A production scraper should use an authorized public API or a source that explicitly permits automated access.

## Troubleshooting

### "Readable text not found"
The PDF is likely scanned/image-only or malformed. Try exporting the resume again as a text-based PDF or use a DOCX file. OCR can be added as a separate enhancement.

### ModuleNotFoundError
Make sure the virtual environment is activated and run:

```text
pip install -r requirements.txt
```

### OpenAI error
Check `.env`, API key validity, available model access, network connection, and account/API limits. The app falls back to local NLP if the call fails.

## Project Structure

- `app.py` — Flask routes and database setup
- `services/resume_parser.py` — PDF/DOCX parsing
- `services/matcher.py` — matching algorithm
- `services/ai_analyzer.py` — optional AI analysis and fallback
- `templates/` — HTML pages
- `static/` — CSS/JavaScript
- `uploads/` — uploaded resumes (ignored by Git)
- `database.db` — generated SQLite database

## Demo Flow
1. Run `python app.py`
2. Open the homepage.
3. Click Upload Resume.
4. Select a text-based PDF/DOCX.
5. Review ranked jobs.
6. Open View Analysis on any job.
7. Review score, matching skills, missing skills and recommendations.
8. Click Apply / Open Job for the demo job URL.

## Academic Submission
For a submission/demo, explain that the system uses:
- document parsing
- skill extraction
- TF-IDF
- cosine similarity
- weighted matching
- optional LLM analysis
- SQLite persistence
- Flask web application architecture

Do not claim that the example.com demo listings are live vacancies.
