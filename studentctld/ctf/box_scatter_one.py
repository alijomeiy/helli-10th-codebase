#!/usr/bin/env python3
"""box_scatter_one.py <username> — re-scatter one student's box flags.
Installed as /usr/local/sbin/studentctl-box-scatter by setup_boxinfra.sh
and invoked automatically by `studentctl-box reset <user>`."""
import sys

import box_scatter

def main():
    if len(sys.argv) < 2:
        raise SystemExit("usage: box_scatter_one.py <username>")
    sys.argv = ["box_scatter.py", "--one", sys.argv[1]]
    box_scatter.main()

if __name__ == "__main__":
    main()
