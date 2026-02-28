# GitHub Actions — Set up secrets (step-by-step)

The workflow needs **1 required secret** (TWITTER_COOKIES_JSON). LLM_API_KEY is optional (templates used if not set).

**Cookie export:** Use a browser extension (e.g. [Cookie-Editor](https://chromewebstore.google.com/detail/cookie-editor/hlkenndednhfkekhgpnkiidkbajdkebn), EditThisCookie) on x.com while logged in → Export as JSON array.

**Session lifetime:** Runs from GitHub Actions use a datacenter IP; X often invalidates sessions after a while. Re-export cookies when you see "session invalid or expired". To re-export less often, run the workflow weekly (edit the cron in the workflow) or run the engine locally.

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
   Export cookies from x.com (extension Cookie-Editor) → format JSON array.  
   Or if you have `credentials.json`: copy only the array after `"twitter_cookies":` (from `[` to `]`).  
   If your export has `"domain": "x.com"` (no dot), that’s fine—the app normalizes it to `.x.com`.  
   So you copy only the array, e.g.:
   ```text
   [{"domain":".x.com","expirationDate":1806427706.885005,...},...]
   ```
   - Do **not** include `"twitter_cookies":` — only the `[...]` part.
   - The copied value can be one long line (that’s fine).
   - Paste that entire array into the **Secret** field.
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
| `TWITTER_COOKIES_JSON` | Yes      | Export cookies from x.com (Cookie-Editor) → only the `[...]` array |
| `LLM_API_KEY`          | No       | Groq API key (templates used if not set)                    |
| `LLM_MODEL`            | No       | e.g. `llama-3.1-8b-instant`                                  |

**Direct link to add secrets:**  
**https://github.com/AnthonyNadjari/NBAVisionEngine/settings/secrets/actions**
