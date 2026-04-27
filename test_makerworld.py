#!/usr/bin/env python3
"""
MakerWorld API endpoint probe.
Run with: python test_makerworld.py
Requires MW_AUTH_TOKEN env var (or paste token below).
"""
import json, os, sys, urllib.request, urllib.error

TOKEN = os.environ.get("MW_AUTH_TOKEN", "")
UID   = "162313973"

if not TOKEN:
    print("Set MW_AUTH_TOKEN env var, e.g.:")
    print('  $env:MW_AUTH_TOKEN = "eyJ..."')
    sys.exit(1)

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept":        "application/json",
    "User-Agent":    "Mozilla/5.0",
}

def try_get(url, label):
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            body = r.read().decode("utf-8")
            data = json.loads(body)
            print(f"  [OK {r.status}] {label}")
            print(f"    keys: {list(data.keys()) if isinstance(data, dict) else type(data).__name__}")
            if isinstance(data, dict):
                # show top-level numeric info
                for k, v in data.items():
                    if isinstance(v, (int, float)):
                        print(f"    {k}: {v}")
                    elif isinstance(v, list):
                        print(f"    {k}: list[{len(v)}]")
                    elif isinstance(v, dict):
                        print(f"    {k}: dict{{{', '.join(list(v.keys())[:4])}}}")
            return data
    except urllib.error.HTTPError as e:
        print(f"  [HTTP {e.code}] {label}")
        print(f"    {e.read().decode('utf-8', errors='replace')[:200]}")
        return None

def try_post(url, body_dict, label):
    payload = json.dumps(body_dict).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={**HEADERS, "Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            body = r.read().decode("utf-8")
            data = json.loads(body)
            print(f"  [OK {r.status}] {label}")
            print(f"    keys: {list(data.keys()) if isinstance(data, dict) else type(data).__name__}")
            if isinstance(data, dict):
                for k, v in data.items():
                    if isinstance(v, (int, float)):
                        print(f"    {k}: {v}")
                    elif isinstance(v, list):
                        print(f"    {k}: list[{len(v)}]")
                    elif isinstance(v, dict):
                        print(f"    {k}: dict{{{', '.join(list(v.keys())[:4])}}}")
                # Show first item of any list
                for k, v in data.items():
                    if isinstance(v, list) and len(v) > 0 and isinstance(v[0], dict):
                        print(f"    first {k}[0] keys: {list(v[0].keys())[:8]}")
                        break
            return data
    except urllib.error.HTTPError as e:
        print(f"  [HTTP {e.code}] {label}")
        print(f"    {e.read().decode('utf-8', errors='replace')[:200]}")
        return None

print("=== MakerWorld API probe ===\n")

print("--- GET endpoints (no auth) ---")
NO_AUTH = {"Accept": "application/json", "User-Agent": "Mozilla/5.0"}
def try_get_noauth(url, label):
    req = urllib.request.Request(url, headers=NO_AUTH)
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            body = r.read().decode("utf-8")
            data = json.loads(body)
            print(f"  [OK {r.status}] {label}")
            if isinstance(data, dict):
                for k, v in data.items():
                    if isinstance(v, list): print(f"    {k}: list[{len(v)}]")
                    elif isinstance(v, dict): print(f"    {k}: dict{{{', '.join(list(v.keys())[:4])}}}")
                    elif isinstance(v, (int, float)): print(f"    {k}: {v}")
            return data
    except urllib.error.HTTPError as e:
        print(f"  [HTTP {e.code}] {label}")
        return None

try_get_noauth(f"https://makerworld.com/api/v1/design-service/design/page?designerId={UID}&page=1&pageSize=5", "design/page GET (no auth)")
try_get_noauth(f"https://makerworld.com/api/v1/design-user-service/user/profile/{UID}", "profile GET (no auth)")

print("\n--- GET endpoints (with auth) ---")
try_get(f"https://makerworld.com/api/v1/design-user-service/user/profile/{UID}", "profile (current)")
try_get(f"https://makerworld.com/api/v1/design-service/design/list?designerId={UID}&page=1&pageSize=5", "design/list GET")
try_get(f"https://makerworld.com/api/v1/design-service/design/search?designerId={UID}&page=1&pageSize=5", "design/search GET")
try_get(f"https://makerworld.com/api/v1/design-user-service/user/{UID}/designs?page=1&pageSize=5", "user designs GET v1")
try_get(f"https://makerworld.com/api/v2/design?userId={UID}&page=1&pageSize=5", "design GET v2 userId")
try_get(f"https://makerworld.com/api/v1/design-service/designs?creatorUid={UID}&page=1&pageSize=5", "designs GET creatorUid")
try_get(f"https://makerworld.com/api/v1/design-service/designs?userId={UID}&page=1&pageSize=5", "designs GET userId")

print("\n--- POST endpoints ---")
try_post("https://makerworld.com/api/v1/design-service/design/page",
         {"designerId": int(UID), "page": 1, "pageSize": 5, "keyword": ""},
         "design/page POST int designerId")
try_post("https://makerworld.com/api/v1/design-service/design/page",
         {"designerId": UID, "page": 1, "pageSize": 5, "keyword": ""},
         "design/page POST str designerId")
try_post("https://makerworld.com/api/v1/design-service/design/page",
         {"uid": int(UID), "page": 1, "pageSize": 5},
         "design/page POST uid")
try_post("https://makerworld.com/api/v1/design-service/design/page",
         {"creatorId": int(UID), "page": 1, "pageSize": 5},
         "design/page POST creatorId")
try_post("https://makerworld.com/api/v1/design-service/design/list",
         {"designerId": int(UID), "page": 1, "pageSize": 5},
         "design/list POST")

print("\nDone.")
