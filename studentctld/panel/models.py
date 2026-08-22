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

    # grading hub: super admin sees everything, plain admins (teachers)
    # see only the students assigned to them
    is_super = db.Column(db.Boolean, default=False, nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    student_no = db.Column(db.String(32), default="", index=True)

    # Linux account metadata (set when approved)
    status = db.Column(db.String(16), default=STATUS_PENDING, nullable=False, index=True)
    uid = db.Column(db.Integer, nullable=True)
    port = db.Column(db.Integer, nullable=True)
    ssh_password = db.Column(db.String(64), default="")       # generated SSH password

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


class Task(db.Model):
    __tablename__ = "tasks"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), unique=True, nullable=False)   # task1, task2
    title = db.Column(db.String(120), default="")
    description = db.Column(db.Text, default="")
    max_points = db.Column(db.Integer, default=100)
    is_active = db.Column(db.Boolean, default=False)
    deployed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class TaskAttempt(db.Model):
    __tablename__ = "task_attempts"
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey("tasks.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    expected_answer = db.Column(db.String(64), default="")
    completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    time_taken_seconds = db.Column(db.Integer, nullable=True)
    score = db.Column(db.Integer, default=0)
    wrong_attempts = db.Column(db.Integer, default=0)
    rank = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint("task_id", "user_id"),)


class Activity(db.Model):
    """A gradable class event: quiz (manual scores) or ctf (auto-synced)."""
    __tablename__ = "activities"
    id = db.Column(db.Integer, primary_key=True)
    kind = db.Column(db.String(16), nullable=False, index=True)   # quiz | ctf
    title = db.Column(db.String(120), nullable=False)
    held_on = db.Column(db.Date, nullable=True)
    max_score = db.Column(db.Float, default=20.0, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Score(db.Model):
    __tablename__ = "scores"
    id = db.Column(db.Integer, primary_key=True)
    activity_id = db.Column(db.Integer, db.ForeignKey("activities.id"),
                            nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"),
                        nullable=False, index=True)
    score = db.Column(db.Float, default=0.0, nullable=False)
    detail = db.Column(db.Text, default="")      # free note or JSON (ctf solves)
    updated_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow,
                           onupdate=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint("activity_id", "user_id"),)
