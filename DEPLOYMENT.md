# Deployment Guide

Everything needed to take this project from local dev to a live, working
deployment, in order. Follow it top to bottom once; you shouldn't need to
improvise anything.

## ⚠️ Do this first: rotate your MongoDB credentials

`.env.example` previously had a **real MongoDB username/password
committed in plaintext**, and this repo was pushed to GitHub with it in
there. Fixing the file doesn't remove it from git history — anyone who
ever cloned or viewed the repo already has it. Before anything else:

1. MongoDB Atlas -> Database Access -> edit your database user -> **change
   the password**.
2. Update `MONGODB_URL` everywhere you use it: local `.env`, Render
   environment variables.
3. Also regenerate `SECRET_KEY` the same way (`python -c "import secrets;
   print(secrets.token_hex(32))"`) and update it everywhere too, since a
   leaked `SECRET_KEY` lets anyone forge valid login tokens.

Do this even if the repo is currently private — private repos can be made
public later, and this removes the risk permanently.

## 1. Backend -> Render

Using `render.yaml` (already in the repo root):

1. Push this repo to GitHub (after rotating credentials above).
2. Render dashboard -> New -> **Blueprint** -> connect the repo. Render
   reads `render.yaml` automatically and creates the service.
3. It will prompt you for the 3 secrets marked `sync: false`:
   - `MONGODB_URL` (your new connection string)
   - `DATABASE_NAME` (e.g. `fatigue_db`)
   - `SECRET_KEY` (your new one)
4. Deploy. Once live, check `https://<your-service>.onrender.com/health`
   — should show `"database": "connected"`.
5. **Required for mobile QR pairing:** go back into Render's environment
   variables and add `BACKEND_PUBLIC_URL=https://<your-service>.onrender.com`
   (the exact URL Render just gave you), then redeploy. Without this, QR
   codes silently embed the server's local WiFi IP instead of a real
   public URL, and phone pairing will fail with no obvious error.

**Without render.yaml** (manual dashboard setup) works too — New -> Web
Service -> root directory `backend` -> build `pip install -r
requirements.txt` -> start `python run.py` -> add the same env vars from
`render.yaml` manually.

**Free tier note:** Render's free plan sleeps after ~15 min idle and
takes 30-60s to wake on the next request. Expect a delayed first
heartbeat/health check after any period of inactivity — this is normal,
not a bug.

## 2. Frontend -> Netlify

Using `netlify.toml` (already in the repo root):

1. Netlify -> Add new site -> Import from Git -> select this repo.
   `netlify.toml` sets the base directory, build command, and publish
   directory automatically.
2. Site settings -> Environment variables -> add:
   ```
   VITE_API_BASE_URL = https://<your-render-service>.onrender.com/api/v1
   ```
3. Deploy. Env var changes require a rebuild — trigger one if you add
   this after the first deploy.
4. Visit the site, register, log in. You should land on the "Connect
   this laptop" onboarding page (see below), not an error.

## 3. Desktop Agent -> build and host the installer

This step **cannot be automated from a website** — browsers can't
execute downloaded files, so this one-time packaging step is manual, done
by you (not by each end user):

```bat
cd desktop-agent
pip install -r requirements.txt
build_exe.bat
```

Copy the result into the frontend so Netlify serves it:
```
desktop-agent\dist\CongiGuardAgent.exe  ->  frontend\public\downloads\CongiGuardAgent.exe
```
Delete `frontend/public/downloads/PLACE_EXE_HERE.txt`, then redeploy the
frontend (`git push` if using Netlify's auto-deploy, or drag-and-drop
rebuild). It becomes reachable at
`https://<your-site>.netlify.app/downloads/CongiGuardAgent.exe`, which is
the exact path the onboarding page links to — no code change needed if
the filename matches.

## 4. Post-deploy verification checklist

Run through this once after every deploy:

- [ ] `GET https://<render-service>.onrender.com/health` -> `database: connected`
- [ ] `GET https://<render-service>.onrender.com/api/v1/auth/debug` -> `404 Not Found`
      (confirms `DEBUG_MODE` is off; if this returns user data, fix your
      Render env vars immediately)
- [ ] Netlify site loads, register + login work
- [ ] After login: "Connect this laptop" onboarding page appears (first
      time) with a pairing code
- [ ] Download button on that page returns the real `.exe` (not a 404)
- [ ] Run `CongiGuardAgent.exe pair <code>` then `CongiGuardAgent.exe run`
      on a Windows machine -> onboarding page auto-redirects to dashboard
      within ~10 seconds
- [ ] Wait ~10 minutes -> Dashboard shows non-zero, proportionate
      screen-time/fatigue/productivity numbers (not inflated -- see the
      unit-consistency note below)
- [ ] Log in from a second browser/device as the same user -> should skip
      straight to dashboard (no onboarding page), confirming heartbeat
      detection works across sessions

## 6. Data retention (MongoDB won't grow forever)

`usage_data` and `predictions` now have **TTL indexes** on `timestamp` —
MongoDB itself automatically deletes documents older than
`USAGE_DATA_RETENTION_DAYS` / `PREDICTIONS_RETENTION_DAYS` (default: 10
days each), no cron job or app code involved. This is set safely above
the dashboard's actual 7-day lookback window (see `usage.py`'s
`trends`/`analytics` endpoints), so nothing the UI ever queries gets
deleted early.

This applies automatically to your **existing** Atlas data too, including
old test junk from earlier debugging sessions — MongoDB's TTL background
process runs every ~60 seconds and will clean up anything already past
the retention window within a minute or two of the backend's next
restart (when the index gets created/verified).

To verify it's active: Atlas -> Browse Collections -> `usage_data` ->
Indexes tab -> you should see a `timestamp_1` index with
`expireAfterSeconds` set. Adjust the retention via the env vars above if
you ever want more/less history kept (e.g. bump both to 30-60 days if you
later add month-over-month trend views).

## 8. Mobile: pairing works, activity tracking does not (by design, not a bug)

The backend has a real `/api/v1/usage/mobile` endpoint ready to receive
phone activity data, and QR-code pairing correctly registers a phone as
a connected device. But **no mobile app exists in this repo** to actually
collect and send that data. A browser tab (which is all a QR scan opens)
cannot read a phone's OS-level screen time or app usage — that requires
a native Android/iOS app with special permissions (Usage Access API /
Screen Time API), which is a separate app-development project, not
something addable to a website. A paired phone will show as "connected"
but will never contribute real fatigue/productivity data unless a native
app is built later.

## 9. Known limitations, by design (not bugs)

- **The `.exe` must be built on Windows.** PyInstaller can't cross-compile
  a Windows binary from Linux/Mac. If you don't have Windows available,
  a GitHub Actions `windows-latest` runner can build it for you headlessly
  — ask if you want that workflow file added.
- **First install always needs one manual double-click.** No website can
  auto-run a downloaded executable; this is a browser security boundary,
  not something specific to this project.
- **Render free tier sleeps.** Consider a paid instance (or an external
  uptime pinger hitting `/health` every 10 min) if you need the backend
  always warm for a live demo.
- **Data units matter if you ever touch `desktop-agent/logger.py`
  again:** `usage_duration` must always be in **minutes**, matching
  `backend/src/routes/usage.py`'s `total_minutes = sum(usage_duration)`
  convention. Getting this wrong (as an earlier version of this file did)
  silently inflates every dashboard number by whatever factor is off.
