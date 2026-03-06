# Self-hosted runner (one-time setup)

The workflow runs on **your PC** so X sees your **home IP**. That way the same cookies you export in your browser work for days instead of failing immediately on GitHub’s datacenter IP.

**You only do this once.** After that, scheduled and manual runs use this runner automatically.

---

## Your steps (minimal)

| # | Where | What to do |
|---|--------|------------|
| 1 | GitHub repo | **Settings** → **Actions** → **Runners** → **New self-hosted runner** → choose **Windows**, **x64**. Keep the page open. |
| 2 | Your PC | Install **Git for Windows** and **Python 3.11** if not already installed. |
| 3 | Your PC | In PowerShell: create `C:\actions-runner`, download the runner zip from the GitHub page, extract, run `.\config.cmd` (repo URL + token from GitHub), then `.\svc install` and `.\svc start`. |
| 4 | GitHub | In **Settings** → **Actions** → **Runners**, confirm the runner shows **Idle** (green). |
| 5 | GitHub | **Actions** → **NBAVision Engine** → **Run workflow** to test. Export cookies from this PC so the IP matches. |

Details for each step are below.

---

## What you need before starting

- **Windows PC** that can stay on (or at least on at 9am and 4pm UK when the schedule runs).
- **Git for Windows** installed (for `bash` in the workflow). If you don’t have it: [https://git-scm.com/download/win](https://git-scm.com/download/win) — use default options.
- **Python 3.11** installed and on PATH. [https://www.python.org/downloads/](https://www.python.org/downloads/) — tick “Add Python to PATH”.

---

## Step 1: Add the runner in GitHub

1. Open your repo: **https://github.com/AnthonyNadjari/NBAVisionEngine**
2. Go to **Settings** → **Actions** → **Runners**.
3. Click **New self-hosted runner**.
4. Select **Windows** and **x64**, then use the commands GitHub shows (Step 2 below is the same thing in one place).

---

## Step 2: On your PC — download and configure

Open **PowerShell** or **Command Prompt** and run the following. Replace nothing unless your repo or username is different.

```powershell
# Create folder and go into it
mkdir C:\actions-runner
cd C:\actions-runner

# Download the runner (Windows x64). If the version is newer, use the link from GitHub’s runner page.
Invoke-WebRequest -Uri "https://github.com/actions/runner/releases/download/v2.321.0/actions-runner-win-x64-2.321.0.zip" -OutFile "actions-runner-win-x64.zip" -UseBasicParsing
Expand-Archive -Path "actions-runner-win-x64.zip" -DestinationPath "."

# Configure (you will be asked for the URL and a token)
.\config.cmd
```

When `config.cmd` asks:

- **Repository URL:** `https://github.com/AnthonyNadjari/NBAVisionEngine`
- **Token:** paste the value GitHub showed on the **New self-hosted runner** page (under “Configure”).
- **Runner name:** e.g. `home-pc` (or leave default).
- **Labels:** press Enter (default is fine).
- **Work folder:** press Enter (default).

---

## Step 3: Install and start the runner as a service

In the **same** folder (`C:\actions-runner`):

```powershell
.\svc install
.\svc start
```

The runner is now a Windows service: it starts with Windows and keeps listening for jobs.

---

## Step 4: Check it’s connected

In GitHub: **Settings** → **Actions** → **Runners**. You should see your runner with a green dot (Idle).

---

## Step 5: Trigger a run

- Go to **Actions** → **NBAVision Engine** → **Run workflow** → **Run workflow**.
- The job will run on your PC. Export cookies from the **same PC** (or same home network) so the IP matches and X keeps the session valid.

---

## Summary of what you did

| Step | What you did |
|------|------------------|
| 1 | Added a self-hosted runner in the repo settings. |
| 2 | On your PC: downloaded runner, ran `config.cmd` with repo URL and token. |
| 3 | Ran `svc install` and `svc start` so the runner runs as a service. |
| 4 | Confirmed the runner appears as Idle in GitHub. |
| 5 | Triggered a workflow run; it runs on your PC with your home IP. |

**If the runner is offline** (PC off or service stopped), the workflow job will sit in the queue until the runner is back. No code changes are required to “switch back” — just leave the workflow as `runs-on: self-hosted`.

**Official docs:** [Hosting your own runners](https://docs.github.com/en/actions/hosting-your-own-runners).
