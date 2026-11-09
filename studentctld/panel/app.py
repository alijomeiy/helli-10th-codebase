import json
import re
import os
import secrets
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from functools import wraps

from flask import (
    Flask, render_template, redirect, url_for, request, flash, jsonify, abort,
    Blueprint,
)
from flask_login import (
    LoginManager, login_user, logout_user, login_required, current_user,
)
from werkzeug.middleware.proxy_fix import ProxyFix

import server_api
from server_api import (
        passwd as srv_passwd, kill as srv_kill,
)
from config import Config
from models import (
    db, User, Setting, LoginLog, Task, TaskAttempt,
    STATUS_PENDING, STATUS_APPROVED, STATUS_REJECTED, STATUS_DISABLED,
)
import tasks as task_mgr
import activities as hub
from activities import hub_bp, my_bp

app = Flask(__name__)
app.config.from_object(Config)
# Correct scheme/host behind an optional nginx reverse proxy.
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
db.init_app(app)

login_mgr = LoginManager(app)
login_mgr.login_view = "student_login"
login_mgr.login_message_category = "error"


@login_mgr.user_loader
def load_user(uid):
    return User.query.get(int(uid))


# ---------- helpers -----------------------------------------------------------

def max_concurrent():
    return 999


def idle_timeout():
    return 0


def next_uid_port():
    """Find the next free (uid, port) pair in the configured range."""
    used = {u.uid for u in User.query.filter(User.uid.isnot(None)).all()}
    for uid in range(Config.UID_START, Config.UID_END + 1):
        if uid not in used:
            port = Config.PORT_BASE + (uid - Config.UID_START)
            if port <= Config.PORT_END:
                return uid, port
    abort(500, "No free UID/port slots left")


def gen_password():
    # pronounce-ish but strong enough for a classroom
    return secrets.token_urlsafe(9).replace("-", "").replace("_", "")[:10]


def build_users_map():
    """Build the {username: {...}} dict pushed to the server."""
    rows = User.query.filter(
        User.role == "student",
        User.status.in_([STATUS_APPROVED, STATUS_DISABLED]),
        User.uid.isnot(None),
    ).all()
    return {
        r.username: {
            "enabled": r.status == STATUS_APPROVED,
            "uid": r.uid,
            "port": r.port,
        }
        for r in rows
    }


def sync_server():
    """No-op: server concurrency and idle limiters have been removed."""
    return True


def log_event(username, action, detail=""):
    db.session.add(LoginLog(username=username, action=action, detail=detail))
    db.session.commit()


def ctfd_provision(username, password):
    """Create the matching CTFd account (same creds as the Linux account).

    Same convention as ctf/sync_users.py. Best-effort: returns True/False,
    None when CTFd isn't configured (approval proceeds regardless).
    """
    import requests
    url = (app.config.get("CTFD_URL") or "").rstrip("/")
    token = app.config.get("CTFD_TOKEN") or ""
    if not url or not token:
        return None
    try:
        h = {"Authorization": f"Token {token}",
             "Content-Type": "application/json"}
        r = requests.post(f"{url}/api/v1/users", headers=h, timeout=15, json={
            "name": username,
            "email": f"{username}@students.helli-10th-computer.ir",
            "password": password,
            "type": "user",
            "verified": True,
            "hidden": False,
            "banned": False,
        })
        return r.status_code == 200
    except Exception:
        return False


def ctfd_get_user_id(username):
    """Find CTFd user id for a given username."""
    import requests
    url = (app.config.get("CTFD_URL") or "").rstrip("/")
    token = app.config.get("CTFD_TOKEN") or ""
    if not url or not token:
        return None
    try:
        h = {"Authorization": f"Token {token}", "Content-Type": "application/json"}
        r = requests.get(f"{url}/api/v1/users?view=admin&field=name&q={username}", headers=h, timeout=10, verify=False)
        if r.status_code == 200:
            for item in r.json().get("data", []):
                if item.get("name") == username:
                    return item.get("id")
    except Exception as e:
        app.logger.warning(f"ctfd_get_user_id failed for {username}: {e}")
    return None


