#!/bin/bash
# mybox — the one-word door into your own private Linux lab.
# The sudoers rule allows students EXACTLY this: `studentctl-box enter`
# (argument-matched — no other box command is reachable by students).
exec /usr/bin/sudo /usr/local/sbin/studentctl-box enter
