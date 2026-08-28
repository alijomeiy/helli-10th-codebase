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
import base64
import codecs
import json
import os
import random
import re
import string
import subprocess
import sys
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor

from challenges import CHALLENGES

CONFIG_PATH = "/etc/studentctl/config.json"
BOXCTL = "/usr/local/sbin/studentctl-box"
WORKERS = 4          # parallel boxes during scatter/reset

R_NAMES = [c["name"] for c in CHALLENGES
           if re.match(r"^[rehv]\d-", c["name"])]


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

def box_payload(u, flags):
    """Bash script executed INSIDE the box as root.

    flags: dict challenge-name -> flag. r-series share one flag; e/h/v have
    their own; h1/v1 write only their SECOND half here (host halves are
    scattered by ctf_scatter.py). f-string: doubled braces are for the few
    inner-python literals."""
    rnd = random.Random(f"{u}-rootlab")

    r_flag = flags["r1-roothome"]
    log_lines = []
    for _ in range(300):
        hh, mm = rnd.randint(0, 23), rnd.randint(0, 59)
        log_lines.append(f"2026-08-2{rnd.randint(1, 8)} {hh:02d}:{mm:02d} "
                         f"service={rnd.choice(['sshd', 'cron', 'kernel', 'labd'])} "
                         f"status={rnd.choice(['ok', 'ok', 'ok', 'warn'])} "
                         f"msg=heartbeat {rnd.randint(1000, 9999)}")
    log_lines[rnd.randint(80, 280)] += f" treasure={r_flag}"
    # h1: the 03:00 line carries the second half of the detective's flag
    h1_part2 = flags["h1-lead"][len(flags["h1-lead"]) // 2:]

    # r7 / v3: which ports carry the goods
    flag_port = rnd.choice([9001, 9002, 9003, 9004])
    ghost_port = rnd.choice([7731, 7732, 7733, 7734, 7735])

    # e3: json-wrapped base64
    b64 = base64.b64encode(flags["e3-json"].encode()).decode()

    # h2: tarball with decoys + one real hidden treasure (dot-named files)
    h2_flag = flags["h2-tarhunt"]
    h2_lines = "\n".join(
        f"printf '%s' 'treasure note {i}: nothing here, keep looking.' "
        f"> /opt/lab/h2src/treasures/.treasure-{rnd.randint(1000, 9999)}.txt"
        for i in range(1, 4))

    # h3: ROT13 of the flag
    h3_rot13 = codecs.encode(flags["h3-shift"], "rot13")

    # v1: second half served by the dormant web app
    v1_part2 = flags["v1-oldsite"][len(flags["v1-oldsite"]) // 2:]

    return f"""set -e
# ---- r1: secret in root's home
cat > /root/.secret.txt <<'EOF'
Welcome home, root. This folder was always yours.
{r_flag}
EOF
chmod 600 /root/.secret.txt

# ---- r2: the lab user's hidden file
cat > /home/lab/flag.txt <<'EOF'
My neighbour root may read this... can you?
{r_flag}
EOF
chown lab:lab /home/lab/flag.txt
chmod 600 /home/lab/flag.txt

# ---- r3 + h1: the night log
cat > /var/log/lab.log <<'EOF'
{chr(10).join(log_lines)}
2026-08-29 03:00:00 service=labd status=ok msg=nightshift note={h1_part2}
EOF
chmod 600 /var/log/lab.log

# ---- r4: sleepy web service
mkdir -p /opt/labweb
cat > /opt/labweb/flag <<'EOF'
{r_flag}
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
printf '%s\\n' '{r_flag}' > /opt/lab/prize.txt
chmod 644 /opt/lab/prize.txt
grep -q prize.txt /etc/crontab 2>/dev/null || \\
  echo '* * * * * root cat /opt/lab/prize.txt > /tmp/prize.txt' >> /etc/crontab

# ---- r6: history leftovers
cat > /home/lab/.bash_history <<'EOF'
ls -la /home
vim report.txt
export SECRET="{r_flag}"
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
echo "<h1>door {flag_port}</h1><p>you found the right door!</p><p>{r_flag}</p>" > /opt/lab/servers/{flag_port}/index.html
cat > /opt/lab/servers/run.sh <<'EOF'
#!/bin/bash
for p in 9001 9002 9003 9004; do
  (cd /opt/lab/servers/$p && nohup python3 -m http.server $p >/dev/null 2>&1 &)
done
echo "4 doors are open. Which one hides the flag?"
EOF
chmod 755 /opt/lab/servers/run.sh

# ---- e1: the mystery local package
mkdir -p /opt/lab/pkgs/flagpkg/DEBIAN /opt/lab/pkgs/flagpkg/usr/share/flagpkg
cat > /opt/lab/pkgs/flagpkg/DEBIAN/control <<'EOF'
Package: flagpkg
Version: 1.0
Architecture: all
Maintainer: lab <lab@localhost>
Description: a small surprise package for the lab student
 A flag sleeps inside. Install and inspect.
EOF
printf '%s\\n' '{flags["e1-kit"]}' > /opt/lab/pkgs/flagpkg/usr/share/flagpkg/flag.txt
dpkg-deb --build /opt/lab/pkgs/flagpkg /opt/lab/kit.deb >/dev/null
rm -rf /opt/lab/pkgs
chmod 644 /opt/lab/kit.deb

# ---- e2: forest of directories (install `tree` to see it at a glance)
mkdir -p /opt/lab/e2
prev="/opt/lab/e2"
for i in 1 2 3 4; do
  cur=""
  for j in 1 2 3 4 5; do
    d="$prev/d$RANDOM$RANDOM"
    mkdir -p "$d"
    echo "nothing here" > "$d/placeholder.txt"
    cur="$d"
  done
  prev="$cur"
done
printf '%s\\n' '{flags["e2-forest"]}' > "$prev/deepest-leaf.txt"

# ---- e3: json secret (install jq)
printf '{{"user": "lab", "note": "the secret is encoded", "secret": "%s"}}\\n' '{b64}' > /opt/lab/data.json
chmod 644 /opt/lab/data.json

# ---- h2: archive with buried treasure (dot-named, among decoys)
mkdir -p /opt/lab/h2src/treasures
{h2_lines}
printf '%s\\n' '{h2_flag}' > /opt/lab/h2src/treasures/.treasure-real-$RANDOM.txt
tar -C /opt/lab/h2src -czf /opt/lab/backup.tar.gz treasures
rm -rf /opt/lab/h2src

# ---- h3: the nightshift job (ROT13)
cat > /opt/lab/input.txt <<'EOF'
{h3_rot13}
EOF
cat > /opt/lab/job.sh <<'EOF'
#!/bin/bash
tr 'A-Za-z' 'N-ZA-Mn-za-m' < /opt/lab/input.txt > /tmp/out.txt
EOF
chmod 755 /opt/lab/job.sh
grep -q job.sh /etc/crontab 2>/dev/null || \\
  echo '* * * * * root /opt/lab/job.sh' >> /etc/crontab

# ---- v1: the old site (second half)
mkdir -p /opt/lab/old-web
cat > /opt/lab/old-web/flag <<'EOF'
{v1_part2}
EOF
cat > /opt/lab/old-web/web.py <<'EOF'
from http.server import BaseHTTPRequestHandler, HTTPServer
PART = open('/opt/lab/old-web/flag').read().strip()
class H(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write('<html><body><h1>old site</h1><!-- archive: ' + PART + ' --></body></html>'.encode())
    def log_message(self, *a):
        pass
HTTPServer(('0.0.0.0', 9999), H).serve_forever()
EOF
cat > /opt/lab/README.txt <<'EOF'
Our old website was split in two halves.
One half sleeps in the host's home archive (level5/old-site.tar.gz),
the other one is served by the dormant app in /opt/lab/old-web (port 9999).
EOF

# ---- v3: the ghost servant (hidden dir, random port, clue in history)
mkdir -p /opt/lab/.ghost
cat > /opt/lab/.ghost/flag <<'EOF'
{flags["v3-ghost"]}
EOF
cat > /opt/lab/.ghost/ghost.py <<EOF
from http.server import BaseHTTPRequestHandler, HTTPServer
FLAG = open('/opt/lab/.ghost/flag').read().strip()
class H(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write('<h1>you found the ghost</h1><p>' + FLAG + '</p>'.encode())
    def log_message(self, *a):
        pass
HTTPServer(('127.0.0.1', {ghost_port}), H).serve_forever()
EOF
chmod 700 /opt/lab/.ghost
chmod 700 /opt/lab/.ghost/ghost.py
cat >> /home/lab/.bash_history <<'EOF'
curl localhost:{ghost_port}
EOF
"""
    # source files may carry CRLF (Windows checkout) — bash inside the box
    # needs clean LF
    return out.replace("\r\n", "\n")


# ---------------- r8 + v2: images for the docker challenges ------------------
# The busybox FROM layer is cached after the first build, so per-student
# builds are config-only and fast. Builds use fixed tags -> serialize them
# with BUILD_LOCK when running parallel workers.

BUILD_LOCK = threading.Lock()


def make_flagbox_tar(u, flag, tmpdir):
    """Build flagbox:1 on the host (FROM busybox, prints the flag when run),
    docker-save it, return the tar path. Caller cp's it into the box."""
    ctx = os.path.join(tmpdir, f"flagctx-{u}")
    os.makedirs(ctx, exist_ok=True)
    with open(os.path.join(ctx, "Dockerfile"), "w") as f:
        f.write('FROM busybox:latest\n'
                'CMD ["echo", "The hidden machine says:", "%s"]\n' % flag)
    with BUILD_LOCK:
        sh(["docker", "build", "-q", "-t", "flagbox:1", ctx])
        tar = os.path.join(tmpdir, f"flagbox-{u}.tar")
        sh(["docker", "save", "-o", tar, "flagbox:1"])
    return tar


def make_buried_tar(u, flag, tmpdir):
    """v2: an image where /flag.txt was ADDED then DELETED in the next
    layer. Running it shows nothing; the flag survives in the older layer
    (docker save + untar forensics)."""
    mid_ctx = os.path.join(tmpdir, f"mid-{u}")
    os.makedirs(mid_ctx, exist_ok=True)
    with open(os.path.join(mid_ctx, "f.txt"), "w") as f:
        f.write(flag + "\n")
    with open(os.path.join(mid_ctx, "Dockerfile"), "w") as f:
        f.write('FROM busybox:latest\nCOPY f.txt /flag.txt\n')
    deep_ctx = os.path.join(tmpdir, f"deep-{u}")
    os.makedirs(deep_ctx, exist_ok=True)
    with open(os.path.join(deep_ctx, "Dockerfile"), "w") as f:
        f.write('FROM flagbox:mid\nRUN rm /flag.txt\n'
                'CMD ["echo", "nothing to see here"]\n')
    with BUILD_LOCK:
        sh(["docker", "build", "-q", "-t", "flagbox:mid", mid_ctx])
        sh(["docker", "build", "-q", "-t", "flagbox:2", deep_ctx])
        tar = os.path.join(tmpdir, f"buried-{u}.tar")
        sh(["docker", "save", "-o", tar, "flagbox:2"])
    return tar


def scatter_one(u, manifest, tmpdir, lock, results):
    box = f"box-{u}"

    # per-challenge flags; reuse manifest values when present so re-scatter
    # never invalidates flags already registered in CTFd
    flags = {}
    with lock:
        for name in R_NAMES:
            got = manifest["flags"].get(name, {}).get(u)
            if not got:
                got = make_flag(u)
                manifest["flags"].setdefault(name, {})[u] = got
            flags[name] = got
    # r-series share ONE flag per student
    for name in R_NAMES:
        if name.startswith("r"):
            flags[name] = flags["r1-roothome"]

    if not box_exists(u):
        sh([BOXCTL, "create", u])
    sh([BOXCTL, "start", u])

    # all in-box artifacts (r1..r8 prep, e1..e3, h2, h3, v1 part2, v3)
    sh(["docker", "exec", "-i", box, "bash", "-s"],
       stdin_data=box_payload(u, flags))

    # r8: the loadable machine
    tar = make_flagbox_tar(u, flags["r8-dind"], tmpdir)
    sh(["docker", "cp", tar, f"{box}:/root/flag.tar"])
    os.remove(tar)

    # v2: the buried-flag image
    tar = make_buried_tar(u, flags["v2-layers"], tmpdir)
    sh(["docker", "cp", tar, f"{box}:/root/buried.tar"])
    os.remove(tar)

    sh([BOXCTL, "stop", u])
    results[u] = True


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

    lock = threading.Lock()
    results = {}
    n_ok = 0
    with tempfile.TemporaryDirectory() as tmpdir:
        with ThreadPoolExecutor(max_workers=WORKERS) as ex:
            futures = {ex.submit(scatter_one, username, manifest, tmpdir,
                                 lock, results): username
                       for username, uid in students}
            for fu, username in futures.items():
                try:
                    fu.result()
                except Exception as e:
                    print(f"  FAIL {username}: {str(e)[:200]}", file=sys.stderr)
        n_ok = len(results)

    known = {s["username"] for s in manifest["students"]}
    for username, uid in students:
        if username not in known:
            manifest["students"].append({"username": username, "uid": uid})

    with open(args.manifest, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)
    print(f"box scatter done ({n_ok}/{len(students)}) -> {args.manifest}")


if __name__ == "__main__":
    main()
