def build_analysis_prompt(cv_summary: str, post_text: str) -> str:
    summary = (cv_summary or "").strip()[:4000]
    post_excerpt = (post_text or "")[:3000]

    return f"""
You are screening LinkedIn posts for a Python developer named Pinaki.

Your task is to decide if the post is a good lead for a freelance or contract opportunity.
Return valid JSON only, with the following schema:

{{
  "relevance_score": 7,
  "client_need": "Looking for a FastAPI developer to optimize REST APIs.",
  "matched_skills": ["FastAPI", "Python", "API Optimization"],
  "connection_note": "Hi [Name], I saw your post about needing a FastAPI developer..."
}}

Rules:
- relevance_score must be an integer from 0 to 10.
- 0-3 = not relevant
- 4-6 = somewhat relevant
- 7-10 = highly relevant, especially for Python, FastAPI, Django, AI/ML, backend engineering, APIs, and software architecture
- If relevance_score < 4, set connection_note to an empty string "".
- connection_note must be under 250 characters and sound human.
- matched_skills should be a list of concrete skills only, matching Pinaki's profile.
- Keep client_need brief and specific to the client's need.
- Do not output markdown fences or explanations.

Pinaki's CV summary:
{summary}

Post to analyze:
{post_excerpt}
""".strip()
