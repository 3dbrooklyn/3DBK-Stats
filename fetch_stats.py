#!/usr/bin/env python3
"""
3D Print Platform Stats Aggregator
Fetches stats from Thingiverse, Printables, and MakerWorld
and saves them to stats_history.json for the dashboard.

Run this script daily (manually or via Task Scheduler).
"""

import json
import os
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, date

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION — Fill these in before running!
# ─────────────────────────────────────────────────────────────────────────────

CONFIG = {
    "thingiverse": {
        "enabled": True,
        "username":     os.environ.get("TV_USERNAME",     "3DBrooklyn"),
        "access_token": os.environ.get("TV_ACCESS_TOKEN", "18e202ccdaa399fd401ad644c206ff09"),
    },
    "printables": {
        "enabled": True,
        "username": os.environ.get("PR_USERNAME", "3DBrooklyn"),
        "user_id":  os.environ.get("PR_USER_ID",  "273681"),
    },
    "makerworld": {
        "enabled": True,
        "username":   os.environ.get("MW_USERNAME",   "3DBrooklyn"),
        "auth_token": os.environ.get("MW_AUTH_TOKEN", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJVc2VySUQiOiIxNjIzMTM5NzMiLCJQbGF0Zm9ybUlEIjo1LCJleHAiOjE3ODQ2ODY1NzUsIm5iZiI6MTc2OTEzNDI3NSwiaWF0IjoxNzY5MTM0NTc1fQ.hfLVd0VVrfEdwO5T19WYPC7id2zFSsb6HjDwG5WYPPk"),
    },
    "myminifactory": {
        "enabled": True,
        "username": os.environ.get("MMF_USERNAME", "3DBrooklyn"),
        "api_key":  os.environ.get("MMF_API_KEY",  "4ef253f6-408b-4d16-ae6a-a72406f46163"),
    },
}

HISTORY_FILE = os.path.join(os.path.dirname(__file__), "stats_history.json")

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def http_get(url, headers=None, timeout=15):
    """Simple HTTP GET, returns parsed JSON or None on error."""
    req = urllib.request.Request(url, headers=headers or {})
    req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"  HTTP {e.code} for {url}")
        return None
    except Exception as e:
        print(f"  Error fetching {url}: {e}")
        return None

def graphql_post(url, query, variables=None, headers=None, timeout=15):
    """POST a GraphQL query, returns parsed JSON or None."""
    payload = json.dumps({"query": query, "variables": variables or {}}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers=headers or {}, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"  HTTP {e.code}: {body[:200]}")
        return None
    except Exception as e:
        print(f"  Error: {e}")
        return None

# ─────────────────────────────────────────────────────────────────────────────
# THINGIVERSE
# ─────────────────────────────────────────────────────────────────────────────

def fetch_thingiverse(cfg):
    print("Fetching Thingiverse...")
    username = cfg["username"]
    token = cfg["access_token"]
    base = "https://api.thingiverse.com"

    totals = {"views": 0, "downloads": 0, "likes": 0}
    models = []
    page = 1

    while True:
        url = f"{base}/users/{username}/things?access_token={token}&page={page}&per_page=30"
        data = http_get(url)
        if not data or not isinstance(data, list) or len(data) == 0:
            break

        for thing in data:
            v = thing.get("view_count", 0) or 0
            d = thing.get("download_count", 0) or 0
            l = thing.get("like_count", 0) or 0
            totals["views"] += v
            totals["downloads"] += d
            totals["likes"] += l
            models.append({
                "id": thing.get("id"),
                "name": thing.get("name", "Unknown"),
                "url": thing.get("public_url", ""),
                "views": v,
                "downloads": d,
                "likes": l,
                "thumbnail": thing.get("thumbnail", ""),
            })

        print(f"  Page {page}: {len(data)} models")
        if len(data) < 30:
            break
        page += 1
        time.sleep(0.5)

    print(f"  ✓ Thingiverse: {len(models)} models | {totals['views']} views | {totals['downloads']} downloads")
    return {"totals": totals, "models": models}


# ─────────────────────────────────────────────────────────────────────────────
# PRINTABLES
# ─────────────────────────────────────────────────────────────────────────────

