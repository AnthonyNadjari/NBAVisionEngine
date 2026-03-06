# NBAVision Engine — What We Built and Why

One-page overview of the project, what was implemented, and the reasoning behind it.

---

## What the project is

**NBAVision Engine** is an X (Twitter) bot that:

1. **Scrapes** live search results for many NBA-related keywords (teams, players, topics).
2. **Filters** tweets by recency, follower count, engagement, and text rules.
3. **Scores** remaining tweets and picks the top ones.
4. **Generates** replies (templates or LLM) and **posts** them as replies on X.

It runs as a **scheduled or manually triggered** GitHub Actions job. The job runs on **your own PC** via a **self-hosted runner**, not on GitHub’s servers.

---

## What we built (and why)

| What | Why |
|------|-----|
| **Self-hosted runner** | X sessions and cookies are tied to an IP/browser. Running on GitHub’s cloud caused “session invalid” quickly. Running the job on your PC (same IP as where you’re logged in to X) keeps the session stable. |
| **Run logs in the repo** | Each run writes logs under `run_logs/<run_id>/` and the workflow pushes them so you can inspect failures and behavior without digging into Actions artifacts only. |
| **Detailed session log** | The engine writes a structured JSON session log (cycles, events, errors) so we can debug timing, scrape results, and posting without reading raw console output. |
| **Many keywords, shorter cycles** | More keywords and a shorter cycle interval (e.g. 1.5 min) give more candidate tweets per run; config is centralized in `config.py`. |
| **Cookie handling** | Cookies are provided via GitHub secret `TWITTER_COOKIES_JSON` (or `credentials.json` / env). A script converts Netscape `cookies.txt` to the JSON format the app expects. |
| **Sequential keyword scraping** | We first tried parallel keyword scraping with multiple Playwright contexts/pages in worker threads. Playwright’s **sync** API is not thread-safe (greenlets + asyncio), which caused `greenlet.error: cannot switch to a different thread`. We reverted to **sequential** keyword scraping on a single page/context so all Playwright use stays on the main thread. |
| **Single entry doc (START-HERE.md)** | One place to see: runner status, how to run (manual + schedule), optional Startup shortcut, and pointers to runner setup and secrets. |
| **Docs cleanup** | Removed redundant HOW-TO-USE and TUTORIAL; kept START-HERE, SELF-HOSTED-RUNNER, SECRETS-SETUP, and this PROJECT.md. |

---

## Main files

- **Workflow:** `.github/workflows/nbavision.yml` — self-hosted, bash, pushes `run_logs/<run_id>/`.
- **Config:** `config.py` — KEYWORDS, limits, delays, browser user-agent/viewport (used by auth).
- **Engine:** `main.py` → `engine.py` — cycle loop; `auth.py` — browser + cookies; `scraper.py` — sequential keyword scrape + follower fetch; filter, scoring, LLM, poster as in spec.
- **Docs:** `docs/START-HERE.md` (start here), `docs/SELF-HOSTED-RUNNER.md`, `docs/SECRETS-SETUP.md`, `docs/PROJECT.md` (this file).

---

## How to run

1. **Runner:** On your PC, in `C:\actions-runner`, run `.\run.cmd` and leave the window open (or use the Startup shortcut from START-HERE).
2. **Secrets:** In the repo, set `TWITTER_COOKIES_JSON` (and optionally `LLM_API_KEY`, `LLM_MODEL`) in Settings → Secrets.
3. **Trigger:** GitHub → Actions → NBAVision Engine → **Run workflow** (or rely on the 9am/4pm UK schedule).

For more detail and troubleshooting, see **docs/START-HERE.md**.
