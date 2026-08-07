from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

db = SQLAlchemy()

STATUS_PENDING = "pending"
STATUS_APPROVED = "approved"
STATUS_REJECTED = "rejected"
STATUS_DISABLED = "disabled"


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(16), default="student", nullable=False)  # student | admin
    username = db.Column(db.String(32), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(120), default="")
    email = db.Column(db.String(120), default="")
    pw_hash = db.Column(db.String(255), default="")           # panel login password

    # Linux account metadata (set when approved)
    status = db.Column(db.String(16), default=STATUS_PENDING, nullable=False, index=True)
    uid = db.Column(db.Integer, nullable=True)
    port = db.Column(db.Integer, nullable=True)
    ssh_password = db.Column(db.String(64), default="")       # generated SSH password
    preferred_day = db.Column(db.Integer, default=1)          # 1=Mon..7=Sun

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_at = db.Column(db.DateTime, nullable=True)

    def set_password(self, raw):
        self.pw_hash = generate_password_hash(raw)

    def check_password(self, raw):
        if not self.pw_hash:
            return False
        return check_password_hash(self.pw_hash, raw)

    @property
    def is_admin(self):
        return self.role == "admin"

    @property
    def is_active_account(self):
        return self.status == STATUS_APPROVED


class Setting(db.Model):
    __tablename__ = "settings"
    key = db.Column(db.String(64), primary_key=True)
    value = db.Column(db.String(255), default="")

    @classmethod
    def get_int(cls, key, default):
        row = cls.query.get(key)
        return int(row.value) if row and row.value.isdigit() else default

    @classmethod
    def set(cls, key, value):
        row = cls.query.get(key)
        if row:
            row.value = str(value)
        else:
            db.session.add(cls(key=key, value=str(value)))


class LoginLog(db.Model):
    __tablename__ = "login_log"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), index=True)
    action = db.Column(db.String(16))   # allow / deny / provision / disable ...
    detail = db.Column(db.String(255), default="")
    at = db.Column(db.DateTime, default=datetime.utcnow)