PRINTABLES_QUERY = """
query ProfileModels($userId: ID!, $limit: Int!, $cursor: String) {
  morePrints(
    userId: $userId
    limit: $limit
    cursor: $cursor
    ordering: "-likes_count"
  ) {
    cursor
    items {
      id
      name
      slug
      likesCount
      downloadCount
      displayCount
      image { filePath }
    }
  }
}
"""

def fetch_printables(cfg):
    print("Fetching Printables...")
    user_id = cfg["user_id"]
    url = "https://api.printables.com/graphql/"

    totals = {"views": 0, "downloads": 0, "likes": 0}
    models = []
    cursor = None

    while True:
        variables = {"userId": user_id, "limit": 50, "cursor": cursor}
        resp = graphql_post(url, PRINTABLES_QUERY, variables)

        if not resp:
            print("  Failed to get Printables data")
            break

        items = resp.get("data", {}).get("morePrints", {})
        batch = items.get("items", [])
        cursor = items.get("cursor")

        if not batch:
            break

        for m in batch:
            v = m.get("displayCount", 0) or 0
            d = m.get("downloadCount", 0) or 0
            l = m.get("likesCount", 0) or 0
            totals["views"] += v
            totals["downloads"] += d
            totals["likes"] += l

            img_path = (m.get("image") or {}).get("filePath", "")
            thumb = f"https://media.printables.com/{img_path}" if img_path else ""

            models.append({
                "id": m.get("id"),
                "name": m.get("name", "Unknown"),
                "url": f"https://www.printables.com/model/{m.get('id')}-{m.get('slug', '')}",
                "views": v,
                "downloads": d,
                "likes": l,
                "thumbnail": thumb,
            })

        print(f"  Got {len(batch)} models (total so far: {len(models)})")
        if not cursor:
            break
        time.sleep(0.3)

    print(f"  ✓ Printables: {len(models)} models | {totals['views']} views | {totals['downloads']} downloads")
    return {"totals": totals, "models": models}


# ─────────────────────────────────────────────────────────────────────────────
# MAKERWORLD
# ─────────────────────────────────────────────────────────────────────────────

def fetch_makerworld(cfg):
    print("Fetching MakerWorld...")
    token = cfg["auth_token"]
    uid = cfg.get("user_id", "162313973")

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }

    profile_url = f"https://makerworld.com/api/v1/design-user-service/user/profile/{uid}"
    profile = http_get(profile_url, headers=headers)

    if not profile:
        print("  Could not fetch MakerWorld profile. Check your auth token.")
        return None

    mw = profile.get("MWCount", {})
    totals = {
        "downloads": mw.get("myDesignDownloadCount", 0) or 0,
        "views":     profile.get("collectionCount", 0) or 0,
        "likes":     profile.get("likeCount", 0) or 0,
        "prints":    mw.get("myDesignPrintCount", 0) or 0,
    }

    # Build model list from pinned/featured designs in profile
    models = []
    for m in profile.get("personal", {}).get("designsInfo", []):
        mid = m.get("id", "")
        models.append({
            "id": mid,
            "name": m.get("title") or m.get("name", "Unknown"),
            "url": f"https://makerworld.com/en/models/{mid}",
            "views": 0,
            "downloads": 0,
            "likes": 0,
            "prints": 0,
            "thumbnail": m.get("cover", ""),
        })

    print(f"  ✓ MakerWorld: {mw.get('designCount', 0)} models | {totals['downloads']} downloads | {totals['prints']} prints")
    return {"totals": totals, "models": models}


# ─────────────────────────────────────────────────────────────────────────────
# MYMINIFACTORY
# ─────────────────────────────────────────────────────────────────────────────

