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
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

MANIFEST = sys.argv[1] if len(sys.argv) > 1 else \
    "/root/helli-10th-codebase/studentctld/ctf/manifest.json"

SHARE_NAMES = ["report-q1.txt", "notes.txt", "team.txt",
               "todo.txt", "backup.sql", "readme.md"]

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


class H(BaseHTTPRequestHandler):
    def _send(self, code, body=b"", headers=()):
        self.send_response(code)
        for k, v in headers:
            self.send_header(k, v)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parts = self.path.strip("/").split("/")
        if len(parts) < 3 or parts[0] != "lab":
            return self._send(404, b"<p>lab service: nothing here</p>")
        key = parts[1]
        username = users_by_key().get(key)
        if username is None:
            return self._send(404, b"<p>lab service: unknown key</p>")
        flags = load_flags()

        def flag(ch):
            return flags.get(ch, {}).get(username,
                                         "FLAG{missing}").encode()

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
            return self._send(200, b"<h1>farm door</h1>"
                                   b"<p>FAKEFLAG{decoy-door}</p>")
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
        return self._send(404, b"<p>lab service: nothing here</p>")

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    HTTPServer(("127.0.0.1", 8901), H).serve_forever()
