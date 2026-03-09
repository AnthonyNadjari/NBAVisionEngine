# Prompt: Scalable Twitter/X Bot — Architecture & Auth Strategy

**Copy everything below the line to ask an AI or consultant for a scalable, maintainable solution. Adjust the “What we want” section if your priorities differ.**

---

## Project overview

**Name:** NBAVision Engine  
**Purpose:** Automated Twitter/X bot that discovers NBA-related tweets (search), filters and ranks them, generates short replies with an LLM (Groq), validates replies, and posts replies as a logged-in user. Goal: human-like engagement at scale without manual cookie/session maintenance.

**Repository layout (Python):**
- `main.py` — entry point; launches browser auth then runs the engine.
- `auth.py` — Playwright Chromium, loads cookies from `TWITTER_COOKIES_JSON` (or persisted `state.json`), navigates to X home, verifies session (avatar/timeline visible). Saves session state on success.
- `scraper.py` — Playwright: opens X search URLs (`https://x.com/search?q={query}&f=live`), scrolls, extracts tweet DOM (tweet_id, username, text, likes, replies, retweets, has_media, timestamp). Batches ~28 keywords per cycle, 3 parallel tabs per batch. No official Twitter API.
- `filter_tweets.py` — Filters by: NBA keyword in text, min/max age, min likes, text length, media caption rules, hashtag limit, dedup by tweet_id.
- `scorer.py` — Engagement velocity + text quality score; keeps top N (e.g. 40) per cycle.
- `llm_client.py` — Calls Groq API for reply generation; strict NBA-only prompt; can skip with reasons. Serial calls with delay to avoid 429.
- `reply_validator.py` — Validates length, emoji count, sentence count, similarity to recent replies.
- `poster.py` — Playwright: for each reply, navigates to tweet URL, clicks reply button, types in composer via `page.keyboard.insert_text()`, clicks send. Retries once on `reply_button_not_found`. Uses delays (e.g. 20–45 s between tweets) to appear human-like.
- `engine.py` — Orchestrates cycles: scrape → filter → rank → LLM (per candidate) → validate → post. Stops on max_replies (e.g. 60), max_posting_failures (e.g. 5), or max_consecutive_errors (e.g. 5). Periodic session health check; saves session state after cycles.
- **Config** (`config.py`): ~80+ search keywords (teams, players, “NBA trade”, “NBA playoffs”, etc.), KEYWORDS_PER_CYCLE=28, TOP_N_SCORED=40, MAX_REPLIES=60, MAX_POSTING_FAILURES=5, CYCLE_INTERVAL ~0.5 min, various filter/validation thresholds.
- **CI:** GitHub Actions workflow (`nbavision.yml`) on **self-hosted** runner (home PC). Required secret: `TWITTER_COOKIES_JSON` (Netscape cookies converted to JSON). Optional: `LLM_API_KEY`, `LLM_MODEL`, `DISCORD_WEBHOOK_URL`. A separate **Scheduler** workflow runs every 30 minutes, reads `docs/schedule.json` (e.g. 09:00 and 16:00 UTC), and triggers the main workflow when current time is within 15 minutes of a slot.

---

## Current scale and usage pattern

- **Discovery:** ~28 keywords per cycle, 3 parallel browser tabs, multiple cycles per run until hitting MAX_REPLIES or stop conditions. Typical run: hundreds of tweets scraped per cycle (e.g. 150–250), filtered to dozens, top 40 scored, then a subset sent to LLM and posted (with 20–45 s gaps). So **read volume** is high (many search result pages per run).
- **Posting:** Up to 60 replies per session, 1 reply per author, human-like delays. Target order of magnitude: **tens to low hundreds of posts per day** if we ran more often or increased limits.
- **Schedule:** 2 scheduled runs per day (e.g. 09:00 and 16:00 UTC); manual runs possible. Each run can last tens of minutes (scrape + LLM + posting delays).

---

## Problems we want to get away from

1. **Cookie/session dependency**  
   Auth is browser-based: we load cookies (e.g. `auth_token`, `ct0`, `twid`, `kdt`) from `TWITTER_COOKIES_JSON`. Cookies expire or get invalidated; then we get `session_invalid` or `cookies_expired` and the run fails immediately or after a few posts. Re-exporting from the browser and updating the secret is manual and recurring. We want to **stop depending on manual cookie export** for a production-ready, “set and forget” setup.

2. **Browser-based posting fragility**  
   Posting is done via Playwright (click reply, type, send). We’ve seen: clipboard “Write permission denied” in headless (mitigated with `insert_text`), `reply_button_not_found` (timing/selectors), and general fragility when X changes the DOM or rate-limits the session. We want a **stable, scalable way to post** that doesn’t rely on UI automation.

