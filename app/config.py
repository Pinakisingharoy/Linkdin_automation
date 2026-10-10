from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CV_SUMMARY_PATH = BASE_DIR / "cv_summary.txt"

DEFAULT_OLLAMA_HOST = "http://localhost:11434"
DEFAULT_MODEL = "qwen3.5:9b-mlx"
RATE_LIMIT_SECONDS = 8
MAX_POST_TEXT_CHARS = 3000
DEFAULT_MIN_RELEVANCE = 4
DEFAULT_MAX_POSTS_PER_QUERY = 5
