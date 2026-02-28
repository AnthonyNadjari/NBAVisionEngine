"""
NBAVision Engine — Safe subprocess launcher for webhook-triggered runs.
Prevents concurrent execution; used by server.py.
"""
import asyncio
import os
import subprocess
import sys
import threading
from pathlib import Path

# Project root (where main_engine.py lives)
PROJECT_ROOT = Path(__file__).resolve().parent
LOCK_FILE = PROJECT_ROOT / ".nbavision_run.lock"


def _acquire_lock() -> bool:
    """Acquire file-based lock. Returns True if acquired."""
    try:
        fd = os.open(LOCK_FILE, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        return True
    except FileExistsError:
        return False


def _release_lock() -> None:
    """Release lock by removing lock file."""
    try:
        LOCK_FILE.unlink(missing_ok=True)
    except OSError:
        pass


def is_running() -> bool:
    """Check if a run is in progress (lock exists)."""
    return LOCK_FILE.exists()


def _run_and_release() -> None:
    """Blocking: run engine, release lock when done."""
    log_file = PROJECT_ROOT / "logs" / "engine_output.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with open(log_file, "a", encoding="utf-8") as f:
        proc = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "main_engine.py")],
            cwd=str(PROJECT_ROOT),
            stdout=f,
            stderr=subprocess.STDOUT,
            env=os.environ.copy(),
        )
    _release_lock()


async def run_engine() -> tuple[bool, str]:
    """
    Launch NBAVision Engine as subprocess. Non-blocking.
    Returns (success, message).
    """
    if _acquire_lock():
        try:
            # Dedicated thread: engine can run hours; don't block executor
            t = threading.Thread(target=_run_and_release, daemon=True)
            t.start()
            return True, "NBAVision Engine launched"
        except Exception as e:
            _release_lock()
            return False, str(e)
    return False, "Run already in progress"
