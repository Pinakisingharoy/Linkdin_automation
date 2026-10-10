import importlib.util
import time

from app.config import RATE_LIMIT_SECONDS
from app.models import LinkedInPost


def _mock_posts_for_query(query: str, limit: int) -> list[LinkedInPost]:
    keyword_hint = query.lower()

    templates = [
        {
            "author": "Alex Morgan",
            "author_url": "https://linkedin.com/in/alexmorgan",
            "post_url": "https://linkedin.com/posts/alexmorgan-python-fastapi",
            "post_text": "We need a Python developer with FastAPI experience to help build a new internal API platform.",
        },
        {
            "author": "Priya Nair",
            "author_url": "https://linkedin.com/in/priyanair",
            "post_url": "https://linkedin.com/posts/priyanair-django-ai",
            "post_text": "Looking for a Django or FastAPI engineer to support a backend stack and AI-powered product roadmap.",
        },
        {
            "author": "Lucas Chen",
            "author_url": "https://linkedin.com/in/lucaschen",
            "post_url": "https://linkedin.com/posts/lucaschen-python-lead",
            "post_text": "Hiring a Python developer with REST API experience and strong backend thinking. Remote freelance work available.",
        },
        {
            "author": "Sofia Patel",
            "author_url": "https://linkedin.com/in/sofiapatel",
            "post_url": "https://linkedin.com/posts/sofiapatel-ml-api",
            "post_text": "We are looking for someone familiar with Python, API optimization, and ML project integration.",
        },
        {
            "author": "Rahul Verma",
            "author_url": "https://linkedin.com/in/rahulverma",
            "post_url": "https://linkedin.com/posts/rahulverma-mentor",
            "post_text": "Need help with SEO content strategy and marketing, not a software role.",
        },
    ]

    if "python" not in keyword_hint and "fastapi" not in keyword_hint and "django" not in keyword_hint:
        templates = [templates[-1]]

    return [
        LinkedInPost(
            author=item["author"],
            author_url=item["author_url"],
            post_url=item["post_url"],
            post_text=item["post_text"],
            posted_date="2026-10-08",
        )
        for item in templates[: max(1, min(limit, len(templates)))]
    ]


def _search_using_open_linkedin_api(query: str, limit: int):
    if importlib.util.find_spec("open_linkedin_api") is None:
        return None

    try:
        import open_linkedin_api  # type: ignore
    except Exception:
        return None

    try:
        searcher = getattr(open_linkedin_api, "LinkedInSearchClient", None)
        if searcher is None:
            return None

        client = searcher()
        fetch_posts = getattr(client, "search_posts", None)
        if fetch_posts is None:
            return None

        raw_posts = fetch_posts(query=query, limit=limit)
        normalized = []
        for entry in raw_posts:
            normalized.append(
                LinkedInPost(
                    author=entry.get("author", "Unknown author"),
                    author_url=entry.get("author_url", "https://linkedin.com"),
                    post_url=entry.get("post_url", "https://linkedin.com"),
                    post_text=entry.get("post_text", ""),
                    posted_date=entry.get("posted_date"),
                )
            )
        return normalized
    except Exception:
        return None


def fetch_posts_for_queries(queries: list[str], max_posts_per_query: int) -> list[LinkedInPost]:
    all_posts: list[LinkedInPost] = []

    for index, query in enumerate(queries):
        if index > 0:
            time.sleep(RATE_LIMIT_SECONDS)

        result = _search_using_open_linkedin_api(query, max_posts_per_query)
        if result is None:
            result = _mock_posts_for_query(query, max_posts_per_query)
        all_posts.extend(result)

    return all_posts
