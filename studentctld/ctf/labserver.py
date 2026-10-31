#!/usr/bin/env python3
"""Shared localhost lab service for the networking (week 2) challenges.

Identifies a student by a per-student URL key — md5(username)[:10], the same
derivation as ctf_scatter.lab_key — and serves that student's flags straight
from manifest.json. Bound to 127.0.0.1:8901 only; a classroom tool, not a
hardened internet service.

Routes (BASE = /lab/<key>, served by systemd student-lab-flags.service):
  BASE/header             -> 200, flag in the X-Lab-Secret header    (n2)
  BASE/share              -> listing of six file names               (n3)
  BASE/share/<name>       -> flag (per-student real name) or decoy   (n3)
  BASE/farm/doorN (1..6)  -> flag (per-student real door) or decoy   (n4)
  BASE/hop1 / hop2        -> 301 chain, Location headers             (n5)
  BASE/final              -> flag                                    (n5)
  BASE/vault              -> 403 unless X-Lab-Code matches the code
                             scattered into the student's code.txt   (n6)
"""
import hashlib
import json
import os
import random
import socket
import sys
import threading
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, HTTPServer

MANIFEST = sys.argv[1] if len(sys.argv) > 1 else \
    "/root/helli-10th-codebase/studentctld/ctf/manifest.json"

SHARE_NAMES = ["report-q1.txt", "notes.txt", "team.txt",
               "todo.txt", "backup.sql", "readme.md"]
CODE_LETTERS = "abcdefgh"
VHOST_NAME = "attic.lab.local"

_cache = {"mtime": 0, "flags": {}}


def load_flags():
    """Read manifest.json on change only (it is rewritten by ctf_scatter)."""
    mtime = os.path.getmtime(MANIFEST)
    if mtime != _cache["mtime"]:
        with open(MANIFEST, encoding="utf-8") as f:
            data = json.load(f)
        _cache["flags"] = data.get("flags", {})
        _cache["mtime"] = mtime
    return _cache["flags"]


def key_for(username):
    return hashlib.md5(username.encode()).hexdigest()[:10]


def users_by_key():
    return {key_for(u): u for u in load_flags().get("n2-headerbox", {})}


def code_for(key):
    return str(int(hashlib.md5((key + "code").encode()).hexdigest(), 16)
               % 10000).zfill(4)


def real_door(key):
    return int(hashlib.md5((key + "farm").encode()).hexdigest(), 16) % 6 + 1


def real_share(key):
    return SHARE_NAMES[int(hashlib.md5(
        (key + "share").encode()).hexdigest(), 16) % len(SHARE_NAMES)]


def ticket_for(key):
    return hashlib.md5((key + "cookie").encode()).hexdigest()[:12]


def real_code(key):
    return CODE_LETTERS[int(hashlib.md5(
        (key + "codes").encode()).hexdigest(), 16) % len(CODE_LETTERS)]


# decoy status codes for the code-hunt endpoints (never 200)
DECOY_CODES = [404, 403, 500, 410, 418, 405, 503, 401]


