# 3D Print Stats Dashboard — Setup Guide

A local dashboard that pulls your stats from Thingiverse, Printables,
and MakerWorld into one place, with history tracking over time.

## Files
- `fetch_stats.py`   — Fetches stats from all platforms, saves to stats_history.json
- `dashboard.html`   — Open in your browser to see your stats
- `run_dashboard.bat`— Double-click to fetch + open dashboard (Windows)
- `stats_history.json` — Created automatically after first run

---

## Step 1: Install Python

If you don't have Python, download it from https://python.org/downloads
(tick "Add to PATH" during install). No extra packages needed — uses only stdlib.

---

## Step 2: Configure fetch_stats.py

Open `fetch_stats.py` in Notepad and fill in the CONFIG section at the top:

### Thingiverse
1. Go to https://www.thingiverse.com/developers
2. Create an App → get your access token
3. Fill in `username` and `access_token`

### Printables
1. Your `username` is your display name (e.g. "CoolMaker3D")
2. Your `user_id` is the number in your profile URL:
   `printables.com/@YourName_XXXXXX` → the number after the underscore
   OR go to your profile → the URL shows your numeric ID

### MakerWorld (requires a session token — refreshed periodically)
1. Log into makerworld.com in Chrome/Edge
2. Press F12 to open DevTools → click "Network" tab
3. Refresh the page
4. Click any request to makerworld.com in the list
5. Look in "Request Headers" for: `Authorization: Bearer eyJ...`
6. Copy everything AFTER "Bearer " and paste as `auth_token`

Note: MakerWorld tokens expire after a few days/weeks. When MW stops
working, repeat steps 1-6 above to get a fresh token.

---

## Step 3: Run it

Double-click `run_dashboard.bat` — it will:
1. Fetch your stats from all configured platforms
2. Save them to stats_history.json
3. Open dashboard.html in your browser

---

## Step 4: Run it daily (optional, for trend charts)

To automatically fetch every day:
1. Press Win+R → type `taskschd.msc` → Enter
2. Click "Create Basic Task"
3. Name: "3D Stats Fetcher" → Daily → set your preferred time
4. Action: "Start a program"
5. Program: `python`
6. Arguments: `C:\path\to\your\fetch_stats.py`
7. Start in: `C:\path\to\your\folder\`

After a week of daily runs, the trend chart in the dashboard will show history.

---

## Troubleshooting

**"No stats data found"** — Run fetch_stats.py first, then refresh the dashboard.

**Thingiverse returns nothing** — Their API is flaky. Try again later.

**Printables returns no view counts** — Detailed analytics require login.
  The public GraphQL API returns totals but not per-day breakdown.

**MakerWorld fails** — Token expired. Get a fresh one (see Step 2 above).

**Dashboard shows old data** — Re-run fetch_stats.py (or run_dashboard.bat).
