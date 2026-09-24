"""Moving a file between the filesystem and the can without ever losing it.

spec: P2@2602edf1b7, D6@66ddcfadcc, S10@cfc99d2a43

A rename is atomic: at every instant the file is in exactly one place. When
the two paths are on different filesystems a rename is impossible, so the
file is copied, the copy is flushed to disk, and only then is the source
removed. If anything fails before that point the partial copy is removed and
the source is untouched.
"""

import errno
import os
import shutil


def _remove(path):
    if os.path.isdir(path) and not os.path.islink(path):
        shutil.rmtree(path)
    else:
        os.unlink(path)


def _fsync(path):
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _copy(src, dest):
    if os.path.islink(src):
        os.symlink(os.readlink(src), dest)          # spec: S7@86185d4e04 (a link is moved as a link)
    elif os.path.isdir(src):
        shutil.copytree(src, dest, symlinks=True)
        for d, dirs, files in os.walk(dest):        # spec: S10@cfc99d2a43 (every file and directory flushed)
            for f in files:
                if not os.path.islink(os.path.join(d, f)):
                    _fsync(os.path.join(d, f))
            _fsync(d)
    else:
        shutil.copy2(src, dest)
        _fsync(dest)
    _fsync(os.path.dirname(dest))


def move(src, dest):
    """Move src to dest (dest must not exist). Returns "renamed" or "copied"."""
    try:
        os.rename(src, dest)
        return "renamed"
    except OSError as e:
        if e.errno != errno.EXDEV:
            raise
    try:
        _copy(src, dest)
    except BaseException:
        if os.path.lexists(dest):
            _remove(dest)
        raise
    _remove(src)
    return "copied"
