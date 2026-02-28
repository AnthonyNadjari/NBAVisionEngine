"""
NBAVision Engine — Secure webhook server for remote trigger.
Requires NBAVISION_SECRET in environment (or .env). Rate limited (5/hour).
"""
import os

from dotenv import load_dotenv
load_dotenv()

import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Header, Request, HTTPException
from fastapi.responses import JSONResponse

from runner import is_running, run_engine

LOG_FILE = Path(__file__).resolve().parent / "nbavision_server.log"
RATE_LIMIT_WINDOW = 3600  # 1 hour
RATE_LIMIT_MAX = 5

# In-memory rate limit: timestamps of recent triggers
_trigger_timestamps: deque[float] = deque()


def _log(msg: str) -> None:
    """Append to log file with timestamp."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"{ts} {msg}\n"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line)


def _check_rate_limit() -> bool:
    """True if under limit, False if exceeded."""
    now = time.time()
    while _trigger_timestamps and _trigger_timestamps[0] < now - RATE_LIMIT_WINDOW:
        _trigger_timestamps.popleft()
    return len(_trigger_timestamps) < RATE_LIMIT_MAX


def _record_trigger() -> None:
    _trigger_timestamps.append(time.time())


app = FastAPI(title="NBAVision Webhook", docs_url=None, redoc_url=None)


@app.post("/trigger")
async def trigger(request: Request, x_api_key: str | None = Header(None, alias="X-API-KEY")):
    """
    Trigger NBAVision Engine. Requires X-API-KEY header matching NBAVISION_SECRET.
    Returns 409 if a run is already in progress.
    """
    client_ip = request.client.host if request.client else "unknown"
    secret = os.getenv("NBAVISION_SECRET", "").strip()

    if not secret:
        _log(f"ERROR server misconfigured: NBAVISION_SECRET not set")
        raise HTTPException(status_code=500, detail="Server misconfigured")

    if not x_api_key or x_api_key != secret:
        _log(f"unauthorized ip={client_ip}")
        raise HTTPException(status_code=401, detail="Unauthorized")

    if not _check_rate_limit():
        _log(f"rate_limit_exceeded ip={client_ip}")
        raise HTTPException(status_code=429, detail="Rate limit exceeded (5/hour)")

    if is_running():
        _log(f"conflict run_in_progress ip={client_ip}")
        raise HTTPException(status_code=409, detail="Run already in progress")

    _record_trigger()
    _log(f"authorized trigger ip={client_ip}")

    success, message = await run_engine()
    if not success:
        _log(f"ERROR run_failed {message} ip={client_ip}")
        raise HTTPException(status_code=500, detail=message)

    _log(f"run_started ip={client_ip}")
    return JSONResponse(
        status_code=200,
        content={
            "status": "started",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message": message,
        },
    )


@app.get("/health")
async def health():
    """Simple health check."""
    return {"status": "ok", "running": is_running()}
