"""
NBAVision Engine — Configuration centralisée (Spec Section 2, 4, 11).
"""
import os
from dotenv import load_dotenv

load_dotenv()

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

# Twitter
TWITTER_HOME_URL = "https://twitter.com/home"
TWITTER_SEARCH_BASE = "https://twitter.com/search?q={query}&f=live"

# Secrets (injected via env / GitHub Secrets)
def get_twitter_cookies_json() -> str:
    raw = os.getenv("TWITTER_COOKIES_JSON", "")
    if not raw or raw.strip() in ("", "[]"):
        return "[]"
    return raw.strip()


def get_llm_api_key() -> str:
    return os.getenv("LLM_API_KEY", "").strip()


def get_llm_model() -> str:
    return os.getenv("LLM_MODEL", "llama-3.1-8b-instant").strip()
