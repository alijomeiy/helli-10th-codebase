"""Periodic config re-sync. Run from cron/systemd-timer on the panel VM so the
Linux box always has a fresh config even if an interactive push failed.

  */2 * * * *  /opt/studentctl/panel/venv/bin/python /opt/studentctl/panel/sync.py
"""
import logging
from app import app, db, sync_server

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

if __name__ == "__main__":
    with app.app_context():
        if sync_server():
            logging.info("config synced OK")
        else:
            logging.error("config sync FAILED")
