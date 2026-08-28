#!/bin/bash
# mybox — the one-word door into your own private Linux lab.
# Students run this on the shared host; it drops them in as ROOT of their
# own box. Only the caller's OWN box is ever touched (SUDO_USER, no args).
exec /usr/bin/sudo /usr/local/sbin/studentctl-box enter
