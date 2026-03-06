"""
NBAVision Engine — Orchestration: scrape → filter → score → LLM → validate → post.
Respects session limits, logging, and error handling (Sections 11–15).
"""
import os
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


def _event(step: str, detail: dict | None = None) -> dict:
    at = datetime.now(timezone.utc).isoformat()
    return {"step": step, "at": at, "detail": detail or {}}


def run_session(page, context, *, browser, playwright_instance):
    """
    Run one full session: cycles until max_replies or stop conditions.
    Returns dict of session stats for logging.
    """
    run_id = os.environ.get("NBAVISION_RUN_ID")
    start_time = datetime.now(timezone.utc).isoformat()
    seen_tweet_ids = set()
    replied_author_count = {}
    session_replies = []
    replies_posted = []  # for session log: { tweet_url, reply_text, posted_at }
    total_scraped = 0
    total_filtered = 0
    total_scored = 0
    total_llm_calls = 0
    total_replied = 0
    total_skipped = 0
    skip_reasons = {}
    response_lengths = []
    engagement_velocities = []
    cycles = []
    events = [_event("session_start", {"max_replies": MAX_REPLIES})]

    consecutive_errors = 0
    posting_failures = 0
    cookie_valid = True
    cycle_index = 0

    while total_replied < MAX_REPLIES and cookie_valid and posting_failures < MAX_POSTING_FAILURES:
        if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
            events.append(_event("session_stop", {"reason": "max_consecutive_errors"}))
            break

        events.append(_event("cycle_start", {"cycle_index": cycle_index}))
        print(f"[Cycle {cycle_index}] Scraping...", flush=True)
        try:
            from scraper import scrape_all_keywords
            raw = scrape_all_keywords(browser, page, context)
            total_scraped += len(raw)
            events.append(_event("scrape_done", {"raw_count": len(raw)}))
        except Exception as e:
            consecutive_errors += 1
            events.append(_event("scrape_error", {"error": str(e)}))
            print(f"[Cycle {cycle_index}] Scrape error: {e}", flush=True)
            time.sleep(random.uniform(60, 120))
            continue

        accepted, cycle_skip = filter_tweets(raw, seen_tweet_ids)
        total_filtered += len(accepted)
        skip_detail = ", ".join(f"{k}={v}" for k, v in sorted(cycle_skip.items())) if cycle_skip else "none"
        print(f"[Cycle {cycle_index}] Scraped {len(raw)}, accepted {len(accepted)} (filter out: {skip_detail})", flush=True)
        for k, v in cycle_skip.items():
            skip_reasons[k] = skip_reasons.get(k, 0) + v
        events.append(_event("filter_done", {"accepted_count": len(accepted), "cycle_skip_reasons": cycle_skip}))

        top = rank_and_top(accepted)
        total_scored += len(top)
        cycles.append({
            "cycle_index": cycle_index,
            "scraped_count": len(raw),
            "accepted_count": len(accepted),
            "top_count": len(top),
            "at": datetime.now(timezone.utc).isoformat(),
        })
        events.append(_event("rank_done", {"top_count": len(top)}))
        top_preview = [f"@{t.get('username')}(L{t.get('likes') or 0})" for t in top[:5]]
        print(f"[Cycle {cycle_index}] Top {len(top)} to evaluate: {', '.join(top_preview)}{'...' if len(top) > 5 else ''}", flush=True)

        for tweet in top:
            if total_replied >= MAX_REPLIES:
                break
            tweet_id = tweet.get("tweet_id")
            author = tweet.get("username") or ""
            if replied_author_count.get(author, 0) >= MAX_REPLIES_PER_AUTHOR:
                total_skipped += 1
                skip_reasons["max_per_author"] = skip_reasons.get("max_per_author", 0) + 1
                print(f"  Skip: max replies per @{author} ({tweet_id})", flush=True)
                events.append(_event("skip", {"tweet_id": tweet_id, "reason": "max_per_author", "author": author}))
                continue

            tweet_url = f"https://x.com/{author}/status/{tweet_id}"
            seen_tweet_ids.add(tweet_id)

            # LLM
            total_llm_calls += 1
            print(f"  Evaluating @{author} ({tweet_id})...", flush=True)
            events.append(_event("llm_call", {"tweet_id": tweet_id, "author": author}))
            llm_result = call_llm(tweet.get("text") or "", author)
            if llm_result is None:
                total_skipped += 1
                skip_reasons["llm_timeout"] = skip_reasons.get("llm_timeout", 0) + 1
                consecutive_errors += 1
                print(f"  Skip: LLM timeout", flush=True)
                events.append(_event("llm_skip", {"tweet_id": tweet_id, "reason": "llm_timeout"}))
                continue
            decision = (llm_result.get("decision") or "").upper()
            reason = llm_result.get("reason") or ""
            response = (llm_result.get("response") or "").strip()

            if "SKIP" in decision or not response:
                total_skipped += 1
                skip_reasons[reason or "skip"] = skip_reasons.get(reason or "skip", 0) + 1
                consecutive_errors = 0
                print(f"  Skip: {decision} — {reason or '(no reason)'}", flush=True)
                events.append(_event("llm_skip", {"tweet_id": tweet_id, "reason": reason or "skip", "decision": decision}))
                continue

            response = response[:180].strip()  # Section 8: ≤180 characters
            reply_preview = (response[:60] + "…") if len(response) > 60 else response
            print(f"  Reply ({len(response)} chars): {reply_preview!r}", flush=True)
            valid, fail_reason = validate_reply(response, session_replies)
            if not valid:
                total_skipped += 1
                skip_reasons[fail_reason or "validation"] = skip_reasons.get(fail_reason or "validation", 0) + 1
                print(f"  Skip: validation — {fail_reason}", flush=True)
                events.append(_event("validation_fail", {"tweet_id": tweet_id, "reason": fail_reason}))
                continue

            print(f"  Posting reply to {tweet_url}...", flush=True)
            events.append(_event("post_attempt", {"tweet_id": tweet_id, "tweet_url": tweet_url}))
            success, err = post_reply(page, tweet_url, response)
            if not success:
                posting_failures += 1
                print(f"  Post failed: {err}", flush=True)
                if posting_failures >= MAX_POSTING_FAILURES:
                    events.append(_event("post_fail", {"tweet_id": tweet_id, "error": str(err)}))
                    break
                # Retry once (Section 13)
                success, err = post_reply(page, tweet_url, response)
                if not success:
                    total_skipped += 1
                    skip_reasons["post_failed"] = skip_reasons.get("post_failed", 0) + 1
                    events.append(_event("post_fail", {"tweet_id": tweet_id, "error": str(err)}))
                    continue

            total_replied += 1
            replied_author_count[author] = replied_author_count.get(author, 0) + 1
            session_replies.append(response)
            replies_posted.append({
                "tweet_url": tweet_url,
                "reply_text": response,
                "posted_at": datetime.now(timezone.utc).isoformat(),
            })
            response_lengths.append(len(response))
            engagement_velocities.append(_engagement_velocity(tweet))
            consecutive_errors = 0
            posting_failures = 0
            print(f"  Posted to {tweet_url}. Session: {total_replied}/{MAX_REPLIES} replies", flush=True)
            events.append(_event("post_ok", {"tweet_id": tweet_id, "tweet_url": tweet_url, "reply_length": len(response)}))

            wait_before_next_tweet()

        cycle_index += 1
        # Cycle interval ± jitter (Section 14)
        if total_replied < MAX_REPLIES:
            interval_sec = CYCLE_INTERVAL_MINUTES * 60 + random.uniform(-CYCLE_INTERVAL_JITTER_SEC, CYCLE_INTERVAL_JITTER_SEC)
            mins = max(1, int(interval_sec / 60))
            print(f"[Cycle {cycle_index}] Sleeping ~{mins} min until next cycle", flush=True)
            time.sleep(max(60, interval_sec))

    end_time = datetime.now(timezone.utc).isoformat()
    events.append(_event("session_end", {"total_replied": total_replied, "total_skipped": total_skipped}))
    avg_response_length = sum(response_lengths) / len(response_lengths) if response_lengths else 0
    avg_engagement_velocity = sum(engagement_velocities) / len(engagement_velocities) if engagement_velocities else 0

    print("--- Session summary ---", flush=True)
    print(f"  Replied: {total_replied}, skipped: {total_skipped}, LLM calls: {total_llm_calls}", flush=True)
    print(f"  Scraped: {total_scraped}, passed filter: {total_filtered}, scored: {total_scored}", flush=True)
    if skip_reasons:
        print(f"  Skip reasons: {dict(skip_reasons)}", flush=True)
    print("---", flush=True)

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
        replies_posted=replies_posted,
        run_id=run_id,
        cycles=cycles,
        events=events,
    )
    write_session_log(log_data)
    return log_data
