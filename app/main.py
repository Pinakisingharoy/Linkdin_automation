from fastapi import FastAPI, HTTPException
from fastapi.responses import Response

import ollama

from app.config import CV_SUMMARY_PATH
from app.models import SearchRequest, SearchResponse
from app.services.search import run_search

app = FastAPI(title="LinkedIn Lead Finder", version="1.0.0")


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "message": "LinkedIn Lead Finder API is running.",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/favicon.ico", include_in_schema=False)
async def favicon() -> Response:
    return Response(status_code=204)


def read_cv_summary() -> str:
    if CV_SUMMARY_PATH.exists():
        return CV_SUMMARY_PATH.read_text(encoding="utf-8")
    return "Python developer with FastAPI, Django, REST APIs, backend architecture, AI/ML, and data-driven product work."


@app.get("/health")
async def health() -> dict[str, str]:
    try:
        ollama.list()
        return {"status": "ok"}
    except Exception as exc:  # pragma: no cover - runtime environment check
        raise HTTPException(
            status_code=503,
            detail="Ollama is not running. Start it with 'ollama serve' and pull the model with 'ollama pull qwen3.5:9b-mlx'.",
        ) from exc


@app.get("/models")
async def models() -> dict[str, list[str]]:
    try:
        raw_models = ollama.list()
        items = raw_models.get("models", []) if isinstance(raw_models, dict) else raw_models
        names = []
        for item in items:
            if isinstance(item, dict):
                names.append(item.get("name") or item.get("model") or "unknown")
            else:
                names.append(str(item))
        return {"models": names}
    except Exception as exc:  # pragma: no cover - runtime environment check
        raise HTTPException(
            status_code=503,
            detail="Ollama is not running. Start it with 'ollama serve' and pull the model with 'ollama pull qwen3.5:9b-mlx'.",
        ) from exc


@app.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest) -> SearchResponse:
    try:
        response = await run_search(request, read_cv_summary())
        return response
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="Ollama is not running or the model is unavailable. Start it with 'ollama serve' and pull the model with 'ollama pull qwen3.5:9b-mlx'.",
        ) from exc
