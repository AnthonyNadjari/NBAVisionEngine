"""
NBAVision Engine — Main entry point.
Authentication via cookies, then engine execution.
"""
import os
import sys
from auth import launch_and_auth, save_session_state
from engine import run_session
from notify import notify_auth_failure
from config import (
    MAX_REPLIES,
    CYCLE_INTERVAL_MINUTES,
    MAX_CONSECUTIVE_ERRORS,
    MAX_POSTING_FAILURES,
    DRY_RUN,
    KEYWORDS_PER_CYCLE,
)


def main() -> int:
    run_id = os.environ.get("NBAVISION_RUN_ID", "")
    print(f"NBAVision Engine starting. Run ID: {run_id or '(local)'}", flush=True)
    print(
        f"Config: max_replies={MAX_REPLIES}, cycle_interval_min={CYCLE_INTERVAL_MINUTES}, "
        f"max_consecutive_errors={MAX_CONSECUTIVE_ERRORS}, max_posting_failures={MAX_POSTING_FAILURES}, "
        f"keywords_per_cycle={KEYWORDS_PER_CYCLE}, dry_run={DRY_RUN}",
        flush=True,
    )

    result = launch_and_auth()
    if len(result) == 5 and result[0] is None:
        reason = result[4]
        if reason == "no_cookies":
            msg = "No cookies. Set TWITTER_COOKIES_JSON (repo secret or env)."
        elif reason == "cookies_expired":
            msg = "Critical cookies are expired. Re-export from browser."
        else:
            msg = "Cookies present but session invalid or expired. Re-export cookies from the browser where you're logged in to X."
        print(f"ERR: {msg}", flush=True)
        notify_auth_failure(reason)
        return 1

    pw, browser, context, page = result[0], result[1], result[2], result[3]
    print("Auth OK. Session started.", flush=True)

    try:
        log_data = run_session(page, context, browser=browser, playwright_instance=pw)
        print("Session ended.", flush=True)
        save_session_state(context)
        return 0
    except Exception as e:
        print(f"Session error: {e}", flush=True)
        return 1
    finally:
        try:
            save_session_state(context)
        except Exception:
            pass
        if browser:
            browser.close()
        if pw:
            pw.stop()


if __name__ == "__main__":
    sys.exit(main())
