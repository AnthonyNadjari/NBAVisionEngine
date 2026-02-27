"""
NBAVision Engine — Point d'entrée principal.
Authentification par cookies, puis exécution du moteur (Section 3, 15).
"""
import sys
from auth import launch_and_auth
from engine import run_session


def main() -> int:
    pw, browser, context, page = launch_and_auth()
    if page is None:
        print("ERR: Cookie invalid or login required. Set TWITTER_COOKIES_JSON.")
        return 1

    try:
        log_data = run_session(page, context, browser=browser, playwright_instance=pw)
        print("Session ended.", log_data)
        return 0
    except Exception as e:
        print("Session error:", e)
        return 1
    finally:
        if browser:
            browser.close()
        if pw:
            pw.stop()


if __name__ == "__main__":
    sys.exit(main())
