# NBAVision Engine — Tutorial (one path)

Everything runs **on GitHub’s servers**, not on your PC. You set up secrets once; the engine runs twice daily (9am and 4pm UK) or you trigger it manually from Actions. The GitHub Pages dashboard is **display-only** (no trigger).

---

## 1. Where is the schedule?

- **File:** `.github/workflows/nbavision.yml`
- **Schedule:** Every day **09:00 UTC** and **16:00 UTC** (= 9am and 4pm UK in winter; in summer BST that’s 10am and 5pm UK).
- **Where it runs:** On **GitHub’s machines** (Actions), **not on your computer**. Your PC can be off.

---

## 2. One-time setup: GitHub secrets

The engine needs your X (Twitter) cookies so it can post. You add them as a **repository secret**.

1. Open: **https://github.com/AnthonyNadjari/NBAVisionEngine/settings/secrets/actions**
2. Click **New repository secret**
3. **Name:** `TWITTER_COOKIES_JSON`
4. **Value:** Export cookies from x.com (e.g. [Cookie-Editor](https://chromewebstore.google.com/detail/cookie-editor/hlkenndednhfkekhgpnkiidkbajdkebn)) → copy **only the JSON array** (from `[` to `]`), no `"twitter_cookies":` label.
5. Save.

Optional: add `LLM_API_KEY` (Groq) for AI replies; without it, template replies are used. See [docs/SECRETS-SETUP.md](SECRETS-SETUP.md) for details.

---

## 3. How runs are started

| How | Where |
|-----|--------|
| **Automatic** | Every day at 9am and 4pm UK (09:00 and 16:00 UTC). |
| **Manual** | Repo → **Actions** → **NBAVision Engine** → **Run workflow** → **Run workflow**. |

Runs last up to **5 hours** and can post up to **60 replies** per run (config in `config.py`).

---

## 4. Dashboard (display-only)

The GitHub Pages page is a **dashboard only**: it does **not** trigger runs. With a GitHub token in the URL it can show:

- **Live status** — Last workflow run (queued / in progress / completed / cancelled) and link to the run.
- **Schedule** — 9am and 4pm UK; link to run manually from Actions.
- **Last run summary** — If the last run has a session-logs artifact: scraped/replied/skipped counts, skip reasons, and the list of **tweets posted** (tweet link + reply text).

1. **Get a token:** GitHub → **Settings** → **Developer settings** → **Personal access tokens** → **Tokens (classic)** → **Generate new token**. Give it at least the **repo** scope (read is enough).
2. **Open the dashboard** with the token in the URL:  
   `https://anthonynadjari.github.io/NBAVisionEngine/#ghp_YOUR_TOKEN_HERE`
3. Click **Refresh status** to load the latest run and, when available, the last run summary and posted tweets.

To **start a run**, use **Actions → NBAVision Engine → Run workflow** on GitHub; the dashboard does not have a trigger button.

---

## 5. See runs and logs

- **On GitHub:** Repo → **Actions** → **NBAVision Engine** → click a run → view steps and download the **session-logs** artifact.
- **On the dashboard:** After **Refresh status**, if the last run completed and uploaded artifacts, the “Last run summary” card shows counts and the list of posted tweets.

---

## Quick reference

| Question | Answer |
|----------|--------|
| Where is the schedule? | `.github/workflows/nbavision.yml` — 09:00 and 16:00 UTC (9am / 4pm UK). |
| Does it run on my PC? | **No.** It runs on GitHub’s servers. |
| What do I do once? | Add the secret `TWITTER_COOKIES_JSON` (and optionally `LLM_API_KEY`). |
| How do I run it manually? | **Actions** → **NBAVision Engine** → **Run workflow**. |
| Can the dashboard start a run? | **No.** Dashboard is display-only. |
| More on secrets? | [docs/SECRETS-SETUP.md](SECRETS-SETUP.md) |
