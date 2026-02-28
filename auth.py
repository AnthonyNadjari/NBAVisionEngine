"""
NBAVision Engine — Authentification Twitter par cookies (Spec Section 3).
"""
import json
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page

from config import get_twitter_cookies_json, TWITTER_HOME_URL


def _normalize_cookie_domain(domain: str | None) -> str:
    """Use .x.com / .twitter.com so Playwright sends cookies to x.com."""
    if not domain or not isinstance(domain, str):
        return ".x.com"
    d = domain.strip().lower()
    if d in ("x.com", ".x.com") or d.endswith(".x.com"):
        return ".x.com"
    if d in ("twitter.com", ".twitter.com") or d.endswith(".twitter.com"):
        return ".twitter.com"
    return domain if domain.startswith(".") else "." + domain


def parse_cookies(raw: str) -> list[dict]:
    """Parse TWITTER_COOKIES_JSON into list of cookie dicts. Normalize for Playwright (.x.com or .twitter.com)."""
    if not raw or raw.strip() in ("", "[]"):
        return []
    raw_list = json.loads(raw)
    out = []
    for c in raw_list:
        if not isinstance(c, dict) or not c.get("name") or c.get("value") is None:
            continue
        # Playwright expects: name, value, domain, path, [expires], [httpOnly], [secure], [sameSite]
        p = {
            "name": str(c["name"]),
            "value": str(c["value"]),
            "domain": _normalize_cookie_domain(c.get("domain")),
            "path": c.get("path") or "/",
        }
        if c.get("httpOnly") is not None:
            p["httpOnly"] = bool(c["httpOnly"])
        if c.get("secure") is not None:
            p["secure"] = bool(c["secure"])
        exp = c.get("expirationDate") or c.get("expires")
        if exp is not None:
            p["expires"] = int(float(exp))
        if c.get("sameSite"):
            s = str(c["sameSite"]).lower()
            if s == "no_restriction":
                p["sameSite"] = "None"
            elif s in ("strict", "lax", "none"):
                p["sameSite"] = s.capitalize() if s != "none" else "None"
        out.append(p)
    return out


def launch_and_auth() -> tuple:
    """
    Ordre strict (Section 3.2):
    1. launch headless chromium
    2. new_context
    3. add_cookies
    4. new_page
    5. goto home
    Returns (playwright, browser, context, page) or (None, None, None, None).
    When invalid, the fifth value is "no_cookies" or "session_invalid".
    """
    raw = get_twitter_cookies_json()
    cookies = parse_cookies(raw)
    if not cookies:
        return None, None, None, None, "no_cookies"

    pw = sync_playwright().start()
    browser: Browser = pw.chromium.launch(
        headless=True,
        args=["--disable-blink-features=AutomationControlled"],
    )
    context: BrowserContext = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        viewport={"width": 1280, "height": 720},
        locale="en-US",
    )
    context.add_cookies(cookies)
    page: Page = context.new_page()

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

    page.goto(TWITTER_HOME_URL, wait_until="domcontentloaded", timeout=30000)
    if _check_logged_in():
        return pw, browser, context, page

    # One retry: first load from new IP can get a soft block; reload sometimes helps
    page.reload(wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(2000)
    if _check_logged_in():
        return pw, browser, context, page

    browser.close()
    pw.stop()
    return None, None, None, None, "session_invalid"
