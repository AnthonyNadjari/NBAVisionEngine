# NBAVision Engine — Tutorial (one path)

Everything runs **on GitHub’s servers**, not on your PC. You only set up secrets once and optionally use the Control Center to see status and start runs manually.

---

## 1. Where is the weekly schedule?

- **File:** `.github/workflows/nbavision.yml`
- **Line:** `cron: "0 14 * * 0"` → every **Sunday at 14:00 UTC**
- **Where it runs:** On **GitHub’s machines** (Actions), **not on your computer**. Your PC can be off; the run still happens.

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
| **Weekly** | Automatically every Sunday 14:00 UTC (see step 1). |
| **Manual (GitHub)** | Repo → **Actions** → **NBAVision Engine** → **Run workflow** → **Run workflow**. |
| **Manual (Control Center)** | Open Control Center once with a token (step 4), then use **Refresh status** and **Start engine run**. |

All of these run the **same workflow on GitHub**; nothing runs on your machine.

---

## 4. Control Center (optional)

The Control Center is a small web page that shows the latest run and lets you start a run without opening GitHub Actions.

1. **Get a GitHub token:** GitHub → **Settings** → **Developer settings** → **Personal access tokens** → **Tokens (classic)** → **Generate new token**. Give it at least the `repo` scope.
2. **Open the Control Center** with the token in the URL so it can talk to GitHub:
   - If you use **GitHub Pages**:  
     `https://anthonynadjari.github.io/NBAVisionEngine/#ghp_YOUR_TOKEN_HERE`
   - If you open the HTML file locally:  
     `file:///C:/Users/nadja/.../docs/index.html#ghp_YOUR_TOKEN_HERE`
3. **First time:** The page will store the token in the browser (sessionStorage) and use it for **Refresh status** and **Start engine run**.
4. **Refresh status** → fetches the latest workflow run from GitHub.  
5. **Start engine run** → triggers the same workflow as “Run workflow” in Actions.

If you see “Token missing or invalid”, open the page again with `#ghp_...` in the URL (step 2) and try again.

---

## 5. See runs and logs

- **On GitHub:** Repo → **Actions** → **NBAVision Engine** → click a run → view steps and **session-logs** artifact.
- **In Control Center:** After **Refresh status**, the card shows the latest run and a link to that run on GitHub.

---

## Quick reference

| Question | Answer |
|----------|--------|
| Where is the schedule? | `.github/workflows/nbavision.yml` — `cron: "0 14 * * 0"` (Sunday 14:00 UTC). |
| Does it run on my PC? | **No.** It runs on GitHub’s servers. Your PC can be off. |
| What do I do once? | Add the secret `TWITTER_COOKIES_JSON` (and optionally `LLM_API_KEY`). |
| How do I run it manually? | GitHub Actions → Run workflow, or Control Center → Start engine run (after opening with token). |
| More on secrets? | [docs/SECRETS-SETUP.md](SECRETS-SETUP.md) |
