"""Put: move files into the can.

spec: D2@fc94e5a920, S1@4e9cc2b09f, S3@0eefe6edd6, S7@86185d4e04
"""

import os

from .move import move


class TrashError(Exception):
    """A failure to report in rm's words; nothing was changed for this file."""


def put(can, path, recursive=False, now=None):
    """Trash one path. Returns the name it has in the can."""
    # abspath, not resolve: a symlink is trashed as itself, never its target (P5, S7)
    original = os.path.abspath(path)
    if not os.path.lexists(original):
        raise TrashError(f"cannot remove '{path}': No such file or directory")
    if can.contains(original):
        raise TrashError(f"refusing to trash '{path}': it is the trash can or holds it")
    if os.path.isdir(original) and not os.path.islink(original) and not recursive:
        raise TrashError(f"cannot remove '{path}': Is a directory")        # spec: S3@0eefe6edd6
    can.ensure()
    name = can.reserve(original, now)                                    # spec: S1@4e9cc2b09f (info first)
    try:
        move(original, can.files / name)
    except BaseException:
        can.release(name)
        raise
    return name
