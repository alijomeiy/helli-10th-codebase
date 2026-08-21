#!/usr/bin/env python3
"""Inject Persian RTL + Vazirmatn font + UI translation overlay into CTFd.

Usage: python3 fa_theme.py --url http://127.0.0.1:8000 --token <admin token>
Patches the official `theme_footer` config key; survives container restarts
(stored in DB). Re-runnable.

Design notes (v2):
- Let dir="rtl" flip layout natively (flexbox/tables auto-flip) instead of
  forcing text-align on cells — that fighting caused the "awkward" v1 look.
- Vazirmatn only on text elements; leave icon fonts and code alone.
- Only code-ish inputs stay LTR; everything else follows RTL.
- Panel-matching dark-friendly rules kept minimal.
"""
import argparse

import requests

THEME = """
<link rel="preconnect" href="https://cdn.jsdelivr.net">
<link rel="stylesheet"
      href="https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css">
<style>
  /* ---- font: body + text elements only (icons/code untouched) ---- */
  body, h1, h2, h3, h4, h5, h6, p, span, a, label, th, td, li,
  small, strong, em, button, .btn, .navbar-brand, .nav-link, .badge,
  .card-title, .modal-title, .modal-body, .form-check-label,
  .dropdown-item, .alert, .text-muted {
    font-family: 'Vazirmatn', Tahoma, 'Segoe UI', sans-serif;
  }

  /* ---- RTL: let the browser mirror; only fix what it can't ---- */
  html[dir="rtl"] body { direction: rtl; text-align: right; }

  /* keep code/flags/technical content LTR and readable */
  code, pre, kbd, samp {
    direction: ltr; text-align: left; unicode-bidi: isolate;
    font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  }
  /* code-like form fields (flag submission, usernames, emails) */
  input[type="password"], input[type="email"], textarea {
    direction: ltr; text-align: left;
  }
  input[type="text"] {
    direction: ltr; text-align: left; unicode-bidi: plaintext;
  }

  /* dropdown menus open anchored correctly under RTL nav */
  .dropdown-menu { text-align: right; }

  /* modals: keep dialog box sane, close button reachable */
  .modal-content { text-align: right; }

  /* Vazirmatn renders slightly taller — avoid clipped headings */
  h1, h2, h3, .card-title { line-height: 1.6; }
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
  }
  if (document.readyState === 'loading')
    document.addEventListener('DOMContentLoaded', run);
  else run();
  /* debounce: one pass per burst of DOM changes, not one per mutation */
  new MutationObserver(function(){
    if (pending) return;
    pending = true;
    requestAnimationFrame(function(){ pending = false; run(); });
  }).observe(document.body, {childList:true, subtree:true});
})();
</script>
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:8000")
    ap.add_argument("--token", required=True)
    args = ap.parse_args()

    h = {"Authorization": f"Token {args.token}",
         "Content-Type": "application/json"}
    r = requests.patch(f"{args.url}/api/v1/configs", headers=h,
                       json={"theme_footer": THEME}, timeout=15)
    print("patch theme_footer:", r.status_code)

    r = requests.get(f"{args.url}/", timeout=15)
    print("font link present:", "Vazirmatn-font-face.css" in r.text,
          "| translations present:", "جدول امتیازات" in r.text)


if __name__ == "__main__":
    main()
