"""The can: where trashed files live and how each one is described.

spec: D1@2dda9b9122, S2@82c356c26c, S9@66901becb0

Layout follows the freedesktop.org Trash specification, so a desktop file
manager shows the same entries: $XDG_DATA_HOME/Trash/files/NAME holds the
file and $XDG_DATA_HOME/Trash/info/NAME.trashinfo says where it came from and
when. Nothing else is stored anywhere.
"""

import datetime
import os
import urllib.parse
from pathlib import Path

INFO_SUFFIX = ".trashinfo"


class Entry:
    def __init__(self, name, original, deleted, can):
        self.name = name
        self.original = original          # absolute path the file was trashed from
        self.deleted = deleted            # datetime, local time, as the spec writes it
        self.file = can.files / name
        self.info = can.info / (name + INFO_SUFFIX)

    @property
    def present(self):
        return os.path.lexists(self.file)


class Can:
    def __init__(self, root=None):
        if root is None:
            data = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
            root = Path(data) / "Trash"
        self.root = Path(root)
        self.files = self.root / "files"
        self.info = self.root / "info"

    def ensure(self):
        for d in (self.files, self.info):
            d.mkdir(parents=True, exist_ok=True, mode=0o700)

    def contains(self, path):
        """True if path is the can or inside it (trashing those would lose the can itself)."""
        p = Path(os.path.abspath(path))
        return p == self.root or self.root in p.parents or p in self.root.parents

    # spec: S2@82c356c26c
    def reserve(self, original, now=None):
        """Claim a free NAME for `original` by creating its info file exclusively.
        Collisions become NAME.2, NAME.3, ...; the O_EXCL create is the lock, so
        two trash processes can never claim the same name."""
        now = now or datetime.datetime.now()
        base = Path(original).name
        body = ("[Trash Info]\n"
                f"Path={urllib.parse.quote(str(original))}\n"
                f"DeletionDate={now.strftime('%Y-%m-%dT%H:%M:%S')}\n").encode()
        n = 1
        while True:
            name = base if n == 1 else f"{base}.{n}"
            n += 1
            if os.path.lexists(self.files / name):
                continue
            try:
                fd = os.open(self.info / (name + INFO_SUFFIX), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            except FileExistsError:
                continue
            try:
                os.write(fd, body)
                os.fsync(fd)
            finally:
                os.close(fd)
            return name

    def release(self, name):
        """Give back a reserved name whose move did not happen."""
        try:
            os.unlink(self.info / (name + INFO_SUFFIX))
        except FileNotFoundError:
            pass

    def entries(self):
        """Every well-formed info file, oldest first. Malformed ones are skipped, never deleted."""
        out = []
        if not self.info.is_dir():
            return out
        for info in self.info.glob("*" + INFO_SUFFIX):
            fields = {}
            try:
                for line in info.read_text(encoding="utf-8").splitlines():
                    if "=" in line:
                        k, v = line.split("=", 1)
                        fields[k.strip()] = v.strip()
                original = urllib.parse.unquote(fields["Path"])
                deleted = datetime.datetime.strptime(fields["DeletionDate"], "%Y-%m-%dT%H:%M:%S")
            except (OSError, KeyError, ValueError):
                continue
            out.append(Entry(info.name[: -len(INFO_SUFFIX)], original, deleted, self))
        return sorted(out, key=lambda e: (e.deleted, e.name))

    def find(self, name):
        for e in self.entries():
            if e.name == name:
                return e
        return None
