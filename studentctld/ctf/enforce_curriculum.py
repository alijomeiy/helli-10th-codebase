#!/usr/bin/env python3
"""
Enforce the targeted, clean curriculum on CTFd:
Week 1 (Linux Fundamentals): 01..08 (8 challenges, 825 pts max)
Week 2 (Networking):         09..19 (11 challenges, 1700 pts max)
Total: 19 challenges, 2525 pts max.
Hides and zeroes all other challenges.
"""
import sys
sys.path.append("/opt/CTFd")
from CTFd import create_app
from CTFd.models import Challenges, db
from CTFd.cache import cache

EXPECTED = {
    # Week 1 - Easy
    40: ("01 — خوش آمدید (ls & cat)", "چالش‌های هفته اول — آسان", 50),
    41: ("02 — خواندن فایل طولانی (cd & tail/cat)", "چالش‌های هفته اول — آسان", 75),
    42: ("03 — کلاف سردرگم (ls -la & cat)", "چالش‌های هفته اول — آسان", 75),
    # Week 1 - Hard
    43: ("04 — سوزن در انبار کاه (grep در فایل‌های بزرگ)", "چالش‌های هفته اول — سخت", 100),
    44: ("05 — هزارتو (find و پوشه‌های تودرتو)", "چالش‌های هفته اول — سخت", 125),
    45: ("06 — ظاهر فریبنده (تشخیص نوع فایل با file)", "چالش‌های هفته اول — سخت", 125),
    46: ("07 — فایل نقطه‌دار (فایل‌های مخفی با ls -a)", "چالش‌های هفته اول — سخت", 125),
    47: ("08 — پرچم شکسته (ترکیب و ویرایش تکه‌ها)", "چالش‌های هفته اول — سخت", 150),
    # Week 2 - Easy
    128: ("09 — سرور خودت (http.server & curl)", "چالش‌های هفته دوم — آسان", 50),
    129: ("10 — روی پاکت نوشته (curl -i)", "چالش‌های هفته دوم — آسان", 75),
    130: ("11 — فایل اشتراکی (share & curl)", "چالش‌های هفته دوم — آسان", 100),
    # Week 2 - Hard
    131: ("12 — مزرعه‌ی درها (حلقه‌ی curl)", "چالش‌های هفته دوم — سخت", 125),
    132: ("13 — دنبال‌کننده‌ی مسیر (curl -L)", "چالش‌های هفته دوم — سخت", 150),
    133: ("14 — کارآگاه شبکه (curl -H)", "چالش‌های هفته دوم — سخت", 175),
    # Week 2 - Optional
    155: ("15 — پیک موتوری (curl -d)", "چالش‌های هفته دوم — اختیاری", 175),
    156: ("16 — بلیت را نگه‌دار (curl -c/-b)", "چالش‌های هفته دوم — اختیاری", 175),
    157: ("17 — پنت‌هاوس (Host header)", "چالش‌های هفته دوم — اختیاری", 200),
    158: ("18 — زیرِ HTTP (nc)", "چالش‌های هفته دوم — اختیاری", 225),
    159: ("19 — شکارچی کدها (status codes)", "چالش‌های هفته دوم — اختیاری", 250),
}

app = create_app()
with app.app_context():
    all_challs = Challenges.query.all()
    hidden_count = 0
    active_count = 0
    for c in all_challs:
        if c.id in EXPECTED:
            name, cat, val = EXPECTED[c.id]
            c.name = name
            c.category = cat
            c.value = val
            c.state = 'visible'
            active_count += 1
        else:
            c.state = 'hidden'
            c.value = 0
            hidden_count += 1

    db.session.commit()
    cache.clear()
    print(f"Curriculum enforced: {active_count} active challenges visible (max 2525 pts), {hidden_count} challenges hidden.")
