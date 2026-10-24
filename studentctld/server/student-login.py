#!/usr/bin/env python3
"""Direct, zero-PAM login program for ttyd web terminal.
Provides instant login without PAM, pam_loginuid, or login daemon hurdles.
"""
import os
import sys
import getpass
import sqlite3
import ctypes
import ctypes.util
import re

# Load system libcrypt for shadow password verification
try:
    libname = ctypes.util.find_library('crypt') or 'libcrypt.so.1'
    libcrypt = ctypes.CDLL(libname)
    libcrypt.crypt.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
    libcrypt.crypt.restype = ctypes.c_char_p
except Exception:
    libcrypt = None

PANEL_DB = "/var/lib/docker/volumes/studentctld_panel-data/_data/panel.db"

def get_shadow_hash(username):
    try:
        with open("/etc/shadow", "r") as f:
            for line in f:
                if line.startswith(f"{username}:"):
                    parts = line.split(":")
                    if len(parts) > 1:
                        return parts[1]
    except Exception:
        pass
    return None

def verify_credentials(username, password):
    if not username or not password:
        return False

    # 1. Verify against /etc/shadow using libcrypt
    if libcrypt:
        shash = get_shadow_hash(username)
        if shash and not shash.startswith(("*", "!")):
            try:
                res = libcrypt.crypt(password.encode("utf-8"), shash.encode("utf-8"))
                if res and res.decode("utf-8") == shash:
                    return True
            except Exception:
                pass

    # 2. Direct verification against panel database
    try:
        if os.path.exists(PANEL_DB):
            conn = sqlite3.connect(PANEL_DB)
            row = conn.execute(
                "SELECT ssh_password FROM users WHERE username=? AND status='approved'",
                (username,)
            ).fetchone()
            conn.close()
            if row and row[0] == password:
                return True
    except Exception:
        pass

    return False

def clean_username(raw):
    u = raw.strip()
    # Strip pasted ssh commands: 'ssh user@host -p 22' -> 'user'
    u = re.sub(r'^.*ssh\s+', '', u)
    u = re.sub(r'@.*$', '', u)
    u = re.sub(r'\s+.*$', '', u)
    u = re.sub(r'[^a-zA-Z0-9_.-]', '', u)
    return u.lower()

def main():
    os.environ["TERM"] = os.environ.get("TERM", "xterm-256color")
    
    while True:
        # Clear screen and display banner
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.write("\033[1;36m==============================================================\033[0m\r\n")
        sys.stdout.write("\033[1;32m             Helli Computer Science Linux Server\033[0m\r\n")
        sys.stdout.write("\033[1;36m==============================================================\033[0m\r\n")
        sys.stdout.write("\033[0;33mPlease enter your panel username and password to log in.\033[0m\r\n\r\n")
        sys.stdout.flush()

        try:
            raw_user = input("login: ")
        except (EOFError, KeyboardInterrupt):
            sys.exit(0)

        username = clean_username(raw_user)
        if not username:
            continue

        if username == "root":
            sys.stdout.write("\r\n\033[1;31mError: root login is not permitted via web terminal.\033[0m\r\n")
            sys.stdout.flush()
            import time; time.sleep(1.5)
            continue

        # Check user exists on system
        try:
            import pwd
            user_entry = pwd.getpwnam(username)
        except KeyError:
            sys.stdout.write(f"\r\n\033[1;31mError: User '{username}' does not exist on this server.\033[0m\r\n")
            sys.stdout.flush()
            import time; time.sleep(1.5)
            continue

        # Prompt for password
        try:
            password = getpass.getpass("Password: ")
        except (EOFError, KeyboardInterrupt):
            sys.exit(0)

        if verify_credentials(username, password):
            sys.stdout.write(f"\r\n\033[1;32mLogin successful. Welcome, {username}!\033[0m\r\n\r\n")
            sys.stdout.flush()
            # Drop all privileges and switch directly into the student's shell
            os.execlp("su", "su", "-", username)
        else:
            sys.stdout.write("\r\n\033[1;31mLogin incorrect.\033[0m\r\n")
            sys.stdout.flush()
            import time; time.sleep(1.5)

if __name__ == "__main__":
    main()
