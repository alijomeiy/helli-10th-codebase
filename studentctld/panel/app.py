import os
import secrets
from datetime import datetime

from flask import (
    Flask, render_template, redirect, url_for, request, flash, jsonify, abort
)
from flask_login import (
    LoginManager, login_user, logout_user, login_required, current_user,
)
from werkzeug.middleware.proxy_fix import ProxyFix

import server_api
from config import Config
from models import (
    db, User, Setting, LoginLog,
    STATUS_PENDING, STATUS_APPROVED, STATUS_REJECTED, STATUS_DISABLED,
)

app = Flask(__name__)
app.config.from_object(Config)
# Correct scheme/host behind the nginx reverse proxy (panel.domain -> 4GB box -> small VM)
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
    return Setting.get_int("max_concurrent", Config.DEFAULT_MAX_CONCURRENT)


def reserved_onday():
    return Setting.get_int("reserved_onday", Config.DEFAULT_RESERVED_ONDAY)


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
            "day": r.preferred_day,
            "enabled": r.status == STATUS_APPROVED,
            "uid": r.uid,
            "port": r.port,
        }
        for r in rows
    }


def sync_server():
    """Push the current config to the Linux box. Best-effort; flashes on error."""
    try:
        server_api.push_config(max_concurrent(), reserved_onday(), build_users_map())
        return True
    except Exception as e:
        flash(f"ارتباط با سرور لینوکس برای همگام‌سازی برقرار نشد: {e}", "error")
        return False


def log_event(username, action, detail=""):
    db.session.add(LoginLog(username=username, action=action, detail=detail))
    db.session.commit()


# ---------- public pages ------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        day = int(request.form.get("preferred_day", 1))

        if not username.isidentifier() or not (3 <= len(username) <= 24):
            flash("نام کاربری باید ۳ تا ۲۴ نویسه و فقط شامل حروف انگلیسی، عدد و خط زیر باشد.", "error")
            return redirect(url_for("register"))
        if len(password) < 8:
            flash("رمز عبور باید حداقل ۸ نویسه باشد.", "error")
            return redirect(url_for("register"))
        if User.query.filter_by(username=username).first():
            flash("این نام کاربری قبلاً گرفته شده است.", "error")
            return redirect(url_for("register"))
        if not (1 <= day <= 7):
            flash("یک روز معتبر از هفته انتخاب کنید.", "error")
            return redirect(url_for("register"))

        u = User(
            role="student", username=username, full_name=full_name, email=email,
            preferred_day=day, status=STATUS_PENDING,
        )
        u.set_password(password)
        db.session.add(u)
        db.session.commit()
        log_event(username, "register", "submitted for approval")
        flash("درخواست شما ثبت شد! به‌زودی یک مدیر آن را تأیید می‌کند.", "ok")
        return redirect(url_for("student_login"))
    return render_template("register.html", weekdays=Config.WEEKDAYS)


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
        return redirect(url_for("admin_index"))
    if current_user.status == STATUS_PENDING:
        return render_template("dashboard.html", pending=True)
    if current_user.status == STATUS_REJECTED:
        return render_template("dashboard.html", rejected=True)

    # live capacity (best effort)
    capacity = None
    try:
        capacity = server_api.status()
    except Exception:
        capacity = None

    return render_template(
        "dashboard.html",
        pending=False, rejected=False, capacity=capacity,
        weekdays=Config.WEEKDAYS,
        today_iso=int(datetime.utcnow().isoweekday()),
    )


@app.route("/dashboard/day", methods=["POST"])
@login_required
def change_day():
    if current_user.is_admin or current_user.role != "student":
        abort(403)
    day = int(request.form.get("preferred_day", 1))
    if 1 <= day <= 7:
        current_user.preferred_day = day
        db.session.commit()
        sync_server()
        flash("روز مورد نظر به‌روزرسانی شد. در روز انتخابی‌تان اولویت دسترسی دارید.", "ok")
    return redirect(url_for("dashboard"))


# ---------- admin -------------------------------------------------------------

def admin_required(f):
    from functools import wraps
    @wraps(f)
    @login_required
    def wrap(*a, **kw):
        if not current_user.is_admin:
            abort(403)
        return f(*a, **kw)
    return wrap


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        u = User.query.filter_by(
            username=request.form.get("username", "").strip(),
            role="admin",
        ).first()
        if u and u.check_password(request.form.get("password", "")):
            login_user(u)
            return redirect(url_for("admin_index"))
        flash("اطلاعات ورود مدیر نادرست است.", "error")
        return redirect(url_for("admin_login"))
    return render_template("admin_login.html")