3. **Scaling limits of the free Twitter/X API**  
   The official X API free tier (as of 2024–2025) is roughly **500 posts/month** and **100 read requests/month**. Our current usage would burn the 100 reads in a few runs (many search queries per run). So the free API tier is **not enough** for our target scale (many searches per run, many replies per day). We need a solution that is **scalable** (higher read and post capacity), not just “free but severely limited.”

4. **Self-hosted runner**  
   We use a self-hosted runner for IP consistency with the cookie-exported session. If we move to an API-based or otherwise cookie-free design, we’d prefer to run on **standard cloud runners** (e.g. GitHub-hosted or other CI) so the system is “fully online” and not tied to a home machine.

---

## What we want (scalable, maintainable)

- **Scalable:**  
  - **Reads:** Ability to run many searches per run (order of magnitude: dozens of search queries, hundreds to low thousands of tweet “reads” per day) without hitting a tiny cap like 100/month.  
  - **Posts:** Ability to post on the order of tens to low hundreds of replies per day (or more), without fragile browser automation.  
  So we’re explicitly **not** limited to the free X API tier; we’re open to **paid X API tiers**, **alternative data sources for discovery**, or **hybrid architectures** (e.g. third-party or scraped discovery + official API for posting only), as long as the solution is clearly scalable and cost-understandable.

- **No cookie/session maintenance:**  
  No recurring manual export of browser cookies. Prefer **OAuth 2.0 (or similar)** with long-lived refresh tokens so we set secrets once and only re-authorize if the app or token is revoked. If some part of the pipeline must still use a browser (e.g. for discovery), we’d want that clearly scoped and, if possible, alternatives suggested for when we’re ready to scale further.

- **Fully online / cloud-friendly:**  
  Prefer running on GitHub-hosted or other cloud runners; no dependency on a self-hosted home PC for IP/cookie consistency, unless there’s a strong reason.

- **Cost-conscious but not “free-only”:**  
  We’re okay with paid APIs or services if they’re predictable and scale with usage (e.g. X API Basic/Pro, or a dedicated tweet-data provider). We want a **concrete recommendation** (e.g. “use X API Basic for posting + provider X for search”) with rough cost ranges and limits, not only the free tier.

---

## What we need from you

1. **Recommended architecture**  
   Propose a scalable architecture that:  
   - Removes or minimizes cookie/session dependency (prefer OAuth 2.0 or equivalent for X).  
   - Provides enough **read** capacity for our discovery pattern (many keywords/searches per run).  
   - Provides **stable, scalable posting** (prefer official API over browser automation).  
   - Is runnable on standard cloud/CI (e.g. GitHub Actions on `ubuntu-latest` or similar).  
   Specify clearly: what does discovery (search/tweet ingestion), what does posting, and what credentials/secrets are needed (e.g. X API keys, OAuth client id/secret, access/refresh tokens, third-party API keys).

2. **Data source options for discovery**  
   If the official X API is too expensive for our search volume, suggest **alternative or complementary** data sources (e.g. third-party Twitter/X firehose or search APIs, RSS, or other feeds) that can supply “tweets to reply to” (tweet_id, text, author, engagement, etc.) in a scalable way. Include:  
   - Name of service / product.  
   - Rough pricing and rate/volume limits.  
   - How we’d get tweet_id and enough metadata to filter/score and then post a reply via the official API (so we still only post through X’s API).

3. **Posting path**  
   Confirm the recommended way to post replies at scale (e.g. X API Create Tweet with `reply.in_reply_to_tweet_id`), which X API tier is needed (Basic, Pro, etc.), approximate post limits and cost, and how OAuth 2.0 (access + refresh token) is used so we don’t rely on cookies.

4. **Migration steps**  
   High-level steps to go from our current setup (Playwright + cookies, self-hosted runner) to the proposed setup (e.g. “(1) Register X app and get OAuth tokens; (2) Add poster module using X API; (3) Replace or supplement scraper with provider X; (4) Switch workflow to ubuntu-latest and remove cookie validation”). No need to write full code; we need a clear roadmap.

5. **Risks and tradeoffs**  
   Short note on: ToS (Twitter/X automation and third-party data), rate limits, and any remaining single points of failure (e.g. one API key, one account).

---

## Summary one-liner

We have a Python Twitter bot that scrapes X search with Playwright and posts LLM-generated replies via the same browser session; it’s brittle (cookies, DOM, self-hosted) and the official free API tier is too small. We want a **scalable, cookie-free, cloud-run architecture** with enough read and post capacity, and are open to paid X API and/or third-party data sources—please recommend a concrete architecture, data sources, posting path, migration steps, and tradeoffs.