class H(BaseHTTPRequestHandler):
    def _send(self, code, body=b"", headers=()):
        self.send_response(code)
        for k, v in headers:
            self.send_header(k, v)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(body)

    def _flag(self, username, ch):
        flags = load_flags()
        return flags.get(ch, {}).get(username,
                                     "FLAG{missing}").encode()

    def do_GET(self):
        parts = self.path.strip("/").split("/")
        if len(parts) < 3 or parts[0] != "lab":
            return self._send(404, b"<p>lab service: nothing here</p>")
        key = parts[1]
        username = users_by_key().get(key)
        if username is None:
            return self._send(404, b"<p>lab service: unknown key</p>")

        def flag(ch):
            return self._flag(username, ch)

        route, rest = parts[2], parts[3:]
        if route == "header" and not rest:
            return self._send(
                200,
                b"<h1>headerbox</h1><p>the page knows nothing. "
                b"look at the envelope.</p>",
                [("X-Lab-Secret", flag("n2-headerbox").decode("ascii"))])
        if route == "share" and not rest:
            names = "".join(f"<li>{n}</li>" for n in SHARE_NAMES)
            return self._send(200, ("<h1>share</h1><ul>%s</ul>"
                                    % names).encode())
        if route == "share" and len(rest) == 1 and rest[0] in SHARE_NAMES:
            if rest[0] == real_share(key):
                return self._send(200, b"<pre>" + flag("n3-fileshare")
                                       + b"</pre>")
            return self._send(200, b"<pre>nothing interesting in this one."
                                   b"</pre>")
        if route == "farm" and len(rest) == 1 and rest[0].startswith("door"):
            try:
                door = int(rest[0][4:])
            except ValueError:
                door = 0
            if door == real_door(key):
                return self._send(200, b"<h1>farm door</h1><p>"
                                       + flag("n4-portfarm") + b"</p>")
            # no braces in the decoy: a student grepping FLAG{...} must not
            # get a false-positive match from a decoy page
            return self._send(200, b"<h1>farm door</h1><p>FAKEFLAG decoy "
                                    b"door " + str(door).encode()
                                    + b" - keep trying</p>")
        if route == "hop1" and not rest:
            return self._send(301, b"", [("Location", f"/lab/{key}/hop2")])
        if route == "hop2" and not rest:
            return self._send(301, b"", [("Location", f"/lab/{key}/final")])
        if route == "final" and not rest:
            return self._send(200, b"<h1>destination</h1><p>"
                                    + flag("n5-redirect") + b"</p>")
        if route == "vault" and not rest:
            if self.headers.get("X-Lab-Code") == code_for(key):
                return self._send(200, b"<h1>access granted</h1><p>"
                                        + flag("n6-detective") + b"</p>")
            return self._send(403, b"<h1>403: who is asking?</h1>"
                                    b"<p>protocol says: send header "
                                    b"X-Lab-Code</p>")
        # ---- optional batch (n7..n11) ----
        if route == "parcel" and not rest:
            return self._send(405, b"<h1>405: this door does not take GET"
                                    b"</h1><p>the courier only accepts "
                                    b"POSTed parcels (curl -d).</p>")
        if route == "cookie" and rest == ["start"]:
            return self._send(
                200,
                b"<h1>entrance</h1><p>here is your ticket. keep it and "
                b"show it: GET /cookie/flag with the LabTicket cookie "
                b"(curl -c jar ... then curl -b jar ...).</p>",
                [("Set-Cookie", f"LabTicket={ticket_for(key)}; Path=/")])
        if route == "cookie" and rest == ["flag"]:
            jar = SimpleCookie(self.headers.get("Cookie", ""))
            if jar.get("LabTicket") and \
                    jar["LabTicket"].value == ticket_for(key):
                return self._send(200, b"<h1>welcome back</h1><p>"
                                        + flag("n8-cookiejar") + b"</p>")
            return self._send(403, b"<h1>no ticket</h1><p>start at "
                                    b"/cookie/start and keep the cookie "
                                    b"with curl -c / -b.</p>")
        if route == "penthouse" and not rest:
            if (self.headers.get("Host") or "") == VHOST_NAME:
                return self._send(200, b"<h1>penthouse</h1><p>"
                                        + flag("n9-vhost") + b"</p>")
            return self._send(
                404, b"<h1>no such floor</h1><p>this building answers to "
                     b"many addresses; this floor only opens for a "
                     b"different Host.</p>")
        if route == "codes" and len(rest) == 1 and rest[0] in CODE_LETTERS:
            if rest[0] == real_code(key):
                return self._send(200, b"<h1>code hunter</h1><p>"
                                        + flag("n11-codehunt") + b"</p>")
            decoy = DECOY_CODES[ord(rest[0]) % len(DECOY_CODES)]
            return self._send(decoy, b"<p>nothing for you here.</p>")
        return self._send(404, b"<p>lab service: nothing here</p>")

    def do_POST(self):
        parts = self.path.strip("/").split("/")
        if len(parts) == 3 and parts[0] == "lab" and parts[2] == "parcel":
            key = parts[1]
            username = users_by_key().get(key)
            if username is None:
                return self._send(404, b"<p>lab service: unknown key</p>")
            try:
                length = int(self.headers.get("Content-Length") or 0)
            except ValueError:
                length = 0
            body = (self.rfile.read(length).decode(errors="replace")
                    if length else "")
            if "gift=" in body:
                return self._send(200, b"<h1>parcel received</h1><p>"
                                        + self._flag(username,
                                                     "n7-postbox")
                                        + b"</p>")
            return self._send(400, b"<h1>empty parcel</h1><p>send a form "
                                    b"field: curl -d 'gift=something'.</p>")
        return self._send(404, b"<p>lab service: nothing here</p>")

    def log_message(self, *a):
        pass


# ---- raw TCP side port (n10): below HTTP, plain words over the wire ----

def handle_raw(conn, clients):
    try:
        conn.settimeout(90)

        def send(msg):
            conn.sendall(msg.encode())

        def recv_line():
            buf = b""
            while b"\n" not in buf:
                chunk = conn.recv(1024)
                if not chunk:
                    return None
                buf += chunk
            return buf.decode(errors="replace").strip()

        send("== lab raw port (no HTTP down here) ==\n"
             "who is knocking? (your username): ")
        username = recv_line()
        key = key_for(username or "")
        if key not in clients:
            send("unknown student. bye.\n")
            return
        a, b = random.randint(10, 99), random.randint(10, 99)
        send(f"fine, {username}. prove you can count: {a}+{b} = ")
        if recv_line() != str(a + b):
            send("wrong. bye.\n")
            return
        send("and your vault code (from ~/netlab/code.txt): ")
        if recv_line() != code_for(key):
            send("wrong code. bye.\n")
            return
        send("access granted: " + load_flags().get(
            "n10-rawport", {}).get(username, "FLAG{missing}") + "\n")
    except (OSError, ValueError):
        pass
    finally:
        try:
            conn.close()
        except OSError:
            pass


def raw_port_server():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", 8902))
    srv.listen(16)
    while True:
        conn, _ = srv.accept()
        threading.Thread(target=handle_raw, args=(conn, users_by_key()),
                         daemon=True).start()


if __name__ == "__main__":
    threading.Thread(target=raw_port_server, daemon=True).start()
    HTTPServer(("127.0.0.1", 8901), H).serve_forever()
