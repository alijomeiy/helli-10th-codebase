#!/usr/bin/env python3
"""box_scatter.py — scatter the ROOT-LAB flag INTO each student's box.

  sudo python3 box_scatter.py --manifest manifest.json          # all students
  sudo python3 box_scatter_one.py <username> --manifest m.json  # one student

Per student: ensures box-<user> exists (studentctl-box create), wakes it,
pipes an in-box setup script (writes the r1..r7 artifacts), builds a tiny
`flagbox:1` image on the host (FROM busybox; prints the flag when run) and
`docker cp`s its `docker save` tar into the box as /root/flag.tar (r8).
The same per-student flag is recorded in manifest.json under every r-*
challenge so ctf_setup.py registers them as usual.

Note: all r-challenges of one student share ONE flag — the point is WHERE it
hides (8 different root superpowers), not 8 different strings.
"""
import argparse
import json
import os
import random
import re
import string
import subprocess
import sys
import tempfile

from challenges import CHALLENGES

CONFIG_PATH = "/etc/studentctl/config.json"
BOXCTL = "/usr/local/sbin/studentctl-box"

R_NAMES = [c["name"] for c in CHALLENGES if re.match(r"^r\d-", c["name"])]


def sh(cmd, stdin_data=None, timeout=300, check=True):
    # bytes in/out: text=True would translate \n to \r\n on some platforms
    # and corrupt the bash payload we pipe into the box
    stdin_bytes = stdin_data.encode() if isinstance(stdin_data, str) else stdin_data
    r = subprocess.run(cmd, input=stdin_bytes, timeout=timeout,
                       capture_output=True)
    out = r.stdout.decode(errors="replace")
    err = r.stderr.decode(errors="replace")
    if check and r.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd)} -> rc={r.returncode}\n"
                           f"{out[-300:]} {err[-300:]}")
    return r


def make_flag(username):
    tail = "".join(random.choices(string.hexdigits.lower()[:16], k=6))
    return f"FLAG{{{username}-{tail}}}"


def box_exists(u):
    return sh(["docker", "inspect", f"box-{u}"], check=False).returncode == 0


def load_students():
    try:
        with open(CONFIG_PATH) as f:
            cfg = json.load(f)
        out = [(n, d["uid"]) for n, d in cfg.get("users", {}).items()
               if d.get("enabled") and d.get("uid", 0) >= 2000]
        if out:
            return sorted(out)
    except (OSError, ValueError, KeyError):
        pass
    out = []
    with open("/etc/passwd") as f:
        for line in f:
            parts = line.rstrip("\n").split(":")
            if len(parts) < 6:
                continue
            name, _, uid, _, _, home = parts[:6]
            if int(uid) >= 2000 and home.startswith("/home/"):
                out.append((name, int(uid)))
    return sorted(out)


# ---------------- in-box setup script (r1..r7) --------------------------------

def box_payload(u, flag):
    """Bash script executed INSIDE the box as root. f-string: the only
    doubled braces are for the inner python one-liner in web.py."""
    rnd = random.Random(f"{u}-rootlab")

    log_lines = []
    for _ in range(300):
        hh, mm = rnd.randint(0, 23), rnd.randint(0, 59)
        log_lines.append(f"2026-08-2{rnd.randint(1, 8)} {hh:02d}:{mm:02d} "
                         f"service={rnd.choice(['sshd', 'cron', 'kernel', 'labd'])} "
                         f"status={rnd.choice(['ok', 'ok', 'ok', 'warn'])} "
                         f"msg=heartbeat {rnd.randint(1000, 9999)}")
    log_lines[rnd.randint(80, 280)] += f" treasure={flag}"

    flag_port = rnd.choice([9001, 9002, 9003, 9004])

    out = f"""set -e
# ---- r1: secret in root's home
cat > /root/.secret.txt <<'EOF'
Welcome home, root. This folder was always yours.
{flag}
EOF
chmod 600 /root/.secret.txt

# ---- r2: the lab user's hidden file
cat > /home/lab/flag.txt <<'EOF'
My neighbour root may read this... can you?
{flag}
EOF
chown lab:lab /home/lab/flag.txt
chmod 600 /home/lab/flag.txt

# ---- r3: the night log
cat > /var/log/lab.log <<'EOF'
{chr(10).join(log_lines)}
EOF
chmod 600 /var/log/lab.log

# ---- r4: sleepy web service
mkdir -p /opt/labweb
cat > /opt/labweb/flag <<'EOF'
{flag}
EOF
cat > /opt/labweb/web.py <<'EOF'
from http.server import BaseHTTPRequestHandler, HTTPServer
FLAG = open('/opt/labweb/flag').read().strip()
class H(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write('<h1>Lab Web Service</h1><p>The secret is: ' + FLAG + '</p>'.encode())
    def log_message(self, *a):
        pass
HTTPServer(('0.0.0.0', 8080), H).serve_forever()
EOF

# ---- r5: the every-minute job
mkdir -p /opt/lab
printf '%s\\n' '{flag}' > /opt/lab/prize.txt
chmod 644 /opt/lab/prize.txt
grep -q prize.txt /etc/crontab 2>/dev/null || \\
  echo '* * * * * root cat /opt/lab/prize.txt > /tmp/prize.txt' >> /etc/crontab

# ---- r6: history leftovers
cat > /home/lab/.bash_history <<'EOF'
ls -la /home
vim report.txt
export SECRET="{flag}"
grep -rn todo ~/projects
service cron status
exit
EOF
chown lab:lab /home/lab/.bash_history

# ---- r7: four closed doors
mkdir -p /opt/lab/servers
for p in 9001 9002 9003 9004; do
  mkdir -p /opt/lab/servers/$p
  echo "<h1>door $p</h1><p>nothing behind this door</p>" > /opt/lab/servers/$p/index.html
done
echo "<h1>door {flag_port}</h1><p>you found the right door!</p><p>{flag}</p>" > /opt/lab/servers/{flag_port}/index.html
cat > /opt/lab/servers/run.sh <<'EOF'
#!/bin/bash
for p in 9001 9002 9003 9004; do
  (cd /opt/lab/servers/$p && nohup python3 -m http.server $p >/dev/null 2>&1 &)
done
echo "4 doors are open. Which one hides the flag?"
EOF
chmod 755 /opt/lab/servers/run.sh
"""
    # source files may carry CRLF (Windows checkout) — bash inside the box
    # needs clean LF
    return out.replace("\r\n", "\n")


