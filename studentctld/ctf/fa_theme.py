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

LOGO_URL = "https://www.helli.ir/portal/sites/all/themes/helli/image/Logo1.png"
CTF_NAME = "پیدا کردن پرچم - گروه کامپیوتر دبیرستان حلی تهران"


def build_theme(logo_url: str) -> str:
    return f"""
<link rel="preconnect" href="https://cdn.jsdelivr.net">
<link rel="stylesheet"
      href="https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css">
<script>var HELLI_LOGO = "{logo_url}";</script>
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


def upload_logo(url, token, png_bytes):
    """Upload logo via CTFd files API, return its served URL."""
    h = {"Authorization": f"Token {token}"}
    r = requests.post(f"{url}/api/v1/files",
                      headers=h,
                      files={"file": ("helli-logo.png", png_bytes, "image/png")},
                      data={"type": "page", "location": "assets/helli-logo.png"},
                      timeout=30)
    if r.status_code != 200:
        raise RuntimeError(f"logo upload failed: {r.status_code} {r.text[:120]}")
    return r.json()["data"][0]["location"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:8000")
    ap.add_argument("--token", required=True)
    args = ap.parse_args()

    png = requests.get(LOGO_URL, timeout=30).content
    print(f"logo png: {len(png)//1024}KB")
    logo_url = upload_logo(args.url, args.token, png)
    print("logo served at:", logo_url)

    theme = build_theme(logo_url)
    h = {"Authorization": f"Token {args.token}",
         "Content-Type": "application/json"}
    for key, val in [("theme_footer", theme),
                     ("ctf_name", CTF_NAME),
                     ("ctf_logo", "")]:
        r = requests.patch(f"{args.url}/api/v1/configs", headers=h,
                           json={key: val}, timeout=15)
        print(f"patch {key}:", r.status_code)

    r = requests.get(f"{args.url}/", timeout=15)
    print("logo url in footer:", logo_url in r.text,
          "| name ok:", "پیدا کردن پرچم" in r.text)


if __name__ == "__main__":
    main()
