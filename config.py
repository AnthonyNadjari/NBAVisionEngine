"""
NBAVision Engine — Configuration centralisée (Spec Section 2, 4, 11).
Credentials: credentials.json (or env vars).
"""
import json
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Fichier credentials à la racine du projet (ou CWD)
def _credentials_path() -> Path | None:
    for base in (Path(__file__).resolve().parent, Path.cwd()):
        p = base / "credentials.json"
        if p.is_file():
            return p
    return None

def _load_credentials() -> dict | None:
    path = _credentials_path()
    if not path:
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

# Python 3.11 — runtime
KEYWORDS = [
    "NBA",
    "Lakers",
    "Celtics",
    "LeBron",
    "Kevin Durant",
    "NBA trade",
    "NBA injury",
    "NBA playoffs",
    "NBA rumors",
]

# Session limits (Section 11)
MAX_REPLIES = 30
MAX_REPLIES_PER_AUTHOR = 1
CYCLE_INTERVAL_MINUTES = 5
MAX_CONSECUTIVE_ERRORS = 3
MAX_POSTING_FAILURES = 2

# Filtering (Section 5)
MAX_MINUTES_SINCE_POST = 15
MIN_FOLLOWERS = 5000
MAX_FOLLOWERS = 200_000
MIN_LIKES = 10
MIN_TEXT_LENGTH = 20
MAX_HASHTAGS = 3
MAX_PROFILES_OPENED_PER_CYCLE = 10

# Scoring (Section 6) — top N kept
TOP_N_SCORED = 20

# LLM (Section 7)
LLM_TIMEOUT_SECONDS = 20
LLM_RETRY_MAX = 2

# Reply validation (Section 9)
MAX_RESPONSES_SAME_FIRST_WORD = 3
MAX_EMOJIS_IN_SESSION = 3
MAX_SENTENCES = 2
TFIDF_SIMILARITY_THRESHOLD = 0.7

# Posting (Section 10)
TYPING_DELAY_MS_MIN = 50
TYPING_DELAY_MS_MAX = 120
WAIT_BEFORE_NEXT_TWEET_SEC_MIN = 120
WAIT_BEFORE_NEXT_TWEET_SEC_MAX = 360

# Scraping delays (Section 4.3, 14)
SEARCH_WAIT_SEC_MIN = 4
SEARCH_WAIT_SEC_MAX = 6
SCROLL_WAIT_SEC_MIN = 2
SCROLL_WAIT_SEC_MAX = 4
SCROLL_DELTA_MIN = 1200
SCROLL_DELTA_MAX = 2000
CYCLE_INTERVAL_JITTER_SEC = 30

# X (Twitter) — use x.com so .x.com cookies are sent
TWITTER_HOME_URL = "https://x.com/home"
TWITTER_SEARCH_BASE = "https://x.com/search?q={query}&f=live"

# Credentials: credentials.json (prioritaire) ou variables d'environnement
def get_twitter_cookies_json() -> str:
    raw = os.getenv("TWITTER_COOKIES_JSON", "").strip()
    if raw and raw not in ("", "[]"):
        return raw
    creds = _load_credentials()
    if creds and isinstance(creds.get("twitter_cookies"), list):
        return json.dumps(creds["twitter_cookies"], separators=(",", ":"))
    path = os.getenv("TWITTER_COOKIES_FILE", "cookies.json").strip()
    if path and os.path.isfile(path):
        with open(path, encoding="utf-8") as f:
            return f.read().strip()
    return "[]"


def get_llm_api_key() -> str:
    s = os.getenv("LLM_API_KEY", "").strip()
    if s:
        return s
    creds = _load_credentials()
    if creds and isinstance(creds.get("llm_api_key"), str):
        return creds["llm_api_key"].strip()
    return ""


def get_llm_model() -> str:
    s = os.getenv("LLM_MODEL", "").strip()
    if s:
        return s
    creds = _load_credentials()
    if creds and isinstance(creds.get("llm_model"), str):
        return creds["llm_model"].strip()
    return "llama-3.1-8b-instant"
