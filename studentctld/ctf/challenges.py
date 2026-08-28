CHALLENGES = [
    # ---------------- mandatory: simple & direct (what/where, never how) -----
    {
        "name": "m-welcome",
        "title": "خوش آمدید",
        "category": "اجباری",
        "points": 50,
        "description": "فایل welcome.txt در پوشه‌ی خانه‌ی شما پرچم اول را نگه داشته است.",
        "hint": "فایل welcome.txt را با vim باز کنید: vim welcome.txt",
        "hint_cost": 10,
    },
    {
        "name": "m-readme",
        "title": "خواندن فایل طولانی",
        "category": "اجباری",
        "points": 75,
        "description": "در level1 فایل README.txt خیلی طولانی است؛ پرچم در انتهای آن پنهان شده است.",
        "hint": "در vim با /FLAG جستجو کنید (n برای بعدی)، یا grep FLAG level1/README.txt",
        "hint_cost": 15,
    },
    {
        "name": "m-manyfiles",
        "title": "کلاف سردرگم",
        "category": "اجباری",
        "points": 75,
        "description": "در پوشه‌ی level1/lost ده‌ها فایل یکسان‌نما هست؛ فقط یکی از آن‌ها پرچم را دارد.",
        "hint": "tree level1/lost بزنید و نام متفاوت را پیدا کنید.",
        "hint_cost": 15,
    },
    {
        "name": "m-grep",
        "title": "سوزن در انبار کاه",
        "category": "اجباری",
        "points": 100,
        "description": "فایل level2/server.log صدها خط گزارش دارد. خطی که پرچم در آن است را پیدا کنید.",
        "hint": "grep FLAG level2/server.log",
        "hint_cost": 20,
    },
    {
        "name": "m-maze",
        "title": "هزارتو",
        "category": "اجباری",
        "points": 100,
        "description": "در level2/maze پوشه‌های تودرتو ساخته شده است. فایلی به نام end.flag را پیدا کنید.",
        "hint": "find level2/maze -name end.flag و بعد vim روی مسیر پیدا‌شده.",
        "hint_cost": 20,
    },
    {
        "name": "m-fakeext",
        "title": "ظاهر فریبنده",
        "category": "اجباری",
        "points": 125,
        "description": "فایل level2/photo.jpg آن چیزی نیست که به نظر می‌رسد!",
        "hint": "vim level2/photo.jpg — پسوند فایل همیشه حقیقت را نمی‌گوید.",
        "hint_cost": 25,
    },
    {
        "name": "m-dots",
        "title": "فایل نقطه‌دار",
        "category": "اجباری",
        "points": 100,
        "description": "در level3 فایلی پنهان شده که نامش با نقطه شروع می‌شود و در فهرستِ معمولی دیده نمی‌شود.",
        "hint": "find level3 -type f همه‌ی فایل‌ها را نشان می‌دهد (حتی مخفی‌ها)؛ بعد vim کنید.",
        "hint_cost": 20,
    },
    {
        "name": "m-vimedit",
        "title": "پرچم شکسته",
        "category": "اجباری",
        "points": 125,
        "description": "در ctf/fixme.txt پرچم شما به ۴ تکه شکسته شده است. تکه‌ها را به ترتیب در یک خط "
                       "به هم بچسبانید، فایل را ذخیره کنید و همان رشته‌ی کامل را ثبت کنید.",
        "hint": "در vim: با v روی حروف بروید تا انتخاب شود، y بزنید، روی مقصد بروید و p بزنید؛ آخرش :w",
        "hint_cost": 25,
    },

    # ---------------- optional: new skills for fast students ----------------
    {
        "name": "o1-hidden",
        "title": "پوشه‌ی مخفی",
        "category": "اختیاری — پیشرفته",
        "points": 150,
        "description": "در پوشه‌ی خانه‌ی شما چیزی مخفی شده که در فهرستِ معمولی جایی ندارد...",
        "hint": "ls -a فایل‌ها/پوشه‌های نقطه‌دار را هم نشان می‌دهد (چیزی که در کلاس نگفتیم!).",
        "hint_cost": 30,
    },
    {
        "name": "o2-archive",
        "title": "بسته‌ی بسته‌بندی‌شده",
        "category": "اختیاری — پیشرفته",
        "points": 200,
        "description": "نسخه‌ی پشتیبان سرور، بسته‌بندی و مهروموم شده است. آن را باز کنید. "
                       "(ابزارش را در کلاس ندیدید — خودتان پیدا کنید!)",
        "hint": "اول tar tzf level3/backup.tar.gz برای فهرست، بعد tar xzf level3/backup.tar.gz برای باز کردن.",
        "hint_cost": 40,
    },
    {
        "name": "o3-regex-class",
        "title": "ریجکس: کلاس‌ها",
        "category": "اختیاری — ریجکس",
        "points": 150,
        "description": "در میان ده‌ها پرچمِ تقلبی، فقط یکی شکلِ درست را دارد: "
                       "دقیقاً دو حرف کوچک، خط تیره، دقیقاً دو رقم — مثل FLAG{ab-12}. "
                       "درس ریجکس: docs.helli-10th-computer.ir/regex.html",
        "hint": "grep -E 'FLAG\\{[a-z]{2}-[0-9]{2}\\}' ctf/regex/decoys.txt",
        "hint_cost": 30,
    },
    {
        "name": "o4-regex-anchor",
        "title": "ریجکس: لنگرها",
        "category": "اختیاری — ریجکس",
        "points": 175,
        "description": "در این دفترِ ثبتِ رخدادها، خطی که «دقیقاً از ابتدای خط» با err شروع می‌شود "
                       "حامل پرچم است؛ خطوط دیگری هم err دارند ولی تله‌اند. "
                       "درس: docs.helli-10th-computer.ir/regex.html",
        "hint": "grep -E '^err' ctf/regex/anchor.log — علامت ^ یعنی ابتدای خط.",
        "hint_cost": 35,
    },
    {
        "name": "o5-web-source",
        "title": "سورس را ببینید",
        "category": "اختیاری — وب",
        "points": 150,
        "description": "صفحه‌ی «درباره‌ی ما» وب‌سایت خودتان را ببینید. گاهی رازها در همان صفحه‌ی"
                       "ای که نگاه می‌کنید، پنهان‌اند!",
        "hint": "در مرورگر Ctrl+U را بزنید و دنبال <!-- بگردید.",
        "hint_cost": 30,
    },
    {
        "name": "o6-web-robots",
        "title": "راهنمای ربات‌ها",
        "category": "اختیاری — وب",
        "points": 150,
        "description": "روبات‌ها حق ندارند همه‌جا بروند... اما شما ربات نیستید!",
        "hint": "آدرس /robots.txt را باز کنید؛ بعد مسیر جلوی Disallow را به انتهای آدرس اضافه کنید.",
        "hint_cost": 30,
    },

    # ---------------- optional: permissions (host side, pairs with the lesson)
    {
        "name": "p1-locked",
        "title": "قفل شده",
        "category": "اختیاری — دسترسی‌ها",
        "points": 100,
        "description": "فایلی در level4 تمام راه‌هایش به رویتان بسته است — "
                       "اما مالکش خودِ شما هستید. درس دسترسی‌ها: "
                       "docs.helli-10th-computer.ir/permissions.html",
        "hint": "شما مالکید پس اجازه‌ی تغییر قفل را دارید: chmod 644 level4/flag.txt و بعد cat",
        "hint_cost": 20,
    },
    {
        "name": "p2-sealed",
        "title": "جعبه‌ی مهروموم",
        "category": "اختیاری — دسترسی‌ها",
        "points": 125,
        "description": "پوشه‌ی box در level4 اجازه‌ی ورود به هیچ‌کس را نمی‌دهد. "
                       "روی پوشه، x یعنی چه؟ (درس: docs.helli-10th-computer.ir/permissions.html)",
        "hint": "chmod u+x level4/box و بعد ls و cat داخلش.",
        "hint_cost": 25,
    },
    {
        "name": "p3-brothers",
        "title": "سه برادر",
        "category": "اختیاری — دسترسی‌ها",
        "points": 150,
        "description": "در level4/brothers سه فایل هم‌شکل هستند؛ فقط یکی از آن‌ها "
                       "اجازه‌ی خواندن به شما می‌دهد. قفل‌ها را بخوانید، نه اسم‌ها را.",
        "hint": "ls -l level4/brothers — فقط فایلی که برای owner حرف r دارد قابل cat است.",
        "hint_cost": 30,
    },

    # ---------------- root lab: challenges living INSIDE each student's box ---
    {
        "name": "r1-roothome",
        "title": "خانه‌ی ریشه",
        "category": "آزمایشگاه",
        "points": 150,
        "description": "در آزمایشگاه (mybox) پوشه‌ای هست که تا امروز هرگز ندیده‌اید: "
                       "خانه‌ی خودِ root. رازی در آن جا خوش کرده است.",
        "hint": "mybox → ls -a /root → cat /root/.secret.txt",
        "hint_cost": 30,
    },
    {
        "name": "r2-labuser",
        "title": "همسایه‌ی lab",
        "category": "آزمایشگاه",
        "points": 175,
        "description": "کاربری به نام lab در آزمایشگاه شما زندگی می‌کند و فایلش را "
                       "از چشم‌ها پنهان کرده. شما root هستید — راه‌هایتان باز است.",
        "hint": "cat /home/lab/flag.txt (شما root هستید!) — یا با su lab وارد شوید.",
        "hint_cost": 35,
    },
    {
        "name": "r3-nightlog",
        "title": "گزارش شبانه",
        "category": "آزمایشگاه",
        "points": 200,
        "description": "گزارش رخدادهای سیستم در /var/log/lab.log صدها خط دارد؛ "
                       "یکی از آن‌ها پرچم را بار است.",
        "hint": "grep FLAG /var/log/lab.log",
        "hint_cost": 40,
    },
    {
        "name": "r4-web",
        "title": "سرویس وب",
        "category": "آزمایشگاه",
        "points": 225,
        "description": "در /opt/labweb یک وب‌سرور کوچک خواب است. بیدارش کنید و "
                       "از همان داخل آزمایشگاه به آن سر بزنید.",
        "hint": "apt install python3 را اول نصب کنید؛ بعد: python3 /opt/labweb/web.py &  و در پایان  curl localhost:8080",
        "hint_cost": 45,
    },
    {
        "name": "r5-cron",
        "title": "کارِ هر دقیقه",
        "category": "آزمایشگاه",
        "points": 225,
        "description": "زنگ‌زده‌ی این سیستم هر یک دقیقه یک جایزه در جای مشخصی "
                       "می‌گذارد. برنامه‌اش را پیدا کنید و صبور باشید.",
        "hint": "cat /etc/crontab ببینید؛ یک دقیقه صبر کنید و بعد cat /tmp/prize.txt",
        "hint_cost": 45,
    },
    {
        "name": "r6-history",
        "title": "ردپای تاریخچه",
        "category": "آزمایشگاه",
        "points": 175,
        "description": "کاربر lab سابقه‌ی فرمان‌هایش را پاک نکرده است...",
        "hint": "cat /home/lab/.bash_history",
        "hint_cost": 35,
    },
    {
        "name": "r7-ports",
        "title": "چهار درِ بسته",
        "category": "آزمایشگاه",
        "points": 250,
        "description": "اسکریپتی در /opt/lab/servers چهار در پشت‌سرِهم باز می‌کند. "
                       "پرچم فقط پشت یکی از آن‌هاست — کدام در؟",
        "hint": "apt install iproute2  بعد  bash /opt/lab/servers/run.sh  سپس  ss -tlnp  و در آخر curl localhost:9001 تا 9004",
        "hint_cost": 50,
    },
    {
        "name": "r8-dind",
        "title": "داکر داخل داکر",
        "category": "آزمایشگاه",
        "points": 250,
        "description": "در /root آزمایشگاه شما فایلی هست که یک ماشین کامل را درون "
                       "خودش قفل کرده است. بارش کنید، روشنش کنید تا رازش را بگوید.",
        "hint": "docker load -i /root/flag.tar  سپس  docker run flagbox:1",
        "hint_cost": 50,
    },

    # ---------------- tiered mixed set: easy / hard / very hard --------------
    # «آسان» — apt + box basics (pairs with docs/mybox.html and docs/apt.html)
    {
        "name": "e1-kit",
        "title": "بسته‌ی مرموز",
        "category": "آسان",
        "points": 150,
        "description": "در آزمایشگاه (mybox) یک بسته‌ی آماده برای شما گذاشته‌ایم: "
                       "/opt/lab/kit.deb — نصبش کنید و ببینید داخلش چه است. "
                       "درس apt: docs.helli-10th-computer.ir/apt.html",
        "hint": "apt install /opt/lab/kit.deb  (یا dpkg -i) — بعد فایل را که در /usr/share گذاشت پیدا و بخوانید: dpkg -L flagpkg",
        "hint_cost": 25,
    },
    {
        "name": "e2-forest",
        "title": "جنگل درخت‌ها",
        "category": "آسان",
        "points": 150,
        "description": "در /opt/lab/e2 هزارتویی از پوشه‌ها ساخته شده. ابزارِ مناسب "
                       "نصب کنید تا یک‌نگاهی تهِ جنگل را ببینید؛ پرچم در عمیق‌ترین برگ است.",
        "hint": "apt install tree  بعد  tree /opt/lab/e2 — فایل انتهایی عمیق‌ترین مسیر",
        "hint_cost": 25,
    },
    {
        "name": "e3-json",
        "title": "داده‌ی رمزی",
        "category": "آسان",
        "points": 150,
        "description": "فایل /opt/lab/data.json یک راز دارد؛ اما خودش را ساده لوحانه "
                       "لو نمی‌دهد. ابزارِ پرس‌وجوی JSON را نصب کنید و «secret» را "
                       "کدگشایی کنید (راهنمایی: base64).",
        "hint": "apt install jq  بعد  jq -r .secret /opt/lab/data.json | base64 -d",
        "hint_cost": 25,
    },

    # «سخت» — mixed host + box skills
    {
        "name": "h1-lead",
        "title": "کارآگاه",
        "category": "سخت",
        "points": 300,
        "description": "در خانه‌ی میزبان شما (روی سرور، نه آزمایشگاه) پوشه‌ی level5 "
                       "یک سرنخ بسته‌بندی‌شده دارد. آن را باز کنید؛ بقیه‌ی ماجرا در "
                       "گزارشِ ساعت ۰۳:۰۰ آزمایشگاه شماست. پرچم = نیمه‌ی اول + نیمه‌ی دوم.",
        "hint": "میزبان: tar xzf level5/lead.tar.gz → نیمه‌ی اول. آزمایشگاه: mybox → grep '03:00' /var/log/lab.log → نیمه‌ی دوم. بچسبانید!",
        "hint_cost": 50,
    },
    {
        "name": "h2-tarhunt",
        "title": "گنج پنهان در بایگانی",
        "category": "سخت",
        "points": 250,
        "description": "در آزمایشگاه، /opt/lab/backup.tar.gz یک بایگانی شلوغ است. "
                       "چند فایل «گنج‌نما» دارد؛ فقط یکی پرچم واقعی دارد — و اسمش "
                       "با نقطه شروع می‌شود.",
        "hint": "cd /opt/lab && tar xzf backup.tar.gz -C /tmp/h2 && find /tmp/h2 -name '.treasure*' → هرکدام را cat کنید؛ FLAG واقعی را پیدا کنید",
        "hint_cost": 40,
    },
    {
        "name": "h3-shift",
        "title": "شیفت شب",
        "category": "سخت",
        "points": 300,
        "description": "در آزمایشگاه هر دقیقه کاری انجام می‌شود که خروجی‌اش را در "
                       "/tmp می‌گذارد. متنِ خروجی عجیب است... انگار حروفش را جابه‌جا "
                       "کرده‌اند. (راهنمایی: هر حرف ۱۳ پله جلوتر.)",
        "hint": "cat /etc/crontab → job را ببین؛ یک دقیقه صبر کن یا دستی اجرا کن؛ بعد decode با: tr 'A-Za-z' 'N-ZA-Mn-za-m' < /tmp/out.txt",
        "hint_cost": 50,
    },

    # «بسیار سخت» — deep mixed, container-flavored
    {
        "name": "v1-oldsite",
        "title": "سایت قدیمی",
        "category": "بسیار سخت",
        "points": 400,
        "description": "وب‌اپ خاموشی در آزمایشگاه شماست (/opt/lab/old-web) و بایگانی‌ای "
                       "در خانه‌ی میزبان (level5/old-site.tar.gz). سایتِ قدیمی دو نیمه‌ی "
                       "پرچم شما را بین خودش و بایگانی تقسیم کرده. پرچم = نیمه‌ها به هم.",
        "hint": "میزبان: tar xzf level5/old-site.tar.gz → کامنت HTML. آزمایشگاه: python3 /opt/lab/old-web/web.py &  بعد  curl localhost:9999. دو نیمه را بچسبانید.",
        "hint_cost": 60,
    },
    {
        "name": "v2-layers",
        "title": "لایه‌های مدفون",
        "category": "بسیار سخت",
        "points": 400,
        "description": "در آزمایشگاه، /root/buried.tar تصویری داکری است که یک راز را "
                       "داشته و بعد آن را پاک کرده! اجرایش کنید تا قانع شوید چیزی "
                       "نمی‌گوید. اما... لایه‌ها دروغ نمی‌گویند.",
        "hint": "docker load -i /root/buried.tar → docker run flagbox:2 (چیزی نمی‌دهد) → خودِ تصویر را save کنید: docker save flagbox:2 -o /tmp/x.tar → tar xf → در لایه‌ها بگردید (flag حذف‌شده در لایه‌ی قبلی است)",
        "hint_cost": 60,
    },
    {
        "name": "v3-ghost",
        "title": "پاسخ‌گوی شب",
        "category": "بسیار سخت",
        "points": 400,
        "description": "در آزمایشگاه شما خدمتکاری پنهان است: اسکریپتی که خودش را "
                       "خوب جا خوش کرده و پورتِ خودش را هم لو نمی‌دهد... تقریباً. "
                       "کاربر lab یک بار به او سر زده است. پیدایش کنید، روشنش کنید، "
                       "و پورتِ واقعی‌اش را پیدا کنید.",
        "hint": "find / -name '*.py' -path '*lab*' 2>/dev/null → اجرا با: python3 <مسیر> &  بعد: apt install iproute2 && ss -tlnp → curl localhost:<پورت>",
        "hint_cost": 60,
    },
]
