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
           if re.match(r"^([rehv]\d-|(m|oe|om|oh)-s\d+-\d+-)", c["name"])]


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

    # ---- session exercises (s6 archives / s7 pipes / s8 texttools).
    # Every rnd use below is deliberately AFTER all legacy draws above so
    # re-scatter regenerates the legacy artifacts byte-identically. ----

    def ts():
        return f"{rnd.randint(0, 23):02d}:{rnd.randint(0, 59):02d}:" \
               f"{rnd.randint(0, 59):02d}"

    mods = ["authx", "billing", "cache", "queue", "mailer", "storage"]

    # m-s6-1: odd member name inside the cron archive
    rnd61 = rnd.randint(100, 999)
    # om-s6-1: the single sized member among 200 empty ones
    m66real = rnd.randint(1, 200)
    # oh-s6-1: 300 same-size vault members; FAKEFLAG decoys + dot padding,
    # exactly one carries the real flag pattern
    real67 = flags["oh-s6-1-singlemember"]
    real67 += "." * (40 - len(real67))
    m67 = []
    for i in range(1, 301):
        fake = f"FAKEFLAG{{decoy-{i:03d}}}"
        m67.append(fake + "." * (40 - len(fake)))
    m67[rnd.randint(0, 299)] = real67
    m67_block = "\n".join(
        f"printf '%s\\n' '{content}' > /opt/lab/m67src/vault/.treasure-{i:03d}.txt"
        for i, content in enumerate(m67, 1))

    # m-s6-3: notes viewed through gzip
    m63 = [f"note {i:02d}: routine maintenance, nothing unusual."
           for i in range(1, 26)]
    m63[rnd.randint(5, 20)] = f"night backup passphrase: {flags['m-s6-3-gzview']}"
    m63_text = chr(10).join(m63) + "\n"

    # oe-s6-2: twin notes — plain decoy, gz real
    m65 = [f"shopping list item {i}: nothing interesting." for i in range(1, 13)]
    m65[rnd.randint(3, 9)] = flags["oe-s6-2-singlefile"]
    m65_text = chr(10).join(m65) + "\n"

    # m-s7-1: exactly m71_k lines carry ERROR; the flag sits on line m71_k
    m71_k = rnd.randint(150, 700)
    words = ["alpha", "bravo", "cargo", "delta", "echo", "fox", "gold",
             "hotel", "iris", "juno", "kiwi", "lime", "mango", "nile",
             "opal", "pico", "quartz", "ray", "solar", "tango", "umbra",
             "vela", "wren", "xenon", "yonder", "zinc"]
    m71 = [f"line {i}: " + " ".join(rnd.choice(words) for _ in range(6))
           for i in range(1, 2001)]
    for i in rnd.sample([j for j in range(1, 2001) if j != m71_k], m71_k):
        m71[i - 1] += " ERROR"
    m71[m71_k - 1] = f"line {m71_k}: ALERT note={flags['m-s7-1-linepick']}"
    m71_text = chr(10).join(m71) + "\n"

    # m-s7-2: journal — first half in the top 5 lines, second in the last 10
    m72 = flags["m-s7-2-appendlogs"]
    m72_p1, m72_p2 = m72[: len(m72) // 2], m72[len(m72) // 2:]
    jtop = [f"journal entry {i}: morning pages, nothing special."
            for i in range(1, 6)]
    jtop[1] = f"journal entry 2: PART1={m72_p1}"
    jmid = [f"journal entry {i}: midday pages, nothing here."
            for i in range(6, 31)]
    jbot = [f"journal entry {i}: evening pages, still nothing."
            for i in range(31, 41)]
    jbot[6] = f"PART2={m72_p2}"
    m72_text = chr(10).join(jtop + jmid + jbot) + "\n"

    # om-s7-1: EXACTLY 17 bash+/home users; flag waits on gate.txt line 17
    m73 = [f"stu{i}:x:{2000 + i}:{2000 + i}::/home/stu{i}:/bin/bash"
           for i in range(1, 18)]
    m73 += ["root:x:0:0::/root:/bin/bash",
            "svc:x:100:100::/srv/svc:/bin/bash",
            "build:x:105:105::/var/build:/bin/bash"]
    m73 += [f"old{i}:x:{1500 + i}:{1500 + i}::/home/old{i}:/usr/sbin/nologin"
            for i in range(1, 21)]
    while len(m73) < 500:
        i = len(m73)
        m73.append(f"sys{i}:x:{100 + i}:{100 + i}::/var/empty{rnd.randint(1, 9)}:"
                   f"{rnd.choice(['/usr/sbin/nologin', '/bin/false'])}")
    m73_text = chr(10).join(m73) + "\n"
    gate = [f"gate line {i}: sealed" for i in range(1, 401)]
    gate[16] = flags["om-s7-1-usercount"]
    m73_gate = chr(10).join(gate) + "\n"

    # oh-s7-1: 7 clue files (two names carry spaces), SEG pieces in order
    m76 = flags["oh-s7-1-xargchain"]
    seg = -(-len(m76) // 7)
    m76_parts = [m76[k * seg:(k + 1) * seg] for k in range(7)]
    clue_names = [f"report-{n}.txt" for n in rnd.sample(range(1000, 10000), 5)]
    clue_names += [f"old report {rnd.randint(100, 999)}.txt",
                   f"final note {rnd.randint(100, 999)}.txt"]
    rnd.shuffle(clue_names)
    m76_clues = chr(10).join(clue_names) + "\n"
    m76_files = "\n".join(
        f'cat > "/opt/lab/haystack/{name}" << "EOF"\n'
        f"SEG{k + 1}={m76_parts[k]}\nEOF"
        for k, name in enumerate(clue_names))

    # m-s8-1: attendees.csv — exactly one winner row
    m81 = ["name,city,uid,note"]
    for i in range(1, 300):
        m81.append(f"guest{i},{rnd.choice(['tehran', 'esfahan', 'shiraz', 'tabriz'])},"
                   f"{3000 + i},-")
    m81.append(f"winner,tehran,{3300},{flags['m-s8-1-firstcol']}")
    rnd.shuffle(m81[1:])
    m81_text = chr(10).join(m81) + "\n"

    # m-s8-2: chat.log — pineapple-42 is the top word (40x), cactus-17 decoy
    toks = (["pineapple-42"] * 40 + ["cactus-17"] * 25
            + [f"tok-{rnd.randint(1, 400)}" for _ in range(2335)])
    rnd.shuffle(toks)
    m82_text = chr(10).join(
        " ".join(toks[i:i + 8]) for i in range(0, len(toks), 8)) + "\n"

    # om-s8-1: app.log — billing FAILs most (25), cache runner-up (18)
    m88 = [f"{ts()} status=FAIL module=billing msg=timeout" for _ in range(25)]
    m88 += [f"{ts()} status=FAIL module=cache msg=evicted" for _ in range(18)]
    m88 += [f"{ts()} status=FAIL module={mo} msg=retry"
            for mo in ("queue", "authx", "mailer", "storage")
            for _ in range(rnd.randint(2, 7))]
    m88 += [f"{ts()} status=OK module={rnd.choice(mods)} msg=ok"
            for _ in range(430)]
    rnd.shuffle(m88)
    m88_text = chr(10).join(m88) + "\n"

    # oh-s8-1: 30 case files; cronmond FAILs in exactly 18 (top); the
    # culprit's suspect file stores the flag with case flipped (tr to read)
    assign = ["cronmond"] * 18 + ["webhookd"] * 12
    rnd.shuffle(assign)
    case_blocks = []
    for c in range(1, 31):
        lines = [f"{ts()} status=OK module={rnd.choice(mods)} msg=ok"
                 for _ in range(rnd.randint(8, 14))]
        lines.append(f"{ts()} status=FAIL module={assign[c - 1]} msg=crash")
        rnd.shuffle(lines)
        body = chr(10).join(lines) + "\n"
        case_blocks.append(
            f"mkdir -p /opt/lab/cases/case-{c:02d}\n"
            f"cat > /opt/lab/cases/case-{c:02d}/notes.txt << 'EOF'\n"
            f"{body}EOF")
    m89_cases = "\n".join(case_blocks) + "\n"
    m89_suspects = "\n".join(
        f"cat > /opt/lab/suspects/{name} << 'EOF'\n{content}\nEOF"
        for name, content in [
            ("cronmond", flags["oh-s8-1-chainforensic"].swapcase()),
            ("webhookd", "FAKEFLAG{not-the-culprit}".swapcase()),
            ("cache", "FAKEFLAG{keep-looking}".swapcase()),
            ("authx", "FAKEFLAG{nope}".swapcase()),
        ])


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

# ---- session 6: archives exercises ------------------------------------------

# m-s6-1: cron-pack archive with one oddly-named member (list before extract)
mkdir -p /opt/lab/m61src
for i in 01 02 03 04 05 06 07 08 09 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24; do
  printf 'cron note %s: nothing special here\n' "$i" > /opt/lab/m61src/job-$i.conf
done
printf '%s\n' '{flags["m-s6-1-packcron"]}' > /opt/lab/m61src/special-{rnd61}.conf
tar -C /opt/lab/m61src -czf /opt/lab/cron-pack.tar.gz $(ls /opt/lab/m61src)
rm -rf /opt/lab/m61src

# m-s6-2: site backup tree (extract with -C into a fresh dir)
mkdir -p /opt/lab/m62src/var/www/html/assets
printf '<h1>old site</h1>\n' > /opt/lab/m62src/var/www/html/index.html
printf 'body {{ color: #333; }}\n' > /opt/lab/m62src/var/www/html/assets/style.css
printf '%s\n' '{flags["m-s6-2-restore"]}' > /opt/lab/m62src/var/www/html/.restored.flag
tar -C /opt/lab/m62src -czf /opt/lab/site-backup.tar.gz var
rm -rf /opt/lab/m62src

# m-s6-3: read-only backups dir with a gzipped note (zcat lesson)
mkdir -p /opt/lab/ro-backups
gzip -c > /opt/lab/ro-backups/notes.gz << 'EOF'
{m63_text}EOF
chmod 644 /opt/lab/ro-backups/notes.gz
chmod 555 /opt/lab/ro-backups

# oe-s6-1: a plain tar wearing a .tar.gz name (file(1) tells the truth)
mkdir -p /opt/lab/m64src/notes
printf 'plain note: the extension lies sometimes.\n' > /opt/lab/m64src/notes/list.txt
printf '%s\n' '{flags["oe-s6-1-tarkeys"]}' > /opt/lab/m64src/notes/true-flag.txt
tar -C /opt/lab/m64src -cf /opt/lab/mystery.tar.gz notes
rm -rf /opt/lab/m64src

# oe-s6-2: twin notes — plain decoy, gzipped real
printf '%s\n' 'FAKEFLAG{{the-plain-one-lies}}' > /opt/lab/notes.txt
gzip -c > /opt/lab/notes.txt.gz << 'EOF'
{m65_text}EOF

# om-s6-1: 200 empty members, exactly one sized (tar tvzf)
mkdir -p /opt/lab/m66src/items
for i in $(seq 1 200); do
  : > /opt/lab/m66src/items/item-$i.dat
done
printf 'THIS ONE IS REAL. %s\n' '{flags["om-s6-1-tablemode"]}' > /opt/lab/m66src/items/item-{m66real}.dat
tar -C /opt/lab/m66src -czf /opt/lab/table.tar.gz items
rm -rf /opt/lab/m66src

# oh-s6-1: 300 same-size vault members, one real flag pattern
mkdir -p /opt/lab/m67src/vault
{m67_block}
tar -C /opt/lab/m67src -czf /opt/lab/vault.tar.gz vault
rm -rf /opt/lab/m67src

# ---- session 7: pipes exercises ---------------------------------------------

# m-s7-1: rows.txt (ERROR count == flag line number)
cat > /opt/lab/rows.txt << 'EOF'
{m71_text}EOF

# m-s7-2: journal with split halves (head -5 / tail -10, > then >>)
cat > /opt/lab/journal.txt << 'EOF'
{m72_text}EOF

# m-s7-3: noisy script; the whisper goes to stderr
cat > /opt/lab/noisy.sh << 'SH'
#!/bin/bash
for i in $(seq 1 60); do
  echo "packet $i: nothing to see here, keep moving..."
done
SH
echo 'echo "whisper: tonight it is {flags["m-s7-3-silence"]}" >&2' >> /opt/lab/noisy.sh
chmod 755 /opt/lab/noisy.sh

# oe-s7-1: sensor script (tee it, then grep the saved copy)
cat > /opt/lab/sensor.sh << 'SH'
#!/bin/bash
hit=$((RANDOM % 180 + 10))
for i in $(seq 1 200); do
  if [ "$i" -eq "$hit" ]; then
    echo "reading $i: FLAG_PLACEHOLDER"
  else
    echo "reading $i: temp=$((RANDOM % 30 + 20))C pressure=$((RANDOM % 40 + 900))"
  fi
done
SH
sed -i "s|FLAG_PLACEHOLDER|{flags["oe-s7-1-teekeep"]}|" /opt/lab/sensor.sh
chmod 755 /opt/lab/sensor.sh

# om-s7-1: passwd-like (exactly 17 bash+/home users) + gate.txt line 17
cat > /opt/lab/passwd-like << 'EOF'
{m73_text}EOF
cat > /opt/lab/gate.txt << 'EOF'
{m73_gate}EOF

# oh-s7-1: haystack dust + 7 clue files (two names carry spaces)
mkdir -p /opt/lab/haystack
for i in $(seq 1 500); do
  printf 'dust %s: nothing here\n' "$i" > /opt/lab/haystack/grain-$i.txt
done
{m76_files}
cat > /opt/lab/clues.txt << 'EOF'
{m76_clues}EOF

# ---- session 8: texttools exercises -----------------------------------------

# m-s8-1: attendees.csv (grep the winner row, cut the note column)
cat > /opt/lab/attendees.csv << 'EOF'
{m81_text}EOF

# m-s8-2: chat.log + words/ (top word names the file)
mkdir -p /opt/lab/words
cat > /opt/lab/chat.log << 'EOF'
{m82_text}EOF
printf '%s\n' '{flags["m-s8-2-topword"]}' > /opt/lab/words/pineapple-42
printf '%s\n' 'FAKEFLAG{{second-place}}' > /opt/lab/words/cactus-17
for w in tok-7 tok-88 tok-291; do
  printf '%s\n' 'nothing here' > /opt/lab/words/$w
done

# m-s8-3: byte-position hint (wc -c -> tail -c +N)
printf '%s' 'REMEMBER: count everything, trust nothing, and always carry a towel.' > /opt/lab/hint.txt
N=$(wc -c < /opt/lab/hint.txt)
head -c $((N - 1)) /dev/urandom > /opt/lab/blob.bin
printf '%s' '{flags["m-s8-3-countpos"]}' >> /opt/lab/blob.bin
printf '\n' >> /opt/lab/blob.bin

# oe-s8-1: two conf versions (diff)
cat > /opt/lab/old.conf << 'EOF'
[server]
port = 8080
timeout = 30
loglevel = info
max_clients = 50
EOF
cat > /opt/lab/new.conf << 'EOF'
[server]
port = 8080
timeout = 30
loglevel = debug
max_clients = 50
secret_token = {flags["oe-s8-1-confdiff"]}
EOF

# om-s8-1: app log + module keys (billing fails most)
mkdir -p /opt/lab/modules
cat > /opt/lab/app.log << 'EOF'
{m88_text}EOF
for mo in authx cache queue mailer storage; do
  printf '%s\n' 'FAKEFLAG{{wrong-module}}' > /opt/lab/modules/$mo.key
done
printf '%s\n' '{flags["om-s8-1-logtop"]}' > /opt/lab/modules/billing.key

# oh-s8-1: 30 case files + suspects (culprit stores the flag reversed)
mkdir -p /opt/lab/suspects
{m89_cases}
{m89_suspects}
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
