#!/usr/bin/env python3
"""Patch descriptions+hints of the 22 restored challenges on live CTFd."""
import sys

import requests

sys.path.insert(0, ".")
from challenges import CHALLENGES, numbered_titles  # noqa: E402
from ctf_setup import docs_line  # noqa: E402

TOKEN = "ctfd_dd6a2d6927c2ebcce1952831b47fd3942bb317f08aa00c951907c7c4228bdfe5"
s = requests.Session()
s.headers.update({"Authorization": f"Token {TOKEN}",
                  "Content-Type": "application/json"})

titles = numbered_titles()
by_name = {}
rows, page = [], 1
while True:
    j = s.get("http://127.0.0.1:8000/api/v1/challenges",
              params={"view": "admin", "page": page, "per_page": 100},
              timeout=15).json()
    rows += j["data"]
    if not (j.get("meta", {}).get("pagination", {}) or {}).get("next"):
        break
    page += 1
for c in rows:
    by_name[c["name"]] = c["id"]

NAMES = ["e1-kit", "e2-forest", "e3-json", "r3-nightlog", "r4-web", "r6-history", "h2-tarhunt", "h3-shift",
         "v3-ghost", "m-s6-1-packcron", "m-s6-2-restore", "m-s6-3-gzview",
         "oe-s6-1-tarkeys", "oe-s6-2-singlefile", "om-s6-1-tablemode",
         "oh-s6-1-singlemember", "m-s7-1-linepick", "m-s7-2-appendlogs",
         "m-s7-3-silence", "oe-s7-1-teekeep", "om-s7-1-usercount",
         "oh-s7-1-xargchain", "m-s8-1-firstcol", "m-s8-2-topword",
         "m-s8-3-countpos"]
for n in NAMES:
    ch = next(c for c in CHALLENGES if c["name"] == n)
    name = titles[n]
    cid = by_name.get(name)
    if cid is None:
        print(f"MISSING on CTFd: {n} ({name})")
        continue
    desc = ch["description"] + docs_line(ch)
    r = s.patch(f"http://127.0.0.1:8000/api/v1/challenges/{cid}",
                json={"description": desc}, timeout=15)
    assert r.status_code == 200, (n, r.status_code)
    hints = s.get("http://127.0.0.1:8000/api/v1/hints",
                  params={"challenge_id": cid}, timeout=15).json()["data"]
    if hints and ch.get("hint"):
        r = s.patch(f"http://127.0.0.1:8000/api/v1/hints/{hints[0]['id']}",
                    json={"content": ch["hint"]}, timeout=15)
        assert r.status_code == 200, (n, r.status_code)
    print(f"patched {name} (id {cid})")
print("done")
