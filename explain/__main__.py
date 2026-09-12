"""Entry point. Works both as `python3 -m explain` and as `python3 path/to/explain`
(a directory run directly has no package context, so we add its parent to the
path and import ourselves absolutely)."""

import sys

if __package__ in (None, ""):
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from explain.cli import main
else:
    from .cli import main

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
