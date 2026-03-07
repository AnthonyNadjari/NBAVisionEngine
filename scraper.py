"""
NBAVision Engine — Scraping Twitter via Playwright DOM (Spec Section 4).
Playwright sync API is not thread-safe; keywords are scraped sequentially.
Each cycle samples a random subset of keywords to reduce detection footprint.
High-priority keywords (broad terms) are always included.
"""
import random
import re
import time
from urllib.parse import quote_plus

from playwright.sync_api import Page

from config import (
    KEYWORDS,
    KEYWORDS_PER_CYCLE,
    TWITTER_SEARCH_BASE,
    SEARCH_WAIT_SEC_MIN,
    SEARCH_WAIT_SEC_MAX,
    SCROLL_DELTA_MIN,
    SCROLL_DELTA_MAX,
    SCROLL_WAIT_SEC_MIN,
    SCROLL_WAIT_SEC_MAX,
    SCROLL_COUNT,
)

# These broad keywords tend to yield more and better results
HIGH_PRIORITY_KEYWORDS = {
    "NBA", "NBA playoffs", "NBA trade", "NBA game", "NBA tonight",
    "LeBron", "Stephen Curry", "Luka Doncic", "Victor Wembanyama",
}


def _wait_random(low: float, high: float) -> None:
    time.sleep(random.uniform(low, high))


def _parse_int_from_aria(aria_label: str | None) -> int:
    """Extract number from aria-label like '1,234 Followers'."""
    if not aria_label:
        return 0
    digits = re.sub(r"[^\d]", "", aria_label)
    return int(digits) if digits else 0


def _safe_locator_attr(locator, attr: str, default=None):
    """Safely get attribute from a locator, returning default on failure."""
    try:
        if locator.count():
            return locator.get_attribute(attr)
    except Exception:
        pass
    return default


def extract_tweets_from_page(page: Page) -> list[dict]:
    """Extract tweets from current page using article[data-testid='tweet']."""
    try:
        articles = page.locator('article[data-testid="tweet"]')
        count = articles.count()
    except Exception:
        return []

    tweets = []
    for i in range(count):
        try:
            art = articles.nth(i)

            link_el = art.locator('a[href*="/status/"]').first
            href = _safe_locator_attr(link_el, "href")
            tweet_id = None
            if href:
                match = re.search(r"/status/(\d+)", href)
                if match:
                    tweet_id = match.group(1)

            text_el = art.locator('div[data-testid="tweetText"]').first
            try:
                text = (text_el.inner_text() if text_el.count() else "") or ""
            except Exception:
                text = ""

            user_el = art.locator('a[href^="/"][role="link"]').first
            user_href = _safe_locator_attr(user_el, "href")
            username = (user_href or "").strip("/").split("/")[0] if user_href else ""

            like_el = art.locator('[data-testid="like"]').first
            reply_el = art.locator('[data-testid="reply"]').first
            retweet_el = art.locator('[data-testid="retweet"]').first
            likes = _parse_int_from_aria(_safe_locator_attr(like_el, "aria-label"))
            replies = _parse_int_from_aria(_safe_locator_attr(reply_el, "aria-label"))
            retweets = _parse_int_from_aria(_safe_locator_attr(retweet_el, "aria-label"))

            time_el = art.locator("time").first
            timestamp = _safe_locator_attr(time_el, "datetime") or ""

            if tweet_id and username:
                tweets.append({
                    "tweet_id": tweet_id,
                    "text": text,
                    "username": username,
                    "likes": likes,
                    "replies": replies,
                    "retweets": retweets,
                    "timestamp": timestamp,
                    "followers": None,
                })
        except Exception:
            continue
    return tweets


def scrape_keyword(page: Page, keyword: str) -> list[dict]:
    """Navigate to search URL, scroll, extract tweets."""
    query = quote_plus(keyword)
    url = TWITTER_SEARCH_BASE.format(query=query)
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
    except Exception as e:
        print(f"      Navigation timeout for {keyword!r}: {e}", flush=True)
        return []

    _wait_random(SEARCH_WAIT_SEC_MIN, SEARCH_WAIT_SEC_MAX)

    for _ in range(SCROLL_COUNT):
        delta = random.randint(SCROLL_DELTA_MIN, SCROLL_DELTA_MAX)
        page.mouse.wheel(0, delta)
        _wait_random(SCROLL_WAIT_SEC_MIN, SCROLL_WAIT_SEC_MAX)

    tweets = extract_tweets_from_page(page)
    if not tweets:
        _wait_random(2, 4)
        tweets = extract_tweets_from_page(page)
    return tweets


def _select_keywords(cycle_index: int) -> list[str]:
    """
    Smart keyword selection: always include a few high-priority keywords,
    then fill the rest randomly. Rotate which high-priority ones are included.
    """
    sample_size = min(KEYWORDS_PER_CYCLE, len(KEYWORDS))

    hp_in_keywords = [k for k in KEYWORDS if k in HIGH_PRIORITY_KEYWORDS]
    other = [k for k in KEYWORDS if k not in HIGH_PRIORITY_KEYWORDS]

    # Always include 5 high-priority keywords (rotated based on cycle)
    hp_count = min(5, len(hp_in_keywords))
    random.shuffle(hp_in_keywords)
    selected_hp = hp_in_keywords[:hp_count]

    remaining_slots = sample_size - len(selected_hp)
    selected_other = random.sample(other, min(remaining_slots, len(other)))

    result = selected_hp + selected_other
    random.shuffle(result)
    return result


def scrape_all_keywords(page: Page, cycle_index: int = 0) -> list[dict]:
    """
    Sample a smart subset of KEYWORDS, scrape them sequentially.
    Deduplicates by tweet_id.
    """
    keywords = _select_keywords(cycle_index)
    print(f"    Scraping {len(keywords)} keywords this cycle", flush=True)

    seen_ids: set[str] = set()
    all_tweets: list[dict] = []
    consecutive_kw_errors = 0
    empty_count = 0

    for i, keyword in enumerate(keywords, 1):
        if consecutive_kw_errors >= 5:
            print("    Circuit breaker: 5 consecutive keyword errors, pausing 60s", flush=True)
            _wait_random(55, 65)
            consecutive_kw_errors = 0

        try:
            print(f"    Keyword {i}/{len(keywords)}: {keyword!r}", flush=True)
            batch = scrape_keyword(page, keyword)
            new_in_batch = 0
            for t in batch:
                tid = t.get("tweet_id")
                if tid and tid not in seen_ids:
                    seen_ids.add(tid)
                    all_tweets.append(t)
                    new_in_batch += 1
            print(f"      -> {len(batch)} tweets, {new_in_batch} new (total: {len(all_tweets)})", flush=True)
            consecutive_kw_errors = 0
            if len(batch) == 0:
                empty_count += 1
        except Exception as ex:
            consecutive_kw_errors += 1
            print(f"      -> error ({consecutive_kw_errors}/5): {ex}", flush=True)
            continue

    if empty_count > len(keywords) * 0.7:
        print(f"    WARNING: {empty_count}/{len(keywords)} keywords returned 0 tweets — session may be degraded", flush=True)

    print(f"    Scrape done: {len(all_tweets)} unique tweets.", flush=True)
    return all_tweets
