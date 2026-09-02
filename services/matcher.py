import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

SKILLS = [
    "python","java","c++","c","sql","oracle","mongodb","html","css","javascript",
    "django","flask","machine learning","deep learning","artificial intelligence","ai",
    "data structures","algorithms","pandas","numpy","scikit-learn","tensorflow","pytorch",
    "git","github","rest api","api","etl","data analysis","data science","statistics",
    "aws","azure","gcp","cloud","excel","nlp","natural language processing","power bi"
]

def tokens(text):
    low=text.lower()
    return {s for s in SKILLS if s in low}

def match_resume_to_job(resume_text, job):
    job_text=f'{job.get("title","")} {job.get("description","")} {job.get("skills","")}'
    rs, js=tokens(resume_text), tokens(job_text)
    matching=sorted(rs & js)
    missing=sorted(js-rs)
    try:
        vec=TfidfVectorizer(stop_words="english")
        matrix=vec.fit_transform([resume_text, job_text])
        similarity=float(cosine_similarity(matrix[0:1],matrix[1:2])[0][0])
    except Exception:
        similarity=0.0
    skill_score=(len(matching)/len(js)*100) if js else 0
    score=round(min(100, skill_score*0.65 + similarity*100*0.35))
    return {"score":score,"matching_skills":matching,"missing_skills":missing,"similarity":round(similarity*100,1)}
