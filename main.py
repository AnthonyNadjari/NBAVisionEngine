"""
NBAVision Engine — Point d'entrée principal.
Authentification par cookies, puis exécution du moteur (Section 3, 15).
"""
import os
import sys
from auth import launch_and_auth
from engine import run_session
from config import MAX_REPLIES, CYCLE_INTERVAL_MINUTES, MAX_CONSECUTIVE_ERRORS, MAX_POSTING_FAILURES


def main() -> int:
    run_id = os.environ.get("NBAVISION_RUN_ID", "")
    print(f"NBAVision Engine starting. Run ID: {run_id or '(local)'}", flush=True)
    print(f"Config: max_replies={MAX_REPLIES}, cycle_interval_min={CYCLE_INTERVAL_MINUTES}, max_consecutive_errors={MAX_CONSECUTIVE_ERRORS}, max_posting_failures={MAX_POSTING_FAILURES}", flush=True)

    result = launch_and_auth()
    if len(result) == 5 and result[0] is None:
        reason = result[4]
        if reason == "no_cookies":
            print("ERR: No cookies. Set TWITTER_COOKIES_JSON (repo secret or env).", flush=True)
        else:
            print("ERR: Cookies present but session invalid or expired. Re-export cookies from the browser where you're logged in to X.", flush=True)
        return 1
    pw, browser, context, page = result[0], result[1], result[2], result[3]
    print("Auth OK. Session started.", flush=True)

    try:
        log_data = run_session(page, context, browser=browser, playwright_instance=pw)
        print("Session ended.", log_data, flush=True)
        return 0
    except Exception as e:
        print("Session error:", e, flush=True)
        return 1
    finally:
        if browser:
            browser.close()
        if pw:
            pw.stop()


if __name__ == "__main__":
    sys.exit(main())
