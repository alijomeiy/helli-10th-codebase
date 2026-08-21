#!/usr/bin/env python3
"""v3: Helli logo (centered), custom homepage, fixed navbar icons.

- Logo: https://www.helli.ir/portal/sites/all/themes/helli/image/Logo1.png
  CTFd config key `ctf_logo` (URL) — used by theme where logo belongs,
  plus homepage override below shows it big and centered.
- Homepage: default "A cool CTF platform from ctfd.io..." junk replaced by
  a clean Persian landing (config key `ctf_theme_config` JSON? no — CTFd
  homepage comes from theme; we override the marketing block via footer
  CSS/JS since the setup page shows only when setup is incomplete).
- Navbar settings/profile/notification icons: core-beta uses plain text
  links on small screens and awkward icons on some; we normalize with
  spacing + hide redundant icon-only elements that overlap in RTL.
"""
import argparse

import requests

THEME = """
<link rel="preconnect" href="https://cdn.jsdelivr.net">
<link rel="preconnect" href="https://www.helli.ir">
<link rel="stylesheet"
      href="https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css">
<script>var HELLI_LOGO = "https://www.helli.ir/portal/sites/all/themes/helli/image/Logo1.png";</script>
<style>
  /* ---- font: body + text elements only (icons/code untouched) ---- */
  body, h1, h2, h3, h4, h5, h6, p, span, a, label, th, td, li,
  small, strong, em, button, .btn, .navbar-brand, .nav-link, .badge,
  .card-title, .modal-title, .modal-body, .form-check-label,
  .dropdown-item, .alert, .text-muted {
    font-family: 'Vazirmatn', Tahoma, 'Segoe UI', sans-serif;
  }

  /* ---- RTL ---- */
  html[dir="rtl"] body { direction: rtl; text-align: right; }

  code, pre, kbd, samp {
    direction: ltr; text-align: left; unicode-bidi: isolate;
    font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  }
  input[type="password"], input[type="email"], textarea {
    direction: ltr; text-align: left;
  }
  input[type="text"] { direction: ltr; text-align: left; unicode-bidi: plaintext; }

  .dropdown-menu { text-align: right; }
  .modal-content { text-align: right; }
  h1, h2, h3, .card-title { line-height: 1.6; }

  /* ---- homepage logo: big + centered ---- */
  img[src*="helli.ir"], .ctf-logo {
    display: block;
    margin-left: auto;
    margin-right: auto;
  }
  /* CTFd core theme homepage logo block */
  .main-img, img.w-100.mx-auto.d-block { margin: 0 auto; }

  /* ---- navbar: brand logo small, right-aligned in RTL ---- */
  .navbar-brand img { height: 40px; width: auto; }

  /* ---- navbar right side: even spacing for profile/settings/notif icons ---- */
  .navbar-nav.ml-md-auto { gap: 4px; }
  .navbar-nav.ml-md-auto .nav-item { margin-left: 2px; margin-right: 2px; }
  .navbar-nav.ml-md-auto .nav-link {
    display: inline-flex; align-items: center; gap: 6px;
    white-space: nowrap; padding: .5rem .6rem;
  }
  /* icon-only links (bell / gear) get labels so they aren't cryptic blobs */
  .navbar .fa-bell::after { content: 'اطلاع‌رسانی'; font-size: 13px; }
  .navbar .fa-cog::after   { content: 'تنظیمات';   font-size: 13px; }
  .navbar .fa-user::after  { content: 'پروفایل';  font-size: 13px; }
  .navbar .fa-sign-out-alt::after { content: 'خروج'; font-size: 13px; }
  @media (max-width: 768px) {
    .navbar .fa-bell::after, .navbar .fa-cog::after,
    .navbar .fa-user::after, .navbar .fa-sign-out-alt::after { display: none; }
  }
</style>
<script>
(function(){
  var TR = {
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
    'Total':'مجموع','Hidden':'مخفی','Banned':'مسدود','Team Captain':'سرتیم'
  };
  var pending = false;
  function trNode(n){
    var k = n.nodeValue.trim();
    if (TR[k]) n.nodeValue = n.nodeValue.replace(k, TR[k]);
  }
  function run(){
    document.documentElement.setAttribute('dir','rtl');
    document.documentElement.setAttribute('lang','fa');
    var w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, null, false);
    while (w.nextNode()) trNode(w.currentNode);
    /* homepage cleanup: strip ctfd.io marketing block if present */
    var main = document.querySelector('.jumbotron, main.container .row');
    (document.querySelectorAll('h3.text-center, h4.text-center') || []).forEach(function(h){
      if (/ctfd\\.io|Follow us on social|setup your CTF/i.test(h.textContent)) h.remove();
    });
    /* swap big homepage logo -> helli logo, centered */
    (document.querySelectorAll('img.w-100.mx-auto.d-block, img[src*="logo.png"]') || []).forEach(function(img){
      if (img.src.indexOf('helli.ir') === -1) {
        img.src = HELLI_LOGO;
        img.style.maxWidth = '360px';
        img.style.padding = '24px';
        img.style.paddingTop = '8vh';
      }
    });
  }
  if (document.readyState === 'loading')
    document.addEventListener('DOMContentLoaded', run);
  else run();
  var pending2 = false;
  new MutationObserver(function(){
    if (pending2) return;
    pending2 = true;
    requestAnimationFrame(function(){ pending2 = false; run(); });
  }).observe(document.body, {childList:true, subtree:true});
})();
</script>
"""

LOGO_URL = "https://www.helli.ir/portal/sites/all/themes/helli/image/Logo1.png"
CTF_NAME = "پیدا کردن پرچم - گروه کامپیوتر دبیرستان حلی تهران"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:8000")
    ap.add_argument("--token", required=True)
    args = ap.parse_args()

    h = {"Authorization": f"Token {args.token}",
         "Content-Type": "application/json"}

    for key, val in [
        ("theme_footer", THEME),
        ("ctf_name", CTF_NAME),
        ("ctf_logo", LOGO_URL),
    ]:
        r = requests.patch(f"{args.url}/api/v1/configs", headers=h,
                           json={key: val}, timeout=15)
        print(f"patch {key}:", r.status_code)

    r = requests.get(f"{args.url}/", timeout=15)
    print("logo:", LOGO_URL in r.text,
          "| name:", "پیدا کردن پرچم" in r.text,
          "| marketing removed by JS at runtime")


if __name__ == "__main__":
    main()
