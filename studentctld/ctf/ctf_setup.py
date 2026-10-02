#!/usr/bin/env python3
"""Create CTFd challenges + register per-student flags + hints via the API.

Usage: python3 ctf_setup.py --url http://127.0.0.1:8000 --token <admin token> \
                            [--manifest manifest.json]
Idempotent: skips anything that already exists.
"""
import argparse
import json

import requests

from challenges import CHALLENGES, numbered_titles, docs_line, DOCS_MARKER


class CTFd:
    def __init__(self, base, token):
        self.base = base.rstrip("/") + "/api/v1"
        self.url = base.rstrip("/")
        self.s = requests.Session()
        self.s.headers.update({
            "Authorization": f"Token {token}",
            "Content-Type": "application/json",
        })

    def get(self, path, **params):
        r = self.s.get(f"{self.base}{path}", params=params, timeout=15)
        r.raise_for_status()
        return r.json()["data"]

    def post(self, path, payload):
        r = self.s.post(f"{self.base}{path}", json=payload, timeout=15)
        r.raise_for_status()
        return r.json()["data"]

    def patch(self, path, payload):
        r = self.s.patch(f"{self.base}{path}", json=payload, timeout=15)
        r.raise_for_status()
        return r.json().get("data", {})


def get_or_create_challenge(api, ch, display_name):
    # view=admin so hidden (draft) challenges are seen too — otherwise
    # re-runs would create duplicates of every draft. per_page explicit:
    # never rely on CTFd's default page size.
    for existing in api.get("/challenges", view="admin", per_page=200):
        if existing["name"] == display_name:
            return existing["id"], False
    data = api.post("/challenges", {
        "name": display_name,
        "category": ch["category"],
        "description": ch["description"] + docs_line(ch),
        "value": ch["points"],
        "type": "standard",
        "state": "hidden" if ch.get("draft") else "visible",
    })
    return data["id"], True


def ensure_docs_line(api, cid, ch):
    """Make the description footer exactly match docs_line(ch): strips any
    previous/over-broad footer, then adds the approved-only one. Description
    PATCH never touches flags or solves."""
    orig = api.get(f"/challenges/{cid}").get("description") or ""
    desc = orig
    if DOCS_MARKER in desc:
        desc = desc.split("\n---\n" + DOCS_MARKER)[0]
    new_desc = desc + docs_line(ch)
    if new_desc == orig:
        return False
    api.patch(f"/challenges/{cid}", {"description": new_desc})
    return True


def register_flags(api, challenge_id, flags):
    existing = {f["content"] for f in
                api.get("/flags", challenge_id=challenge_id, per_page=500)}
    added = 0
    for flag in flags:
        if flag in existing:
            continue
        api.post("/flags", {
            "challenge_id": challenge_id,
            "content": flag,
            "type": "static",
            "data": "",
        })
        added += 1
    return added


def add_hint(api, challenge_id, content, cost):
    hints = api.get("/hints", challenge_id=challenge_id)
    if hints:
        # the challenge already has hints (API returns different shapes per
        # version) — never duplicate; live-edit hints from the panel instead
        return False
    api.post("/hints", {
        "challenge_id": challenge_id,
        "content": content,
        "cost": cost,
        "requirements": {},
    })
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:8000")
    ap.add_argument("--token", required=True)
    ap.add_argument("--manifest", default="manifest.json")
    ap.add_argument("--fresh", action="store_true",
                    help="delete ALL existing challenges first (full re-deploy)")
    args = ap.parse_args()

    with open(args.manifest, encoding="utf-8") as f:
        manifest = json.load(f)

    api = CTFd(args.url, args.token)
    titles = numbered_titles()

    if args.fresh:
        n = 0
        for ch in api.get("/challenges", view="admin", per_page=200):
            requests.delete(f"{api.url}/api/v1/challenges/{ch['id']}",
                            headers=api.s.headers, timeout=15)
            n += 1
        print(f"  fresh: deleted {n} old challenges")

    for ch in CHALLENGES:
        cid, created = get_or_create_challenge(api, ch, titles[ch["name"]])
        flags = list(manifest["flags"].get(ch["name"], {}).values())
        added = register_flags(api, cid, flags)
        hinted = add_hint(api, cid, ch["hint"], ch["hint_cost"])
        doced = ensure_docs_line(api, cid, ch)
        state = "created" if created else "exists"
        tag = " (draft)" if ch.get("draft") else ""
        print(f"  {ch['name']:16s} {state:8s} +{added} flags"
              + ("  +hint" if hinted else "")
              + ("  +docs" if doced and not created else "") + tag)

    print("done.")


if __name__ == "__main__":
    main()
