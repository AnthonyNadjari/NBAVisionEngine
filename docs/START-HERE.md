# START HERE — NBAVision Engine

One place. Where you are, what to do.

---

## Where we stand

| Step | Done? | What it is |
|------|--------|------------|
| **1. Runner on your PC** | You did this | You added a self-hosted runner, run `.\run.cmd` in `C:\actions-runner` so it listens. Leave that window open when you want runs to happen. |
| **2. Cookie secret** | You did this | In GitHub: Settings → Secrets → `TWITTER_COOKIES_JSON` = your X cookies (export from same PC). |
| **3. Run the bot** | Automatic or manual | Schedule runs at 9am and 4pm UK by itself. You only click “Run workflow” when you want an extra run. |

---

## How to run (manual)

1. On your PC: **leave the runner window open** (`C:\actions-runner`, `.\run.cmd` running).
2. On GitHub: **Actions** → click **NBAVision Engine** in the left sidebar.
3. Click the **Run workflow** dropdown (right side), leave branch as **main**, click the green **Run workflow** button.
4. The run will appear in the list; click it to see live logs. It runs on your PC.

Scheduled runs (9am and 4pm UK) use the same workflow; the runner must be on at those times.

---

## Start the runner with Windows (optional)

So you don’t have to launch `run.cmd` by hand:

1. Press **Windows + R**, type `shell:startup`, Enter.
2. Right‑click in the folder → **New** → **Shortcut**.
3. **Target:** `C:\Windows\System32\cmd.exe /c "cd /d C:\actions-runner && run.cmd"`
4. Name it e.g. **GitHub Runner** → Finish.

After that, the runner starts when you log in. A command window will stay open while it runs.

---

## If the run doesn’t start

- **Queued forever:** The runner isn’t connected. Open `C:\actions-runner`, run `.\run.cmd`, leave the window open.
- **“Session invalid”:** Re-export cookies from x.com on this PC, update the `TWITTER_COOKIES_JSON` secret, then run again.

---

## More detail (only if you need it)

- **What we built and why:** [PROJECT.md](PROJECT.md)
- **Runner setup from scratch:** [SELF-HOSTED-RUNNER.md](SELF-HOSTED-RUNNER.md)
- **Secrets (cookies, LLM key):** [SECRETS-SETUP.md](SECRETS-SETUP.md)
