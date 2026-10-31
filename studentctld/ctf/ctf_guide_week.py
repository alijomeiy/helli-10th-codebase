import sys
sys.path.append("/opt/CTFd")
from CTFd import create_app
from CTFd.models import Challenges, Pages, db
from CTFd.cache import cache

DOCS = [
    ("html.html", "HTML", "📖"),
    ("regex.html", "ریجکس", "🔎"),
    ("permissions.html", "دسترسی‌ها", "🔐"),
    ("apt.html", "apt", "📦"),
    ("archives.html", "آرشیو و فشرده‌سازی", "🗜️"),
    ("pipes.html", "لوله‌ها و تغییر مسیر", "⛓️"),
    ("texttools.html", "پردازش متن", "✂️"),
    ("networking.html", "شبکه", "🌐"),
]

app = create_app()
with app.app_context():
    def rows(cat):
        return Challenges.query.filter_by(
            category=cat, state="visible").order_by(Challenges.name).all()

    def table(rows_):
        out = ["| چالش | امتیاز |", "|---|---|"]
        for c in rows_:
            out.append(f"| {c.name} | {c.value} |")
        return out

    w1 = (rows("چالش‌های هفته اول — آسان")
          + rows("چالش‌های هفته اول — سخت"))
    w2e = rows("چالش‌های هفته دوم — آسان")
    w2h = rows("چالش‌های هفته دوم — سخت")
    w2o = rows("چالش‌های هفته دوم — اختیاری")

    lines = [
        "## 🗺️ راهنمای هفته‌ها",
        "",
        "چالش‌ها روی همین تابلو هستند و همه روی سرور کلاس با ترمینال خودت "
        "حل می‌شوند. شماره‌ی هر چالش، ترتیب پیشنهادی است.",
        "",
        "### هفته ۱ — فرمان‌های پایه",
        "",
    ] + table(w1) + [
        "",
        "### هفته ۲ — شبکه (درس: [آموزش شبکه]"
        "(https://docs.helli-10th-computer.ir/networking.html))",
        "",
        "اول درس را بخوان؛ ابزارهای اصلی این هفته `ss` و `curl` هستند و "
        "فایل‌های شخصی هر نفر در پوشه‌ی `netlab` خانه‌اش است.",
        "",
    ] + table(w2e + w2h)
    if w2o:
        lines += ["", "**اختیاری** (پروتکل‌های عمیق‌تر):", ""] + table(w2o)
    lines += [
        "",
        "### 📚 درس‌های مرتبط",
        "",
    ]
    for slug, title, icon in DOCS:
        lines.append(f"- {icon} [آموزش {title}]"
                     f"(https://docs.helli-10th-computer.ir/{slug}.html)")

    page = Pages.query.filter_by(route="index").first()
    if page is None:
        page = Pages(title="CTF Computer Helli 10th", route="index",
                     draft=False)
        db.session.add(page)
    page.content = "\n".join(lines) + "\n"
    db.session.commit()
    cache.clear()
    print("guide page rebuilt:", len(page.content), "bytes")
    print("  week1 rows:", len(w1),
          "| week2:", len(w2e) + len(w2h),
          "| optional:", len(w2o))
