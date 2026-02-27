"""
NBAVision Engine — Logging session (Spec Section 12).
"""
import json
import os
from datetime import datetime, timezone
from pathlib import Path


def ensure_logs_dir() -> Path:
    d = Path(__file__).resolve().parent / "logs"
    d.mkdir(exist_ok=True)
    return d


def session_log_path() -> Path:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return ensure_logs_dir() / f"session_{ts}.json"


def write_session_log(data: dict) -> str:
    path = session_log_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return str(path)


def build_session_log(
    start_time: str,
    end_time: str,
    total_scraped: int,
    total_filtered: int,
    total_scored: int,
    total_llm_calls: int,
    total_replied: int,
    total_skipped: int,
    skip_reasons: dict,
    avg_response_length: float,
    avg_engagement_velocity: float,
) -> dict:
    return {
        "start_time": start_time,
        "end_time": end_time,
        "total_scraped": total_scraped,
        "total_filtered": total_filtered,
        "total_scored": total_scored,
        "total_llm_calls": total_llm_calls,
        "total_replied": total_replied,
        "total_skipped": total_skipped,
        "skip_reasons": skip_reasons,
        "avg_response_length": round(avg_response_length, 2),
        "avg_engagement_velocity": round(avg_engagement_velocity, 2),
    }