@app.route("/admin")
@admin_required
def admin_index():
    pending = User.query.filter_by(role="student", status=STATUS_PENDING).order_by(User.created_at).all()
    active = User.query.filter(User.role == "student",
                               User.status.in_([STATUS_APPROVED, STATUS_DISABLED])).order_by(User.username).all()
    capacity = None
    try:
        capacity = server_api.status()
    except Exception:
        pass
    return render_template(
        "admin.html", pending=pending, active=active, capacity=capacity,
        max_conc=max_concurrent(), reserved=reserved_onday(),
        weekdays=Config.WEEKDAYS,
    )


@app.route("/admin/approve/<int:uid>", methods=["POST"])
@admin_required
def approve(uid):
    u = User.query.get_or_404(uid)
    if u.status != STATUS_PENDING:
        flash("این حساب در حالت انتظار نیست.", "error")
        return redirect(url_for("admin_index"))

    new_uid, port = next_uid_port()
    pw = gen_password()
    try:
        server_api.provision(u.username, new_uid, port, pw, u.preferred_day)
    except Exception as e:
        flash(f"ایجاد حساب روی سرور لینوکس ناموفق بود: {e}", "error")
        return redirect(url_for("admin_index"))

    u.uid = new_uid
    u.port = port
    u.ssh_password = pw
    u.status = STATUS_APPROVED
    u.approved_at = datetime.utcnow()
    db.session.commit()
    sync_server()
    log_event(u.username, "provision", f"uid={new_uid} port={port}")
    flash(f"حساب {u.username} تأیید شد. رمز SSH او در پنل کاربری‌اش نمایش داده می‌شود.", "ok")
    return redirect(url_for("admin_index"))


@app.route("/admin/reject/<int:uid>", methods=["POST"])
@admin_required
def reject(uid):
    u = User.query.get_or_404(uid)
    u.status = STATUS_REJECTED
    db.session.commit()
    log_event(u.username, "reject")
    flash(f"درخواست {u.username} رد شد.", "ok")
    return redirect(url_for("admin_index"))


@app.route("/admin/disable/<int:uid>", methods=["POST"])
@admin_required
def disable(uid):
    u = User.query.get_or_404(uid)
    if u.uid is None:
        return redirect(url_for("admin_index"))
    try:
        server_api.disable(u.username)
    except Exception as e:
        flash(f"خطای سرور: {e}", "error")
    u.status = STATUS_DISABLED
    db.session.commit()
    sync_server()
    log_event(u.username, "disable")
    flash(f"دسترسی {u.username} غیرفعال شد.", "ok")
    return redirect(url_for("admin_index"))


@app.route("/admin/enable/<int:uid>", methods=["POST"])
@admin_required
def enable(uid):
    u = User.query.get_or_404(uid)
    if u.uid is None:
        return redirect(url_for("admin_index"))
    try:
        server_api.enable(u.username)
    except Exception as e:
        flash(f"خطای سرور: {e}", "error")
    u.status = STATUS_APPROVED
    db.session.commit()
    sync_server()
    log_event(u.username, "enable")
    flash(f"دسترسی {u.username} دوباره فعال شد.", "ok")
    return redirect(url_for("admin_index"))


@app.route("/admin/delete/<int:uid>", methods=["POST"])
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
    sync_server()
    log_event(uname, "delete")
    flash(f"{uname} از همه‌جا حذف شد.", "ok")
    return redirect(url_for("admin_index"))


@app.route("/admin/settings", methods=["POST"])
@admin_required
def settings():
    mc = int(request.form.get("max_concurrent", max_concurrent()))
    rv = int(request.form.get("reserved_onday", reserved_onday()))
    mc = max(1, min(mc, 50))
    rv = max(0, min(rv, mc))
    Setting.set("max_concurrent", mc)
    Setting.set("reserved_onday", rv)
    db.session.commit()
    sync_server()
    flash("تنظیمات ذخیره و همگام‌سازی شد.", "ok")
    return redirect(url_for("admin_index"))


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
            ensure_admin()
        app._db_ready = True


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        ensure_admin()
    app.run(host="0.0.0.0", port=5000, debug=False)