def ctfd_set_banned(username, banned=True):
    """Ban or unban a user on CTFd."""
    import requests
    user_id = ctfd_get_user_id(username)
    if not user_id:
        return False
    url = (app.config.get("CTFD_URL") or "").rstrip("/")
    token = app.config.get("CTFD_TOKEN") or ""
    try:
        h = {"Authorization": f"Token {token}", "Content-Type": "application/json"}
        r = requests.patch(f"{url}/api/v1/users/{user_id}", headers=h, json={"banned": banned}, timeout=10, verify=False)
        return r.status_code == 200
    except Exception as e:
        app.logger.warning(f"ctfd_set_banned failed for {username}: {e}")
        return False


def ctfd_change_password(username, new_password):
    """Update user password on CTFd."""
    import requests
    user_id = ctfd_get_user_id(username)
    if not user_id:
        return False
    url = (app.config.get("CTFD_URL") or "").rstrip("/")
    token = app.config.get("CTFD_TOKEN") or ""
    try:
        h = {"Authorization": f"Token {token}", "Content-Type": "application/json"}
        r = requests.patch(f"{url}/api/v1/users/{user_id}", headers=h, json={"password": new_password}, timeout=10, verify=False)
        return r.status_code == 200
    except Exception as e:
        app.logger.warning(f"ctfd_change_password failed for {username}: {e}")
        return False


def get_locked_classes():
    return set()


def set_locked_classes(locked_set):
    pass


def ctfd_fetch_all_users():
    """Fetch mapping of username -> ctfd user id for all CTFd users."""
    import requests
    url = (app.config.get("CTFD_URL") or "").rstrip("/")
    token = app.config.get("CTFD_TOKEN") or ""
    if not url or not token:
        return {}
    mapping = {}
    try:
        h = {"Authorization": f"Token {token}", "Content-Type": "application/json"}
        page = 1
        while page:
            r = requests.get(f"{url}/api/v1/users?view=admin&page={page}", headers=h, timeout=10, verify=False)
            if r.status_code != 200:
                break
            payload = r.json()
            data = payload.get("data", [])
            for u in data:
                mapping[u.get("name")] = u.get("id")
            meta = payload.get("meta", {}).get("pagination", {})
            page = meta.get("next")
    except Exception as e:
        app.logger.warning(f"ctfd_fetch_all_users error: {e}")
    return mapping


# ---------- public pages ------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/leaderboard")
def leaderboard():
    t_list, rows = task_mgr.leaderboard_data()
    return render_template("leaderboard.html", tasks=t_list, rows=rows)


@app.route("/api/tasks/submit", methods=["POST"])
def api_submit_task():
    data = request.get_json(force=True, silent=True) or {}
    username = data.get("username", "").strip().lower()
    answer = str(data.get("answer", "")).strip()
    task1_exists = bool(data.get("task1_exists", False))
    task2_ok = bool(data.get("task2_ok", False))
    result, code = task_mgr.process_submission(
        username, answer, task1_exists, task2_ok
    )
    return jsonify(result), code


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        class_label = request.form.get("class_label", "").strip()

        if not username.isidentifier() or not (3 <= len(username) <= 24):
            flash("نام کاربری باید ۳ تا ۲۴ نویسه و فقط شامل حروف انگلیسی، عدد و خط زیر باشد.", "error")
            return redirect(url_for("register"))
        if len(password) < 8:
            flash("رمز عبور باید حداقل ۸ نویسه باشد.", "error")
            return redirect(url_for("register"))
        if User.query.filter_by(username=username).first():
            flash("این نام کاربری قبلاً گرفته شده است.", "error")
            return redirect(url_for("register"))

        u = User(
            role="student", username=username, full_name=full_name, email=email,
            status=STATUS_PENDING, class_label=class_label,
        )
        u.set_password(password)
        db.session.add(u)
        db.session.commit()
        log_event(username, "register", "submitted for approval")
        flash("درخواست شما ثبت شد! به‌زودی یک مدیر آن را تأیید می‌کند.", "ok")
        return redirect(url_for("student_login"))
    return render_template("register.html")


