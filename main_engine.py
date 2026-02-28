"""
NBAVision Engine — Entry point for webhook-triggered local runs.
Uses persistent Chromium profile (log in once, no cookie export).
"""
import sys

from auth_persistent import launch_persistent_context
from engine import run_session


def main() -> int:
    pw, context, page = launch_persistent_context()
    if page is None:
        print("ERR: Not logged in. Run Chromium once with this profile and log into X manually.")
        print("  Profile dir: set NBAVISION_BROWSER_PROFILE or use ./browser_profile")
        return 1

    try:
        # engine.run_session expects (page, context, browser, playwright_instance)
        # For persistent context, context acts as browser (has .close())
        log_data = run_session(page, context, browser=context, playwright_instance=pw)
        print("Session ended.", log_data)
        return 0
    except Exception as e:
        print("Session error:", e)
        return 1
    finally:
        if context:
            context.close()
        if pw:
            pw.stop()


if __name__ == "__main__":
    sys.exit(main())
