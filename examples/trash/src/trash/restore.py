"""Restore and list: getting a file back.

spec: D3@fdca28b6a1, S5@751a0d2781
"""

import os
from pathlib import Path

from .move import move
from .put import TrashError


def listing(can):
    """(name, deleted, original) for every entry whose file is present, oldest first."""
    return [(e.name, e.deleted, e.original) for e in can.entries() if e.present]


def restore(can, name, to=None):
    """Move entry NAME back to its original path, or to `to`. Never overwrites."""
    entry = can.find(name)
    if entry is None or not entry.present:
        raise TrashError(f"no entry '{name}' in the trash (see trash --list)")
    target = Path(os.path.abspath(to)) if to else Path(entry.original)
    if os.path.lexists(target):                                          # spec: S5@751a0d2781
        raise TrashError(f"'{target}' exists; restore elsewhere with --to PATH")
    target.parent.mkdir(parents=True, exist_ok=True)
    move(entry.file, target)
    os.unlink(entry.info)
    return target
