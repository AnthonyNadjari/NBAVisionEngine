# GitHub Actions — Set up secrets (step-by-step)

The workflow needs **2 repository secrets**. Follow these steps exactly.

**Cookie export:** Use a browser extension (e.g. [Cookie-Editor](https://chromewebstore.google.com/detail/cookie-editor/hlkenndednhfkekhgpnkiidkbajdkebn), EditThisCookie) on x.com while logged in → Export as JSON array.

---

## Step 1: Open the secrets page

1. Go to **https://github.com/AnthonyNadjari/NBAVisionEngine**
2. Click **Settings** (top tab bar of the repo).
3. In the left sidebar, under **Security**, click **Secrets and variables** → **Actions**.
4. You should see **Repository secrets**. Click **New repository secret** for each secret below.

---

## Step 2: Create the secret `LLM_API_KEY`

1. Click **New repository secret**.
2. **Name** (exactly): `LLM_API_KEY`
3. **Secret** (value):  
   Open your local file **`credentials.json`** in the project root.  
   Copy the value of **`llm_api_key`** (the long string in quotes, e.g. `gsk_...`).  
   Paste it into the **Secret** field.  
   Do **not** include the key name or the quotes—only the key value.
4. Click **Add secret**.

---

## Step 3: Create the secret `TWITTER_COOKIES_JSON`

1. Click **New repository secret** again.
2. **Name** (exactly): `TWITTER_COOKIES_JSON`
3. **Secret** (value):  
   Open **`credentials.json`**.  
   Find the part that says `"twitter_cookies":` followed by a **square bracket** `[`.  
   Copy **everything from that `[` to the matching `]`** at the end of the cookies array.  
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

| Secret name            | Where to get the value                                      |
|------------------------|--------------------------------------------------------------|
| `LLM_API_KEY`          | In `credentials.json`: the value of `"llm_api_key"`          |
| `TWITTER_COOKIES_JSON` | In `credentials.json`: only the `[...]` array after `"twitter_cookies":` |
| `LLM_MODEL` (optional) | e.g. `llama-3.1-8b-instant`                                  |

**Direct link to add secrets:**  
**https://github.com/AnthonyNadjari/NBAVisionEngine/settings/secrets/actions**
