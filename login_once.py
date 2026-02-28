"""
One-time script: open Chromium with persistent profile so you can log into X.
Run once, then never export cookies again.
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

PROFILE = Path(__file__).resolve().parent / "browser_profile"


def main() -> int:
    print("Opening browser. Log into X (Twitter), then press Enter here to close.")
    pw = sync_playwright().start()
    ctx = pw.chromium.launch_persistent_context(
        str(PROFILE),
        headless=False,
        args=["--disable-blink-features=AutomationControlled"],
    )
    input("Press Enter when done logging in...")
    ctx.close()
    pw.stop()
    print("Profile saved. You can now run main_engine.py or trigger via webhook.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