def fetch_myminifactory(cfg):
    print("Fetching MyMiniFactory...")
    username = cfg["username"]
    api_key  = cfg["api_key"]
    base     = "https://www.myminifactory.com/api/v2"

    totals = {"views": 0, "likes": 0}
    models = []
    page   = 1

    while True:
        url  = f"{base}/users/{username}/objects?key={api_key}&per_page=20&page={page}"
        data = http_get(url)
        if not data:
            print("  Could not fetch MyMiniFactory data. Check your API key and username.")
            break

        items = data.get("items", [])
        if not items:
            break

        for obj in items:
            v = obj.get("views", 0) or 0
            l = obj.get("likes", 0) or 0
            totals["views"]  += v
            totals["likes"]  += l

            images = obj.get("images") or []
            thumb  = ""
            if images:
                primary = next((i for i in images if i.get("is_primary")), images[0])
                thumb = (primary.get("tiny") or primary.get("original") or {}).get("url", "")

            models.append({
                "id":        obj.get("id"),
                "name":      obj.get("name", "Unknown"),
                "url":       obj.get("url", f"https://www.myminifactory.com/object/{obj.get('id')}"),
                "views":     v,
                "downloads": 0,
                "likes":     l,
                "thumbnail": thumb,
            })

        print(f"  Page {page}: {len(items)} models")
        total_count = data.get("total_count", 0)
        if len(models) >= total_count or len(items) < 20:
            break
        page += 1
        time.sleep(0.5)

    print(f"  ✓ MyMiniFactory: {len(models)} models | {totals['views']} views | {totals['likes']} likes")
    return {"totals": totals, "models": models}


# ─────────────────────────────────────────────────────────────────────────────
# HISTORY MANAGEMENT
# ─────────────────────────────────────────────────────────────────────────────

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"snapshots": [], "config": {}}

def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  3D Platform Stats Fetcher")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Validate config
    placeholders = ["YOUR_", "YOUR_THINGIVERSE", "YOUR_PRINTABLES", "YOUR_MAKERWORLD"]
    for platform, cfg in CONFIG.items():
        for key, val in cfg.items():
            if key == "enabled":
                continue
            if any(p in str(val) for p in placeholders):
                print(f"\n⚠️  CONFIG NEEDED: Set your {platform} '{key}' in fetch_stats.py")

    snapshot = {
        "date": date.today().isoformat(),
        "timestamp": datetime.now().isoformat(),
        "platforms": {}
    }

    tv_cfg = CONFIG["thingiverse"]
    if tv_cfg["enabled"] and "YOUR_" not in tv_cfg["access_token"]:
        result = fetch_thingiverse(tv_cfg)
        if result:
            snapshot["platforms"]["thingiverse"] = result
    else:
        print("Skipping Thingiverse (not configured)")

    pr_cfg = CONFIG["printables"]
    if pr_cfg["enabled"] and "YOUR_" not in pr_cfg["user_id"]:
        result = fetch_printables(pr_cfg)
        if result:
            snapshot["platforms"]["printables"] = result
    else:
        print("Skipping Printables (not configured)")

    mw_cfg = CONFIG["makerworld"]
    if mw_cfg["enabled"] and "YOUR_" not in mw_cfg["auth_token"]:
        result = fetch_makerworld(mw_cfg)
        if result:
            snapshot["platforms"]["makerworld"] = result
    else:
        print("Skipping MakerWorld (not configured)")

    mmf_cfg = CONFIG["myminifactory"]
    if mmf_cfg["enabled"] and "YOUR_" not in mmf_cfg["api_key"]:
        result = fetch_myminifactory(mmf_cfg)
        if result:
            snapshot["platforms"]["myminifactory"] = result
    else:
        print("Skipping MyMiniFactory (not configured)")

    # Load history and append new snapshot
    history = load_history()

    # Replace today's entry if we already ran today
    existing_dates = [s["date"] for s in history["snapshots"]]
    if snapshot["date"] in existing_dates:
        idx = existing_dates.index(snapshot["date"])
        history["snapshots"][idx] = snapshot
        print(f"\nUpdated today's snapshot ({snapshot['date']})")
    else:
        history["snapshots"].append(snapshot)
        print(f"\nAdded new snapshot ({snapshot['date']})")

    # Keep last 90 days
    history["snapshots"] = history["snapshots"][-90:]
    history["last_updated"] = snapshot["timestamp"]

    save_history(history)
    print(f"Saved to: {HISTORY_FILE}")

    js_file = os.path.join(os.path.dirname(__file__), "stats_data.js")
    with open(js_file, "w", encoding="utf-8") as f:
        f.write("window.STATS_DATA = ")
        json.dump(history, f, ensure_ascii=False)
        f.write(";")
    print(f"Saved to: {js_file}")
    print("\nDone! Open dashboard.html in your browser.")

if __name__ == "__main__":
    main()
