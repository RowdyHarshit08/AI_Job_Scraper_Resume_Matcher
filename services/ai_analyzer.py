import os
import json


def ai_analyze(resume_text, job, match):

    key = os.getenv("OPENAI_API_KEY", "").strip()

    if not key or key.lower().startswith("your_"):
        return local_analysis(job, match)

    try:

        from openai import OpenAI

        client = OpenAI(api_key=key)

        prompt = f"""
Analyze this resume against this job.

Return ONLY valid JSON with these keys:
summary, strengths, recommendations, matching_skills, missing_skills, score.

Resume:
{resume_text[:12000]}

Job:
Title: {job['title']}
Description: {job['description']}
Skills: {job['skills']}

Existing score:
{match['score']}
"""

        response = client.responses.create(
            model=os.getenv(
                "OPENAI_MODEL",
                "gpt-4.1-mini"
            ),
            input=prompt
        )

        data = json.loads(
            response.output_text
        )

        data["source"] = "OpenAI"

        return data

    except Exception as e:

        print("OpenAI analysis failed:", e)

        return local_analysis(
            job,
            match
        )


def local_analysis(job, match):

    missing = match.get(
        "missing_skills",
        []
    )

    matching = match.get(
        "matching_skills",
        []
    )

    score = match.get(
        "score",
        0
    )

    summary = (
        f"Your resume has a {score}% estimated "
        "match with this role based on skills "
        "and text similarity."
    )

    strengths = matching[:6]

    recommendations = []

    for skill in missing[:5]:

        recommendations.append(
            f"Consider adding evidence of {skill} "
            "through a project, course, or certification."
        )

    if not recommendations:

        recommendations = [
            "Quantify project impact and keep "
            "the most relevant skills near the "
            "top of the resume."
        ]

    return {
        "summary": summary,
        "strengths": strengths,
        "recommendations": recommendations,
        "matching_skills": matching,
        "missing_skills": missing,
        "score": score,
        "source": "Local NLP fallback"
    }


def analyze_job_with_ai(job, resume_text="", match=None):

    if match is None:

        match = {
            "score": 0,
            "matching_skills": [],
            "missing_skills": []
        }

    return ai_analyze(
        resume_text,
        job,
        match
    )