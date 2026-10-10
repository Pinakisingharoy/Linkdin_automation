# LinkedIn Automation Backend

A FastAPI service that searches for relevant LinkedIn posts, uses a local Ollama model to score and summarize each lead, and returns a filtered list of qualified prospects for manual review.

## Features

- FastAPI backend with search, health, and model inspection endpoints
- LinkedIn post fetcher with mock fallback for offline or blocked environments
- Ollama integration using the local model `qwen3.5:9b-mlx`
- Relevance scoring, client need extraction, matched skills, and personalized connection note generation
- Rate-limited search flow with a mock fallback that keeps testing practical and deterministic

## Tech stack

- Python 3.11+
- FastAPI
- Pydantic v2
- Uvicorn
- Ollama Python client
- Pytest

## Setup

1. Create and activate a virtual environment:

   ```bash
   cd "/Users/pinaki/Desktop/Linkdin Automation"
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Install and run Ollama locally.

3. Pull the model used by the service:

   ```bash
   ollama pull qwen3.5:9b-mlx
   ```

4. Start the API server:

   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

## Endpoints

### Health check

```bash
curl http://localhost:8000/health
```

### Model list

```bash
curl http://localhost:8000/models
```

### Search

```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{
    "queries": [
      "looking for a freelance Python developer",
      "need help with FastAPI"
    ],
    "max_posts_per_query": 5,
    "min_relevance": 4
  }'
```

## LinkedIn login (real account mode)

If you want the app to use your own LinkedIn account, set these environment variables before starting the server:

```bash
export LINKEDIN_EMAIL="your_email@example.com"
export LINKEDIN_PASSWORD="your_password"
```

The app will automatically try the live LinkedIn browser login path first. If the credentials are not available, it falls back to the safe mock dataset for testing.

## Notes

- This service intentionally does not send connection requests.
- The LinkedIn fetcher uses the mock data source when the official library is unavailable, which keeps the pipeline testable without violating LinkedIn terms of service.
- The LLM prompt is intentionally structured to force JSON output and a small connection note.

## Testing

```bash
pytest -q
```

