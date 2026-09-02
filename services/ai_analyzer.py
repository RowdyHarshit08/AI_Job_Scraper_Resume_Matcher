import os, json

def ai_analyze(resume_text, job, match):
    key=os.getenv("OPENAI_API_KEY","").strip()
    if not key or key.lower().startswith("your_"):
        return local_analysis(job,match)
    try:
        from openai import OpenAI
        client=OpenAI(api_key=key)
        prompt=f"""Analyze this resume against this job. Return ONLY valid JSON with keys:
summary, strengths, recommendations, matching_skills, missing_skills, score.
Resume:
{resume_text[:12000]}
Job:
Title: {job['title']}
Description: {job['description']}
Skills: {job['skills']}
Existing score: {match['score']}
"""
        response=client.responses.create(model=os.getenv("OPENAI_MODEL","gpt-4.1-mini"), input=prompt)
        data=json.loads(response.output_text)
        data["source"]="OpenAI"
        return data
    except Exception:
        return local_analysis(job,match)

def local_analysis(job,match):
    missing=match["missing_skills"]
    summary=f"Your resume has a {match['score']}% estimated match with this role based on skills and text similarity."
    strengths=match["matching_skills"][:6]
    recommendations=[f"Consider adding evidence of {x} through a project, course, or certification." for x in missing[:5]]
    if not recommendations: recommendations=["Quantify project impact and keep the most relevant skills near the top of the resume."]
    return {"summary":summary,"strengths":strengths,"recommendations":recommendations,
            "matching_skills":match["matching_skills"],"missing_skills":missing,
            "score":match["score"],"source":"Local NLP fallback"}