# ---------- student auth ------------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def student_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")
        u = User.query.filter_by(username=username, role="student").first()
        if u and u.check_password(password):
            login_user(u)
            return redirect(url_for("dashboard"))
        flash("اطلاعات ورود نادرست است.", "error")
        return redirect(url_for("student_login"))
    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))


@app.route("/dashboard")
@login_required
def dashboard():
    if current_user.is_admin:
        return redirect(url_for("admin.admin_index"))
    if current_user.status == STATUS_PENDING:
        return render_template("dashboard.html", pending=True)
    if current_user.status == STATUS_REJECTED:
        return render_template("dashboard.html", rejected=True)
    if current_user.status == STATUS_DISABLED:
        return render_template("dashboard.html", disabled=True)

    return render_template(
        "dashboard.html",
        pending=False, rejected=False, disabled=False,
    )



# ---------- admin blueprint ---------------------------------------------------
# Admin lives entirely under /admin/* and is NOT linked from the student UI.
# Reach it only by navigating to /admin/login directly.

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required(f):
    @wraps(f)
    def wrap(*a, **kw):
        if not current_user.is_authenticated:
            return redirect(url_for("admin.admin_login"))
        if not current_user.is_admin:
            abort(403)
        return f(*a, **kw)
    return wrap


@admin_bp.route("/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        u = User.query.filter_by(
            username=request.form.get("username", "").strip(),
            role="admin",
        ).first()
        if u and u.check_password(request.form.get("password", "")):
            login_user(u)
            return redirect(url_for("admin.admin_index"))
        flash("اطلاعات ورود مدیر نادرست است.", "error")
        return redirect(url_for("admin.admin_login"))
    return render_template("admin_login.html")


@admin_bp.route("")
@admin_required
def admin_index():
    pending = User.query.filter_by(role="student", status=STATUS_PENDING).order_by(User.created_at).all()
    active = User.query.filter(User.role == "student",
                               User.status.in_([STATUS_APPROVED, STATUS_DISABLED])).order_by(User.username).all()
    tasks_info = []
    for t in Task.query.order_by(Task.id).all():
        completed = TaskAttempt.query.filter_by(task_id=t.id, completed=True).count()
        total_attempts = TaskAttempt.query.filter_by(task_id=t.id).count()
        tasks_info.append({
            "name": t.name,
            "title": t.title,
            "is_active": t.is_active,
            "deployed_at": t.deployed_at,
            "completed": completed,
            "total": total_attempts,
        })

    all_students = User.query.filter_by(role="student").all()
    class_map = {}
    for s in all_students:
        cl = (s.class_label or "").strip()
        if cl not in class_map:
            class_map[cl] = {"class_label": cl, "total": 0, "active": 0}
        class_map[cl]["total"] += 1
        if s.status == STATUS_APPROVED:
            class_map[cl]["active"] += 1

    classes_summary = sorted(class_map.values(), key=lambda x: (x["class_label"] == "", x["class_label"]))

    return render_template(
        "admin.html", pending=pending, active=active, tasks_info=tasks_info,
        classes_summary=classes_summary,
    )


