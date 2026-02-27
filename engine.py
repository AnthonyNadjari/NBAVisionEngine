"""
NBAVision Engine — Orchestration: scrape → filter → score → LLM → validate → post.
Respects session limits, logging, and error handling (Sections 11–15).
"""
import random
import time
from datetime import datetime, timezone
from filter_tweets import filter_tweets, minutes_since_post
from scorer import rank_and_top, compute_score
from llm_client import call_llm
from reply_validator import validate_reply
from poster import post_reply, wait_before_next_tweet
from session_log import write_session_log, build_session_log
from config import (
    MAX_REPLIES,
    MAX_REPLIES_PER_AUTHOR,
    CYCLE_INTERVAL_MINUTES,
    CYCLE_INTERVAL_JITTER_SEC,
    MAX_CONSECUTIVE_ERRORS,
    MAX_POSTING_FAILURES,
)


def _engagement_velocity(tweet: dict) -> float:
    minutes = max(1, minutes_since_post(tweet.get("timestamp") or ""))
    likes = tweet.get("likes") or 0
    replies = tweet.get("replies") or 0
    retweets = tweet.get("retweets") or 0
    return (likes + 2 * replies + 2 * retweets) / minutes


def run_session(page, context, *, browser, playwright_instance):
    """
    Run one full session: cycles until max_replies or stop conditions.
    Returns dict of session stats for logging.
    """
    start_time = datetime.now(timezone.utc).isoformat()
    seen_tweet_ids = set()
    replied_author_count = {}
    session_replies = []
    total_scraped = 0
    total_filtered = 0
    total_scored = 0
    total_llm_calls = 0
    total_replied = 0
    total_skipped = 0
    skip_reasons = {}
    response_lengths = []
    engagement_velocities = []

    consecutive_errors = 0
    posting_failures = 0
    cookie_valid = True

    while total_replied < MAX_REPLIES and cookie_valid and posting_failures < MAX_POSTING_FAILURES:
        if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
            break

        try:
            from scraper import scrape_all_keywords
            raw = scrape_all_keywords(page, context)
            total_scraped += len(raw)
        except Exception:
            consecutive_errors += 1
            time.sleep(random.uniform(60, 120))
            continue

        accepted, cycle_skip = filter_tweets(raw, seen_tweet_ids)
        total_filtered += len(accepted)
        for k, v in cycle_skip.items():
            skip_reasons[k] = skip_reasons.get(k, 0) + v

        top = rank_and_top(accepted)
        total_scored += len(top)

        for tweet in top:
            if total_replied >= MAX_REPLIES:
                break
            author = tweet.get("username") or ""
            if replied_author_count.get(author, 0) >= MAX_REPLIES_PER_AUTHOR:
                total_skipped += 1
                skip_reasons["max_per_author"] = skip_reasons.get("max_per_author", 0) + 1
                continue

            tweet_id = tweet.get("tweet_id")
            tweet_url = f"https://x.com/{author}/status/{tweet_id}"
            seen_tweet_ids.add(tweet_id)

            # LLM
            total_llm_calls += 1
            llm_result = call_llm(tweet.get("text") or "", author)
            if llm_result is None:
                total_skipped += 1
                skip_reasons["llm_timeout"] = skip_reasons.get("llm_timeout", 0) + 1
                consecutive_errors += 1
                continue
            decision = (llm_result.get("decision") or "").upper()
            reason = llm_result.get("reason") or ""
            response = (llm_result.get("response") or "").strip()

            if "SKIP" in decision or not response:
                total_skipped += 1
                skip_reasons[reason or "skip"] = skip_reasons.get(reason or "skip", 0) + 1
                consecutive_errors = 0
                continue

            response = response[:180].strip()  # Section 8: ≤180 characters
            valid, fail_reason = validate_reply(response, session_replies)
            if not valid:
                total_skipped += 1
                skip_reasons[fail_reason or "validation"] = skip_reasons.get(fail_reason or "validation", 0) + 1
                continue

            success, err = post_reply(page, tweet_url, response)
            if not success:
                posting_failures += 1
                if posting_failures >= MAX_POSTING_FAILURES:
                    break
                # Retry once (Section 13)
                success, err = post_reply(page, tweet_url, response)
                if not success:
                    total_skipped += 1
                    skip_reasons["post_failed"] = skip_reasons.get("post_failed", 0) + 1
                    continue

            total_replied += 1
            replied_author_count[author] = replied_author_count.get(author, 0) + 1
            session_replies.append(response)
            response_lengths.append(len(response))
            engagement_velocities.append(_engagement_velocity(tweet))
            consecutive_errors = 0
            posting_failures = 0

            wait_before_next_tweet()

        # Cycle interval ± jitter (Section 14)
        if total_replied < MAX_REPLIES:
            interval_sec = CYCLE_INTERVAL_MINUTES * 60 + random.uniform(-CYCLE_INTERVAL_JITTER_SEC, CYCLE_INTERVAL_JITTER_SEC)
            time.sleep(max(60, interval_sec))

    end_time = datetime.now(timezone.utc).isoformat()
    avg_response_length = sum(response_lengths) / len(response_lengths) if response_lengths else 0
    avg_engagement_velocity = sum(engagement_velocities) / len(engagement_velocities) if engagement_velocities else 0

    log_data = build_session_log(
        start_time=start_time,
        end_time=end_time,
        total_scraped=total_scraped,
        total_filtered=total_filtered,
        total_scored=total_scored,
        total_llm_calls=total_llm_calls,
        total_replied=total_replied,
        total_skipped=total_skipped,
        skip_reasons=skip_reasons,
        avg_response_length=avg_response_length,
        avg_engagement_velocity=avg_engagement_velocity,
    )
    write_session_log(log_data)
    return log_data
