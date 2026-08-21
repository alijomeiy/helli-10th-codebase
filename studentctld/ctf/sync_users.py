#!/usr/bin/env python3
"""Create CTFd user accounts matching panel/Linux credentials.

Students log into CTFd with the SAME username + password as their Linux SSH
account (passwords are stored in the panel DB from provision time).

Usage (root, on the server):
  python3 sync_users.py --url http://127.0.0.1:8000 --token <admin token>

User list comes from the panel container's SQLite DB via `docker exec`.
Idempotent: existing users are skipped; password kept in sync.
"""
import argparse
import json
import subprocess

import requests

DUMP = (
    "import json,sqlite3;"
    "c=sqlite3.connect('/var/lib/studentctl/panel.db');"
    "rows=c.execute("
    "\"select username, ssh_password from users "
    "where role='student' and status='approved' and uid is not null "
    "and ssh_password != ''\").fetchall();"
    "print(json.dumps([{'username':u,'password':p} for u,p in rows]))"
)


def load_panel_students():
    out = subprocess.run(
        ["docker", "exec", "studentctl-panel", "python3", "-c", DUMP],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    return json.loads(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:8000")
    ap.add_argument("--token", required=True)
    ap.add_argument("--close-registration", action="store_true",
                    help="set registration to private after syncing")
    args = ap.parse_args()

    h = {"Authorization": f"Token {args.token}",
         "Content-Type": "application/json"}

    students = load_panel_students()
    print(f"panel students with credentials: {len(students)}")

    existing = {u["name"]: u for u in
                requests.get(f"{args.url}/api/v1/users", headers=h,
                             timeout=15).json()["data"]}
    created = skipped = 0
    for s in students:
        name, pw = s["username"], s["password"]
        if name in existing:
            skipped += 1
            continue
        r = requests.post(f"{args.url}/api/v1/users", headers=h, json={
            "name": name,
            "email": f"{name}@students.helli-10th-computer.ir",
            "password": pw,
            "type": "user",
            "verified": True,
            "hidden": False,
            "banned": False,
        }, timeout=15)
        if r.status_code == 200:
            created += 1
        else:
            print(f"  FAIL {name}: {r.status_code} {r.text[:80]}")
    print(f"created: {created}, already existed: {skipped}")

    if args.close_registration:
        r = requests.patch(f"{args.url}/api/v1/configs", headers=h,
                           json={"registration_visibility": "private"},
                           timeout=15)
        print("close registration:", r.status_code)


if __name__ == "__main__":
    main()
