"""
NBAVision Engine — Scrape bot profile for follower/following count and update daily stats.
Run at the beginning of each run; one value per day (overwritten if same day).
"""
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import Page

from config import BOT_PROFILE_USERNAME, STATS_FILE


def _parse_count(text: str) -> int | None:
    """Parse '1,234', '1.2K', '1.2M' etc. to int."""
    if not text or not isinstance(text, str):
        return None
    text = text.strip().replace(",", "").replace(" ", "")
    if not text:
        return None
    text_upper = text.upper()
    mult = 1
    if text_upper.endswith("K"):
        mult = 1000
        text = text[:-1].strip()
    elif text_upper.endswith("M"):
        mult = 1_000_000
        text = text[:-1].strip()
    try:
        return int(float(text) * mult)
    except (ValueError, TypeError):
        return None


def scrape_profile_stats(page: Page, username: str) -> dict | None:
    """
    Navigate to profile, scrape followers (and following). Returns {'followers': int, 'following': int} or None.
    """
    url = f"https://x.com/{username}"
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=15000)
        page.wait_for_timeout(2000)
    except Exception as e:
        print(f"Profile stats: failed to load profile: {e}", flush=True)
        return None

    result = {"followers": None, "following": None}

    # Try aria-label on links (e.g. "1,234 Followers")
    for label in ["followers", "following"]:
        try:
            link = page.locator(f'a[href*="/{label}"]').first
            if link.count() == 0:
                continue
            aria = link.get_attribute("aria-label") or ""
            # e.g. "1,234 Followers" or "12.5K Followers"
            num_match = re.search(r"([\d,.]+)\s*[KkMm]?\s*", aria)
            if num_match:
                val = _parse_count(num_match.group(1).replace(",", ""))
                if val is not None:
                    result[label] = val
            if result[label] is None:
                # Fallback: text content of the link
                text = link.inner_text()
                val = _parse_count(text.split()[0] if text else "")
                if val is not None:
                    result[label] = val
        except Exception:
            pass

    if result["followers"] is None and result["following"] is None:
        print("Profile stats: could not find followers/following on profile", flush=True)
        return None
    return result


def load_stats() -> list[dict]:
    """Load stats from STATS_FILE. Returns list of {date, followers, following?}."""
    if not STATS_FILE.is_file():
        return []
    try:
        with open(STATS_FILE, encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Profile stats: could not load {STATS_FILE}: {e}", flush=True)
        return []
    if not isinstance(data, list):
        return []
    return data


def save_stats(entries: list[dict]) -> None:
    """Write stats to STATS_FILE. Ensures docs/ exists."""
    STATS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2)
    print(f"Profile stats: saved to {STATS_FILE}", flush=True)


def update_today(entries: list[dict], followers: int | None, following: int | None) -> list[dict]:
    """Update or append today's entry. One value per day (last run of the day wins)."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    new_entry = {"date": today, "followers": followers, "following": following}
    out = [e for e in entries if isinstance(e, dict) and e.get("date") != today]
    out.append(new_entry)
    out.sort(key=lambda e: e.get("date") or "")
    return out


def run_at_start(page: Page) -> None:
    """
    Scrape profile stats and update docs/stats.json with today's value.
    No-op if BOT_PROFILE_USERNAME is not set.
    """
    if not BOT_PROFILE_USERNAME:
        return
    print(f"Profile stats: scraping @{BOT_PROFILE_USERNAME}...", flush=True)
    stats = scrape_profile_stats(page, BOT_PROFILE_USERNAME)
    if not stats:
        return
    print(f"Profile stats: followers={stats.get('followers')}, following={stats.get('following')}", flush=True)
    entries = load_stats()
    entries = update_today(entries, stats.get("followers"), stats.get("following"))
    save_stats(entries)
