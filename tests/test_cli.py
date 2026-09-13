import contextlib
import io

from explain.cli import main
from tests.helpers import SpecCase


class CliTests(SpecCase):
    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def spec(self):
        return self.make({
            "L0-purpose.md": "## Mission\n## Goals\n## G1 — One\nstatus: adopted\n\nBody of one.\n## A1 — Ass\n",
            "L1-principles.md": "## P1 — P\nserves: G1\nassumes: A1\n## P2 — orphan\n",
        })

    def test_check_exit_codes(self):
        root = self.spec()
        code, out, _ = self.run_cli("check", str(root))
        self.assertEqual(code, 0, out)
        self.assertIn("0 errors", out)
        code, out, _ = self.run_cli("check", "--strict", str(root))
        self.assertEqual(code, 1)
        (root / "L1-principles.md").write_text("## P1 — P\nserves: G9\n", encoding="utf-8")
        code, out, _ = self.run_cli("check", str(root))
        self.assertEqual(code, 1)
        self.assertIn("[unknown-id]", out)
        code, out, _ = self.run_cli("check", "--quiet", str(root))
        self.assertNotIn("report:", out)
        code, _, err = self.run_cli("check", str(root / "nope"))
        self.assertEqual(code, 2)

    def test_show(self):
        root = self.spec()
        code, out, _ = self.run_cli("show", "g1", str(root))
        self.assertEqual(code, 0)
        self.assertIn("G1 — One", out)
        self.assertIn("goal at L0", out)
        self.assertIn("served-by: P1", out)
        self.assertIn("Body of one.", out)
        code, out, _ = self.run_cli("show", "A1", str(root))
        self.assertIn("assumed-by: P1", out)
        code, _, err = self.run_cli("show", "G7", str(root))
        self.assertEqual(code, 1)
        self.assertIn("not defined", err)

    def test_bare_id_means_show(self):
        root = self.spec()
        code, out, _ = self.run_cli("g1", str(root))
        self.assertEqual(code, 0)
        self.assertIn("G1 — One", out)
        code, out, _ = self.run_cli("L4-V1", str(root))
        self.assertEqual(code, 1)   # routed to show, which reports it undefined

    def test_show_resolves_old_id(self):
        root = self.make({"L0-purpose.md": "## G1 — One\n", "L1-principles.md": "## P4 — Moved\nserves: G1\nwas: G4\n"})
        code, out, _ = self.run_cli("show", "G4", str(root))
        self.assertEqual(code, 0)
        self.assertIn("G4 was re-homed as P4", out)

    def test_serves_why_orphans(self):
        root = self.spec()
        code, out, _ = self.run_cli("serves", "G1", str(root))
        self.assertEqual(code, 0)
        self.assertIn("P1", out)
        code, out, _ = self.run_cli("serves", "P2", str(root))
        self.assertEqual(code, 1)
        code, out, _ = self.run_cli("why", "P1", str(root))
        self.assertEqual(code, 0)
        self.assertIn("  G1 — One", out)
        code, out, _ = self.run_cli("orphans", str(root))
        self.assertEqual(code, 0)
        self.assertIn("P2", out)
        self.assertIn("1 orphans", out)

    def test_accept_and_drift(self):
        root = self.spec()
        code, out, err = self.run_cli("accept", str(root))
        self.assertEqual(code, 2)
        code, out, _ = self.run_cli("accept", "--all", str(root))
        self.assertEqual(code, 0)
        self.assertIn("2 new", out)
        code, out, _ = self.run_cli("drift", str(root))
        self.assertEqual(code, 1)
        self.assertIn("no drift", out)
        (root / "L0-purpose.md").write_text("## Mission\n## Goals\n## G1 — One\nstatus: adopted\n\nBody of one, changed.\n## A1 — Ass\n", encoding="utf-8")
        code, out, _ = self.run_cli("drift", str(root))
        self.assertEqual(code, 0)
        self.assertIn("G1 — One changed", out)
        self.assertIn("explain accept P1", out)
        code, out, _ = self.run_cli("accept", "P1", str(root))
        self.assertEqual(code, 0)
        self.assertIn("1 re-accepted", out)
        code, out, _ = self.run_cli("drift", str(root))
        self.assertEqual(code, 1)

    def test_review(self):
        root = self.spec()
        code, out, _ = self.run_cli("review", str(root))
        self.assertEqual(code, 0)
        self.assertIn("L0 purpose: 2 items", out)
        self.assertIn("L1 principles: 2 items", out)
        code, out, _ = self.run_cli("review", "L1", str(root))
        self.assertEqual(code, 0)
        self.assertIn("P1 — P", out)
        self.assertIn("serves: G1 (One)", out)
        self.assertIn("P2 — orphan", out)
        self.assertIn("⚑ orphan", out)
        code, _, err = self.run_cli("review", "L9", str(root))
        self.assertEqual(code, 2)

    def test_outline_export_assumptions_patterns(self):
        root = self.spec()
        code, out, _ = self.run_cli("outline", str(root))
        self.assertEqual(code, 0)
        self.assertIn("G1 — One [adopted]", out)
        self.assertIn("L2 architecture: (absent)", out)
        self.assertIn("sections not yet present: Constraints", out)
        code, out, _ = self.run_cli("export", "-o", str(root / "out.json"), str(root))
        self.assertEqual(code, 0)
        self.assertTrue((root / "out.json").exists())
        code, out, _ = self.run_cli("assumptions", str(root))
        self.assertIn("1 assumptions, 1 undischarged", out)
        code, out, _ = self.run_cli("--patterns")
        self.assertEqual(code, 0)
        self.assertIn("DECLARED MISSES", out)
        code, _, _ = self.run_cli()
        self.assertEqual(code, 2)


class AliasCliTests(SpecCase):
    def run_cli(self, *argv):
        import contextlib, io
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def test_show_by_alias(self):
        root = self.make({"L0-purpose.md": "## G1 — One\n", "L1-principles.md": "## P1 — The band keeps itself\nserves: G1\naka: [law 16]\n"})
        code, out, _ = self.run_cli("law 16", str(root))
        self.assertEqual(code, 0)
        self.assertIn("alias of P1", out)
        self.assertIn("aka: [law 16]", out)
        code, out, _ = self.run_cli("why", "law 16", str(root))
        self.assertEqual(code, 0)
        code, _, err = self.run_cli("law 99", str(root))
        self.assertEqual(code, 1)
        self.assertIn("not an id or a known alias", err)


class SymmetricRelationTests(SpecCase):
    def test_conflicts_with_shown_once(self):
        import contextlib, io
        root = self.make({"L0-purpose.md": "## G1 — One\nconflicts-with: G2\n## G2 — Two\n"})
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            main(["G1", str(root)])
        self.assertEqual(out.getvalue().count("conflicts-with"), 1)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            main(["G2", str(root)])
        self.assertIn("conflicts-with: G1", out.getvalue())


class IsolatedCliTests(SpecCase):
    def test_isolated_and_summary(self):
        import contextlib, io
        root = self.make({"L0-purpose.md": "## G1 — linked\n## G2 — lonely\nbuilt: shipped\n", "L1-principles.md": "## P1 — P\nserves: G1\n"})
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = main(["isolated", str(root)])
        self.assertEqual(code, 0)
        self.assertIn("G2", out.getvalue())
        self.assertIn("1 isolated of 3", out.getvalue())
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            main(["check", str(root)])
        self.assertIn("isolated (no link either way): 1 of 3 (33%); built: shipped 1, unstated 2", out.getvalue())
