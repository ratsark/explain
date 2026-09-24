"""The command line: rm's grammar for deleting, options for everything else.

spec: D5@7c20a04012, P3@17f9886937, S6@c1085aa6d5, S8@1f65af996e
"""

import sys

from .can import Can
from .empty import DEFAULT_DAYS, empty
from .put import TrashError, put
from .restore import listing, restore

USAGE = """usage: trash [-rRfiv] [--] FILE...        move files to the trash
       trash --list                       what is in the trash
       trash --restore NAME [--to PATH]   put NAME back where it was (or at PATH)
       trash --empty [--older-than DAYS | --all]   destroy entries (default: older than 30 days)"""

SHORT = set("rRfiv")
LONG = {"--recursive": "r", "--force": "f", "--interactive": "i", "--verbose": "v"}


def _err(msg):
    print(f"trash: {msg}", file=sys.stderr)


def main(argv, can=None, stdin=None):
    can = can or Can()
    stdin = stdin or sys.stdin
    if argv[:1] == ["--list"]:
        for name, deleted, original in listing(can):
            print(f"{deleted:%Y-%m-%d %H:%M}  {name}  (from {original})")
        return 0
    if argv[:1] == ["--restore"]:
        rest = argv[1:]
        to = None
        if "--to" in rest:
            i = rest.index("--to")
            to = rest[i + 1] if i + 1 < len(rest) else None
            rest = rest[:i] + rest[i + 2:]
        if len(rest) != 1 or ("--to" in argv and to is None):
            print(USAGE, file=sys.stderr)
            return 2
        try:
            print(restore(can, rest[0], to))
            return 0
        except (TrashError, OSError) as e:
            _err(e)
            return 1
    if argv[:1] == ["--empty"]:
        rest = argv[1:]
        days = DEFAULT_DAYS
        if rest == ["--all"]:
            days = 0
        elif len(rest) == 2 and rest[0] == "--older-than" and rest[1].isdigit() and int(rest[1]) > 0:
            days = int(rest[1])
        elif rest:
            print(USAGE, file=sys.stderr)
            return 2
        n, freed = empty(can, days)
        print(f"destroyed {n} entr{'y' if n == 1 else 'ies'}, freed {freed} bytes")
        return 0

    # rm's grammar. Parse everything before touching anything: an option we do
    # not support stops the whole command (P3), so nothing is half-done.
    flags, files, done = set(), [], False
    for a in argv:
        if done or a == "-" or not a.startswith("-"):
            files.append(a)
        elif a == "--":
            done = True
        elif a in LONG:
            flags.add(LONG[a])
        elif a in ("-h", "--help"):
            print(USAGE)
            return 0
        elif not a.startswith("--") and set(a[1:]) <= SHORT:
            flags |= set(a[1:])
        else:
            _err(f"unsupported option '{a}'; nothing was moved")
            print(USAGE, file=sys.stderr)
            return 2
    if not files:
        if "f" in flags:
            return 0
        print(USAGE, file=sys.stderr)
        return 2
    status = 0                                                           # spec: S6@c1085aa6d5
    for f in files:
        if "i" in flags and "f" not in flags:
            print(f"trash: move '{f}' to the trash? ", end="", file=sys.stderr, flush=True)
            if not stdin.readline().strip().lower().startswith("y"):
                continue
        try:
            name = put(can, f, recursive=bool(flags & {"r", "R"}))
            if "v" in flags:
                print(f"trashed '{f}' as {name}")
        except TrashError as e:
            if "f" in flags and "No such file" in str(e):
                continue
            _err(e)
            status = 1
        except OSError as e:
            _err(f"cannot trash '{f}': {e.strerror}")
            status = 1
    return status
