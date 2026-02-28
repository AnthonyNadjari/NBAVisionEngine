"""
NBAVision Engine — Point d'entrée principal.
Authentification par cookies, puis exécution du moteur (Section 3, 15).
"""
import sys
from auth import launch_and_auth
from engine import run_session


def main() -> int:
    result = launch_and_auth()
    if len(result) == 5 and result[0] is None:
        reason = result[4]
        if reason == "no_cookies":
            print("ERR: No cookies. Set TWITTER_COOKIES_JSON (repo secret or env).")
        else:
            print("ERR: Cookies present but session invalid or expired. Re-export cookies from the browser where you're logged in to X.")
        return 1
    pw, browser, context, page = result[0], result[1], result[2], result[3]

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
