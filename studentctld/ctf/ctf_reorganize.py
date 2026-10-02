#!/usr/bin/env python3
"""One-shot CTF board cleanup: merge the fragmented "اختیاری — *" categories
into one, rename every challenge to the numbered display name from
challenges.numbered_titles(), and publish a Persian guide page as the CTFd
homepage. Fully rollbackable: before-state (names, categories, index page)
is dumped to /root/ctf_reorg_backup.json and --rollback restores it.

Usage: python3 ctf_reorganize.py --url http://127.0.0.1:8000 --token T --apply
       python3 ctf_reorganize.py --url http://127.0.0.1:8000 --token T --rollback
"""
import argparse
import json

import requests

from challenges import CHALLENGES, numbered_titles

BACKUP = "/root/ctf_reorg_backup.json"
MERGE_TO = "اختیاری"
GUIDE_TITLE = "از کجا شروع کنیم؟"

GUIDE_MD = """## 🧭 راهنمای شروع — از کجا و به چه ترتیب؟

هر چالش یک **پرچم مخصوص خودت** دارد؛ پرچم دیگران به کار تو نمی‌آید.

| مرحله | دسته | چیست | پیش‌نیاز |
|---|---|---|---|
| ۱ | **اجباری** | آشنایی با ترمینال: خواندن، جستجو، vim | فقط حساب سرور |
| ۲ | **اختیاری** | مخفی‌کاری، آرشیو، ریجکس، وب، دسترسی‌ها | حساب سرور |
| ۳ | **آسان** | تمرین درس‌ها: apt، آرشیو، متن، فرایند، شبکه، داکر | آزمایشگاه (mybox) |
| ۴ | **آزمایشگاه** | root واقعی: کاربر، cron، سرویس، داکر-داخل-داکر | آزمایشگاه (mybox) |
| ۵ | **سخت** | کارآگاهی: بایگانی، زمان، نیمه‌های گم‌شده | آزمایشگاه + درس‌ها |
| ۶ | **بسیار سخت** | کانتینر-فورنزیک و سرویس‌های پنهان | همه‌ی بالا |

**راهنمای درس‌ها:** [docs.helli-10th-computer.ir](https://docs.helli-10th-computer.ir)
— هر درس می‌گوید برای کدام چالش‌ها لازم است.

💡 درون هر دسته، شماره‌ی چالش‌ها ترتیب پیشنهادی است.
"""


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

    def patch(self, path, payload):
        r = self.s.patch(f"{self.base}{path}", json=payload, timeout=15)
        r.raise_for_status()
        return r.json().get("data", {})

    def post(self, path, payload):
        r = self.s.post(f"{self.base}{path}", json=payload, timeout=15)
        r.raise_for_status()
        return r.json()["data"]

    def delete(self, path, pid):
        r = self.s.delete(f"{self.base}{path}/{pid}", timeout=15)
        r.raise_for_status()


def all_challenges(api):
    # view=admin: see hidden drafts as well. Page via meta.pagination and
    # cap hard — CTFd keeps returning rows for out-of-range pages, which
    # otherwise loops forever (and OOMs the small session cgroup).
    out, page = [], 1
    while page <= 50:
        r = api.s.get(f"{api.base}/challenges",
                      params={"view": "admin", "page": page,
                              "per_page": 100},
                      timeout=15)
        r.raise_for_status()
        j = r.json()
        data = j.get("data", [])
        out.extend(data)
        nxt = (j.get("meta", {}).get("pagination", {}) or {}).get("next")
        if not nxt or not data:
            break
        page += 1
    return out


def apply(api):
    challenges = all_challenges(api)
    titles = numbered_titles()
    want = {titles[ch["name"]]: ch for ch in CHALLENGES}
    old_by_new = {}          # new display name -> current ctfd name
    for c in challenges:
        base = c["name"]
        # strip a previous "cat NN — " prefix if re-running
        for name, ch in want.items():
            suffix = name.split(" — ", 1)[-1]
            if base == name or base == suffix:
                old_by_new[name] = base
                break

    backup = {
        "challenges": [{"id": c["id"], "name": c["name"],
                        "category": c["category"], "state": c.get("state")}
                       for c in challenges],
        "pages": [],
    }

    # 1) categories: merge the fragmented اختیاری — * ones
    for c in challenges:
        if c["category"].startswith("اختیاری —"):
            api.patch(f"/challenges/{c['id']}", {"category": MERGE_TO})
            print(f"  category: {c['name'][:30]} -> {MERGE_TO}")

    # 2) names -> numbered display names
    renamed = 0
    for new, old in old_by_new.items():
        if old != new:
            cid = next(c["id"] for c in challenges if c["name"] == old)
            api.patch(f"/challenges/{cid}", {"name": new})
            renamed += 1
    print(f"  renamed {renamed} challenges")

    # 3) guide: prepend to the existing index page (keep the original
    # landing content below). CTFd pages use the "route" field ("index" =
    # homepage); idempotent via a first-line marker.
    marker = GUIDE_MD.splitlines()[0]
    for p in api.get("/pages", per_page=100):
        if p.get("route") != "index":
            continue
        if p["content"].lstrip().startswith(marker):
            print("  guide already on index page — skipping")
            break
        backup["pages"].append({k: p.get(k) for k in
                                ("id", "title", "content", "format", "draft")})
        api.patch(f"/pages/{p['id']}",
                  {"content": GUIDE_MD + "\n\n---\n\n" + p["content"],
                   "format": "markdown", "draft": False})
        print("  guide page: prepended to index")
        break
    else:
        api.post("/pages", {"title": GUIDE_TITLE, "content": GUIDE_MD,
                            "route": "index", "format": "markdown",
                            "draft": False})
        print("  guide page: created as index")

    with open(BACKUP, "w", encoding="utf-8") as f:
        json.dump(backup, f, ensure_ascii=False, indent=1)
    print(f"  before-state -> {BACKUP} (rollback anytime with --rollback)")


def rollback(api):
    with open(BACKUP, encoding="utf-8") as f:
        backup = json.load(f)
    for c in backup["challenges"]:
        api.patch(f"/challenges/{c['id']}",
                  {"name": c["name"], "category": c["category"]})
    print(f"  restored {len(backup['challenges'])} challenges")
    marker = GUIDE_MD.splitlines()[0]
    restored = False
    if backup["pages"]:
        p = backup["pages"][0]
        api.patch(f"/pages/{p['id']}", {"content": p["content"],
                                        "format": p.get("format") or "markdown",
                                        "draft": p.get("draft") or False})
        restored = True
        print("  index page restored")
    for p in api.get("/pages", per_page=100):
        if (p.get("route") == "index"
                and not restored
                and p["content"].lstrip().startswith(marker)):
            # no backup (impossible via --apply) — strip the guide part
            _, _, rest = p["content"].partition("\n\n---\n\n")
            api.patch(f"/pages/{p['id']}", {"content": rest})
            restored = True
            print("  guide stripped from index")
        elif p.get("route") is None and p.get("title") == GUIDE_TITLE:
            api.delete("/pages", p["id"])
            print("  stray guide page deleted")
    print("  rollback done.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:8000")
    ap.add_argument("--token", required=True)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--apply", action="store_true")
    g.add_argument("--rollback", action="store_true")
    args = ap.parse_args()
    api = CTFd(args.url, args.token)
    apply(api) if args.apply else rollback(api)


if __name__ == "__main__":
    main()
