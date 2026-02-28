# Export Twitter / X cookies for NBAVision Engine

The engine reads cookies from **`credentials.json`** at the project root (local runs), or from the **`TWITTER_COOKIES_JSON`** repository secret (GitHub Actions). It supports both `.x.com` and `.twitter.com` cookies; **x.com** URLs are used so `.x.com` cookies work. Put the exported array in the `twitter_cookies` key (credentials.json) or paste the same JSON as the value of the **TWITTER_COOKIES_JSON** secret.

## 1. Log in to Twitter

- Open **Chrome** or **Edge** and go to [twitter.com](https://twitter.com) (or x.com).
- Log in with the account you want the bot to use.

## 2. Install a cookie export extension

Use one of these (or any extension that exports cookies as **JSON array**):

- **[Cookie-Editor](https://chromewebstore.google.com/detail/cookie-editor/hlkenndednhfkekhgpnkiidkbajdkebn)** (recommended)
- **[EditThisCookie](https://chromewebstore.google.com/detail/editthiscookie/fngmhnnpilhplaeedifhccceomclgfbg)**

## 3. Export cookies on twitter.com

1. Stay on **twitter.com** (or **x.com**) with your session active.
2. Open the extension (click its icon).
3. **Cookie-Editor:** click **Export** → choose **JSON** → copy the whole output (must be a JSON **array** `[...]`).
4. **EditThisCookie:** export in JSON format; if it gives an object `{}`, convert to array `[{...}]` or use Cookie-Editor.

## 4. Expected format

The value must be a **JSON array** of cookie objects. Each object should have at least:

- `name` (e.g. `auth_token`, `ct0`, `twid`, …)
- `value`
- `domain` (e.g. `.twitter.com`)
- `path` (often `"/"`)

Example (shortened):

```json
[
  {"name":"auth_token","value":"xxxx","domain":".twitter.com","path":"/","httpOnly":true,"secure":true},
  {"name":"ct0","value":"yyyy","domain":".twitter.com","path":"/",...}
]
```

## 5. Where to put the cookies

Put them in **`credentials.json`** at the project root:

```json
{
  "llm_api_key": "your_groq_api_key",
  "llm_model": "llama-3.1-8b-instant",
  "twitter_cookies": [
    {"name":"auth_token","value":"...","domain":".x.com","path":"/",...},
    ...
  ]
}
```

Paste your exported cookie array into the `twitter_cookies` key. Same file is used for local runs and GitHub Actions (no secrets). You can also use env vars or a separate `cookies.json` (see config) if you prefer.

**Note:** If the repo is public, anyone can see `credentials.json`. Prefer a private repo or keep the file out of git if that's a concern.

## 6. Refresh when session expires

If the engine starts failing with “Cookie invalid” or login redirects, your session expired. Export the cookies again from the same browser where you’re logged in and update the `twitter_cookies` array in `credentials.json`.
