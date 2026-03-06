# NBAVisionEngine — Full Technical Investigation Report

## Table of Contents
1. [System Architecture Overview](#1-system-architecture-overview)
2. [End-to-End Flow](#2-end-to-end-flow)
3. [Likely Causes of Instability](#3-likely-causes-of-instability)
4. [Environment Comparison](#4-environment-comparison)
5. [Cookie/Session Strategy Evaluation](#5-cookiesession-strategy-evaluation)
6. [Proposed Robust Architecture](#6-proposed-robust-architecture)
7. [Concrete Improvements](#7-concrete-improvements)
8. [Example GitHub Actions Workflows & Code Fixes](#8-example-github-actions-workflows--code-fixes)

---

## 1. System Architecture Overview

### Entry Points
- **`main.py`** — Primary entry point. Calls `launch_and_auth()` → `run_session()` → cleanup.
- **`scripts/trigger_workflow.py`** — Utility to trigger GitHub Actions via REST API.
- **`scripts/netscape_cookies_to_json.py`** — Converts Netscape `cookies.txt` to JSON for the `TWITTER_COOKIES_JSON` secret.

### Module Breakdown (1,341 lines total)

| File | Lines | Purpose |
|------|-------|---------|
| `main.py` | 43 | Entry point, orchestrates auth + session |
| `auth.py` | 115 | Playwright browser launch, cookie injection, session validation |
| `config.py` | 180 | Centralized config: 56 NBA keywords, limits, URLs, credential loading |
| `engine.py` | 228 | Main session loop: scrape → filter → score → LLM → validate → post |
| `scraper.py` | 181 | Playwright DOM scraping, follower fetch, keyword search |
| `filter_tweets.py` | 105 | Tweet filtering (age, followers, engagement, text rules) |
| `scorer.py` | 43 | Scoring formula (engagement 50%, followers 30%, freshness 20%) |
| `llm_client.py` | 230 | Groq API integration + template fallback, JSON response parsing |
| `reply_validator.py` | 91 | Reply validation: repetition, emoji limits, TF-IDF similarity |
| `poster.py` | 60 | Playwright reply posting with humanoid typing delays |
| `session_log.py` | 65 | JSON session log writing |

### Dependencies (`requirements.txt`)
- `playwright==1.42.0` — Browser automation (Chromium headless)
- `requests` — HTTP client for Groq LLM API
- `numpy`, `scikit-learn` — TF-IDF similarity for reply deduplication
- `python-dotenv` — `.env` file loading
- `fastapi`, `uvicorn` — **Unused** (leftover from dashboard; can be removed)

### Environment Variables

| Variable | Required | Source | Purpose |
|----------|----------|--------|---------|
| `TWITTER_COOKIES_JSON` | **Yes** | GitHub Secret | JSON array of X/Twitter cookies |
| `LLM_API_KEY` | No | GitHub Secret | Groq API key (template mode if absent) |
| `LLM_MODEL` | No | GitHub Secret | Model name (default: `llama-3.1-8b-instant`) |
| `NBAVISION_RUN_ID` | No | Workflow auto-set | GitHub Actions run ID for logging |
| `TWITTER_COOKIES_FILE` | No | Env/`.env` | Path to `cookies.json` (fallback) |

### Authentication Mechanism
- **Cookie-based** — No username/password login, no OAuth
- Cookies are exported from a real browser session (via cookie-editor extension or Netscape export)
- Injected into Playwright via `context.add_cookies()`
- Session validated by checking for `SideNav_AccountSwitcher_Button` (avatar) or `primaryColumn` (timeline) in DOM

### Browser Automation
- **Playwright** (sync API, Chromium headless)
- Anti-detection: `--disable-blink-features=AutomationControlled`, custom user-agent (Windows Chrome 131), custom viewport (1280×720)
- Humanoid behavior: per-character typing delays (50–120ms), waits between actions (3–6s page loads, 60–180s between posts)

---

## 2. End-to-End Flow

### Tweet Generation Pipeline
```
┌─────────────────────────────────────────────────────────────────┐
│                        main.py                                  │
│  1. Load cookies from env/file                                  │
│  2. Launch Playwright Chromium (headless)                        │
│  3. Inject cookies → navigate to x.com/home                     │
│  4. Validate session (check avatar/timeline in DOM)             │
│  5. If valid → run_session()                                    │
└──────────────────────┬──────────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                     engine.py — Session Loop                    │
│  Loop until MAX_REPLIES (60) or stop conditions met:            │
│                                                                 │
│  ┌─ CYCLE ──────────────────────────────────────────────────┐   │
│  │ 1. SCRAPE: For each of 56 keywords:                      │   │
│  │    - Navigate to x.com/search?q={kw}&f=live              │   │
│  │    - Wait 4-6s, scroll 3x (1200-2000px, 2-4s waits)     │   │
│  │    - Extract tweets from DOM (article[data-testid=tweet])│   │
│  │    - Deduplicate by tweet_id                             │   │
│  │    - Fetch follower counts (up to 10 profiles/cycle)     │   │
│  │                                                          │   │
│  │ 2. FILTER: Remove tweets that are:                       │   │
│  │    - Already seen, >15 min old, <5K or >200K followers   │   │
│  │    - <10 likes, <20 chars, URL-only, >3 hashtags         │   │
│  │                                                          │   │
│  │ 3. SCORE: Rank by composite formula:                     │   │
│  │    - 50% engagement velocity, 30% followers, 20% fresh   │   │
│  │    - Keep top 28 tweets                                  │   │
│  │                                                          │   │
│  │ 4. For each top tweet:                                   │   │
│  │    a. LLM CALL: Generate reply via Groq API (or template)│   │
│  │    b. VALIDATE: Check repetition, emoji, similarity      │   │
│  │    c. POST: Navigate to tweet, click reply, type, send   │   │
│  │    d. WAIT: 60-180s before next post                     │   │
│  └──────────────────────────────────────────────────────────┘   │
│  Sleep 1.5 min ± 20s jitter between cycles                      │
└─────────────────────────────────────────────────────────────────┘
```

### Authentication Flow
1. `config.py:get_twitter_cookies_json()` loads cookies (priority: env var → `credentials.json` → file path)
2. `auth.py:parse_cookies()` normalizes domains to `.x.com`/`.twitter.com`
3. Playwright launches headless Chromium with anti-detection args
4. Cookies injected into browser context before any page is created
5. Navigate to `x.com/home`, check for DOM elements confirming login
6. One retry on failure (reload + 2s wait)

### Posting Flow
1. Navigate to tweet URL
2. Wait 3-6s for page load
3. Click `[data-testid="reply"]` button
4. Find editor (`tweetTextarea_0` or contenteditable textbox)
5. Type reply character-by-character (50-120ms per char)
6. Wait 1-2s, click `[data-testid="tweetButton"]`
7. On failure: retry once, then skip

### Scheduling
- GitHub Actions cron: `0 9 * * *` and `0 16 * * *` (UTC)
- Also supports `workflow_dispatch` (manual trigger)
- Self-hosted runner (home PC) — not GitHub-hosted

---

## 3. Likely Causes of Instability

### 3.1 Cookie Expiration & Invalidation (PRIMARY CAUSE)

**This is almost certainly the #1 issue.** X/Twitter cookies have limited lifetimes:

- **`auth_token`** — The main session cookie. X can invalidate it at any time if it detects suspicious activity (new IP, new browser fingerprint, headless browser, rapid API-like behavior).
- **`ct0`** — CSRF token cookie. Rotated by X periodically. If stale, POST requests (replies) silently fail or get 403.
- **`guest_id`**, `personalization_id` — Tracking cookies. Less critical but contribute to fingerprint consistency.

**Why the same cookies "stopped working":**
- X ties sessions to a combination of IP address, user-agent, and browser fingerprint
- When you switch from local → GitHub Actions (different IP, different environment), X sees a "new device" and may invalidate the session
- Even on the same machine, X may invalidate after a period of inactivity or after detecting automation patterns
- X has increasingly aggressive bot detection (2024-2025); what worked 6 months ago may not work now

### 3.2 IP Address Mismatch

The self-hosted runner setup was designed to solve this:
- Export cookies from home browser → run bot from home PC → same IP → X trusts the session
- If the runner goes offline and you switch to GitHub-hosted runners (different datacenter IP), X immediately flags the session

**But even with self-hosted runner:**
- Home IP can change (dynamic IP from ISP)
- VPN or proxy changes break session binding
- Multiple devices on same IP still have different fingerprints

### 3.3 Browser Fingerprint Inconsistencies

Even with `--disable-blink-features=AutomationControlled`, headless Chromium is detectable:
- **WebGL renderer**: Headless Chrome reports a software renderer vs. real GPU
- **Navigator properties**: `navigator.webdriver` may still be `true` in some Playwright versions
- **Missing plugins**: Chrome headless has no plugins, real Chrome has PDF viewer, etc.
- **Canvas fingerprint**: Different rendering in headless mode
- **Screen dimensions**: `1280x720` viewport with no taskbar/chrome is suspicious

X uses these signals to score sessions. A low-trust session gets throttled or invalidated.

### 3.4 Rate Limiting & Anti-Automation

The bot performs **high-volume activity** each session:
- 56 keyword searches × (1 navigation + 3 scrolls) = **224+ page loads per cycle**
- Up to 10 profile page opens per cycle
- Up to 60 replies per session
- Sessions can run up to 5 hours

X applies rate limits:
- Search rate limits (around 50/15 min for normal users)
- Reply rate limits (exact threshold varies; rapid replies get flagged)
- Page navigation limits (too many in short time → CAPTCHA or soft block)

**The bot likely exceeds search rate limits regularly**, which could trigger temporary blocks or session invalidation.

### 3.5 Sequential Keyword Scraping Bottleneck

Scraping 56 keywords sequentially means:
- Each keyword: ~10-14 seconds (4-6s wait + 3 scrolls × 2-4s)
- Full cycle: 56 × ~12s = **~11 minutes** just for scraping
- Plus follower lookups: up to ~30s more
- By the time cycle completes, the "15 min freshness" filter has eliminated early-scraped tweets

### 3.6 No Cookie Refresh Mechanism

The bot loads cookies once at startup and never refreshes them. X rotates `ct0` (CSRF) tokens periodically. After a few hours:
- The `ct0` cookie in memory is stale
- POST requests (replies) start failing with 403
- The bot counts these as `post_fail` and eventually stops (after `MAX_POSTING_FAILURES=2`)

### 3.7 No Session Recovery

If the session becomes invalid mid-run (X invalidates cookies), the bot has no recovery mechanism:
- It detects posting failures but interprets them as errors, not session issues
- There's no re-authentication or cookie refresh
- The session just dies after 2 posting failures

### 3.8 Playwright Version Pinning

`playwright==1.42.0` is pinned (released Feb 2024). X's frontend changes frequently:
- DOM selectors (`data-testid` values) may have changed
- New anti-bot measures may target older browser versions
- Chromium version bundled with Playwright 1.42 is now outdated (detectable)

---

## 4. Environment Comparison

### Local Machine
| Factor | Status |
|--------|--------|
| IP address | Same as cookie export browser |
| Browser fingerprint | Closer to real browser (same GPU, screen) |
| Cookie freshness | Can re-export instantly |
| Debugging | Full visibility (screenshots, headed mode) |
| Persistence | Cookies/state persist on disk |
| Anti-bot detection | Lower risk (residential IP, matching fingerprint) |

### GitHub Actions (Self-Hosted Runner)
| Factor | Status |
|--------|--------|
| IP address | Same as local (it IS local) |
| Browser fingerprint | Different (headless, no GPU, no plugins) |
| Cookie freshness | Static (stored in GitHub Secret, never refreshed) |
| Debugging | Limited (logs only, no screenshots by default) |
| Persistence | No disk persistence between runs |
| Anti-bot detection | Medium risk (headless detection, but residential IP) |
| Reliability | Depends on home PC being on and connected |

### GitHub Actions (GitHub-Hosted Runner)
| Factor | Status |
|--------|--------|
| IP address | **Datacenter IP** — completely different from cookie export |
| Browser fingerprint | Headless, Linux, no GPU |
| Cookie freshness | Static (GitHub Secret) |
| Debugging | Limited (logs + artifacts) |
| Persistence | **None** — fresh VM every run |
| Anti-bot detection | **High risk** (datacenter IP + headless = strong automation signal) |
| Reliability | Very high (Microsoft Azure infrastructure) |

### Why Things Work Locally But Fail on GitHub

1. **IP binding**: X ties session to the IP where cookies were created. Local = same IP. GitHub-hosted = different IP.
2. **Fingerprint consistency**: Local Playwright shares more traits with the real browser on the same machine. GitHub runners have completely different fingerprints.
3. **Cookie freshness**: Locally you can open the browser, re-export cookies, and immediately run. With GitHub, cookies are static in a secret — you must manually update them.
4. **Debugging**: Locally you can run headed (visible browser), take screenshots, and inspect state. On GitHub, you're blind.

---

## 5. Cookie/Session Strategy Evaluation

### Current Strategy
- Cookies exported once from browser, stored as GitHub Secret
- Loaded at startup, injected into Playwright context
- **Never refreshed, never validated mid-session, never persisted back**

### Why Cookies Stop Working

1. **Natural expiration**: `auth_token` cookies typically expire in 1-2 years, but X can shorten this. `ct0` rotates more frequently.

2. **IP change invalidation**: If you export cookies at home (IP 1.2.3.4) and then X sees them used from a datacenter (IP 52.xx.xx.xx), it may immediately invalidate the session as a security measure.

3. **Fingerprint mismatch invalidation**: Even same IP — if the browser fingerprint (WebGL, canvas, navigator properties) doesn't match what X recorded when the cookie was created, X downgrades the session trust level.

4. **Activity-based invalidation**: X monitors session behavior. If a session that normally browses casually suddenly starts making 56 searches and 60 replies in 5 hours, X flags it.

5. **Concurrent session invalidation**: If you're logged in on your real browser AND the bot uses the same cookies simultaneously, X may invalidate one session.

6. **`ct0` (CSRF) rotation**: X's frontend JavaScript refreshes `ct0` periodically. Playwright doesn't run X's JS the same way a real browser does, so `ct0` may not get refreshed, causing POST failures.

### Whether Cookies Are Being Overwritten

- The bot does **not** write cookies back to any file or secret. It's read-only.
- However, X's server-side may invalidate cookies independently.
- There is no mechanism to detect or respond to cookie invalidation mid-session.

### X Anti-Bot Protections

X (formerly Twitter) has significantly increased anti-bot measures since 2023:
- **Arkose Labs CAPTCHA** on login and suspicious actions
- **Browser fingerprinting** via JavaScript (canvas, WebGL, audio context)
- **Behavioral analysis** (typing speed, mouse movements, navigation patterns)
- **Rate limiting** per session and per IP
- **IP reputation scoring** (datacenter IPs are automatically suspicious)
- **Session trust levels** that degrade over time if anomalies are detected

---

## 6. Proposed Robust Architecture

### Goal: Fully automated on GitHub Actions, minimal manual intervention

### Recommended Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    GitHub Actions Workflow                    │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Step 1: Cookie Health Check                         │   │
│  │  - Load cookies from secret                          │   │
│  │  - Launch Playwright, inject cookies                 │   │
│  │  - Navigate to x.com/home                            │   │
│  │  - If session invalid → FAIL EARLY with clear error  │   │
│  │  - Capture + upload screenshot of login state        │   │
│  └──────────────────────┬───────────────────────────────┘   │
│                         ▼                                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Step 2: Reduced Scraping                            │   │
│  │  - Use 10-15 high-value keywords (not 56)            │   │
│  │  - Batch into groups with longer pauses              │   │
│  │  - Respect rate limits (max 40 searches/15 min)      │   │
│  └──────────────────────┬───────────────────────────────┘   │
│                         ▼                                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Step 3: Post with Session Monitoring                │   │
│  │  - Extract fresh ct0 from browser context mid-run    │   │
│  │  - Limit to 5-10 replies per session (not 60)        │   │
│  │  - Longer waits between posts (3-5 min)              │   │
│  │  - Screenshot on every post failure for debugging    │   │
│  └──────────────────────┬───────────────────────────────┘   │
│                         ▼                                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Step 4: Diagnostics & Alerting                      │   │
│  │  - Upload all screenshots as artifacts               │   │
│  │  - Push structured JSON logs to repo                 │   │
│  │  - If session died mid-run → set output flag         │   │
│  │  - Optional: send notification (email/Discord)       │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Best Authentication Strategy

**Continue with cookie-based auth** (OAuth API access costs money and has stricter rate limits), but harden it:

1. **Self-hosted runner is correct** — keep using it. The IP match is critical.
2. **Export cookies from the SAME machine** where the runner runs.
3. **Include all X/Twitter cookies**, not just `auth_token`. Key cookies: `auth_token`, `ct0`, `guest_id`, `personalization_id`, `twid`, `kdt`.
4. **Add cookie freshness validation** at startup — check expiration dates and warn if any expire within 7 days.
5. **Capture cookies after session** — after a successful run, extract cookies from the Playwright context and log them (encrypted) so you can detect `ct0` rotation.

### Proper Session Handling

1. **Periodic health checks**: Every N minutes, verify the session is still valid (check for avatar in DOM).
2. **ct0 refresh**: After navigating to any X page, extract the fresh `ct0` value from `context.cookies()` and log if it changed.
3. **Graceful degradation**: If posting fails, don't immediately count it as a fatal error. First check if the session is still valid (re-navigate to home).
4. **Session timeout**: Limit total session time to 60-90 minutes (not 5 hours). Shorter sessions are less suspicious.

### Safe Cookie Management

1. **Store in GitHub Secret** (current approach is correct).
2. **Never log cookie values** in plain text.
3. **Rotate cookies monthly** — set a reminder to re-export from browser.
4. **Document the exact export process** with screenshots.
5. **Validate cookie format** before run — reject if critical cookies (`auth_token`, `ct0`) are missing.

### Reliable Scheduling

1. **Reduce frequency**: 2 runs/day is fine, but consider randomizing start times slightly (GitHub cron doesn't support this natively, but you can add a random sleep at the start).
2. **Stagger across time zones**: Don't run at round hours. Use off-beat times like `cron: "17 9 * * *"` (9:17 UTC).
3. **Add a health-check-only run**: A lightweight daily run that just validates cookies without posting.

### Logging and Debugging Improvements

1. **Screenshots on failure**: Capture `page.screenshot()` whenever auth fails or posting fails.
2. **Upload screenshots as artifacts**: They're invaluable for debugging.
3. **Log cookie expiration dates** (not values!) at startup.
4. **Log rate limit signals**: If X returns 429 or shows CAPTCHA, log it explicitly.
5. **Structured error categorization**: Distinguish between "session expired", "rate limited", "DOM changed", "network error".

---

## 7. Concrete Improvements

### 7.1 Code Structure Changes

#### Reduce keyword count
Currently 56 keywords means ~11 minutes of scraping per cycle. Reduce to 10-15 high-value keywords and rotate them across runs.

#### Add screenshot capture on failures
In `auth.py` and `poster.py`, add `page.screenshot(path="logs/error_<timestamp>.png")` on failures.

#### Add cookie expiration checking
In `auth.py`, after parsing cookies, check if any have expired or expire within 24 hours.

#### Add session health monitoring
In `engine.py`, periodically (every 5 replies) re-check session validity.

#### Remove unused dependencies
`fastapi` and `uvicorn` are not used in the current codebase. Remove them from `requirements.txt`.

#### Update Playwright version
`playwright==1.42.0` (Feb 2024) is old. Update to latest for newer Chromium and better anti-detection.

### 7.2 GitHub Actions Workflow Improvements

#### Add screenshot upload step
```yaml
- name: Upload debug screenshots
  if: always()
  uses: actions/upload-artifact@v4
  with:
    name: debug-screenshots
    path: logs/*.png
    if-no-files-found: ignore
```

#### Add cookie health check as separate step
Fail fast if cookies are invalid instead of running the full pipeline.

#### Randomize start time
```yaml
- name: Random delay (anti-pattern detection)
  run: sleep $((RANDOM % 300))  # 0-5 min random delay
```

#### Add workflow concurrency control
```yaml
concurrency:
  group: nbavision
  cancel-in-progress: false  # don't cancel running sessions
```

### 7.3 Secrets Management

- **Current approach is sound** — GitHub Secrets are encrypted at rest and masked in logs.
- **Add `COOKIE_UPDATED_AT` secret** — Store the date when cookies were last updated. Log a warning if >30 days old.
- **Consider GitHub Environments** — Use a "production" environment with required reviewers for extra security.

### 7.4 Retry Mechanisms

#### Network retries
Add retry logic for Playwright navigation failures (network errors, timeouts):
```python
def navigate_with_retry(page, url, max_retries=3):
    for attempt in range(max_retries):
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            return True
        except Exception as e:
            if attempt < max_retries - 1:
                page.wait_for_timeout(2000 * (attempt + 1))
            else:
                raise
```

#### Posting retries with session check
Before retrying a failed post, verify the session is still valid:
```python
def post_with_validation(page, tweet_url, reply_text):
    success, error = post_reply(page, tweet_url, reply_text)
    if not success:
        # Check if session is still alive
        page.goto("https://x.com/home", wait_until="domcontentloaded")
        if not _check_logged_in(page):
            return False, "session_expired"
        # Retry once
        success, error = post_reply(page, tweet_url, reply_text)
    return success, error
```

### 7.5 Monitoring/Logging

#### Structured log levels
Add a `status` field to session logs:
- `"completed"` — All went well
- `"partial"` — Some posts succeeded, some failed
- `"session_expired"` — Cookie/session died mid-run
- `"rate_limited"` — Detected rate limiting
- `"dom_changed"` — Expected selectors not found

#### GitHub Actions job summary
Add a workflow step that writes to `$GITHUB_STEP_SUMMARY`:
```yaml
- name: Write job summary
  if: always()
  run: |
    echo "## NBAVision Run Summary" >> $GITHUB_STEP_SUMMARY
    echo "- Run ID: ${{ github.run_id }}" >> $GITHUB_STEP_SUMMARY
    python -c "
    import json, glob
    for f in glob.glob('logs/*.json'):
        d = json.load(open(f))
        print(f'- Replies posted: {d.get(\"total_replied\", 0)}')
        print(f'- Tweets scraped: {d.get(\"total_scraped\", 0)}')
        print(f'- LLM calls: {d.get(\"total_llm_calls\", 0)}')
    " >> $GITHUB_STEP_SUMMARY
```

---

## 8. Example GitHub Actions Workflows & Code Fixes

### 8.1 Improved Workflow (`.github/workflows/nbavision.yml`)

```yaml
name: NBAVision Engine

on:
  workflow_dispatch:
  schedule:
    - cron: "17 9 * * *"    # 9:17 UTC — avoid round hours
    - cron: "43 16 * * *"   # 16:43 UTC — avoid round hours

concurrency:
  group: nbavision
  cancel-in-progress: false

jobs:
  run:
    runs-on: self-hosted
    timeout-minutes: 120     # Reduced from 300 — shorter sessions are safer
    permissions:
      contents: write

    steps:
      - uses: actions/checkout@v4

      - name: Check required secrets
        run: |
          if [ -z "${{ secrets.TWITTER_COOKIES_JSON }}" ]; then
            echo "::error::Missing TWITTER_COOKIES_JSON secret"
            exit 1
          fi

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Install Playwright Chromium
        run: playwright install --with-deps chromium

      - name: Random startup delay
        run: sleep $((RANDOM % 180))   # 0-3 min jitter

      - name: Run NBAVision Engine
        env:
          TWITTER_COOKIES_JSON: ${{ secrets.TWITTER_COOKIES_JSON }}
          LLM_API_KEY: ${{ secrets.LLM_API_KEY }}
          LLM_MODEL: ${{ secrets.LLM_MODEL || 'llama-3.1-8b-instant' }}
          NBAVISION_RUN_ID: ${{ github.run_id }}
        run: python main.py

      - name: Upload session logs
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: session-logs-${{ github.run_id }}
          path: logs/
          if-no-files-found: ignore

      - name: Upload debug screenshots
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: debug-screenshots-${{ github.run_id }}
          path: logs/*.png
          if-no-files-found: ignore

      - name: Write job summary
        if: always()
        run: |
          echo "## NBAVision Run Summary" >> $GITHUB_STEP_SUMMARY
          echo "- **Run ID:** ${{ github.run_id }}" >> $GITHUB_STEP_SUMMARY
          echo "- **Trigger:** ${{ github.event_name }}" >> $GITHUB_STEP_SUMMARY
          if ls logs/*.json 1>/dev/null 2>&1; then
            python -c "
          import json, glob
          for f in sorted(glob.glob('logs/*.json')):
              d = json.load(open(f))
              print(f'- **Replies posted:** {d.get(\"total_replied\", 0)}')
              print(f'- **Tweets scraped:** {d.get(\"total_scraped\", 0)}')
              print(f'- **LLM calls:** {d.get(\"total_llm_calls\", 0)}')
              print(f'- **Skip reasons:** {json.dumps(d.get(\"skip_reasons\", {}))}')
          " >> $GITHUB_STEP_SUMMARY
          else
            echo "- No session logs produced" >> $GITHUB_STEP_SUMMARY
          fi

      - name: Push run logs
        if: always()
        run: |
          if ls logs/*.json 1>/dev/null 2>&1; then
            mkdir -p run_logs/${{ github.run_id }}
            cp logs/*.json run_logs/${{ github.run_id }}/
            git config user.name "github-actions[bot]"
            git config user.email "github-actions[bot]@users.noreply.github.com"
            git pull --rebase origin ${{ github.ref_name }} 2>/dev/null || true
            git add run_logs/
            git diff --staged --quiet || (git commit -m "Run logs: ${{ github.run_id }}" && git push)
          fi
```

### 8.2 Cookie Health Check (add to `auth.py`)

```python
import time

def check_cookie_health(cookies: list[dict]) -> list[str]:
    """Return list of warnings about cookie health."""
    warnings = []
    now = time.time()
    critical_cookies = {"auth_token", "ct0", "twid"}
    found = {c["name"] for c in cookies}

    for name in critical_cookies:
        if name not in found:
            warnings.append(f"MISSING critical cookie: {name}")

    for c in cookies:
        exp = c.get("expires")
        if exp and exp < now:
            warnings.append(f"EXPIRED cookie: {c['name']} (expired {int(now - exp)}s ago)")
        elif exp and exp < now + 86400:
            warnings.append(f"EXPIRING SOON: {c['name']} (expires in {int(exp - now)}s)")

    return warnings
```

### 8.3 Screenshot on Failure (add to `poster.py`)

```python
import os
from datetime import datetime, timezone

def _capture_debug_screenshot(page, label: str):
    """Save a debug screenshot to logs/."""
    os.makedirs("logs", exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = f"logs/{label}_{ts}.png"
    try:
        page.screenshot(path=path, full_page=False)
        print(f"Debug screenshot saved: {path}", flush=True)
    except Exception:
        pass
```

### 8.4 Session Health Monitor (add to `engine.py`)

```python
def _is_session_alive(page) -> bool:
    """Quick check if X session is still valid."""
    try:
        page.goto("https://x.com/home", wait_until="domcontentloaded", timeout=15000)
        avatar = page.locator('[data-testid="SideNav_AccountSwitcher_Button"]').first
        return avatar.is_visible(timeout=5000)
    except Exception:
        return False
```

Call this every 5 replies in the engine loop, and abort early if session is dead.

---

## Summary of Root Causes & Priorities

| Priority | Issue | Impact | Fix Difficulty |
|----------|-------|--------|----------------|
| **P0** | Cookie/session invalidation by X | Bot stops working entirely | Medium — better health checks + shorter sessions |
| **P0** | IP mismatch (if not using self-hosted runner) | Immediate session death | Low — keep using self-hosted runner |
| **P1** | 56 keywords = rate limit risk | Searches throttled/blocked | Low — reduce to 10-15 keywords |
| **P1** | No screenshots on failure | Impossible to debug remotely | Low — add `page.screenshot()` |
| **P1** | No session health monitoring mid-run | Silent failure | Low — periodic session check |
| **P2** | MAX_REPLIES=60 is aggressive | Increases detection risk | Low — reduce to 5-10 |
| **P2** | 5-hour timeout is too long | Longer exposure to detection | Low — reduce to 60-90 min |
| **P2** | Outdated Playwright version | Older Chromium = more detectable | Low — update dependency |
| **P3** | Unused deps (fastapi, uvicorn) | Bloat | Trivial — remove |
| **P3** | No `ct0` refresh mechanism | Posts fail after hours | Medium — extract cookies mid-run |
| **P3** | No alerting on failure | Manual log checking required | Medium — add notifications |

### The Bottom Line

The fundamental tension is: **X actively fights automation, and this bot is automation.** No architecture is 100% reliable against X's anti-bot systems. The best strategy is:

1. **Minimize footprint** — fewer searches, fewer replies, shorter sessions
2. **Match the real user's profile** — same IP, same fingerprint, same activity patterns
3. **Fail gracefully** — detect problems early, take screenshots, log everything
4. **Make cookie refresh easy** — clear docs, validation, expiry warnings
5. **Keep the self-hosted runner** — IP matching is the single most important factor
