# CongiGuard Desktop Agent

Standalone background tracker for Windows. Replaces the old manually-run
`activity_logger.py`. Logs in once, then runs invisibly at every Windows
login, uploading activity to your deployed backend and sending a
heartbeat so the dashboard always knows if the laptop is online.

## Folder contents

| File                   | Purpose                                             |
|-------------------------|------------------------------------------------------|
| `config.py`             | Stores server URL / tokens / device id locally        |
| `auth.py`               | Login + token refresh (reuses your existing `/auth` API) |
| `logger.py`             | Keyboard/mouse/window hooks (your original tracker, refactored) |
| `uploader.py`           | Sends batches to `/api/v1/usage/laptop/batch`         |
| `heartbeat.py`          | Pings `/api/v1/pairing/heartbeat` every 30s           |
| `main.py`               | CLI entry point: `login`, `run`, `status`             |
| `build_exe.bat`         | Packages everything into `CongiGuardAgent.exe`         |
| `install_startup.bat`   | Registers a Scheduled Task to auto-run at logon        |
| `uninstall_startup.bat` | Removes that Scheduled Task                            |

## 0. Recommended flow: pairing code (no password needed)

The website's first-login onboarding page (`/dashboard` when no device is
connected yet) shows a 6-character pairing code -- the same mechanism as
the existing QR pairing. To connect:

```bat
CongiGuardAgent.exe pair 048D9F
CongiGuardAgent.exe run
```

This reuses the backend's existing `/pairing/verify-pairing` endpoint, so
no email/password ever has to be typed into a terminal. `login` (below)
still works as an alternative if you'd rather use credentials directly.

## 1. First-time setup (development / testing)

```bat
cd desktop-agent
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

REM Point the agent at your deployed backend
set CONGIGUARD_SERVER_URL=https://your-backend.onrender.com

python main.py login you@example.com yourpassword
python main.py run
```

You should see `[UPLOAD] Sent N record(s)` in the console every 5 minutes,
and within ~30 seconds the dashboard's Device Pairing page should show
the laptop as **Connected**.

## 2. Build the real installer-free `.exe`

```bat
build_exe.bat
```

This produces `dist\CongiGuardAgent.exe` - a single file with no Python
install required on the target machine.

Before distributing it, either:
- bake the server URL in by editing `DEFAULT_SERVER_URL` logic in
  `config.py`'s fallback return value, or
- tell users to run `CongiGuardAgent.exe login` once, which prompts for
  email/password and saves everything (including server URL, if you set
  `CONGIGUARD_SERVER_URL` as a machine environment variable first).

## 3. Make it start automatically

```bat
CongiGuardAgent.exe login you@example.com yourpassword
install_startup.bat
```

This registers a **Scheduled Task** ("run at logon"), not a Windows
Service. That's intentional: global keyboard/mouse hooks and reading the
foreground window only work in your interactive desktop session. A real
Windows Service runs isolated in Session 0 and would silently see none of
that - a very common mistake in this kind of project. Run-at-logon still
means the user never has to manually start it again.

To remove it: `uninstall_startup.bat`.

## 4. What actually gets sent, and how often

This matches your original `activity_logger.py` design exactly:

- Every **60 seconds**: one raw activity sample (keystrokes, mouse clicks/moves,
  idle time, active app + category, app switch count, time-of-day bucket) is
  captured into an in-memory buffer. Nothing is uploaded yet.
- Every **10 samples** (~10 minutes): those 10 raw samples are collapsed into
  **one single summarized record** -- dominant app/category (most frequent
  across the window), summed keystrokes/clicks/moves/switches, total idle
  seconds, and a precise `session_length_minutes`. That one record is POSTed
  to `/api/v1/usage/laptop/batch`, authenticated with the JWT from login.
  If the upload fails (network/server issue), the 10 samples are **not**
  discarded -- the agent retries with the same window on the next sample
  until it succeeds, so no data is silently lost.
- Every **30 seconds**: a heartbeat POST to `/api/v1/pairing/heartbeat`
  updates `last_heartbeat` / `status: connected` on the device record,
  independent of the upload cadence above -- this is what the dashboard's
  "online" indicator reads from (`GET /api/v1/pairing/agent-status?user_id=...`).

## 5. Troubleshooting

- **"Not logged in" on `run`**: run `login` again; access tokens expire
  (see `ACCESS_TOKEN_EXPIRE_MINUTES` in the backend), but the agent
  auto-refreshes using the stored refresh token as long as it's < 30 days
  old (`REFRESH_TOKEN_EXPIRE_DAYS`).
- **Dashboard still shows offline after starting the agent**: check that
  `CONGIGUARD_SERVER_URL` / the saved `server_url` actually points at your
  Render backend, not `localhost`. Run `python main.py status` to confirm.
- **No activity showing up**: `pywin32` must be installed for
  `win32gui`/`win32process` to work (Windows-only). On non-Windows dev
  machines the logger still runs but active-window detection degrades
  gracefully to `"Unknown"`.
