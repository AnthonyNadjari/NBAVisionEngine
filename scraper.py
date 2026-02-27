"""
NBAVision Engine — Scraping Twitter via Playwright DOM (Spec Section 4).
"""
import random
import re
import time
from urllib.parse import quote_plus

from playwright.sync_api import Page

from config import (
    KEYWORDS,
    TWITTER_SEARCH_BASE,
    SEARCH_WAIT_SEC_MIN,
    SEARCH_WAIT_SEC_MAX,
    SCROLL_WAIT_SEC_MIN,
    SCROLL_WAIT_SEC_MAX,
    SCROLL_DELTA_MIN,
    SCROLL_DELTA_MAX,
    MAX_PROFILES_OPENED_PER_CYCLE,
)


def _wait_random(low: float, high: float) -> None:
    time.sleep(random.uniform(low, high))


def _parse_int_from_aria(aria_label: str | None) -> int:
    """Extract number from aria-label like '1,234 Followers'."""
    if not aria_label:
        return 0
    digits = re.sub(r"[^\d]", "", aria_label)
    return int(digits) if digits else 0


def extract_tweets_from_page(page: Page) -> list[dict]:
    """
    Extract tweets from current page using article[data-testid="tweet"].
    Returns list of dicts with: tweet_id, text, username, likes, replies, retweets, timestamp, (followers filled later).
    """
    articles = page.locator('article[data-testid="tweet"]')
    count = articles.count()
    tweets = []
    for i in range(count):
        try:
            art = articles.nth(i)
            # tweet_id — from link to tweet or from article
            link_el = art.locator('a[href*="/status/"]').first
            href = link_el.get_attribute("href") if link_el.count() else None
            tweet_id = None
            if href:
                match = re.search(r"/status/(\d+)", href)
                if match:
                    tweet_id = match.group(1)

            # text via div[lang]
            text_el = art.locator('div[data-testid="tweetText"]').first
            text = (text_el.inner_text() if text_el.count() else "") or ""

            # username from anchor href
            user_el = art.locator('a[href^="/"][role="link"]').first
            user_href = user_el.get_attribute("href") if user_el.count() else None
            username = (user_href or "").strip("/").split("/")[0] if user_href else ""

            # engagement
            like_el = art.locator('[data-testid="like"]').first
            reply_el = art.locator('[data-testid="reply"]').first
            retweet_el = art.locator('[data-testid="retweet"]').first
            likes = _parse_int_from_aria(like_el.get_attribute("aria-label") if like_el.count() else None)
            replies = _parse_int_from_aria(reply_el.get_attribute("aria-label") if reply_el.count() else None)
            retweets = _parse_int_from_aria(retweet_el.get_attribute("aria-label") if retweet_el.count() else None)

            # timestamp
            time_el = art.locator("time").first
            datetime_attr = time_el.get_attribute("datetime") if time_el.count() else None
            timestamp = datetime_attr or ""

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


def fetch_followers_for_tweets(
    page: Page,
    context,
    tweets: list[dict],
    max_profiles: int = MAX_PROFILES_OPENED_PER_CYCLE,
) -> None:
    """
    Open profile in new tab, get followers from aria-label, close tab. Mutates tweets[].followers.
    """
    base_url = "https://x.com"
    opened = 0
    for t in tweets:
        if opened >= max_profiles:
            break
        if t.get("followers") is not None:
            continue
        username = t.get("username")
        if not username:
            continue
        profile_url = f"{base_url}/{username}"
        new_page = context.new_page()
        try:
            new_page.goto(profile_url, wait_until="domcontentloaded", timeout=15000)
            _wait_random(1.5, 3.5)
            # Followers: aria-label often on a link like "123 Followers"
            follower_el = new_page.locator('a[href*="/followers"]').first
            if follower_el.count():
                aria = follower_el.get_attribute("aria-label")
                t["followers"] = _parse_int_from_aria(aria)
            else:
                t["followers"] = 0
            opened += 1
        except Exception:
            t["followers"] = 0
        finally:
            new_page.close()


def scrape_keyword(page: Page, keyword: str) -> list[dict]:
    """
    Processus exact par keyword (Section 4.3):
    goto search url, wait 4–6s, scroll 3 times (random 1200–2000), wait 2–4s each, extract tweets.
    """
    query = quote_plus(keyword)
    url = TWITTER_SEARCH_BASE.format(query=query)
    page.goto(url, wait_until="domcontentloaded", timeout=30000)
    _wait_random(SEARCH_WAIT_SEC_MIN, SEARCH_WAIT_SEC_MAX)

    for _ in range(3):
        delta = random.randint(SCROLL_DELTA_MIN, SCROLL_DELTA_MAX)
        page.mouse.wheel(0, delta)
        _wait_random(SCROLL_WAIT_SEC_MIN, SCROLL_WAIT_SEC_MAX)

    tweets = extract_tweets_from_page(page)
    # Section 13: DOM change → retry once
    if not tweets:
        _wait_random(2, 4)
        tweets = extract_tweets_from_page(page)
    return tweets


def scrape_all_keywords(page: Page, context) -> list[dict]:
    """
    Scrape all KEYWORDS, optionally fetch followers (with max_profiles limit).
    Returns list of tweet dicts; duplicates by tweet_id are deduplicated (one entry per tweet).
    """
    seen_ids = set()
    all_tweets = []
    for keyword in KEYWORDS:
        try:
            batch = scrape_keyword(page, keyword)
            for t in batch:
                tid = t.get("tweet_id")
                if tid and tid not in seen_ids:
                    seen_ids.add(tid)
                    all_tweets.append(t)
        except Exception:
            continue

    fetch_followers_for_tweets(page, context, all_tweets, MAX_PROFILES_OPENED_PER_CYCLE)
    return all_tweets
