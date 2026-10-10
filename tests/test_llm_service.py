import json

import pytest

from app.services.llm import AnalysisResult, analyze_post


@pytest.mark.asyncio
async def test_analyze_post_parses_valid_json_response(monkeypatch):
    class FakeResponse:
        def __init__(self):
            self.message = {"content": json.dumps({
                "relevance_score": 8,
                "client_need": "Looking for a FastAPI developer.",
                "matched_skills": ["FastAPI", "Python", "REST APIs"],
                "connection_note": "Hi John, I saw your post about needing a FastAPI developer."
            })}

    def fake_client_factory(*args, **kwargs):
        class FakeClient:
            def chat(self, model, messages, options):
                return FakeResponse()
        return FakeClient()

    monkeypatch.setattr("app.services.llm.get_ollama_client", fake_client_factory)

    result = await analyze_post(
        author="John Doe",
        post_text="We are looking for a FastAPI developer to build REST APIs in Python.",
        post_url="https://linkedin.com/posts/example",
        author_url="https://linkedin.com/in/johndoe",
        cv_summary="Python developer with FastAPI, REST APIs, AI projects.",
    )

    assert isinstance(result, AnalysisResult)
    assert result.relevance_score == 8
    assert result.client_need == "Looking for a FastAPI developer."
    assert result.matched_skills == ["FastAPI", "Python", "REST APIs"]
    assert len(result.connection_note) <= 250


@pytest.mark.asyncio
async def test_analyze_post_rejects_low_relevance(monkeypatch):
    class FakeResponse:
        def __init__(self):
            self.message = {"content": json.dumps({
                "relevance_score": 2,
                "client_need": "Something unrelated.",
                "matched_skills": ["Marketing"],
                "connection_note": "Hi there"
            })}

    def fake_client_factory(*args, **kwargs):
        class FakeClient:
            def chat(self, model, messages, options):
                return FakeResponse()
        return FakeClient()

    monkeypatch.setattr("app.services.llm.get_ollama_client", fake_client_factory)

    result = await analyze_post(
        author="Jane Doe",
        post_text="We need an SEO consultant for marketing strategy.",
        post_url="https://linkedin.com/posts/example2",
        author_url="https://linkedin.com/in/janedoe",
        cv_summary="Python developer with FastAPI, REST APIs, AI projects.",
    )

    assert result.relevance_score == 2
    assert result.connection_note == ""
