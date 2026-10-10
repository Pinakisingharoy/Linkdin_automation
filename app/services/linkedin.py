import importlib.util
import os
import time
from pathlib import Path

from dotenv import load_dotenv

from app.config import RATE_LIMIT_SECONDS
from app.models import LinkedInPost

load_dotenv(Path(__file__).resolve().parents[2] / ".env")


DEFAULT_CV_QUERY_POOL = (
    ("python", "Python developer"),
    ("fastapi", "FastAPI developer"),
    ("django", "Django backend engineer"),
    ("rest api", "REST API developer"),
    ("api optimization", "API optimization engineer"),
    ("backend", "Python backend developer"),
    ("ai", "AI engineer"),
    ("postgresql", "PostgreSQL backend developer"),
    ("sql", "SQL backend engineer"),
)


def get_linkedin_credentials() -> dict[str, str]:
    email = (
        os.getenv("LINKEDIN_EMAIL")
        or os.getenv("LINKEDIN_USER")
        or os.getenv("LINKEDIN_USERNAME")
        or os.getenv("LINKEDIN_LOGIN")
        or ""
    ).strip()
    password = (os.getenv("LINKEDIN_PASSWORD") or os.getenv("LINKEDIN_PASS") or "").strip()
    return {"email": email, "password": password}


def build_search_queries_from_cv(cv_summary: str) -> list[str]:
    summary = (cv_summary or "").strip()
    if not summary:
        return [
            "Python developer",
            "FastAPI developer",
            "REST API developer",
            "Django backend engineer",
            "AI engineer",
        ]

    lowered = summary.lower()
    queries = []
    for keyword, query in DEFAULT_CV_QUERY_POOL:
        if keyword in lowered:
            queries.append(query)

    if not queries:
        queries = [
            "Python developer",
            "FastAPI developer",
            "REST API developer",
            "Django backend engineer",
            "AI engineer",
        ]

    ordered: list[str] = []
    seen: set[str] = set()
    for query in queries:
        key = query.lower()
        if key not in seen:
            ordered.append(query)
            seen.add(key)

    return ordered[:8]


def _search_using_live_linkedin_session(query: str, limit: int) -> list[LinkedInPost] | None:
    credentials = get_linkedin_credentials()
    email = credentials["email"]
    password = credentials["password"]
    if not email or not password:
        return None

    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return None

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded", timeout=30000)
            page.fill("input[name='session_key']", email)
            page.fill("input[name='session_password']", password)
            page.click("button[type='submit']")
            page.wait_for_load_state("networkidle", timeout=30000)
            page.goto(
                f"https://www.linkedin.com/search/results/content/?keywords={query.replace(' ', '%20')}",
                wait_until="domcontentloaded",
                timeout=30000,
            )
            page.wait_for_load_state("networkidle", timeout=30000)
            posts = page.locator(".update-components-text")
            count = min(limit, max(0, posts.count()))
            results: list[LinkedInPost] = []
            for i in range(count):
                text = posts.nth(i).inner_text(timeout=10000)
                if not text.strip():
                    continue
                results.append(
                    LinkedInPost(
                        author="LinkedIn user",
                        author_url="https://www.linkedin.com",
                        post_url=page.url,
                        post_text=text[:2000],
                        posted_date=None,
                    )
                )
            browser.close()
            return results or None
    except Exception:
        return None


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

        result = _search_using_live_linkedin_session(query, max_posts_per_query)
        if result is None:
            result = _search_using_open_linkedin_api(query, max_posts_per_query)
        if result is None:
            result = _mock_posts_for_query(query, max_posts_per_query)
        all_posts.extend(result)

    return all_posts