@admin_bp.route("/approve/<int:uid>", methods=["POST"])
@admin_required
def approve(uid):
    u = User.query.get_or_404(uid)
    if u.status != STATUS_PENDING:
        flash("این حساب در حالت انتظار نیست.", "error")
        return redirect(url_for("admin.admin_index"))

    new_uid, port = next_uid_port()
    pw = gen_password()
    try:
        server_api.provision(u.username, new_uid, port, pw)
    except Exception as e:
        flash(f"ایجاد حساب روی سرور لینوکس ناموفق بود: {e}", "error")
        return redirect(url_for("admin.admin_index"))

    u.uid = new_uid
    u.port = port
    u.ssh_password = pw
    u.status = STATUS_APPROVED
    u.approved_at = datetime.utcnow()
    db.session.commit()
    sync_server()
    log_event(u.username, "provision", f"uid={new_uid} port={port}")

    ctfd = ctfd_provision(u.username, pw)
    if ctfd:
        if u.class_label and u.class_label in get_locked_classes():
            ctfd_set_banned(u.username, banned=True)
            log_event(u.username, "ctf_account", f"created & banned (class {u.class_label} is locked)")
        else:
            log_event(u.username, "ctf_account", "created via CTFd API")
        flash(f"حساب {u.username} تأیید شد (لینوکس + آزمایشگاه + CTF). رمز SSH او در پنل کاربری‌اش نمایش داده می‌شود.", "ok")
    elif ctfd is False:
        log_event(u.username, "ctf_account", "FAILED (check CTFD_URL/CTFD_TOKEN)")
        flash(f"حساب {u.username} تأیید شد؛ اما ساخت حساب CTF ناموفق بود — با «sync_users.py» بعداً بسازید.", "error")
    else:
        flash(f"حساب {u.username} تأیید شد. رمز SSH او در پنل کاربری‌اش نمایش داده می‌شود.", "ok")
    return redirect(url_for("admin.admin_index"))


@admin_bp.route("/reject/<int:uid>", methods=["POST"])
@admin_required
def reject(uid):
    u = User.query.get_or_404(uid)
    u.status = STATUS_REJECTED
    db.session.commit()
    log_event(u.username, "reject")
    flash(f"درخواست {u.username} رد شد.", "ok")
    return redirect(url_for("admin.admin_index"))


@admin_bp.route("/disable/<int:uid>", methods=["POST"])
@admin_required
def disable(uid):
    u = User.query.get_or_404(uid)
    if u.uid is None:
        return redirect(url_for("admin.admin_index"))
    try:
        server_api.disable(u.username)
        srv_kill(u.username)
    except Exception as e:
        flash(f"خطای سرور هنگام قطع دسترسی لینوکس: {e}", "error")
    u.status = STATUS_DISABLED
    db.session.commit()
    sync_server()
    ctfd_ok = ctfd_set_banned(u.username, banned=True)
    log_event(u.username, "disable", f"banned by admin {current_user.username}")
    msg = f"دسترسی {u.username} مسدود شد و نشست‌های فعال او قطع شدند."
    if ctfd_ok:
        msg += " (حساب CTF نیز مسدود شد)"
    flash(msg, "ok")
    return redirect(url_for("admin.admin_index"))


@admin_bp.route("/enable/<int:uid>", methods=["POST"])
@admin_required
def enable(uid):
    u = User.query.get_or_404(uid)
    if u.uid is None:
        return redirect(url_for("admin.admin_index"))
    try:
        server_api.enable(u.username)
    except Exception as e:
        flash(f"خطای سرور هنگام فعال‌سازی لینوکس: {e}", "error")
    u.status = STATUS_APPROVED
    db.session.commit()
    sync_server()
    ctfd_ok = ctfd_set_banned(u.username, banned=False)
    log_event(u.username, "enable", f"unbanned by admin {current_user.username}")
    msg = f"دسترسی {u.username} دوباره فعال شد."
    if ctfd_ok:
        msg += " (حساب CTF نیز رفع مسدودی شد)"
    flash(msg, "ok")
    return redirect(url_for("admin.admin_index"))


