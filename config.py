"""
NBAVision Engine — Configuration centralisée (Spec Section 2, 4, 11).
Credentials: credentials.json (or env vars).
"""
import json
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent


def _credentials_path() -> Path | None:
    for base in (PROJECT_ROOT, Path.cwd()):
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


KEYWORDS = [
    "NBA",
    "Lakers",
    "Celtics",
    "Warriors",
    "Bucks",
    "Suns",
    "Nuggets",
    "76ers",
    "Heat",
    "Knicks",
    "Mavericks",
    "Thunder",
    "Cavaliers",
    "Clippers",
    "Grizzlies",
    "Timberwolves",
    "Pelicans",
    "Kings",
    "Pacers",
    "Magic",
    "Rockets",
    "Spurs",
    "Hawks",
    "Bulls",
    "Raptors",
    "Hornets",
    "Wizards",
    "Pistons",
    "Trail Blazers",
    "Jazz",
    "LeBron",
    "Kevin Durant",
    "Stephen Curry",
    "Nikola Jokic",
    "Giannis",
    "Jayson Tatum",
    "Joel Embiid",
    "Luka Doncic",
    "Anthony Edwards",
    "Shai Gilgeous-Alexander",
    "Victor Wembanyama",
    "Ja Morant",
    "Donovan Mitchell",
    "Devin Booker",
    "Damian Lillard",
    "Jimmy Butler",
    "Kawhi Leonard",
    "NBA trade",
    "NBA injury",
    "NBA playoffs",
    "NBA rumors",
    "NBA finals",
    "NBA draft",
    "NBA All-Star",
    "NBA score",
    "NBA game",
    "NBA highlights",
    "NBA news",
    "NBA tonight",
    "NBA trade deadline",
    "NBA free agency",
    "NBA MVP",
    "NBA standings",
]

# How many keywords to sample per cycle (reduces detection footprint)
KEYWORDS_PER_CYCLE = int(os.getenv("KEYWORDS_PER_CYCLE", "20"))

# Session limits
MAX_REPLIES = 60
MAX_REPLIES_PER_AUTHOR = 1
CYCLE_INTERVAL_MINUTES = 1.5
MAX_CONSECUTIVE_ERRORS = 5
MAX_POSTING_FAILURES = 3

# Filtering (Section 5)
MAX_MINUTES_SINCE_POST = 15
MIN_FOLLOWERS = 5000
MAX_FOLLOWERS = 200_000
MIN_LIKES = 10
MIN_TEXT_LENGTH = 20
MAX_HASHTAGS = 3
MAX_PROFILES_OPENED_PER_CYCLE = 10

# Scoring — top N kept per cycle
TOP_N_SCORED = 28

# LLM
LLM_TIMEOUT_SECONDS = 20
LLM_RETRY_MAX = 2

# Reply validation
MAX_RESPONSES_SAME_FIRST_WORD = 3
MAX_EMOJIS_IN_SESSION = 3
MAX_SENTENCES = 2
TFIDF_SIMILARITY_THRESHOLD = 0.7

# Posting
TYPING_DELAY_MS_MIN = 50
TYPING_DELAY_MS_MAX = 120
WAIT_BEFORE_NEXT_TWEET_SEC_MIN = 60
WAIT_BEFORE_NEXT_TWEET_SEC_MAX = 180

# Scraping delays
SEARCH_WAIT_SEC_MIN = 4
SEARCH_WAIT_SEC_MAX = 6
SCROLL_WAIT_SEC_MIN = 2
SCROLL_WAIT_SEC_MAX = 4
SCROLL_DELTA_MIN = 1200
SCROLL_DELTA_MAX = 2000
CYCLE_INTERVAL_JITTER_SEC = 20

# X (Twitter)
TWITTER_HOME_URL = "https://x.com/home"
TWITTER_SEARCH_BASE = "https://x.com/search?q={query}&f=live"
BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)
BROWSER_VIEWPORT = {"width": 1280, "height": 720}

# Cookie / state persistence
STATE_FILE = PROJECT_ROOT / "state.json"

# Dry-run: scrape + LLM but do NOT post replies
DRY_RUN = os.getenv("DRY_RUN", "").strip().lower() in ("1", "true", "yes")

# Discord webhook for failure notifications (optional)
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "").strip()


# --------------- credential helpers ---------------

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
