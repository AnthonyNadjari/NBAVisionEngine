"""
NBAVision Engine — Authentication via persistent Chromium profile.
Log in to X manually once; no cookie export needed.
"""
import os
from pathlib import Path

from playwright.sync_api import sync_playwright, BrowserContext, Page

from config import TWITTER_HOME_URL


def _profile_dir() -> Path:
    """Persistent profile path from env or default."""
    raw = os.getenv("NBAVISION_BROWSER_PROFILE", "").strip()
    if raw:
        return Path(raw).resolve()
    return (Path(__file__).resolve().parent / "browser_profile").resolve()


def launch_persistent_context():
    """
    Launch Chromium with persistent user data. Uses existing session; no cookie injection.
    Returns (playwright, context, page) or (None, None, None) if login check fails.
    """
    profile = _profile_dir()
    profile.mkdir(parents=True, exist_ok=True)

    pw = sync_playwright().start()
    context: BrowserContext = pw.chromium.launch_persistent_context(
        user_data_dir=str(profile),
        headless=True,
        args=["--disable-blink-features=AutomationControlled"],
        viewport={"width": 1280, "height": 720},
        locale="en-US",
    )

    # Reuse existing page or create one
    pages = context.pages
    if pages:
        page: Page = pages[0]
    else:
        page = context.new_page()

    page.goto(TWITTER_HOME_URL, wait_until="domcontentloaded", timeout=30000)

    def _check_logged_in() -> bool:
        try:
            avatar = page.locator('[data-testid="SideNav_AccountSwitcher_Button"]').first
            if avatar.is_visible(timeout=10000):
                return True
        except Exception:
            pass
        try:
            timeline = page.locator('[data-testid="primaryColumn"]').first
            return timeline.is_visible(timeout=8000)
        except Exception:
            return False

    if _check_logged_in():
        return pw, context, page

    # One retry
    page.reload(wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(2000)
    if _check_logged_in():
        return pw, context, page

    context.close()
    pw.stop()
    return None, None, None
