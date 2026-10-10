import json
import logging
import re
from typing import Any

import ollama
from pydantic import Field

from app.config import DEFAULT_MODEL, DEFAULT_OLLAMA_HOST, MAX_POST_TEXT_CHARS
from app.models import PostAnalysis
from app.prompts import build_analysis_prompt

logger = logging.getLogger(__name__)


class OllamaUnavailableError(RuntimeError):
    """Raised when the local Ollama service is unreachable."""


class AnalysisResult(PostAnalysis):
    author: str
    author_url: str
    post_url: str
    post_text: str
    relevance_score: int = Field(ge=0, le=10)
    client_need: str
    matched_skills: list[str]
    connection_note: str = ""


def get_ollama_client():
    return ollama.Client(host=DEFAULT_OLLAMA_HOST)


def _extract_json_payload(raw_response: str) -> dict[str, Any]:
    cleaned = raw_response.strip()
    if cleaned.startswith("```"):
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, re.DOTALL)
        if match:
            cleaned = match.group(1)

    start_idx = cleaned.find("{")
    end_idx = cleaned.rfind("}")
    if start_idx != -1 and end_idx > start_idx:
        cleaned = cleaned[start_idx : end_idx + 1]

    return json.loads(cleaned)


async def analyze_post(
    *,
    author: str,
    author_url: str,
    post_url: str,
    post_text: str,
    cv_summary: str,
) -> AnalysisResult:
    prompt = build_analysis_prompt(cv_summary, post_text[:MAX_POST_TEXT_CHARS])
    client = get_ollama_client()

    try:
        response = client.chat(
            model=DEFAULT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.3},
        )
    except Exception as exc:  # pragma: no cover - real runtime failure path
        logger.warning("Ollama request failed for %s: %s", author, exc)
        raise OllamaUnavailableError(
            "Ollama is not running or the model is unavailable. Start it with 'ollama serve' and pull the model with 'ollama pull qwen3.5:9b-mlx'."
        ) from exc

    if hasattr(response, "message"):
        response_data = getattr(response, "message", {}) or {}
        content = str(response_data.get("content", "") or "")
    else:
        response_data = response or {}
        content = str(response_data.get("message", {}).get("content", "") or "")

    logger.info("Received LLM response for %s", author)
    logger.debug("LLM payload: %s", content[:500])

    try:
        payload = _extract_json_payload(content)
    except (TypeError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError(f"LLM returned invalid JSON for post by {author}: {content[:200]}") from exc

    relevance_score = int(payload.get("relevance_score", 0))
    matched_skills = payload.get("matched_skills", []) or []
    connection_note = str(payload.get("connection_note", "") or "")

    if relevance_score < 4:
        connection_note = ""

    if len(connection_note) > 250:
        connection_note = connection_note[:247].rsplit(" ", 1)[0] + "..."

    result = AnalysisResult(
        author=author,
        author_url=author_url,
        post_url=post_url,
        post_text=post_text,
        relevance_score=max(0, min(10, relevance_score)),
        client_need=str(payload.get("client_need", "")),
        matched_skills=[str(skill).strip() for skill in matched_skills if str(skill).strip()],
        connection_note=connection_note,
    )
    return result
