#!/usr/bin/env python3
"""Scatter per-student CTF flags into Linux home directories (run as root).

Usage: sudo python3 ctf_scatter.py [--manifest manifest.json]
Creates FLAG{username-XXXXXX} in a fixed location per challenge, chowns
everything to the student, and writes a JSON manifest for ctf_setup.py.

v2: challenge set remapped to classroom skills (mandatory = core commands
only; optional = ls -a / tar / regex / web).
"""
import argparse
import json
import os
import random
import shutil
import string
import tarfile
import tempfile

from challenges import CHALLENGES

CONFIG_PATH = "/etc/studentctl/config.json"


def load_students():
    try:
        with open(CONFIG_PATH) as f:
            cfg = json.load(f)
        out = []
        for name, d in cfg.get("users", {}).items():
            if d.get("enabled") and d.get("uid", 0) >= 2000:
                out.append((name, d["uid"]))
        if out:
            return out
    except (OSError, ValueError):
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
    return out


def make_flag(username):
    tail = "".join(random.choices(string.hexdigits.lower()[:16], k=6))
    return f"FLAG{{{username}-{tail}}}"


def w(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


# ---------------- mandatory scatterers ----------------

def scatter_m_welcome(home, flag):
    w(f"{home}/welcome.txt",
      "Welcome to the Flag Hunt!\n"
      "Here is your first and easiest flag:\n" + flag + "\n")


def scatter_m_readme(home, flag):
    lines = [
        "Server Handbook - Classroom Edition",
        "==================================",
        "",
        "This file exists to practice reading long files.",
    ]
    lines += [f"Section {i}: general and repetitive notes about working with the server. " * 2
              for i in range(1, 33)]
    lines += [
        "",
        "End of handbook. Your patience reward:",
        f"FLAG: {flag}",
    ]
    w(f"{home}/level1/README.txt", "\n".join(lines) + "\n")


def scatter_m_manyfiles(home, flag):
    d = f"{home}/level1/lost"
    os.makedirs(d, exist_ok=True)
    for i in range(1, 61):
        w(f"{d}/f{i:03d}.txt", "This file has nothing to say.\n" * 3)
    w(f"{d}/note-{random.randint(1000, 9999)}.txt",
      "Today is your lucky day!\n" + flag + "\n")


def scatter_m_grep(home, flag):
    rnd = random.Random()
    lines = []
    for i in range(400):
        hh, mm, ss = rnd.randint(8, 17), rnd.randint(0, 59), rnd.randint(0, 59)
        ip = ".".join(str(rnd.randint(2, 250)) for _ in range(4))
        path = rnd.choice(["/index.html", "/login", "/about.html", "/api/status"])
        lines.append(f"2026-08-21 {hh:02d}:{mm:02d}:{ss:02d} ip={ip} "
                     f"status=200 path={path}")
    target = rnd.randint(100, 350)
    lines[target] += f" note={flag}"
    w(f"{home}/level2/server.log", "\n".join(lines) + "\n")


def scatter_m_maze(home, flag):
    base = f"{home}/level2/maze"
    shutil.rmtree(base, ignore_errors=True)
    names = ["data", "files", "tmp", "var", "opt", "src", "lib", "bin", "etc", "cache"]
    prev = [base]
    for _ in range(4):
        cur = []
        for _ in range(random.randint(4, 5)):
            parent = random.choice(prev)
            d = os.path.join(parent, random.choice(names))
            while os.path.exists(d):
                d = os.path.join(parent, random.choice(names) + str(random.randint(10, 99)))
            os.makedirs(d)
            cur.append(d)
            w(os.path.join(d, "placeholder.db"), "\x00" * 32)
        prev = cur
    w(os.path.join(random.choice(prev), "end.flag"), flag + "\n")


def scatter_m_fakeext(home, flag):
    # deliberate Persian spice: reading mixed RTL/LTR content in vim is part
    # of the challenge (mandatory but flavor text only)
    w(f"{home}/level2/photo.jpg",
      "٪تصویر-۱.۴ هیچ شکلی اینجا نیست؛ فقط متن است.\n"
      "پسوندِ فایل همیشه نوعِ واقعی‌اش را نشان نمی‌دهد.\n"
      f"{flag}\n")

def scatter_m_dots(home, flag):
    cmds = ["ls", "cd /var/log", "vim notes.txt", "grep ERROR app.log",
            "mkdir projects", "rm old.tar.gz", "tree",
            "find . -name todo.txt", "mv a.txt b.txt", "whoami"] * 3
    w(f"{home}/level3/.old_history",
      "\n".join(cmds) + f"\necho {flag} > /tmp/prize.txt\nclear\n")


def scatter_m_vimedit(home, flag):
    """Flag split into 4 chunks; student reassembles with v/y/p and :w."""
    n = len(flag)
    cuts = sorted(random.sample(range(5, n - 5), 3))
    pieces = [flag[:cuts[0]], flag[cuts[0]:cuts[1]],
              flag[cuts[1]:cuts[2]], flag[cuts[2]:]]
    w(f"{home}/ctf/fixme.txt",
      "Your flag has been broken into 4 pieces!\n"
      "Reassemble the pieces in numbered order into a single line,\n"
      "save with :w, then submit that exact full string on the site.\n"
      "----------------------------------------\n"
      f"Piece 1:\n{pieces[0]}\n"
      f"Piece 2:\n{pieces[1]}\n"
      f"Piece 3:\n{pieces[2]}\n"
      f"Piece 4:\n{pieces[3]}\n"
      "----------------------------------------\n")


# ---------------- optional scatterers ----------------

def scatter_o1_hidden(home, flag):
    w(f"{home}/.level1/.secret-note.txt",
      "پوشه‌های نقطه‌دار در فهرستِ معمولی دیده نمی‌شوند!\n"
      f"پرچم شما:\n{flag}\n")


def scatter_o2_archive(home, flag):
    d = f"{home}/level3"
    os.makedirs(d, exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        # Persian spice kept: optional challenge reward line
        w(os.path.join(td, "flag.txt"), "آفرین که بسته را باز کردید!\n" + flag + "\n")
        w(os.path.join(td, "README.txt"), "Just a decoy file to confuse you!\n")
        with tarfile.open(f"{d}/backup.tar.gz", "w:gz") as tf:
            tf.add(os.path.join(td, "flag.txt"), arcname="flag.txt")
            tf.add(os.path.join(td, "README.txt"), arcname="README.txt")


def scatter_o3_regex_class(home, flag):
    """Real flag shaped FLAG{xx-dd} rides ONE correctly-shaped line; decoys
    are near-miss shapes so only grep -E 'FLAG\\{[a-z]{2}-[0-9]{2}\\}' finds it."""
    rnd = random.Random()

    def rand_letters(k):
        return "".join(rnd.choices(string.ascii_lowercase, k=k))

    def rand_digits(k):
        return "".join(rnd.choices(string.digits, k=k))

    decoy_builders = [
        lambda: f"FLAG{{{rand_letters(1)}}}-{rand_digits(1)}}}",      # 1-1
        lambda: f"FLAG{{{rand_letters(3)}}}-{rand_digits(3)}}}",      # 3-3
        lambda: f"FLAG{{{rand_letters(2)}}}-{rand_digits(3)}}}",      # 2-3
        lambda: f"FLAG{{{rand_letters(3)}}}-{rand_digits(2)}}}",      # 3-2
        lambda: f"FLAG{{{rand_letters(2).upper()}}}-{rand_digits(2)}}}",  # uppercase
        lambda: f"FLAG{{{rand_letters(2)}_{rand_digits(2)}}}",        # underscore
    ]
    body = ["Only ONE line in this file has the correct shape FLAG{aa-dd}; the rest are traps.\n"]
    for _ in range(45):
        body.append(rnd.choice(decoy_builders)() + "\n")
    two_l = rand_letters(2)
    two_d = rand_digits(2)
    # Persian spice kept: the real-flag carrier line (regex still matches the
    # FLAG{xx-dd} part; Persian text around it adds terminal difficulty)
    body.append(f"پرچمِ واقعی این است: FLAG{{{two_l}-{two_d}}} => {flag}\n")
    rnd.shuffle(body[1:])
    w(f"{home}/ctf/regex/decoys.txt", "".join(body))


def scatter_o4_regex_anchor(home, flag):
    rnd = random.Random()
    lines = []
    for i in range(300):
        hh, mm = rnd.randint(8, 17), rnd.randint(0, 59)
        noise = rnd.choice(["disk ok", "cache warm", "user login", "backup done",
                            "healthcheck pass"])
        # decoy: 'err' appears but NOT at line start
        lines.append(f"{hh:02d}:{mm:02d} info module={rnd.randint(1, 99)} {noise} (no err here)")
        if rnd.random() < 0.3:
            lines.append(f"{hh:02d}:{mm:02d} warning … err suppressed … noise={rnd.randint(1, 999)}")
    target = rnd.randint(20, 280)
    lines.insert(target, f"err: critical event id={rnd.randint(100, 999)} FLAG-CARRIER note={flag}")
    w(f"{home}/ctf/regex/anchor.log", "\n".join(lines) + "\n")


ABOUT_PAGE = """<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head><meta charset="utf-8"><title>درباره‌ی ما</title></head>
<body>
<h1>سلام! این صفحه‌ی ماست</h1>
<p>ما داریم در مسابقه‌ی «پیدا کردن پرچم» شرکت می‌کنیم.</p>
<!-- شنبه‌ها جلسه داریم؟ نه! فقط پرچم اینجاست: {flag} -->
<p>موفق باشید!</p>
</body>
</html>
"""

def scatter_o5_web_source(home, flag):
    ph = f"{home}/public_html"
    os.makedirs(ph, exist_ok=True)
    w(f"{ph}/about.html", ABOUT_PAGE.format(flag=flag))


def scatter_o6_web_robots(home, flag):
    ph = f"{home}/public_html"
    os.makedirs(f"{ph}/hidden", exist_ok=True)
    w(f"{ph}/robots.txt", "User-agent: *\nDisallow: /hidden/\n")
    w(f"{ph}/hidden/flag.html",
      "<!DOCTYPE html>\n<html lang=\"fa\" dir=\"rtl\">\n<head><meta charset=\"utf-8\">"
      "<title>!</title></head>\n<body>\n<h1>روبات‌ها اینجا نیایند!</h1>\n"
      f"<p>{flag}</p>\n</body>\n</html>\n")


# ---------------- permissions scatterers (host side, pairs with the lesson) --

def scatter_p1_locked(home, flag):
    """Flag file mode 000, owned by the student — owning it is the key."""
    p = f"{home}/level4/flag.txt"
    w(p, "This file is locked with chmod 000.\n"
         "Its owner can always change the lock...\n" + flag + "\n")
    os.chmod(p, 0o000)


def scatter_p2_sealed(home, flag):
    """Directory mode 000 — x on a directory means 'enter'."""
    d = f"{home}/level4/box"
    os.makedirs(d, exist_ok=True)
    w(os.path.join(d, "prize.txt"), "You unlocked the box!\n" + flag + "\n")
    os.chmod(d, 0o000)


def scatter_p3_brothers(home, flag):
    """Three look-alike files; only the one with owner-r is readable."""
    d = f"{home}/level4/brothers"
    os.makedirs(d, exist_ok=True)
    decoy = "Nothing for you here.\n"
    w(os.path.join(d, "adam.txt"), decoy)
    w(os.path.join(d, "brot.txt"), "The readable brother speaks:\n" + flag + "\n")
    w(os.path.join(d, "cyrus.txt"), decoy)
    os.chmod(os.path.join(d, "adam.txt"), 0o000)
    os.chmod(os.path.join(d, "brot.txt"), 0o400)
    os.chmod(os.path.join(d, "cyrus.txt"), 0o000)


def scatter_r_stub(home, flag):
    """r-series flags live inside each student's box — scattered separately
    by box_scatter.py. Recorded here so the manifest stays complete."""
    pass


SCATTERERS = {
    "m-welcome": scatter_m_welcome,
    "m-readme": scatter_m_readme,
    "m-manyfiles": scatter_m_manyfiles,
    "m-grep": scatter_m_grep,
    "m-maze": scatter_m_maze,
    "m-fakeext": scatter_m_fakeext,
    "m-dots": scatter_m_dots,
    "m-vimedit": scatter_m_vimedit,
    "o1-hidden": scatter_o1_hidden,
    "o2-archive": scatter_o2_archive,
    "o3-regex-class": scatter_o3_regex_class,
    "o4-regex-anchor": scatter_o4_regex_anchor,
    "o5-web-source": scatter_o5_web_source,
    "o6-web-robots": scatter_o6_web_robots,
    "p1-locked": scatter_p1_locked,
    "p2-sealed": scatter_p2_sealed,
    "p3-brothers": scatter_p3_brothers,
    "r1-roothome": scatter_r_stub,
    "r2-labuser": scatter_r_stub,
    "r3-nightlog": scatter_r_stub,
    "r4-web": scatter_r_stub,
    "r5-cron": scatter_r_stub,
    "r6-history": scatter_r_stub,
    "r7-ports": scatter_r_stub,
    "r8-dind": scatter_r_stub,
}


def chown_tree(path, uid):
    for root, dirs, files in os.walk(path):
        for x in dirs + files:
            p = os.path.join(root, x)
            os.chown(p, uid, -1)
        os.chown(root, uid, -1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default="manifest.json")
    ap.add_argument("--only", default="",
                    help="comma-separated challenge names; MERGES into the "
                         "existing manifest instead of overwriting it "
                         "(safe add-only mode for live contests)")
    args = ap.parse_args()

    if os.geteuid() != 0:
        raise SystemExit("run as root: sudo python3 ctf_scatter.py")

    only = [s.strip() for s in args.only.split(",") if s.strip()]
    chals = [c for c in CHALLENGES if not only or c["name"] in only]
    unknown = only and [n for n in only
                        if n not in {c["name"] for c in CHALLENGES}]
    if unknown:
        raise SystemExit(f"unknown challenges: {unknown}")

    merge = bool(only)
    if merge and os.path.exists(args.manifest):
        with open(args.manifest, encoding="utf-8") as f:
            manifest = json.load(f)
        manifest.setdefault("students", [])
        manifest.setdefault("flags", {})
    else:
        manifest = {"students": [], "flags": {c["name"]: {} for c in CHALLENGES}}
    for c in chals:
        manifest["flags"].setdefault(c["name"], {})

    students = load_students()
    if not students:
        raise SystemExit("no students found")

    # dirs wiped before scattering: full pass clears everything; --only
    # (currently the level4 permissions set) clears just what it owns
    wipe = ("level1", "level2", "level3", "level4", ".level1", "ctf") \
        if not merge else ("level4",)
    known = {s["username"] for s in manifest["students"]}

    for username, uid in students:
        home = f"/home/{username}"
        if not os.path.isdir(home):
            print(f"  SKIP {username} (no home)")
            continue
        for sub in wipe:
            shutil.rmtree(os.path.join(home, sub), ignore_errors=True)
        if not merge:
            for junk in (f"{home}/welcome.txt",
                         f"{home}/public_html/about.html",
                         f"{home}/public_html/robots.txt",
                         f"{home}/public_html/hidden"):
                if os.path.isdir(junk):
                    shutil.rmtree(junk, ignore_errors=True)
                elif os.path.exists(junk):
                    os.remove(junk)
        if username not in known:
            manifest["students"].append({"username": username, "uid": uid})
            known.add(username)
        for ch in chals:
            flag = make_flag(username)
            SCATTERERS[ch["name"]](home, flag)
            manifest["flags"][ch["name"]][username] = flag
        for sub in wipe + (".level1", "public_html", "ctf"):
            p = os.path.join(home, sub)
            if os.path.isdir(p):
                chown_tree(p, uid)
        wp = os.path.join(home, "welcome.txt")
        if os.path.exists(wp):
            os.chown(wp, uid, -1)
        print(f"  OK {username}")

    with open(args.manifest, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)
    print(f"scattered {len(students)} students x {len(chals)} challenges "
          f"({'merge' if merge else 'full'}) -> {args.manifest}")


if __name__ == "__main__":
    main()
