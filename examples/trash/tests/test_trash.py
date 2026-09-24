"""Tests for the example trash program. Run from examples/trash:

    python3 -m unittest discover tests
"""

import contextlib
import datetime
import errno
import io
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from trash import move as move_mod                     # noqa: E402
from trash.can import Can                              # noqa: E402
from trash.cli import main                             # noqa: E402
from trash.empty import empty                          # noqa: E402
from trash.put import TrashError, put                  # noqa: E402
from trash.restore import listing, restore             # noqa: E402


class Case(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.can = Can(self.tmp / "Trash")
        self.work = self.tmp / "work"
        self.work.mkdir()

    def tearDown(self):
        self._tmp.cleanup()

    def file(self, name, text="data"):
        p = self.work / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
        return p

    def cli(self, *argv, stdin=""):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(list(argv), can=self.can, stdin=io.StringIO(stdin))
        return code, out.getvalue(), err.getvalue()


class RoundTripTests(Case):
    # spec-guard: G1@522e594d1a, D2@fc94e5a920, D3@fdca28b6a1
    def test_put_then_restore_gives_the_same_file_back(self):
        p = self.file("notes.txt", "hello")
        name = put(self.can, p)
        self.assertFalse(p.exists())
        self.assertEqual((self.can.files / name).read_text(), "hello")
        self.assertEqual([n for n, _, _ in listing(self.can)], ["notes.txt"])
        restore(self.can, name)
        self.assertEqual(p.read_text(), "hello")
        self.assertEqual(listing(self.can), [])


class LayoutTests(Case):
    # spec-guard: D1@2dda9b9122, S1@4e9cc2b09f, S2@82c356c26c
    def test_info_file_is_freedesktop_shaped_and_written_first(self):
        p = self.file("a b.txt")
        seen = []
        real_move = move_mod.move

        def spy(src, dest):
            seen.append(sorted(x.name for x in self.can.info.iterdir()))
            return real_move(src, dest)
        with mock.patch("trash.put.move", spy):
            put(self.can, p, now=datetime.datetime(2026, 9, 24, 12, 0, 0))
        self.assertEqual(seen, [["a b.txt.trashinfo"]])       # S1: info exists before the move
        text = (self.can.info / "a b.txt.trashinfo").read_text()
        self.assertIn("Path=" + str(p).replace(" ", "%20"), text)
        self.assertIn("DeletionDate=2026-09-24T12:00:00", text)

    def test_collisions_get_numbered_names(self):
        names = [put(self.can, self.file("x")) for _ in range(3)]
        self.assertEqual(names, ["x", "x.2", "x.3"])

    def test_failed_move_releases_the_name(self):
        p = self.file("y")
        with mock.patch("trash.put.move", side_effect=PermissionError(13, "Permission denied")):
            with self.assertRaises(PermissionError):
                put(self.can, p)
        self.assertTrue(p.exists())
        self.assertEqual(list(self.can.info.iterdir()), [])


class CrossDeviceTests(Case):
    # spec-guard: S10@cfc99d2a43, C2@056f8c570c, P2@2602edf1b7, D6@66ddcfadcc
    def test_exdev_copies_then_removes(self):
        p = self.file("big.bin", "x" * 1000)
        with mock.patch("os.rename", side_effect=OSError(errno.EXDEV, "cross-device")):
            name = put(self.can, p)
        self.assertFalse(p.exists())
        self.assertEqual((self.can.files / name).read_text(), "x" * 1000)

    def test_exdev_moves_a_directory_whole(self):
        self.file("tree/a/b.txt", "deep")
        with mock.patch("os.rename", side_effect=OSError(errno.EXDEV, "cross-device")):
            name = put(self.can, self.work / "tree", recursive=True)
        self.assertFalse((self.work / "tree").exists())
        self.assertEqual((self.can.files / name / "a" / "b.txt").read_text(), "deep")

    def test_a_failed_copy_leaves_the_original_and_no_partial_copy(self):
        p = self.file("big.bin", "x" * 1000)
        with mock.patch("os.rename", side_effect=OSError(errno.EXDEV, "cross-device")), \
             mock.patch("shutil.copy2", side_effect=OSError(errno.ENOSPC, "No space left on device")):
            with self.assertRaises(OSError):
                put(self.can, p)
        self.assertEqual(p.read_text(), "x" * 1000)
        self.assertEqual(list(self.can.files.iterdir()), [])
        self.assertEqual(list(self.can.info.iterdir()), [])


class SafetyTests(Case):
    # spec-guard: C1@0997b6c388, P5@614ed69307, S3@0eefe6edd6, S5@751a0d2781, S7@86185d4e04
    def test_symlink_is_trashed_as_a_link(self):
        target = self.file("target.txt", "keep me")
        link = self.work / "link"
        link.symlink_to(target)
        name = put(self.can, link)
        self.assertTrue(os.path.islink(self.can.files / name))
        self.assertEqual(target.read_text(), "keep me")

    def test_directory_needs_recursive(self):
        self.file("d/inner.txt")
        with self.assertRaisesRegex(TrashError, "Is a directory"):
            put(self.can, self.work / "d")
        put(self.can, self.work / "d", recursive=True)
        self.assertFalse((self.work / "d").exists())

    def test_restore_never_overwrites(self):
        p = self.file("r.txt", "old")
        name = put(self.can, p)
        self.file("r.txt", "new")
        with self.assertRaisesRegex(TrashError, "exists"):
            restore(self.can, name)
        self.assertEqual(p.read_text(), "new")
        restore(self.can, name, to=self.work / "r.old.txt")
        self.assertEqual((self.work / "r.old.txt").read_text(), "old")

    def test_the_can_cannot_trash_itself(self):
        self.can.ensure()
        with self.assertRaisesRegex(TrashError, "trash can"):
            put(self.can, self.can.root)


class EmptyTests(Case):
    # spec-guard: P1@ec60e192cb, D4@ec606da69e, S4@54a885a968
    def test_default_keeps_the_last_thirty_days(self):
        now = datetime.datetime(2026, 9, 24)
        put(self.can, self.file("old"), now=now - datetime.timedelta(days=31))
        put(self.can, self.file("new"), now=now - datetime.timedelta(days=29))
        n, freed = empty(self.can, now=now)
        self.assertEqual((n, freed), (1, 4))
        self.assertEqual([x for x, _, _ in listing(self.can)], ["new"])

    def test_all_and_stale_info(self):
        put(self.can, self.file("a"))
        name = put(self.can, self.file("b"))
        os.unlink(self.can.files / name)                  # file vanished: info is stale
        self.assertEqual(empty(self.can, days=0)[0], 2)
        self.assertEqual(list(self.can.info.iterdir()), [])


class CliTests(Case):
    # spec-guard: G2@a461ec0df3, P3@17f9886937, S6@c1085aa6d5, S8@1f65af996e
    def test_rm_grammar_and_exit_codes(self):
        a, b = self.file("a"), self.file("b")
        self.assertEqual(self.cli("-v", str(a), str(b))[0], 0)
        code, _, err = self.cli(str(self.work / "missing"))
        self.assertEqual(code, 1)
        self.assertIn("No such file or directory", err)
        self.assertEqual(self.cli("-f", str(self.work / "missing"))[0], 0)

    def test_unsupported_option_moves_nothing(self):
        a = self.file("a")
        code, _, err = self.cli("--one-file-system", str(a))
        self.assertEqual(code, 2)
        self.assertTrue(a.exists())
        self.assertIn("nothing was moved", err)

    def test_a_file_named_list_is_trashed_not_listed(self):
        lst = self.file("list")
        os.chdir(self.work)
        try:
            self.assertEqual(self.cli("list")[0], 0)
        finally:
            os.chdir(self.tmp)
        self.assertFalse(lst.exists())
        code, out, _ = self.cli("--list")
        self.assertIn("list  (from", out)

    def test_interactive_asks(self):
        a = self.file("a")
        self.cli("-i", str(a), stdin="n\n")
        self.assertTrue(a.exists())
        self.cli("-i", str(a), stdin="y\n")
        self.assertFalse(a.exists())


if __name__ == "__main__":
    unittest.main()
