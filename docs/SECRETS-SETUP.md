# GitHub Actions — Set up secrets (step-by-step)

The workflow needs **1 required secret** (TWITTER_COOKIES_JSON). LLM_API_KEY is optional (templates used if not set).

**Cookie export:** Use a browser extension (e.g. [Cookie-Editor](https://chromewebstore.google.com/detail/cookie-editor/hlkenndednhfkekhgpnkiidkbajdkebn), EditThisCookie) on x.com while logged in → Export as JSON array.  
**Or from a Netscape `cookies.txt`:** run `python scripts/netscape_cookies_to_json.py path/to/cookies.txt` and copy the printed JSON array into the secret (see Step 2 below).

**Session lifetime:** The workflow is set up to run on a **self-hosted runner** (your home PC) so X sees your residential IP and cookies last much longer. One-time setup: [Self-hosted runner (docs/SELF-HOSTED-RUNNER.md)](SELF-HOSTED-RUNNER.md). If you see "session invalid or expired", re-export cookies and update the `TWITTER_COOKIES_JSON` secret.

---

## Step 1: Open the secrets page

1. Go to **https://github.com/AnthonyNadjari/NBAVisionEngine**
2. Click **Settings** (top tab bar of the repo).
3. In the left sidebar, under **Security**, click **Secrets and variables** → **Actions**.
4. You should see **Repository secrets**. Click **New repository secret** for each secret below.

---

## Step 2: Create the secret `TWITTER_COOKIES_JSON`

1. Click **New repository secret**.
2. **Name** (exactly): `TWITTER_COOKIES_JSON`
3. **Secret** (value):  
   - **Cookie-Editor (x.com):** export as JSON array; copy only the `[...]` part.  
   - **Netscape cookies.txt:** run `python scripts/netscape_cookies_to_json.py path/to/cookies.txt` and copy the printed JSON.  
   - **From `credentials.json`**: copy only the array after `"twitter_cookies":` (from `[` to `]`).  
   If your export has `"domain": "x.com"` (no dot), that’s fine—the app normalizes it to `.x.com`.  
   So you copy only the array, e.g.:
   ```text
   [{"domain":".x.com","expirationDate":1806427706.885005,...},...]
   ```
   - Do **not** include `"twitter_cookies":` — only the `[...]` part.
   - The copied value can be one long line (that’s fine).
   - Paste that entire array into the **Secret** field, then save.
4. Click **Add secret**.

---

## Step 3 (optional): Create the secret `LLM_API_KEY`

Only if you want AI-generated replies (Groq). Without it, template replies are used.

1. Click **New repository secret**.
2. **Name**: `LLM_API_KEY`
3. **Secret**: your Groq API key (e.g. `gsk_...`)

---

## Step 4 (optional): Create the secret `LLM_MODEL`

Only if you want to override the default model:

1. Click **New repository secret**.
2. **Name**: `LLM_MODEL`
3. **Secret**: e.g. `llama-3.1-8b-instant` (or leave this secret out to use the default).

---

## Step 5: Run the workflow

1. Go to **Actions** (top tab of the repo).
2. Click **NBAVision Engine** in the left sidebar.
3. Click **Run workflow** (right side), then the green **Run workflow** button.
4. The run should pass the “Check required secrets” step and then run the engine.

---

## Quick reference

| Secret name            | Required | Where to get the value                                      |
|------------------------|----------|--------------------------------------------------------------|
| `TWITTER_COOKIES_JSON` | Yes      | Cookie-Editor on x.com → `[...]` array, or `scripts/netscape_cookies_to_json.py cookies.txt` → copy output |
| `LLM_API_KEY`          | No       | Groq API key (templates used if not set)                    |
| `LLM_MODEL`            | No       | e.g. `llama-3.1-8b-instant`                                  |

**Direct link to add secrets:**  
**https://github.com/AnthonyNadjari/NBAVisionEngine/settings/secrets/actions**
