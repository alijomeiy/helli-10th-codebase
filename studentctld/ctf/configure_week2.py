import sys
sys.path.append("/opt/CTFd")
from CTFd import create_app
from CTFd.models import Challenges, Hints, db
from CTFd.cache import cache

app = create_app()
with app.app_context():
    # the six networking challenges, selected by their registered categories
    # (ctf_setup names them «01/02/03 — title» inside these categories)
    easy_cat = "چالش‌های هفته دوم — آسان"
    hard_cat = "چالش‌های هفته دوم — سخت"
    opt_cat = "چالش‌های هفته دوم — اختیاری"

    # final display names: numbering continues across the week-1 set (01..08).
    # lookup keys are matched as prefixes of the registered names, which
    # carry the lesson tag («01 — سرور خودت — درس: شبکه»)
    final_by_old = [
        ("01 — سرور خودت",        "09 — سرور خودت (http.server & curl)", 50),
        ("02 — روی پاکت نوشته",   "10 — روی پاکت نوشته (curl -i)", 75),
        ("03 — فایل اشتراکی",     "11 — فایل اشتراکی (share & curl)", 100),
        ("01 — مزرعه‌ی درها",     "12 — مزرعه‌ی درها (حلقه‌ی curl)", 125),
        ("02 — دنبال‌کننده‌ی مسیر", "13 — دنبال‌کننده‌ی مسیر (curl -L)", 150),
        ("03 — کارآگاه شبکه",     "14 — کارآگاه شبکه (curl -H)", 175),
        # optional batch (15..19)
        ("01 — پیک موتوری",       "15 — پیک موتوری (curl -d)", 175),
        ("02 — بلیت را نگه‌دار",   "16 — بلیت را نگه‌دار (curl -c/-b)", 175),
        ("03 — پنت‌هاوس",         "17 — پنت‌هاوس (Host header)", 200),
        ("04 — زیرِ HTTP",        "18 — زیرِ HTTP (nc)", 225),
        ("05 — شکارچی کدها",      "19 — شکارچی کدها (status codes)", 250),
    ]

    touched = []
    for cat in (easy_cat, hard_cat, opt_cat):
        rows = Challenges.query.filter_by(category=cat).all()
        if not rows:
            print(f"WARNING: no challenges found in category '{cat}'")
        for c in rows:
            hit = next((f for f in final_by_old if c.name.startswith(f[0])),
                       None)
            if hit is None:
                print(f"WARNING: unexpected challenge '{c.name}' in '{cat}'")
                continue
            new_name, pts = hit[1], hit[2]
            c.name = new_name
            c.value = pts
            c.state = "visible"
            touched.append((c.id, new_name, pts))

    # week convention: hints are free
    for c in Challenges.query.filter(
            Challenges.category.in_([easy_cat, hard_cat, opt_cat])).all():
        for h in Hints.query.filter_by(challenge_id=c.id).all():
            h.cost = 0

    db.session.commit()
    cache.clear()

    print("Week 2 (networking) configured!")
    for cid, name, pts in sorted(touched):
        print(f"  [ID {cid}] {name} | {pts} pts")
    vis = Challenges.query.filter_by(state="visible").order_by(
        Challenges.id).all()
    print(f"Total visible challenges: {len(vis)}")
    for v in vis:
        print(f"  [ID {v.id}] Cat='{v.category}' | Pts={v.value:3d} | Name='{v.name}'")
