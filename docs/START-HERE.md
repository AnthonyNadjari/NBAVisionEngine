# START HERE — NBAVision Engine

One place. Where you are, what to do.

---

## Where we stand

| Step | Done? | What it is |
|------|--------|------------|
| **1. Runner on your PC** | You did this | You added a self-hosted runner, run `.\run.cmd` in `C:\actions-runner` so it listens. Leave that window open when you want runs to happen. |
| **2. Cookie secret** | You did this | In GitHub: Settings → Secrets → `TWITTER_COOKIES_JSON` = your X cookies (export from same PC). |
| **3. Run the bot** | You do this when you want a run | See below. |

---

## How to run (manual)

1. On your PC: **leave the runner window open** (`C:\actions-runner`, `.\run.cmd` running).
2. On GitHub: **Actions** → click **NBAVision Engine** in the left sidebar.
3. Click the **Run workflow** dropdown (right side), leave branch as **main**, click the green **Run workflow** button.
4. The run will appear in the list; click it to see live logs. It runs on your PC.

Scheduled runs (9am and 4pm UK) use the same workflow; the runner must be on at those times.

---

## If the run doesn’t start

- **Queued forever:** The runner isn’t connected. Open `C:\actions-runner`, run `.\run.cmd`, leave the window open.
- **“Session invalid”:** Re-export cookies from x.com on this PC, update the `TWITTER_COOKIES_JSON` secret, then run again.

---

## More detail (only if you need it)

- **Runner setup from scratch:** [SELF-HOSTED-RUNNER.md](SELF-HOSTED-RUNNER.md)
- **Secrets (cookies, LLM key):** [SECRETS-SETUP.md](SECRETS-SETUP.md)
