#!/usr/bin/env python3
"""Hide the 26 challenges that have no host-model artifacts (with checks)."""
import sys

import requests

sys.path.insert(0, ".")
from challenges import CHALLENGES, numbered_titles  # noqa: E402

TOKEN = "ctfd_dd6a2d6927c2ebcce1952831b47fd3942bb317f08aa00c951907c7c4228bdfe5"
s = requests.Session()
s.headers.update({"Authorization": f"Token {TOKEN}",
                  "Content-Type": "application/json"})

titles = numbered_titles()
HIDE = ["r1-roothome", "r2-labuser", "r5-cron", "r7-ports", "r8-dind",
        "v2-layers", "e4-archive2", "e5-tailline", "e6-cutcol",
        "e7-psfind", "e9-ghostuser", "e10-shy", "e11-readyimage",
        "e12-oldlog", "e13-doublezip", "h4-catch", "h5-deleted",
        "h6-decoyports", "h7-legacy", "h8-env", "v4-twoworlds",
        "v5-deadcontainer", "v6-sentinel", "v7-vault", "v8-needle2"]

rows, page = [], 1
while True:
    j = s.get("http://127.0.0.1:8000/api/v1/challenges",
              params={"view": "admin", "page": page, "per_page": 100},
              timeout=15).json()
    rows += j["data"]
    if not (j.get("meta", {}).get("pagination", {}) or {}).get("next"):
        break
    page += 1
by_name = {c["name"]: c["id"] for c in rows}

for n in HIDE:
    name = titles[n]
    cid = by_name.get(name)
    if cid is None:
        print(f"skip (not on CTFd): {n}")
        continue
    subs = s.get("http://127.0.0.1:8000/api/v1/submissions",
                 params={"challenge_id": cid, "per_page": 5},
                 timeout=15).json()["data"]
    if subs:
        print(f"KEEP VISIBLE ({len(subs)} solves!): {name}")
        continue
    det = s.get(f"http://127.0.0.1:8000/api/v1/challenges/{cid}",
                timeout=15).json()["data"]
    if det.get("state") == "hidden":
        print(f"already hidden: {name}")
        continue
    r = s.patch(f"http://127.0.0.1:8000/api/v1/challenges/{cid}",
                json={"state": "hidden"}, timeout=15)
    assert r.status_code == 200, (n, r.status_code)
    print(f"hidden: {name}")
print("done")
