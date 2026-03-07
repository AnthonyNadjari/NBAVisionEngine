"""
NBAVision Engine — Posting replies (Spec Section 10).
Uses Playwright insert_text for instant text entry (works in headless).
"""
import random
import time
from pathlib import Path
from playwright.sync_api import Page
from config import (
    WAIT_BEFORE_NEXT_TWEET_SEC_MIN,
    WAIT_BEFORE_NEXT_TWEET_SEC_MAX,
    DRY_RUN,
    PROJECT_ROOT,
)

LOGS_DIR = PROJECT_ROOT / "logs"


def _ensure_logs_dir() -> Path:
    LOGS_DIR.mkdir(exist_ok=True)
    return LOGS_DIR


def _screenshot_on_error(page: Page, label: str) -> None:
    try:
        safe = label.replace("/", "_").replace("\\", "_")[:60]
        path = _ensure_logs_dir() / f"error_{safe}.png"
        page.screenshot(path=str(path))
    except Exception:
        pass


def wait_before_next_tweet() -> None:
    delay = random.uniform(WAIT_BEFORE_NEXT_TWEET_SEC_MIN, WAIT_BEFORE_NEXT_TWEET_SEC_MAX)
    time.sleep(delay)


def _insert_text(page: Page, text: str) -> None:
    """Insert text instantly via Playwright's input method (works in headless)."""
    page.keyboard.insert_text(text)
    time.sleep(random.uniform(0.3, 0.6))


def post_reply(page: Page, tweet_url: str, reply_text: str) -> tuple[bool, str | None]:
    """
    Navigate to tweet, click reply, paste text, send.
    In DRY_RUN mode: navigates and validates the page but does not type or send.
    Returns (success, error_message).
    """
    tweet_id = tweet_url.rstrip("/").split("/")[-1]

    if DRY_RUN:
        print(f"  [DRY RUN] Would post to {tweet_url}: {reply_text!r}", flush=True)
        return True, None

    try:
        page.goto(tweet_url, wait_until="domcontentloaded", timeout=30000)
        time.sleep(random.uniform(2, 4))

        reply_btn = page.locator('[data-testid="reply"]').first
        if not reply_btn.is_visible(timeout=8000):
            _screenshot_on_error(page, f"no_reply_btn_{tweet_id}")
            return False, "reply_button_not_found"
        reply_btn.click()
        time.sleep(random.uniform(0.4, 0.8))

        editor = page.locator('[data-testid="tweetTextarea_0"]').first
        if editor.count() == 0:
            editor = page.locator('div[contenteditable="true"][role="textbox"]').first
        if not editor.count() or not editor.is_visible(timeout=5000):
            _screenshot_on_error(page, f"no_editor_{tweet_id}")
            return False, "reply_box_not_found"
        editor.click()
        time.sleep(random.uniform(0.2, 0.4))

        _insert_text(page, reply_text)
        time.sleep(random.uniform(0.5, 1.0))

        send_btn = page.locator('[data-testid="tweetButton"]').first
        if not send_btn.is_visible(timeout=5000):
            _screenshot_on_error(page, f"no_send_btn_{tweet_id}")
            return False, "send_button_not_found"
        send_btn.click()

        time.sleep(random.uniform(2, 3))

        try:
            toast = page.locator('[data-testid="toast"]').first
            if toast.is_visible(timeout=3000):
                print(f"  Post confirmed (toast visible)", flush=True)
        except Exception:
            pass

        return True, None
    except Exception as e:
        _screenshot_on_error(page, f"exception_{tweet_id}")
        return False, str(e)
