CHALLENGES = [
    {
        "name": "l1-hidden",
        "title": "فایل مخفی",
        "category": "لینوکس ۱",
        "points": 100,
        "description": "در پوشه‌ی خانه‌ی کاربری تیم‌تان فایلی مخفی شده است. "
                       "فایل‌های مخفی در لینوکس با نقطه شروع می‌شوند و در ls معمولی دیده نمی‌شوند!",
        "hint": "دستور ls -a را امتحان کنید و به دنبال پوشه‌ی .level1 بگردید.",
        "hint_cost": 20,
    },
    {
        "name": "l1-readme",
        "title": "خواندن فایل طولانی",
        "category": "لینوکس ۱",
        "points": 100,
        "description": "در پوشه‌ی level1 فایل README.txt خیلی طولانی است. "
                       "پرچم یکی از خط‌های آخر آن پنهان شده است.",
        "hint": "در vim با تایپ :38 به خط ۳۸ بپرید، یا grep FLAG README.txt را امتحان کنید.",
        "hint_cost": 20,
    },
    {
        "name": "l1-manyfiles",
        "title": "کلاف سردرگم",
        "category": "لینوکس ۱",
        "points": 100,
        "description": "در level1/lost ده‌ها فایل یکسان‌نما وجود دارد؛ فقط یکی از آن‌ها پرچم را دارد.",
        "hint": "ls level1/lost کنید و دنبال نامی متفاوت از بقیه بگردید (یا grep -r FLAG بزنید).",
        "hint_cost": 20,
    },
    {
        "name": "l2-grep",
        "title": "سوزن در انبار کاه",
        "category": "لینوکس ۲",
        "points": 150,
        "description": "فایل level2/server.log صدها خط لاگ سرور دارد. "
                       "خطی که پرچم در آن است را پیدا کنید.",
        "hint": "grep FLAG level2/server.log",
        "hint_cost": 30,
    },
    {
        "name": "l2-maze",
        "title": "هزارتو",
        "category": "لینوکس ۲",
        "points": 150,
        "description": "در level2/maze دایرکتوری‌های تودرتو و تصادفی ساخته شده است. "
                       "فایلی به نام end.flag را پیدا و بخوانید.",
        "hint": "find level2/maze -name 'end.flag'",
        "hint_cost": 30,
    },
    {
        "name": "l2-ext",
        "title": "ظاهر فریبنده",
        "category": "لینوکس ۲",
        "points": 150,
        "description": "فایل level2/photo.jpg آن چیزی نیست که به نظر می‌رسد. "
                       "پسوند فایل‌ها همیشه حقیقت را نمی‌گوید!",
        "hint": "با cat level2/photo.jpg آن را به‌عنوان متن بخوانید (یا دستور file را امتحان کنید).",
        "hint_cost": 30,
    },
    {
        "name": "l3-history",
        "title": "ردپای کاربر قبلی",
        "category": "لینوکس ۳",
        "points": 200,
        "description": "کاربر قبلیِ این حساب جایی تاریخچه‌ی دستورهایش را جا گذاشته است. "
                       "پرچم در آن تاریخچه پنهان شده است.",
        "hint": "ls -la level3 بزنید؛ فایل .old_history را با grep یا vim بخوانید.",
        "hint_cost": 40,
    },
    {
        "name": "l3-archive",
        "title": "بسته‌ی بسته‌بندی‌شده",
        "category": "لینوکس ۳",
        "points": 250,
        "description": "فایل level3/backup.tar.gz یک آرشیو فشرده است. "
                       "آن را باز کنید و پرچم را داخلش پیدا کنید.",
        "hint": "اول tar tzf level3/backup.tar.gz تا فهرست را ببینید، بعد tar xzf تا باز کنید.",
        "hint_cost": 40,
    },
    {
        "name": "web-source",
        "title": "سورس را ببینید",
        "category": "وب",
        "points": 150,
        "description": "صفحه‌ی about.html را در سایت خودتان باز کنید "
                       "(پورت اختصاصی حساب لینوکسی‌تان یا آدرس username.domain). "
                       "گاهی رازها در HTML پنهان‌اند!",
        "hint": "در مرورگر Ctrl+U را بزنید تا سورس صفحه را ببینید و دنبال <!-- بگردید.",
        "hint_cost": 30,
    },
    {
        "name": "web-robots",
        "title": "راهنمای ربات‌ها",
        "category": "وب",
        "points": 150,
        "description": "فایل robots.txt در ریشه‌ی سایت خودتان، مسیری را لو می‌دهد "
                       "که قرار است ربات‌ها نبینند... اما شما می‌توانید!",
        "hint": "آدرس /robots.txt را باز کنید، بعد مسیر جلوی Disallow را به انتهای آدرس سایت اضافه کنید.",
        "hint_cost": 30,
    },
]
