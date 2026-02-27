# Export Twitter / X cookies for NBAVision Engine

The engine runs on GitHub Actions and needs your X (Twitter) session as cookies. It supports both `.x.com` and `.twitter.com` cookies; **x.com** URLs are used so `.x.com` cookies work. Here’s how to get them **safely** (never commit or share this JSON).

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

- **Local run:** put the JSON in a `.env` file as:
  ```bash
  TWITTER_COOKIES_JSON=[{"name":"auth_token",...}]
  ```
  (one line, no extra quotes around the JSON; the whole array is the value.)

- **GitHub Actions:** in your repo go to **Settings → Secrets and variables → Actions**, add a secret:
  - **Name:** `TWITTER_COOKIES_JSON`
  - **Value:** paste the **entire** JSON array (one line is fine). Same format as when you export from x.com/twitter.com (Cookie-Editor / EditThisCookie).

- **Local run:** you can also put the JSON in a file named `cookies.json` in the project root (the file is gitignored). If `TWITTER_COOKIES_JSON` is not set, the app will load from `cookies.json` (or from the path in `TWITTER_COOKIES_FILE`).

Do **not** commit `cookies.json`, `.env`, or paste cookies in code or issues. Treat them like a password.

## 6. Refresh when session expires

If the engine starts failing with “Cookie invalid” or login redirects, your session expired. Export the cookies again from the same browser where you’re logged in and update the secret (or `.env`).
