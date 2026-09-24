"""Empty: the only code in trash that destroys data.

spec: D4@ec606da69e, P1@ec60e192cb, S4@54a885a968
"""

import datetime
import os
import shutil

DEFAULT_DAYS = 30                                                        # spec: S4@54a885a968


def _size(path):
    if os.path.islink(path) or not os.path.isdir(path):
        return os.lstat(path).st_size
    total = 0
    for d, _, files in os.walk(path):
        for f in files:
            try:
                total += os.lstat(os.path.join(d, f)).st_size
            except OSError:
                pass
    return total


def empty(can, days=DEFAULT_DAYS, now=None):
    """Destroy entries deleted more than `days` days ago (days=0: all of them).
    Returns (entries destroyed, bytes freed). An info file whose file is already
    gone is removed too; a file with no info file is left alone, because
    nothing says what it is."""
    now = now or datetime.datetime.now()
    cutoff = now - datetime.timedelta(days=days)
    count = freed = 0
    for e in can.entries():
        if days and e.deleted > cutoff:
            continue
        if e.present:
            freed += _size(e.file)
            if os.path.isdir(e.file) and not os.path.islink(e.file):
                shutil.rmtree(e.file)
            else:
                os.unlink(e.file)
        os.unlink(e.info)
        count += 1
    return count, freed