@admin_bp.route("/password/<int:uid>", methods=["POST"])
@admin_required
def change_password(uid):
    u = User.query.get_or_404(uid)
    new_pw = request.form.get("new_password", "").strip()
    if not new_pw:
        new_pw = gen_password()
    elif len(new_pw) < 6:
        flash("رمز عبور باید حداقل ۶ نویسه باشد.", "error")
        return redirect(url_for("admin.admin_index"))

    # 1. Update Linux system account password
    if u.uid is not None:
        try:
            srv_passwd(u.username, new_pw)
        except Exception as e:
            flash(f"خطا در تغییر رمز لینوکس: {e}", "error")

    # 2. Update Web Panel login password & stored SSH password
    u.set_password(new_pw)
    u.ssh_password = new_pw
    db.session.commit()

    # 3. Update CTFd password
    ctfd_ok = ctfd_change_password(u.username, new_pw)

    log_event(u.username, "passwd_change", f"by admin {current_user.username}")
    msg = f"رمز عبور کاربر {u.username} با موفقیت تغییر کرد. رمز جدید: {new_pw}"
    if ctfd_ok:
        msg += " (رمز CTF نیز همگام شد)"
    flash(msg, "ok")
    return redirect(url_for("admin.admin_index"))


@admin_bp.route("/kill/<int:uid>", methods=["POST"])
@admin_required
def kill_user(uid):
    u = User.query.get_or_404(uid)
    try:
        srv_kill(u.username)
        log_event(u.username, "kill_sessions", f"by admin {current_user.username}")
        flash(f"تمامی نشست‌های فعال و پردازه‌های کاربر {u.username} متوقف شدند.", "ok")
    except Exception as e:
        flash(f"خطا در بستن نشست‌های کاربر: {e}", "error")
    return redirect(url_for("admin.admin_index"))


@admin_bp.route("/user/class/<int:uid>", methods=["POST"])
@admin_required
def set_user_class(uid):
    u = User.query.get_or_404(uid)
    new_class = request.form.get("class_label", "").strip()
    old_class = u.class_label or ""
    u.class_label = new_class
    db.session.commit()

    log_event(u.username, "class_changed", f"from '{old_class}' to '{new_class}' by {current_user.username}")
    flash(f"کلاس کاربر {u.username} به «{new_class or 'تعیین‌نشده'}» تغییر یافت.", "ok")
    return redirect(url_for("admin.admin_index"))


@admin_bp.route("/class/bulk_assign", methods=["POST"])
@admin_required
def bulk_assign_class():
    target_class = request.form.get("class_label", "").strip()
    raw_users = request.form.get("usernames", "")
    if not target_class:
        flash("لطفاً نام یا شناسه کلاس را وارد نمایید.", "error")
        return redirect(url_for("admin.admin_index"))

    tokens = [t.strip().lower() for t in re.split(r"[\s,]+", raw_users) if t.strip()]
    if not tokens:
        flash("هیچ نام کاربری وارد نشده است.", "error")
        return redirect(url_for("admin.admin_index"))

    matched = User.query.filter(User.role == "student", User.username.in_(tokens)).all()
    if not matched:
        flash("هیچ کاربری با شناسه‌های وارد شده یافت نشد.", "error")
        return redirect(url_for("admin.admin_index"))

    for u in matched:
        u.class_label = target_class
    db.session.commit()

    log_event(current_user.username, "bulk_class_assign", f"{len(matched)} users -> {target_class}")
    flash(f"کلاس {len(matched)} دانش‌آموز با موفقیت به «{target_class}» تنظیم شد.", "ok")
    return redirect(url_for("admin.admin_index"))


@admin_bp.route("/delete/<int:uid>", methods=["POST"])
@admin_required
def delete(uid):
    u = User.query.get_or_404(uid)
    if u.uid is not None:
        try:
            server_api.delete(u.username)
        except Exception as e:
            flash(f"خطای سرور هنگام حذف: {e}", "error")
    uname = u.username
    db.session.delete(u)
    db.session.commit()
    log_event(uname, "delete")
    flash(f"{uname} از همه‌جا حذف شد.", "ok")
    return redirect(url_for("admin.admin_index"))


