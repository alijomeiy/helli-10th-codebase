#!/usr/bin/env python3
"""Scatter per-student CTF flags into Linux home directories (run as root).

Usage: sudo python3 ctf_scatter.py [--manifest manifest.json]
Creates FLAG{username-XXXXXX} in a fixed location per challenge, chowns
everything to the student, and writes a JSON manifest for ctf_setup.py.
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


def scatter_l1_hidden(home, flag):
    w(f"{home}/.level1/.secret-note.txt",
      "شاید مخفی بودن به‌تنهایی کافی نباشد...\n"
      f"اما اینجا پرچم شماست:\n{flag}\n")


def scatter_l1_readme(home, flag):
    lines = [
        "راهنمای شروع کار با سرور کلاس",
        "================================",
        "",
        "این فایل برای تمرین خواندن فایل‌های طولانی ساخته شده است.",
    ]
    lines += [f"قسمت {i}: توضیحات عمومی و تکراری درباره‌ی کار با سرور. " * 2
              for i in range(1, 33)]
    lines += [
        "",
        "پایان فایل. جایزه‌ی صبر و حوصله‌ی شما:",
        f"پرچم: {flag}",
        "(این خط راحت پیدا نمی‌شود مگر با grep یا پرش مستقیم در vim)",
    ]
    w(f"{home}/level1/README.txt", "\n".join(lines) + "\n")


def scatter_l1_manyfiles(home, flag):
    d = f"{home}/level1/lost"
    os.makedirs(d, exist_ok=True)
    for i in range(1, 61):
        w(f"{d}/f{i:03d}.txt", "این فایل چیزی برای گفتن ندارد.\n" * 3)
    w(f"{d}/note-{random.randint(1000, 9999)}.txt",
      "برنده‌ی امروز شما هستید!\n" + flag + "\n")


def scatter_l2_grep(home, flag):
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


def scatter_l2_maze(home, flag):
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


def scatter_l2_ext(home, flag):
    w(f"{home}/level2/photo.jpg",
      "٪PDF-1.4 شکلی وجود ندارد؛ فقط متن است.\n"
      "پسوند فایل همیشه نوع واقعی را نشان نمی‌دهد.\n"
      f"{flag}\n")


def scatter_l3_history(home, flag):
    cmds = ["ls -la", "cd /var/log", "vim notes.txt", "grep ERROR app.log",
            "mkdir projects", "rm old.tar.gz", "cat /etc/hostname",
            "python3 -m http.server 10000", "df -h", "whoami"] * 3
    w(f"{home}/level3/.old_history",
      "\n".join(cmds) + f"\necho {flag} > /tmp/prize.txt\nclear\n")


def scatter_l3_archive(home, flag):
    d = f"{home}/level3"
    os.makedirs(d, exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        w(os.path.join(td, "flag.txt"), "آفرین که آرشیو را باز کردید!\n" + flag + "\n")
        w(os.path.join(td, "README.txt"), "این هم یک فایل اضافه برای گمراه کردن!\n")
        with tarfile.open(f"{d}/backup.tar.gz", "w:gz") as tf:
            tf.add(os.path.join(td, "flag.txt"), arcname="flag.txt")
            tf.add(os.path.join(td, "README.txt"), arcname="README.txt")


ABOUT_PAGE = """<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head><meta charset="utf-8"><title>درباره تیم ما</title></head>
<body>
<h1>سلام! این صفحه‌ی تیم ماست</h1>
<p>ما داریم در مسابقه‌ی CTF شرکت می‌کنیم.</p>
<!-- شنبه‌ها جلسه‌ی تیم داریم؟ نه! فقط پرچم اینجاست: {flag} -->
<p>موفق باشید!</p>
</body>
</html>
"""


def scatter_web_source(home, flag):
    ph = f"{home}/public_html"
    os.makedirs(ph, exist_ok=True)
    w(f"{ph}/about.html", ABOUT_PAGE.format(flag=flag))


def scatter_web_robots(home, flag):
    ph = f"{home}/public_html"
    os.makedirs(f"{ph}/hidden", exist_ok=True)
    w(f"{ph}/robots.txt", "User-agent: *\nDisallow: /hidden/\n")
    w(f"{ph}/hidden/flag.html",
      "<!DOCTYPE html>\n<html lang=\"fa\" dir=\"rtl\">\n<head><meta charset=\"utf-8\">"
      "<title>!</title></head>\n<body>\n<h1>robot ها اینجا نیایند!</h1>\n"
      f"<p>{flag}</p>\n</body>\n</html>\n")


SCATTERERS = {
    "l1-hidden": scatter_l1_hidden,
    "l1-readme": scatter_l1_readme,
    "l1-manyfiles": scatter_l1_manyfiles,
    "l2-grep": scatter_l2_grep,
    "l2-maze": scatter_l2_maze,
    "l2-ext": scatter_l2_ext,
    "l3-history": scatter_l3_history,
    "l3-archive": scatter_l3_archive,
    "web-source": scatter_web_source,
    "web-robots": scatter_web_robots,
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
    args = ap.parse_args()

    if os.geteuid() != 0:
        raise SystemExit("run as root: sudo python3 ctf_scatter.py")

    students = load_students()
    if not students:
        raise SystemExit("no students found")

    manifest = {"students": [], "flags": {c["name"]: {} for c in CHALLENGES}}
    for username, uid in students:
        home = f"/home/{username}"
        if not os.path.isdir(home):
            print(f"  SKIP {username} (no home)")
            continue
        manifest["students"].append({"username": username, "uid": uid})
        for ch in CHALLENGES:
            flag = make_flag(username)
            fn = SCATTERERS[ch["name"]]
            created = fn(home, flag)
            paths = created if isinstance(created, list) else None
            manifest["flags"][ch["name"]][username] = flag
        for sub in ("level1", "level2", "level3", ".level1", "public_html"):
            p = os.path.join(home, sub)
            if os.path.isdir(p):
                chown_tree(p, uid)
        print(f"  OK {username}")

    with open(args.manifest, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)
    print(f"scattered {len(manifest['students'])} students x "
          f"{len(CHALLENGES)} challenges -> {args.manifest}")


if __name__ == "__main__":
    main()
