#!/usr/bin/env python3
"""One-shot: give every draft challenge per-student flags in the manifest so
ctf_setup can register them (hidden). Reuses box_scatter.make_flag; existing
entries are never regenerated. Safe to re-run."""
import json
import sys

from challenges import CHALLENGES
from box_scatter import make_flag

with open("manifest.json", encoding="utf-8") as f:
    manifest = json.load(f)

students = [s["username"] for s in manifest["students"]]
added = 0
for ch in CHALLENGES:
    if not ch.get("draft"):
        continue
    d = manifest["flags"].setdefault(ch["name"], {})
    for u in students:
        if not d.get(u):
            d[u] = make_flag(u)
            added += 1

with open("manifest.json", "w", encoding="utf-8") as f:
    json.dump(manifest, f, ensure_ascii=False, indent=1)
print(f"draft flags added: {added} "
      f"(students={len(students)}, drafts="
      f"{sum(1 for c in CHALLENGES if c.get('draft'))})")
