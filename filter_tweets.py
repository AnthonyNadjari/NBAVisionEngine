"""
NBAVision Engine — Filtrage strict des tweets (Spec Section 5).
"""
import re
from datetime import datetime, timezone


def _minutes_since_post(iso_timestamp: str) -> float:
    """Parse datetime attribute and return minutes since post."""
    if not iso_timestamp:
        return 999.0
    try:
        # Twitter uses ISO format e.g. 2025-02-27T12:00:00.000Z
        dt = datetime.fromisoformat(iso_timestamp.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        return max(0.0, (now - dt).total_seconds() / 60.0)
    except Exception:
        return 999.0


def _count_hashtags(text: str) -> int:
    return len(re.findall(r"#\w+", text))


def _is_mostly_url(text: str) -> bool:
    """True if text is only or mostly URL(s)."""
    stripped = text.strip()
    if not stripped:
        return True
    # Remove URLs and see if anything left
    no_urls = re.sub(r"https?://\S+", "", stripped, flags=re.IGNORECASE)
    return len(no_urls.strip()) < 5


def filter_tweet(
    tweet: dict,
    seen_tweet_ids: set,
) -> tuple[bool, str | None]:
    """
    Tweet rejeté si (Section 5):
    - minutes_since_post > 15
    - followers < 5000 or > 200000
    - likes < 10
    - texte < 20 caractères
    - contient uniquement URL
    - contient > 3 hashtags
    - déjà vu dans session
    Returns (accepted, reject_reason). accepted=True means keep.
    """
    from config import (
        MAX_MINUTES_SINCE_POST,
        MIN_FOLLOWERS,
        MAX_FOLLOWERS,
        MIN_LIKES,
        MIN_TEXT_LENGTH,
        MAX_HASHTAGS,
    )

    tid = tweet.get("tweet_id")
    if tid and tid in seen_tweet_ids:
        return False, "already_seen"

    minutes = _minutes_since_post(tweet.get("timestamp") or "")
    if minutes > MAX_MINUTES_SINCE_POST:
        return False, "too_old"

    followers = tweet.get("followers")
    if followers is not None:
        if followers < MIN_FOLLOWERS:
            return False, "followers_too_low"
        if followers > MAX_FOLLOWERS:
            return False, "followers_too_high"

    if (tweet.get("likes") or 0) < MIN_LIKES:
        return False, "likes_too_low"

    text = (tweet.get("text") or "").strip()
    if len(text) < MIN_TEXT_LENGTH:
        return False, "text_too_short"
    if _is_mostly_url(text):
        return False, "only_url"
    if _count_hashtags(text) > MAX_HASHTAGS:
        return False, "too_many_hashtags"

    return True, None


def filter_tweets(tweets: list[dict], seen_tweet_ids: set) -> tuple[list[dict], dict]:
    """
    Apply filter to all tweets. Returns (accepted_list, skip_reasons_breakdown).
    """
    accepted = []
    skip_reasons = {}
    for t in tweets:
        ok, reason = filter_tweet(t, seen_tweet_ids)
        if ok:
            accepted.append(t)
        else:
            skip_reasons[reason or "unknown"] = skip_reasons.get(reason, 0) + 1
    return accepted, skip_reasons


def minutes_since_post(iso_timestamp: str) -> float:
    """Public helper for scoring."""
    return _minutes_since_post(iso_timestamp)
