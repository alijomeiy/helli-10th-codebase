CHALLENGES = [
    # ---------------- mandatory: core classroom skills only ----------------
    # descriptions NEVER say how to solve — only what/where. Hints (paid) may.
    {
        "name": "m-welcome",
        "title": "خوش آمدید",
        "category": "اجباری",
        "points": 50,
        "description": "پرچم اول، ساده‌تر از آن است که فکر می‌کنید. سراغ پوشه‌ی خانه‌ی خودتان بروید.",
        "hint": "فایل welcome.txt را با vim باز کنید: vim welcome.txt",
        "hint_cost": 10,
    },
    {
        "name": "m-readme",
        "title": "خواندن فایل طولانی",
        "category": "اجباری",
        "points": 75,
        "description": "در سطح اول، فایلی خیلی طولانی منتظر شماست. پرچم تهِ آن پنهان شده.",
        "hint": "در vim با /FLAG جستجو کنید (n برای بعدی)، یا grep FLAG level1/README.txt",
        "hint_cost": 15,
    },
    {
        "name": "m-manyfiles",
        "title": "کلاف سردرگم",
        "category": "اجباری",
        "points": 75,
        "description": "در میان انبوهی از فایل‌های یکسان‌نما، فقط یکی حقیقت را می‌گوید.",
        "hint": "tree level1/lost بزنید و نام متفاوت را پیدا کنید.",
        "hint_cost": 15,
    },
    {
        "name": "m-grep",
        "title": "سوزن در انبار کاه",
        "category": "اجباری",
        "points": 100,
        "description": "سرور هزاران اتفاق را ثبت کرده است. یکی از آن‌ها برای شما مهم است.",
        "hint": "grep FLAG level2/server.log",
        "hint_cost": 20,
    },
    {
        "name": "m-maze",
        "title": "هزارتو",
        "category": "اجباری",
        "points": 100,
        "description": "در عمقِ هزارتویی از پوشه‌ها، انتها در انتظار شماست.",
        "hint": "find level2/maze -name end.flag و بعد vim روی مسیر پیدا‌شده.",
        "hint_cost": 20,
    },
    {
        "name": "m-fakeext",
        "title": "ظاهر فریبنده",
        "category": "اجباری",
        "points": 125,
        "description": "چیزی که می‌بینید، همیشه چیزی نیست که هست. به پسوند فایل‌ها اعتماد نکنید.",
        "hint": "vim level2/photo.jpg — پسوند فایل همیشه حقیقت را نمی‌گوید.",
        "hint_cost": 25,
    },
    {
        "name": "m-dots",
        "title": "فایل نقطه‌دار",
        "category": "اجباری",
        "points": 100,
        "description": "در سطح سوم چیزی پنهان شده که چشمِ معمولی آن را نمی‌بیند. "
                       "کاربر قبلی ردپایی جا گذاشته است.",
        "hint": "find level3 -type f همه‌ی فایل‌ها را نشان می‌دهد (حتی مخفی‌ها)؛ بعد vim کنید.",
        "hint_cost": 20,
    },
    {
        "name": "m-vimedit",
        "title": "پرچم شکسته",
        "category": "اجباری",
        "points": 125,
        "description": "پرچم شما در Pieces شکسته و پراکنده شده است. تکه‌ها را به هم برسانید و "
                       "رشته‌ی کامل را در همان فایل ذخیره کنید. سپس همان رشته را اینجا ثبت کنید.",
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
]
