CHALLENGES = [
    # ---------------- mandatory: core classroom skills only ----------------
    {
        "name": "m-welcome",
        "title": "خوش آمدید",
        "category": "اجباری",
        "points": 50,
        "description": "فایل welcome.txt در پوشه‌ی خانه‌ی شماست. آن را با vim باز کنید و پرچم را بخوانید.",
        "hint": "vim welcome.txt — برای خروج بدون ذخیره :q بزنید.",
        "hint_cost": 10,
    },
    {
        "name": "m-readme",
        "title": "خواندن فایل طولانی",
        "category": "اجباری",
        "points": 75,
        "description": "در level1 فایل README.txt خیلی طولانی است؛ پرچم یکی از خط‌های آخر آن پنهان شده است.",
        "hint": "در vim با /FLAG جستجو کنید (n برای بعدی)، یا grep FLAG level1/README.txt",
        "hint_cost": 15,
    },
    {
        "name": "m-manyfiles",
        "title": "کلاف سردرگم",
        "category": "اجباری",
        "points": 75,
        "description": "در level1/lost ده‌ها فایل یکسان‌نما وجود دارد؛ فقط یکی از آن‌ها پرچم را دارد.",
        "hint": "tree level1/lost بزنید و نام متفاوت را پیدا کنید.",
        "hint_cost": 15,
    },
    {
        "name": "m-grep",
        "title": "سوزن در انبار کاه",
        "category": "اجباری",
        "points": 100,
        "description": "فایل level2/server.log صدها خط لاگ دارد. خطی که پرچم در آن است را پیدا کنید.",
        "hint": "grep FLAG level2/server.log",
        "hint_cost": 20,
    },
    {
        "name": "m-maze",
        "title": "هزارتو",
        "category": "اجباری",
        "points": 100,
        "description": "در level2/maze دایرکتوری‌های تودرتو ساخته شده است. فایلی به نام end.flag را پیدا و بخوانید.",
        "hint": "find level2/maze -name end.flag و بعد vim روی مسیر پیدا‌شده.",
        "hint_cost": 20,
    },
    {
        "name": "m-fakeext",
        "title": "ظاهر فریبنده",
        "category": "اجباری",
        "points": 125,
        "description": "فایل level2/photo.jpg آن چیزی نیست که به نظر می‌رسد. آن را با vim باز کنید!",
        "hint": "vim level2/photo.jpg — پسوند فایل همیشه حقیقت را نمی‌گوید.",
        "hint_cost": 25,
    },
    {
        "name": "m-dots",
        "title": "فایل نقطه‌دار",
        "category": "اجباری",
        "points": 100,
        "description": "در level3 فایلی پنهان شده که نامش با نقطه شروع می‌شود و در ls معمولی دیده نمی‌شود. "
                       "پیدا و بخوانیدش.",
        "hint": "find level3 -type f همه‌ی فایل‌ها را نشان می‌دهد (حتی مخفی‌ها)؛ بعد vim کنید.",
        "hint_cost": 20,
    },
    {
        "name": "m-vimedit",
        "title": "پرچم شکسته",
        "category": "اجباری",
        "points": 125,
        "description": "در ctf/fixme.txt پرچم شما به چند تکه شکسته شده است. با vim تکه‌ها را در یک خط "
                       "پشت سر هم بچسبانید (v برای انتخاب، y برای کپی، p برای چسباندن، :w برای ذخیره) "
                       "و همان رشته‌ی کامل را ثبت کنید.",
        "hint": "با v روی حروف بروید تا انتخاب شود، y بزنید، روی مقصد بروید و p بزنید. آخرش :w",
        "hint_cost": 25,
    },

    # ---------------- optional: new skills for fast students ----------------
    {
        "name": "o1-hidden",
        "title": "پوشه‌ی مخفی",
        "category": "اختیاری — پیشرفته",
        "points": 150,
        "description": "در پوشه‌ی خانه‌ی شما دایرکتوری‌ای مخفی شده که با ls دیده نمی‌شود... "
                       "داخلش یک فایل متنی است.",
        "hint": "ls -a فایل‌ها/پوشه‌های نقطه‌دار را هم نشان می‌دهد (چیزی که در کلاس نگفتیم!).",
        "hint_cost": 30,
    },
    {
        "name": "o2-archive",
        "title": "بسته‌ی بسته‌بندی‌شده",
        "category": "اختیاری — پیشرفته",
        "points": 200,
        "description": "فایل level3/backup.tar.gz یک آرشیو فشرده است. بازش کنید و پرچم را داخلش پیدا کنید. "
                       "(tar در کلاس ندیدیم — سرچ کنید!)",
        "hint": "اول tar tzf level3/backup.tar.gz برای فهرست، بعد tar xzf level3/backup.tar.gz برای باز کردن.",
        "hint_cost": 40,
    },
    {
        "name": "o3-regex-class",
        "title": "ریجکس: کلاس‌ها",
        "category": "اختیاری — ریجکس",
        "points": 150,
        "description": "در ctf/regex/decoys.txt ده‌ها پرچم تقلبی هست! پرچم واقعی شکلی دارد که: "
                       "دقیقاً دو حرف کوچک، خط تیره، دقیقاً دو رقم، بعد } — "
                       "مثل FLAG{ab-12}. درس ریجکس: docs.helli-10th-computer.ir/regex.html",
        "hint": "grep -E 'FLAG\\{[a-z]{2}-[0-9]{2}\\}' ctf/regex/decoys.txt",
        "hint_cost": 30,
    },
    {
        "name": "o4-regex-anchor",
        "title": "ریجکس: لنگرها",
        "category": "اختیاری — ریجکس",
        "points": 175,
        "description": "در ctf/regex/anchor.log پرچم روی خطی است که «دقیقاً از ابتدای خط» با err شروع می‌شود؛ "
                       "خطوط دیگری هم err وسط‌شان دارند ولی آن‌ها تله‌اند. درس: docs.helli-10th-computer.ir/regex.html",
        "hint": "grep -E '^err' ctf/regex/anchor.log — علامت ^ یعنی ابتدای خط.",
        "hint_cost": 35,
    },
    {
        "name": "o5-web-source",
        "title": "سورس را ببینید",
        "category": "اختیاری — وب",
        "points": 150,
        "description": "صفحه‌ی about.html را در سایت خودتان باز کنید (پورت اختصاصی‌تان یا username.domain). "
                       "گاهی رازها در HTML پنهان‌اند!",
        "hint": "در مرورگر Ctrl+U را بزنید و دنبال <!-- بگردید.",
        "hint_cost": 30,
    },
    {
        "name": "o6-web-robots",
        "title": "راهنمای ربات‌ها",
        "category": "اختیاری — وب",
        "points": 150,
        "description": "فایل robots.txt در ریشه‌ی سایت خودتان مسیری را لو می‌دهد که قرار است ربات‌ها نبینند...",
        "hint": "آدرس /robots.txt را باز کنید؛ بعد مسیر جلوی Disallow را به انتهای آدرس اضافه کنید.",
        "hint_cost": 30,
    },
]
