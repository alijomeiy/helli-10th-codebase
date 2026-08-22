#!/usr/bin/env python3
"""v5: logo uploaded via CTFd files API (served from /assets), text-only
navbar brand, tidy right-side nav items.

Fixes vs v4:
- data-URI hit CTFd's 64KB config limit; logo now uploaded through the
  official files API and referenced by its served URL.
- Navbar brand is plain text; homepage <img> swapped to the uploaded logo.
"""
import argparse

import requests

CTF_NAME = "پیدا کردن پرچم - گروه کامپیوتر دبیرستان حلی تهران"


def build_theme() -> str:
    return f"""
<link rel="preconnect" href="https://cdn.jsdelivr.net">
<link rel="stylesheet"
      href="https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css">
<style>
  body, h1, h2, h3, h4, h5, h6, p, span, a, label, th, td, li,
  small, strong, em, button, .btn, .navbar-brand, .nav-link, .badge,
  .card-title, .modal-title, .modal-body, .form-check-label,
  .dropdown-item, .alert, .text-muted {{
    font-family: 'Vazirmatn', Tahoma, 'Segoe UI', sans-serif;
  }}

  html[dir="rtl"] body {{ direction: rtl; text-align: right; }}

  code, pre, kbd, samp {{
    direction: ltr; text-align: left; unicode-bidi: isolate;
    font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  }}
  input[type="password"], input[type="email"], textarea {{
    direction: ltr; text-align: left;
  }}
  input[type="text"] {{ direction: ltr; text-align: left; unicode-bidi: plaintext; }}

  .dropdown-menu {{ text-align: right; }}
  .modal-content {{ text-align: right; }}
  h1, h2, h3, .card-title {{ line-height: 1.6; }}

  /* ---- homepage: remove big CTFd logo + ctfd.io marketing block ---- */
  img.w-100.mx-auto.d-block[src*="logo"] {{ display: none; }}
  .navbar-brand img {{ display: none; }}

  /* ---- navbar right side: even spacing ---- */
  .navbar-nav.ml-md-auto .nav-link {{
    display: inline-flex; align-items: center; gap: 5px;
    white-space: nowrap; padding: .45rem .55rem; line-height: 1.4;
  }}
  .navbar-nav.ml-md-auto {{ gap: 2px; }}
</style>
<script>
(function(){{
  var TR = {{
    'Challenges':'چالش‌ها','Scoreboard':'جدول امتیازات','Teams':'تیم‌ها','Users':'کاربران',
    'Login':'ورود','Register':'ثبت‌نام','Logout':'خروج','Profile':'پروفایل','Settings':'تنظیمات',
    'Submit':'ثبت پاسخ','Hint':'راهنما','Unlock Hint':'نمایش راهنما','Solved':'حل‌شده',
    'Value':'امتیاز','Points':'امتیاز','Correct':'درست! آفرین','Incorrect':'پاسخ نادرست است',
    'Already Solved':'قبلاً حل شده','Time':'زمان','Date':'تاریخ','Team':'تیم','User':'کاربر',
    'Stats':'آمار','Forgot your password?':'فراموشی رمز؟',
    'User Name or Email':'نام کاربری یا رایانامه','Password':'رمز عبور','Email':'رایانامه',
    'Name':'نام','Confirm Password':'تکرار رمز','Create Account':'ساخت حساب','Search':'جستجو',
    'Notifications':'اطلاع‌رسانی‌ها','Rules':'قوانین','Edit':'ویرایش','Save':'ذخیره',
    'Next':'بعدی','Previous':'قبلی','Create Team':'ساخت تیم','Join Team':'پیوستن به تیم',
    'Team Name':'نام تیم','Website':'وب‌سایت','Country':'کشور','Affiliation':'مدرسه',
    'Show':'نمایش','Hide':'مخفی','Submissions':'پاسخ‌ها','Awards':'جوایز','Account':'حساب',
    'Member':'عضو','Captain':'سرتیم','Rank':'رتبه','Score':'امتیاز','Solves':'حل‌کنندگان',
    'Author':'طراح','Challenge':'چالش','Tags':'برچسب‌ها','Files':'فایل‌ها','Type':'نوع',
    'Posted':'منتشرشده','Overall':'مجموع','General':'عمومی','Theme':'پوسته',
    'Current Password':'رمز فعلی','New Password':'رمز جدید','Delete':'حذف','Update':'به‌روزرسانی',
    'Cancel':'لغو','Close':'بستن','Loading':'در حال بارگذاری...','Error':'خطا',
    'Total':'مجموع','Hidden':'مخفی','Banned':'مسدود','Team Captain':'سرتیم',
    /* --- buttons & popup texts --- */
    'View':'مشاهده','View Challenge':'دیدن چالش','Submit Flag':'ثبت پرچم',
    'Flag':'پرچم','Enter Flag':'پرچم را وارد کنید','Your flag':'پرچم شما',
    'Unlock':'باز کردن','Locked':'قفل‌شده','Unlocked':'باز شد',
    'Are you sure?':'مطمئنید؟','Confirm':'تأیید','Yes':'بله','No':'خیر',
    'Max Attempts':'حداکثر تلاش','Attempts':'تلاش‌ها','Attempt':'تلاش',
    'Incorrect. Please try again.':'نادرست است. دوباره تلاش کنید.',
    'Correct!':'درست! آفرین','You solved the challenge!':'چالش را حل کردید!',
    'Congratulations!':'آفرین! تبریک!',
    'This challenge is unresolved by you':'شما هنوز این چالش را حل نکرده‌اید',
    'Mark as solved':'علامت‌گذاری حل‌شده','Unmark':'برداشتن علامت',
    'Hide solved challenges':'پنهان‌کردن چالش‌های حل‌شده',
    'Show solved challenges':'نمایش چالش‌های حل‌شده',
    'Search Challenges':'جستجوی چالش‌ها','Filter':'فیلتر','Reset':'بازنشانی',
    'Clear':'پاک‌کردن','Copy':'کپی','Copied!':'کپی شد!',
    'Home':'خانه','Back':'بازگشت','Menu':'منو',
    'Welcome':'خوش آمدید','Welcome Back':'خوش برگشتید',
    'Please log in to continue':'برای ادامه وارد شوید',
    'Need an account?':'حساب ندارید؟','Register here':'اینجا ثبت‌نام کنید',
    'Incorrect credentials':'اطلاعات ورود نادرست است',
    'You have been logged out':'از حساب خارج شدید',
    'Rate limited':'درخواست‌های شما زیاد است؛ کمی صبر کنید',
    'Too many attempts':'تلاش‌های شما زیاد است',
    'An error occurred':'خطایی رخ داد','Try again later':'بعداً دوباره تلاش کنید',
    'Solve':'حل','Unsolve':'لغو حل','Solver':'حل‌کننده',
    'Progress':'پیشرفت','Activity':'فعالیت',
    'Top 10':'۱۰ نفر برتر','Me':'من','Graph':'نمودار','Distribution':'توزیع'
  }};
  function trNode(n){{
    var k = n.nodeValue.trim();
    if (TR[k]) n.nodeValue = n.nodeValue.replace(k, TR[k]);
  }}
  function run(){{
    document.documentElement.setAttribute('dir','rtl');
    document.documentElement.setAttribute('lang','fa');
    var w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, null, false);
    while (w.nextNode()) trNode(w.currentNode);

    /* translate placeholder attributes (form hints) */
    var PH = {{
      'Enter flag':'پرچم را وارد کنید','Flag':'پرچم','Username':'نام کاربری',
      'Password':'رمز عبور','Email':'رایانامه','Search':'جستجو',
      'User Name or Email':'نام کاربری یا رایانامه','Team Name':'نام تیم',
      'New Password':'رمز جدید','Confirm Password':'تکرار رمز'
    }};
    (document.querySelectorAll('input[placeholder],textarea[placeholder]') || []).forEach(function(el){{
      var p = el.getAttribute('placeholder');
      if (PH[p]) el.setAttribute('placeholder', PH[p]);
    }});

    /* translate title attributes (tooltips) */
    (document.querySelectorAll('[title]') || []).forEach(function(el){{
      var t = el.getAttribute('title');
      if (TR[t]) el.setAttribute('title', TR[t]);
    }});

    /* homepage: remove the ctfd.io marketing block + setup link —
       walk from <p> text up to the heading that wraps it */
    (document.querySelectorAll('p, a') || []).forEach(function(el){{
      var t = el.textContent || '';
      if (/A cool CTF platform|Follow us on social|to login and setup your CTF/i.test(t)) {{
        var kill = el.closest('h3, h4, .row, .col-md-6') || el.parentElement;
        if (kill) kill.remove();
      }}
    }});
  }}
  if (document.readyState === 'loading')
    document.addEventListener('DOMContentLoaded', run);
  else run();
  var pending = false;
  new MutationObserver(function(){{
    if (pending) return;
    pending = true;
    requestAnimationFrame(function(){{ pending = false; run(); }});
  }}).observe(document.body, {{childList:true, subtree:true}});
}})();
</script>
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:8000")
    ap.add_argument("--token", required=True)
    args = ap.parse_args()

    theme = build_theme()
    h = {"Authorization": f"Token {args.token}",
         "Content-Type": "application/json"}
    for key, val in [("theme_footer", theme),
                     ("ctf_name", CTF_NAME),
                     # empty = CTFd default logo; manage it from the admin
                     # panel (Admin > Config > Theme > Logo) if wanted
                     ("ctf_logo", "")]:
        r = requests.patch(f"{args.url}/api/v1/configs", headers=h,
                           json={key: val}, timeout=15)
        print(f"patch {key}:", r.status_code)

    r = requests.get(f"{args.url}/", timeout=15)
    print("default logo restored:", "logo.png" in r.text,
          "| name ok:", "پیدا کردن پرچم" in r.text)


if __name__ == "__main__":
    main()
