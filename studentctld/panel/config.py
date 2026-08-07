import os

BASE = os.path.dirname(os.path.abspath(__file__))

class Config:
    SECRET_KEY = os.environ.get("STUDENTCTL_SECRET", "change-this-in-production")

    # SQLite lives on the small VM (the panel host) in the writable data dir
    DB_PATH = os.environ.get("STUDENTCTL_DB", "/var/lib/studentctl/panel.db")
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + DB_PATH
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # How the panel talks to the big Linux box over SSH (restricted sudo user)
    SSH_HOST = os.environ.get("STUDENTCTL_SSH_HOST", "10.0.0.10")
    SSH_PORT = int(os.environ.get("STUDENTCTL_SSH_PORT", "22"))
    SSH_USER = os.environ.get("STUDENTCTL_SSH_USER", "studentctl")
    SSH_KEY = os.environ.get("STUDENTCTL_SSH_KEY", os.path.join(BASE, "panel_key"))

    # Public hostname/IP students use to SSH in / reach their service
    SERVER_DOMAIN = os.environ.get("STUDENTCTL_SERVER_DOMAIN", SSH_HOST)
    SSH_PORT_PUBLIC = int(os.environ.get("STUDENTCTL_SSH_PORT_PUBLIC", "22"))

    # Defaults (editable from admin UI)
    DEFAULT_MAX_CONCURRENT = int(os.environ.get("STUDENTCTL_MAX_CONCURRENT", "15"))
    DEFAULT_RESERVED_ONDAY = int(os.environ.get("STUDENTCTL_RESERVED_ONDAY", "3"))

    # UID / port allocation ranges (must match server firewall: 10000-10100)
    UID_START = 2000
    UID_END = 2099
    PORT_BASE = 10000          # port = PORT_BASE + (uid - UID_START)
    PORT_END = 10099

    # Seed admin (created on first run; change the password immediately)
    SEED_ADMIN_USER = os.environ.get("STUDENTCTL_ADMIN_USER", "admin")
    SEED_ADMIN_PASS = os.environ.get("STUDENTCTL_ADMIN_PASS", "changeme123")

    WEEKDAYS = [
        (1, "دوشنبه"), (2, "سه‌شنبه"), (3, "چهارشنبه"),
        (4, "پنج‌شنبه"), (5, "جمعه"), (6, "شنبه"), (7, "یکشنبه"),
    ]
