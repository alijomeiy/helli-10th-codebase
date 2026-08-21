#!/usr/bin/env python3
"""Create CTFd challenges + register per-student flags + hints via the API.

Usage: python3 ctf_setup.py --url http://127.0.0.1:8000 --token <admin token> \
                            [--manifest manifest.json]
Idempotent: skips anything that already exists.
"""
import argparse
import json

import requests

from challenges import CHALLENGES


class CTFd:
    def __init__(self, base, token):
        self.base = base.rstrip("/") + "/api/v1"
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


def get_or_create_challenge(api, ch):
    for existing in api.get("/challenges"):
        if existing["name"] == ch["name"]:
            return existing["id"], False
    data = api.post("/challenges", {
        "name": ch["name"],
        "category": ch["category"],
        "description": ch["description"],
        "value": ch["points"],
        "type": "standard",
        "state": "visible",
        "attribution": ch["title"],
    })
    return data["id"], True


def register_flags(api, challenge_id, flags):
    existing = {f["content"] for f in api.get("/flags", challenge_id=challenge_id)}
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
    for h in api.get("/hints", challenge_id=challenge_id):
        if h["content"] == content:
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
    args = ap.parse_args()

    with open(args.manifest, encoding="utf-8") as f:
        manifest = json.load(f)

    api = CTFd(args.url, args.token)
    for ch in CHALLENGES:
        cid, created = get_or_create_challenge(api, ch)
        flags = list(manifest["flags"].get(ch["name"], {}).values())
        added = register_flags(api, cid, flags)
        hinted = add_hint(api, cid, ch["hint"], ch["hint_cost"])
        state = "created" if created else "exists"
        print(f"  {ch['name']:14s} {state:8s} +{added} flags"
              + ("  +hint" if hinted else ""))

    print("done.")


if __name__ == "__main__":
    main()