@admin_bp.route("/tasks/deploy/<task_name>", methods=["POST"])
@admin_required
def deploy_task(task_name):
    try:
        if task_name == "task1":
            n = task_mgr.deploy_task1()
            flash(f"تسک ۱ برای {n} دانشجو مستقر شد.", "ok")
        elif task_name == "task2":
            n = task_mgr.deploy_task2()
            flash(f"تسک ۲ برای {n} دانشجو فعال شد.", "ok")
        else:
            flash("تسک نامعتبر.", "error")
    except Exception as e:
        flash(f"خطا در استقرار تسک: {e}", "error")
    return redirect(url_for("admin.admin_index"))


@admin_bp.route("/tasks/reset/<task_name>", methods=["POST"])
@admin_required
def reset_task(task_name):
    task = Task.query.filter_by(name=task_name).first()
    if task:
        TaskAttempt.query.filter_by(task_id=task.id).delete()
        task.is_active = False
        task.deployed_at = None
        db.session.commit()
        flash(f"تسک {task_name} بازنشانی شد.", "ok")
    return redirect(url_for("admin.admin_index"))


app.register_blueprint(admin_bp)
app.register_blueprint(hub_bp)
app.register_blueprint(my_bp)


# ---------- init / CLI --------------------------------------------------------

def ensure_admin():
    if not User.query.filter_by(role="admin").first():
        a = User(role="admin", username=Config.SEED_ADMIN_USER,
                 full_name="Administrator", status=STATUS_APPROVED)
        a.set_password(Config.SEED_ADMIN_PASS)
        db.session.add(a)
        db.session.commit()
        print(f"[studentctl] seeded admin '{Config.SEED_ADMIN_USER}' "
              f"(password from STUDENTCTL_ADMIN_PASS). CHANGE IT NOW.")


def migrate_sqlite():
    """create_all() won't add columns to existing tables — do it by hand.

    Idempotent: checks PRAGMA table_info first. Promotes existing admins to
    super exactly once (the single admin that existed before the hub).
    """
    from sqlalchemy import text
    adds = {
        "teacher_id": "ALTER TABLE users ADD COLUMN teacher_id INTEGER "
                      "REFERENCES users(id)",
        "student_no": "ALTER TABLE users ADD COLUMN student_no VARCHAR(32) "
                      "DEFAULT ''",
        "is_super": "ALTER TABLE users ADD COLUMN is_super BOOLEAN NOT NULL "
                    "DEFAULT 0",
    }
    try:
        with db.engine.connect() as conn:
            user_cols = {r[1] for r in
                         conn.execute(text("PRAGMA table_info(users)"))}
            for name, ddl in adds.items():
                if name not in user_cols:
                    conn.execute(text(ddl))
                    conn.commit()
                    print(f"[studentctl] migrated: users.{name} added")
    except Exception:
        return  # table not there yet; create_all will make it fresh
    if not User.query.filter_by(role="admin", is_super=True).first():
        for a in User.query.filter_by(role="admin").all():
            a.is_super = True
        db.session.commit()
        print("[studentctl] migrated: existing admin promoted to super")


@app.before_request
def _first_run():
    # Cheap one-time init guard using an attribute.
    if not getattr(app, "_db_ready", False):
        # Make sure the SQLite data dir exists (writable by the service user).
        db_dir = os.path.dirname(app.config["DB_PATH"])
        try:
            os.makedirs(db_dir, exist_ok=True)
        except OSError:
            pass
        with app.app_context():
            db.create_all()
            migrate_sqlite()   # BEFORE any ORM query on users
            ensure_admin()
        app._db_ready = True


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        ensure_admin()
    app.run(host="0.0.0.0", port=5000, debug=False)
