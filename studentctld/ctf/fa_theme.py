#!/usr/bin/env python3
"""v4: data-URI Helli logo on homepage (left of nothing — centered),
text-only navbar brand, tidy right-side nav items.

Fixes vs v3:
- ctf_logo config cleared (CTFd proxied the external URL through /files/
  and broke the image). Logo now embedded as data-URI in the footer and
  swapped into the homepage <img> by JS — zero external deps.
- Navbar brand is plain text again; the ::after labels on icons removed
  (they caused crowding); right nav items get clean inline-flex spacing.
"""
import argparse
import base64
import os
import tempfile

import requests

LOGO_URL = "https://www.helli.ir/portal/sites/all/themes/helli/image/Logo1.png"
CTF_NAME = "پیدا کردن پرچم - گروه کامپیوتر دبیرستان حلی تهران"


def build_theme(logo_b64: str) -> str:
    return f"""
<link rel="preconnect" href="https://cdn.jsdelivr.net">
<link rel="stylesheet"
      href="https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css">
<script>var HELLI_LOGO = "data:image/png;base64,{logo_b64}";</script>
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

  /* ---- homepage logo (set by JS to data-URI): centered ---- */
  img.helli-main-logo {{
    display: block; margin: 0 auto;
    max-width: 320px; width: 100%;
    padding: 40px 0 10px;
  }}

  /* ---- navbar: text-only brand, clean spacing ---- */
  .navbar-brand img {{ display: none; }}
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
    'Total':'مجموع','Hidden':'مخفی','Banned':'مسدود','Team Captain':'سرتیم'
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

    /* homepage: strip marketing, swap logo */
    (document.querySelectorAll('h3.text-center, h4.text-center') || []).forEach(function(h){{
      if (/ctfd\\.io|Follow us on social|setup your CTF/i.test(h.textContent)) h.remove();
    }});
    (document.querySelectorAll('img.w-100.mx-auto.d-block, img[src*="logo.png"]') || []).forEach(function(img){{
      img.src = HELLI_LOGO;
      img.classList.add('helli-main-logo');
      img.removeAttribute('style');
      img.alt = 'لوگو';
    }});
    /* navbar brand: kill any broken /files/ proxy img (belt & braces) */
    (document.querySelectorAll('.navbar-brand img') || []).forEach(function(img){{
      img.style.display = 'none';
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
    ap.add_argument("--logo-cache", default="/tmp/helli_logo.b64")
    args = ap.parse_args()

    if os.path.exists(args.logo_cache):
        b64 = open(args.logo_cache).read().strip()
    else:
        b64 = base64.b64encode(
            requests.get(LOGO_URL, timeout=30).content).decode()
        with open(args.logo_cache, "w") as f:
            f.write(b64)
    print(f"logo: {len(b64)//1024}KB (base64)")

    theme = build_theme(b64)
    h = {"Authorization": f"Token {args.token}",
         "Content-Type": "application/json"}
    for key, val in [("theme_footer", theme),
                     ("ctf_name", CTF_NAME),
                     ("ctf_logo", "")]:
        r = requests.patch(f"{args.url}/api/v1/configs", headers=h,
                           json={key: val}, timeout=15)
        print(f"patch {key}:", r.status_code)

    r = requests.get(f"{args.url}/", timeout=15)
    print("data-uri logo embedded:", "data:image/png;base64" in r.text,
          "| name ok:", "پیدا کردن پرچم" in r.text)


if __name__ == "__main__":
    main()
