"""
NBAVision Engine — Scoring des tweets (Spec Section 6).
"""
import math
from filter_tweets import minutes_since_post
from config import TOP_N_SCORED


def compute_score(tweet: dict) -> float:
    """
    Formules exactes (Section 6):
    engagement_velocity = (likes + 2*replies + 2*retweets) / max(minutes_since_post, 1)
    freshness_score = 1 - (minutes_since_post / 15)
    normalized_followers = log(author_followers)
    score = 0.5 * engagement_velocity + 0.3 * normalized_followers + 0.2 * freshness_score
    """
    minutes = minutes_since_post(tweet.get("timestamp") or "")
    likes = tweet.get("likes") or 0
    replies = tweet.get("replies") or 0
    retweets = tweet.get("retweets") or 0
    followers = tweet.get("followers") or 1

    engagement_velocity = (likes + 2 * replies + 2 * retweets) / max(minutes, 1)
    freshness_score = 1.0 - (minutes / 15.0)
    freshness_score = max(0.0, min(1.0, freshness_score))
    normalized_followers = math.log(max(followers, 1))

    score = (
        0.5 * engagement_velocity
        + 0.3 * normalized_followers
        + 0.2 * freshness_score
    )
    return score


def rank_and_top(tweets: list[dict], top_n: int = TOP_N_SCORED) -> list[dict]:
    """
    Compute score for each tweet, sort descending, return top N.
    """
    for t in tweets:
        t["_score"] = compute_score(t)
    sorted_tweets = sorted(tweets, key=lambda x: x["_score"], reverse=True)
    return sorted_tweets[:top_n]
