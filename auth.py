"""
NBAVision Engine — Authentification Twitter par cookies (Spec Section 3).
"""
import json
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page

from config import get_twitter_cookies_json, TWITTER_HOME_URL


def parse_cookies(raw: str) -> list[dict]:
    """Parse TWITTER_COOKIES_JSON into list of cookie dicts."""
    if not raw or raw.strip() in ("", "[]"):
        return []
    return json.loads(raw)


def launch_and_auth():
    """
    Ordre strict (Section 3.2):
    1. launch headless chromium
    2. new_context
    3. add_cookies
    4. new_page
    5. goto home
    Returns (playwright, browser, context, page) or (None, None, None, None) if invalid.
    """
    raw = get_twitter_cookies_json()
    cookies = parse_cookies(raw)
    if not cookies:
        return None, None, None, None

    pw = sync_playwright().start()
    browser: Browser = pw.chromium.launch(headless=True)
    context: BrowserContext = browser.new_context()
    context.add_cookies(cookies)
    page: Page = context.new_page()
    page.goto(TWITTER_HOME_URL, wait_until="domcontentloaded", timeout=30000)

    # Validation: vérifier présence élément DOM avatar (Section 3.2)
    try:
        avatar = page.locator('[data-testid="SideNav_AccountSwitcher_Button"]').first
        if not avatar.is_visible(timeout=10000):
            browser.close()
            pw.stop()
            return None, None, None, None
    except Exception:
        # Fallback: check for timeline or any logged-in indicator
        try:
            timeline = page.locator('[data-testid="primaryColumn"]').first
            if not timeline.is_visible(timeout=8000):
                browser.close()
                pw.stop()
                return None, None, None, None
        except Exception:
            browser.close()
            pw.stop()
            return None, None, None, None

    return pw, browser, context, page
