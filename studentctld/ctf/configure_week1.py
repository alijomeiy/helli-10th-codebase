import sys
sys.path.append("/opt/CTFd")
from CTFd import create_app
from CTFd.models import Challenges, Hints, db
from CTFd.cache import cache

app = create_app()
with app.app_context():
    easy_ids = [40, 41, 42]
    hard_ids = [43, 44, 45, 46, 47]
    active_ids = easy_ids + hard_ids

    # 1. Update states and categories
    all_challs = Challenges.query.all()
    for c in all_challs:
        if c.id in easy_ids:
            c.state = 'visible'
            c.category = 'چالش‌های هفته اول — آسان'
        elif c.id in hard_ids:
            c.state = 'visible'
            c.category = 'چالش‌های هفته اول — سخت'
        else:
            c.state = 'hidden'

    # 2. Detailed configurations for EASY challenges
    c40 = Challenges.query.get(40)
    c40.name = "01 — خوش آمدید (ls & cat)"
    c40.value = 50
    c40.description = (
        "فایل `welcome.txt` در پوشه‌ی خانه‌ی شما (`~`) پرچم اول را نگه داشته است.\n\n"
        "با دستورهای پایه‌ای مانند `ls` (مشاهده فایل‌ها) و `cat` (نمایش محتوا) پرچم را بخوانید و ثبت کنید."
    )

    c41 = Challenges.query.get(41)
    c41.name = "02 — خواندن فایل طولانی (cd & tail/cat)"
    c41.value = 75
    c41.description = (
        "در پوشه‌ی `level1` فایل `README.txt` متنی طولانی دارد و پرچم در انتهای آن پنهان شده است.\n\n"
        "با دستور `cd level1` وارد پوشه شوید و با دستورهایی مانند `tail`، `cat`، `less` یا `grep` پرچم را در انتهای فایل بیابید."
    )

    c42 = Challenges.query.get(42)
    c42.name = "03 — کلاف سردرگم (ls -la & cat)"
    c42.value = 75
    c42.description = (
        "در پوشه‌ی `level1/lost` ده‌ها فایل یکسان‌نما وجود دارند، اما یکی از آن‌ها متفاوت است و پرچم را در خود دارد!\n\n"
        "با دستورهای `cd level1/lost` و `ls -la` یا `ls -lh` فایل‌ها را مقایسه کنید، فایل متمایز را پیدا کنید و با `cat` محتوای آن را بخوانید."
    )

    # 3. Detailed configurations for HARD challenges
    c43 = Challenges.query.get(43)
    c43.name = "04 — سوزن در انبار کاه (grep در فایل‌های بزرگ)"
    c43.value = 100
    c43.description = (
        "فایل `level2/server.log` صدها خط گزارش دارد و پیدا کردن دستی پرچم غیرممکن است!\n\n"
        "با دستور `grep` کلمه‌ی کلیدی `FLAG` را داخل این فایل جستجو کنید تا خط حامل پرچم پیدا شود."
    )

    c44 = Challenges.query.get(44)
    c44.name = "05 — هزارتو (find و پوشه‌های تودرتو)"
    c44.value = 125
    c44.description = (
        "در پوشه‌ی `level2/maze` پوشه‌های تودرتو و عمیقی ساخته شده است. فایلی به نام `end.flag` در یکی از این پوشه‌هاست.\n\n"
        "با دستور `find` یا پیمایش با `cd` و `ls` این فایل را پیدا کنید و محتوای آن را ببینید."
    )

    c45 = Challenges.query.get(45)
    c45.name = "06 — ظاهر فریبنده (تشخیص نوع فایل با file)"
    c45.value = 125
    c45.description = (
        "فایل `level2/photo.jpg` به ظاهر یک تصویر است، اما پسوند فایل‌ها در لینوکس همیشه حقیقت را نمی‌گوید!\n\n"
        "با دستور `file` نوع واقعی فایل را بررسی کنید و اگر متنی است، با `cat` محتوای پرچم را بخوانید."
    )

    c46 = Challenges.query.get(46)
    c46.name = "07 — فایل نقطه‌دار (فایل‌های مخفی با ls -a)"
    c46.value = 125
    c46.description = (
        "در پوشه‌ی `level3` فایلی پنهان شده که نامش با نقطه (`.`) شروع می‌شود و در دستور معمولی `ls` نمایش داده نمی‌شود.\n\n"
        "از سوییچ نمایش فایل‌های مخفی در دستور `ls` استفاده کنید و محتوای فایل را بخوانید."
    )

    c47 = Challenges.query.get(47)
    c47.name = "08 — پرچم شکسته (ترکیب و ویرایش تکه‌ها)"
    c47.value = 150
    c47.description = (
        "در فایل `ctf/fixme.txt` پرچم شما به ۴ تکه شکسته شده است!\n\n"
        "تکه‌ها را به ترتیب شماره پشت سر هم قرار دهید و عبارت کامل پرچم (با فرمت `FLAG{...}`) را ثبت کنید."
    )

    # 4. Hints setup
    hints_map = {
        40: "دستور cat welcome.txt را در ترمینال بزنید تا محتوای فایل چاپ شود.",
        41: "دستور cd level1 و سپس tail -n 20 README.txt را اجرا کنید. همچنین grep FLAG README.txt هم کار می‌کند.",
        42: "دستور ls -la level1/lost را اجرا کنید. حجم یکی از فایل‌ها با بقیه فرق دارد! آن را با cat بخوانید.",
        43: "دستور grep FLAG level2/server.log را اجرا کنید تا مستقیماً خط پرچم فیلتر و چاپ شود.",
        44: "دستور find level2/maze -name 'end.flag' را بزنید، مسیر فایل ظاهر می‌شود؛ سپس با cat آن مسیر را چاپ کنید.",
        45: "دستور file level2/photo.jpg نشان می‌دهد که این در واقع یک فایل متنی است! با cat level2/photo.jpg بخوانیدش.",
        46: "دستور ls -la level3 یا ls -a level3 را بزنید تا فایل‌های شروع‌شونده با نقطه را ببینید، سپس با cat آن را بخوانید.",
        47: "فایل ctf/fixme.txt را بخوانید و تکه‌های ۱ تا ۴ را پشت سر هم در یک خط به هم بچسبانید."
    }

    for cid, hint_text in hints_map.items():
        h = Hints.query.filter_by(challenge_id=cid).first()
        if h:
            h.content = hint_text
            h.cost = 0
        else:
            new_h = Hints(challenge_id=cid, content=hint_text, cost=0)
            db.session.add(new_h)

    db.session.commit()
    cache.clear()

    print("Challenges successfully updated!")
    vis = Challenges.query.filter_by(state='visible').order_by(Challenges.id).all()
    print(f"Total visible challenges: {len(vis)}")
    for v in vis:
        print(f"  [ID {v.id}] Cat='{v.category}' | Pts={v.value:3d} | Name='{v.name}'")