# ---------------- r8: the flagbox image (docker load challenge) ---------------

def make_flagbox_tar(u, flag, tmpdir):
    """Build flagbox:1 on the host (FROM busybox, prints the flag when run),
    docker-save it, return the tar path. Caller cp's it into the box."""
    ctx = os.path.join(tmpdir, f"flagctx-{u}")
    os.makedirs(ctx, exist_ok=True)
    with open(os.path.join(ctx, "Dockerfile"), "w") as f:
        f.write('FROM busybox:latest\n'
                'CMD ["echo", "The hidden machine says:", "%s"]\n' % flag)
    sh(["docker", "build", "-q", "-t", "flagbox:1", ctx])
    tar = os.path.join(tmpdir, f"flagbox-{u}.tar")
    sh(["docker", "save", "-o", tar, "flagbox:1"])
    return tar


def scatter_one(u, manifest, tmpdir):
    box = f"box-{u}"
    # flag reuse: if this student already has r-flags in the manifest (and
    # they are registered in CTFd), keep them so re-scattering never
    # invalidates registered flags
    flag = manifest["flags"].get("r1-roothome", {}).get(u)
    if not flag:
        flag = make_flag(u)

    if not box_exists(u):
        sh([BOXCTL, "create", u])
    sh([BOXCTL, "start", u])

    # r1..r7 artifacts
    sh(["docker", "exec", "-i", box, "bash", "-s"],
       stdin_data=box_payload(u, flag))

    # r8: the loadable machine
    tar = make_flagbox_tar(u, flag, tmpdir)
    sh(["docker", "cp", tar, f"{box}:/root/flag.tar"])
    os.remove(tar)

    sh([BOXCTL, "stop", u])

    for name in R_NAMES:
        manifest["flags"].setdefault(name, {})[u] = flag


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default="manifest.json")
    ap.add_argument("--one", help="scatter only this student (for reset hook)")
    args = ap.parse_args()

    if os.geteuid() != 0:
        raise SystemExit("run as root")

    if os.path.exists(args.manifest):
        with open(args.manifest) as f:
            manifest = json.load(f)
    else:
        manifest = {"students": [], "flags": {}}
    for name in R_NAMES:
        manifest["flags"].setdefault(name, {})

    students = load_students()
    if args.one:
        students = [s for s in students if s[0] == args.one]
        if not students:
            raise SystemExit(f"student not found: {args.one}")

    n_ok = 0
    with tempfile.TemporaryDirectory() as tmpdir:
        for username, uid in students:
            try:
                scatter_one(username, manifest, tmpdir)
                n_ok += 1
                print(f"  OK {username}")
            except Exception as e:
                print(f"  FAIL {username}: {str(e)[:200]}", file=sys.stderr)

    known = {s["username"] for s in manifest["students"]}
    for username, uid in students:
        if username not in known:
            manifest["students"].append({"username": username, "uid": uid})

    with open(args.manifest, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)
    print(f"box scatter done ({n_ok}/{len(students)}) -> {args.manifest}")


if __name__ == "__main__":
    main()
