# Webhook-triggered local automation

Run NBAVision Engine on your local machine, triggered remotely from GitHub Pages. Uses a **persistent Chromium profile** — log into X once, never export cookies again.

---

## 1. One-time setup

### 1.1 Install dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### 1.2 Create browser profile and log in

1. Run the login script (opens a browser window):

   ```bash
   python login_once.py
   ```

   Log into X in the browser, then press Enter in the terminal.

2. After that, the profile in `./browser_profile` contains your session. No cookie export needed.

### 1.3 Set secret

```bash
export NBAVISION_SECRET="your_strong_random_secret"
```

Generate a strong secret, e.g.:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 1.4 Start the server

```bash
uvicorn server:app --host 127.0.0.1 --port 8000
```

The webhook is at `http://localhost:8000/trigger`.

---

## 2. Expose webhook via tunnel (HTTPS)

GitHub Pages cannot call your localhost. Use a free tunnel to expose `http://localhost:8000` over HTTPS.

### Option A: Cloudflare Tunnel (free, no account data shared)

1. Install: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/
2. Authenticate: `cloudflared tunnel login`
3. Create tunnel: `cloudflared tunnel create nbavision`
4. Run tunnel (no config file):

   ```bash
   cloudflared tunnel --url http://localhost:8000
   ```

   You get a URL like `https://xxxx-xx-xx-xx-xx.trycloudflare.com`. Use that as the webhook base.

### Option B: ngrok (free tier)

1. Sign up: https://ngrok.com
2. Install: https://ngrok.com/download
3. Run:

   ```bash
   ngrok http 8000
   ```

   Use the HTTPS URL shown (e.g. `https://abc123.ngrok-free.app`).

---

## 3. Trigger from GitHub Pages

Update your Control Center or add a "Trigger local" button that sends:

```http
POST https://YOUR_TUNNEL_URL/trigger
X-API-KEY: your_strong_random_secret
```

Example with `fetch`:

```javascript
fetch('https://YOUR_TUNNEL_URL/trigger', {
  method: 'POST',
  headers: { 'X-API-KEY': 'your_secret' }
}).then(r => r.json()).then(console.log);
```

---

## 4. Run as a service

### Linux (systemd)

1. Copy and edit `nbavision.service`:
   - Set `User`, `WorkingDirectory`, `ExecStart` path, `NBAVISION_SECRET`, `NBAVISION_BROWSER_PROFILE`
2. Install:

   ```bash
   sudo cp nbavision.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable nbavision
   sudo systemctl start nbavision
   ```

3. Run the tunnel in another terminal or as a separate service.

### Windows (Task Scheduler)

1. Create a batch file `start_server.bat`:

   ```bat
   @echo off
   cd C:\path\to\NBAVisionEngine
   set NBAVISION_SECRET=your_secret
   .venv\Scripts\uvicorn server:app --host 127.0.0.1 --port 8000
   ```

2. Task Scheduler → Create Basic Task → Trigger: At log on → Action: Start a program → Program: `C:\path\to\start_server.bat`
3. Run the tunnel (ngrok/cloudflared) separately or add it to the batch file.

---

## 5. Security

- **NBAVISION_SECRET** must be strong and kept private.
- The server listens on `127.0.0.1` by default; only the tunnel should expose it.
- Rate limit: 5 triggers per hour.
- All trigger attempts are logged to `nbavision_server.log`.

---

## 6. Concurrency

- Only one engine run at a time.
- If a run is in progress, `POST /trigger` returns **409 Conflict**.
- Use `GET /health` to check `running` status.
