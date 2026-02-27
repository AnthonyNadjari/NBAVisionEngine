"""
NBAVision Engine — Posting des réponses (Spec Section 10).
"""
import random
import time
from playwright.sync_api import Page
from config import (
    TYPING_DELAY_MS_MIN,
    TYPING_DELAY_MS_MAX,
    WAIT_BEFORE_NEXT_TWEET_SEC_MIN,
    WAIT_BEFORE_NEXT_TWEET_SEC_MAX,
)


def wait_before_next_tweet() -> None:
    """Wait 120–360 seconds before next tweet (Section 10)."""
    delay = random.randint(WAIT_BEFORE_NEXT_TWEET_SEC_MIN, WAIT_BEFORE_NEXT_TWEET_SEC_MAX)
    time.sleep(delay)


def post_reply(page: Page, tweet_url: str, reply_text: str) -> tuple[bool, str | None]:
    """
    Procédure exacte (Section 10):
    1. page.goto(tweet_url)
    2. wait 3–6 seconds
    3. click reply button
    4. simulate typing char by char, delay 50–120 ms between chars
    5. wait random 1–2 seconds
    6. click send
    Returns (success, error_message).
    """
    try:
        page.goto(tweet_url, wait_until="domcontentloaded", timeout=30000)
        time.sleep(random.uniform(3, 6))

        # Reply button
        reply_btn = page.locator('[data-testid="reply"]').first
        if not reply_btn.is_visible(timeout=8000):
            return False, "reply_button_not_found"
        reply_btn.click()
        time.sleep(random.uniform(0.5, 1.0))

        # Focus the reply composer (div with contenteditable or data-testid)
        editor = page.locator('[data-testid="tweetTextarea_0"]').first
        if editor.count() == 0:
            editor = page.locator('div[contenteditable="true"][role="textbox"]').first
        if not editor.count() or not editor.is_visible(timeout=5000):
            return False, "reply_box_not_found"
        editor.click()
        time.sleep(0.3)

        # Type char by char
        for ch in reply_text:
            page.keyboard.type(ch, delay=random.randint(TYPING_DELAY_MS_MIN, TYPING_DELAY_MS_MAX))
        time.sleep(random.uniform(1, 2))

        # Send
        send_btn = page.locator('[data-testid="tweetButton"]').first
        if not send_btn.is_visible(timeout=5000):
            return False, "send_button_not_found"
        send_btn.click()
        return True, None
    except Exception as e:
        return False, str(e)
