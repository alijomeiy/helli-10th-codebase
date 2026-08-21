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
      "به مسابقه خوش آمدید!\n"
      "پرچم شما:\n" + flag + "\n")


def scatter_m_readme(home, flag):
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
    ]
    w(f"{home}/level1/README.txt", "\n".join(lines) + "\n")


def scatter_m_manyfiles(home, flag):
    d = f"{home}/level1/lost"
    os.makedirs(d, exist_ok=True)
    for i in range(1, 61):
        w(f"{d}/f{i:03d}.txt", "این فایل چیزی برای گفتن ندارد.\n" * 3)
    w(f"{d}/note-{random.randint(1000, 9999)}.txt",
      "برنده‌ی امروز شما هستید!\n" + flag + "\n")


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
    w(f"{home}/level2/photo.jpg",
      "٪PDF-1.4 شکلی وجود ندارد؛ فقط متن است.\n"
      "پسوند فایل همیشه نوع واقعی را نشان نمی‌دهد.\n"
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
      "پرچم شما به ۴ تکه شکسته شده است!\n"
      "با vim تکه‌ها را به همان ترتیبِ شماره‌ها، در یک خط پشت سر هم بچسبانید\n"
      "و در پایان با :w ذخیره کنید. سپس همان رشته‌ی کامل را در سایت ثبت کنید.\n"
      "----------------------------------------\n"
      f"تکه ۱:\n{pieces[0]}\n"
      f"تکه ۲:\n{pieces[1]}\n"
      f"تکه ۳:\n{pieces[2]}\n"
      f"تکه ۴:\n{pieces[3]}\n"
      "----------------------------------------\n"
      "راهنمای کلیدها: v انتخاب، y کپی، p چسباندن، i درج، :w ذخیره، :q خروج\n")


# ---------------- optional scatterers ----------------

def scatter_o1_hidden(home, flag):
    w(f"{home}/.level1/.secret-note.txt",
      "پوشه‌های نقطه‌دار در ls معمولی دیده نمی‌شوند!\n"
      f"پرچم شما:\n{flag}\n")


def scatter_o2_archive(home, flag):
    d = f"{home}/level3"
    os.makedirs(d, exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        w(os.path.join(td, "flag.txt"), "آفرین که آرشیو را باز کردید!\n" + flag + "\n")
        w(os.path.join(td, "README.txt"), "این هم یک فایل اضافه برای گمراه کردن!\n")
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
    body = ["در این فایل فقط یک خط شکل درست FLAG{aa-dd} دارد؛ بقیه تله‌اند.\n"]
    for _ in range(45):
        body.append(rnd.choice(decoy_builders)() + "\n")
    two_l = rand_letters(2)
    two_d = rand_digits(2)
    body.append(f"پرچم واقعی این است: FLAG{{{two_l}-{two_d}}} => {flag}\n")
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
<head><meta charset="utf-8"><title>درباره ما</title></head>
<body>
<h1>سلام! این صفحه‌ی ماست</h1>
<p>ما داریم در مسابقه‌ی CTF شرکت می‌کنیم.</p>
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
      "<title>!</title></head>\n<body>\n<h1>robot ها اینجا نیایند!</h1>\n"
      f"<p>{flag}</p>\n</body>\n</html>\n")


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
        # wipe previous contest artifacts (keep student's own files:
        # public_html/index.html and anything outside these paths)
        for sub in ("level1", "level2", "level3", ".level1", "ctf"):
            shutil.rmtree(os.path.join(home, sub), ignore_errors=True)
        for junk in (f"{home}/welcome.txt",
                     f"{home}/public_html/about.html",
                     f"{home}/public_html/robots.txt",
                     f"{home}/public_html/hidden"):
            if os.path.isdir(junk):
                shutil.rmtree(junk, ignore_errors=True)
            elif os.path.exists(junk):
                os.remove(junk)
        manifest["students"].append({"username": username, "uid": uid})
        for ch in CHALLENGES:
            flag = make_flag(username)
            SCATTERERS[ch["name"]](home, flag)
            manifest["flags"][ch["name"]][username] = flag
        for sub in ("level1", "level2", "level3", ".level1", "public_html", "ctf"):
            p = os.path.join(home, sub)
            if os.path.isdir(p):
                chown_tree(p, uid)
        # welcome.txt sits in home root
        wp = os.path.join(home, "welcome.txt")
        if os.path.exists(wp):
            os.chown(wp, uid, -1)
        print(f"  OK {username}")

    with open(args.manifest, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)
    print(f"scattered {len(manifest['students'])} students x "
          f"{len(CHALLENGES)} challenges -> {args.manifest}")


if __name__ == "__main__":
    main()
