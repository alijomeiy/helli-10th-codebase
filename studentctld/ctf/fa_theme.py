#!/usr/bin/env python3
"""Inject Persian RTL + Vazirmatn font + UI translation overlay into CTFd.

Usage: python3 fa_theme.py --url http://127.0.0.1:8000 --token <admin token>
Patches the official `theme_footer` config key; survives container restarts
(stored in DB). Re-runnable.
"""
import argparse

import requests

THEME = """
<link rel="stylesheet"
      href="https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css">
<style>
  body, .navbar, .modal, .btn, input, select, textarea {
    font-family: 'Vazirmatn', Tahoma, 'Segoe UI', sans-serif !important;
  }
  body { direction: rtl; text-align: right; }
  /* keep technical content LTR */
  code, pre, .flag-input, input[type="text"], input[type="password"],
  input[type="email"], .form-control {
    direction: ltr; text-align: left; unicode-bidi: plaintext;
  }
  .navbar-nav { padding-right: 0; }
  td, th { text-align: right; }
</style>
<script>
(function(){
  // real RTL for the whole document
  document.documentElement.setAttribute('dir', 'rtl');
  document.documentElement.setAttribute('lang', 'fa');

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
  function trNode(n){
    var k = n.nodeValue.trim();
    if (TR[k]) n.nodeValue = n.nodeValue.replace(k, TR[k]);
  }
  function walk(root){
    var w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null, false);
    while (w.nextNode()) trNode(w.currentNode);
  }
  function run(){
    document.documentElement.setAttribute('dir','rtl');
    walk(document.body);
  }
  if (document.readyState === 'loading')
    document.addEventListener('DOMContentLoaded', run);
  else run();
  new MutationObserver(function(){ run(); }).observe(
    document.body, {childList:true, subtree:true, characterData:true});
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
    ok_font = "Vazirmatn-font-face.css" in r.text
    ok_tr = "جدول امتیازات" in r.text
    print("font link present:", ok_font, "| translations present:", ok_tr)


if __name__ == "__main__":
    main()
