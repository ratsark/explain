"""Golden test: the aircraft/cas example pair reports exactly what it was written to show."""

import unittest
from collections import Counter
from pathlib import Path

from explain.checks import downstream, externals, run_checks, upstream
from explain.parse import parse_spec

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


class ChildSpecTests(unittest.TestCase):
    def setUp(self):
        self.spec = parse_spec(EXAMPLES / "cas")
        self.findings = run_checks(self.spec)

    def test_no_errors(self):
        self.assertEqual([f.format() for f in self.findings if f.severity == "error"], [])

    def test_reports(self):
        codes = Counter(f.code for f in self.findings if f.severity == "report")
        self.assertEqual(codes["derived-from-parent"], 1)      # G3
        self.assertEqual(codes["undischarged-assumption"], 1)  # A2, not A1
        self.assertEqual(codes["orphan"], 0)
        self.assertEqual(codes["missing-ref"], 0)
        self.assertNotIn("unresolvable-namespace", codes)
        derived = [f.message.split()[0] for f in self.findings if f.code == "derived-from-parent"]
        self.assertEqual(derived, ["G3"])

    def test_cross_spec_links_resolve(self):
        ext = externals(self.spec)
        self.assertEqual(sorted(ext), ["aircraft"])
        self.assertIsNone(ext["aircraft"].error)
        self.assertIn("D1", ext["aircraft"].ids)
        tree = upstream(self.spec, "G1", ext)
        self.assertEqual(tree[2][0][:2], ("aircraft:D1", "Collision avoidance system"))

    def test_queries(self):
        self.assertEqual(sorted(i.id for i, _, _, _ in downstream(self.spec, "A2")), ["D2", "P2"])
        self.assertEqual(sorted(i.id for i, _, _, _ in downstream(self.spec, "G1")), ["D1", "D2", "P1"])
        self.assertEqual(self.spec.items["L4-V1"].prefix_level, 4)


class ParentSpecTests(unittest.TestCase):
    def setUp(self):
        self.spec = parse_spec(EXAMPLES / "aircraft")
        self.findings = run_checks(self.spec)

    def test_no_errors_and_child_resolves(self):
        self.assertEqual([f.format() for f in self.findings if f.severity == "error"], [])
        ext = externals(self.spec)
        self.assertEqual(sorted(ext), ["cas"])
        self.assertIn("G3", ext["cas"].ids)

    def test_reports(self):
        codes = Counter(f.code for f in self.findings if f.severity == "report")
        self.assertEqual(codes["orphan"], 0)
        self.assertEqual(codes["undischarged-assumption"], 1)   # A1: ATC separation is assumed
        self.assertEqual(codes["skip-level"], 0)


class AllocationTests(unittest.TestCase):
    def test_parent_allocations(self):
        import contextlib, io
        from explain.checks import allocations
        from explain.cli import main
        spec = parse_spec(EXAMPLES / "aircraft")
        served, obligations, unresolved = allocations(spec)
        self.assertEqual(unresolved, [])
        self.assertEqual(sorted((c, i.id) for c, i in served["D1"]), [("cas", "G1"), ("cas", "G2")])
        self.assertEqual([(c, a.id, p) for c, a, p in obligations], [("cas", "A1", "D2")])
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = main(["allocations", str(EXAMPLES / "aircraft")])
        self.assertEqual(code, 0)
        self.assertIn("D1", out.getvalue()); self.assertIn("cas:G1", out.getvalue()); self.assertIn("discharged-by D2", out.getvalue())
        self.assertIn("1 of 3 design elements", out.getvalue())


class TrashExampleTests(unittest.TestCase):
    """examples/trash is the README's walkthrough: a full five-level spec over working code."""

    ROOT = EXAMPLES / "trash"

    def setUp(self):
        self.spec = parse_spec(self.ROOT / "spec")
        self.findings = run_checks(self.spec)

    def test_clean(self):
        from explain.components import Components
        self.assertEqual([f.format() for f in self.findings if f.severity == "error"], [])
        codes = Counter(f.code for f in self.findings if f.severity == "report")
        # what is left is honest: beliefs about users nothing guarantees, and elided sections
        self.assertEqual(set(codes) - {"sections-absent"}, {"undischarged-assumption"})
        self.assertEqual(sorted(self.spec.levels), [0, 1, 2, 3, 4])
        self.assertEqual(Components(self.spec).crossings(), [])

    def test_code_index_is_current_and_nothing_drifted(self):
        import json
        from explain.checks import child_suspects, scan_sources, suspects
        committed = json.loads((self.ROOT / "spec" / "code-index.json").read_text())
        fresh, unresolved = scan_sources(self.spec, ".")
        self.assertEqual(unresolved, [])
        self.assertEqual(fresh["links"], committed["links"], "re-run: explain scan . -o spec/code-index.json spec")
        ext = externals(self.spec)
        self.assertEqual(suspects(self.spec, ext), [])
        self.assertEqual(child_suspects(self.spec, ext), [])

    def test_the_example_program_passes_its_own_tests(self):
        import subprocess
        import sys
        r = subprocess.run([sys.executable, "-m", "unittest", "discover", "tests"], cwd=self.ROOT,
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr[-2000:])
