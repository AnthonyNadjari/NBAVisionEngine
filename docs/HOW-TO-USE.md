# How to use NBAVision Engine (concise)

The bot runs **on your PC** via a self-hosted GitHub Actions runner, scrapes X for NBA keywords, and posts replies (template or LLM). Runs are triggered manually or on a schedule (9am and 4pm UK).

---

## One-time setup

1. **Self-hosted runner (so X keeps your session)**  
   Follow [SELF-HOSTED-RUNNER.md](SELF-HOSTED-RUNNER.md): install Git for Windows + Python 3.11, add the runner in GitHub, download and configure it on your PC, then run `.\run.cmd` (or set up Startup/Task Scheduler). Export cookies from **this same PC** so the IP matches.

2. **GitHub secret: cookies**  
   Repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**  
   - Name: `TWITTER_COOKIES_JSON`  
   - Value: from [Cookie-Editor](https://chromewebstore.google.com/detail/cookie-editor/hlkenndednhfkekhgpnkiidkbajdkebn) on x.com (copy only the `[...]` array), or run `python scripts/netscape_cookies_to_json.py path/to/cookies.txt` and paste the output.

3. **Optional: AI replies**  
   Add secret `LLM_API_KEY` (Groq key). Without it, template replies are used.

---

## Running the bot

| How | What to do |
|-----|------------|
| **Manual** | GitHub → **Actions** → **NBAVision Engine** → **Run workflow** → **Run workflow**. Your PC must be on and the runner window (`run.cmd`) open. |
| **Schedule** | Same workflow runs automatically at **09:00** and **16:00 UTC** (9am and 4pm UK). Runner must be on at those times. |

Each run can post up to **60 replies** and lasts up to **5 hours** (config in `config.py`).

---

## Logs and results

- **Live logs:** Actions → open the run → click the **run** job → log panel on the right (streams from your PC).
- **Session JSON:** After a run, logs are in the **session-logs** artifact and in the repo under **run_logs/<run_id>/**.
- **Dashboard:** [GitHub Pages](https://anthonynadjari.github.io/NBAVisionEngine/) with `#ghp_YOUR_TOKEN` in the URL shows last run status and posted tweets (display only).

---

## Refreshing cookies

When you see **"Session invalid or expired"**: export cookies again from x.com (same browser/PC), update the `TWITTER_COOKIES_JSON` secret, then trigger a new run.

---

## Quick reference

| Task | Where |
|------|--------|
| Runner setup | [SELF-HOSTED-RUNNER.md](SELF-HOSTED-RUNNER.md) |
| Secrets (cookies, LLM) | [SECRETS-SETUP.md](SECRETS-SETUP.md) |
| Trigger a run | **Actions** → **NBAVision Engine** → **Run workflow** |
| Change schedule / limits | `.github/workflows/nbavision.yml`, `config.py` |
