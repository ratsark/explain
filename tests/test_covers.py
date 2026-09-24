"""covers, scan (source citations as a child index) and orphans --suggested."""

import contextlib
import io
import json

from explain.checks import externals, run_checks, scan_sources, source_citations, suggested_parents, suspects
from explain.cli import main
from explain.parse import parse_spec
from tests.helpers import SpecCase


def run(*argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main(list(argv))
    return code, out.getvalue(), err.getvalue()


class CoversCase(SpecCase):
    def build(self, manifest="name: t\nprofile: software\nrefs-root: ..\n"):
        root = self.make({
            "L0-purpose.md": "## G1 — One\n## G2 — Two\n",
            "L1-principles.md": "## P1 — P\nserves: G1\n",
            "L2-architecture.md": "## D1 — Ledger\nserves: P1\nrefs: [src/ledger.ts]\n## D2 — Whole dir\nserves: P1\nrefs: [src/ui/]\n",
            "L3-specs.md": "## S1 — S\nserves: D1\nrefs: [src/ledger.ts, src/other.ts]\n\nSuggested parent (unrecorded in source): D2\n## S2 — T\nserves: D1\n\nSuggested parent (unrecorded in source): D9, D1\n",
        }, manifest=manifest)
        src = self.tmp / "src"
        (src / "ui").mkdir(parents=True)
        (src / "ledger.ts").write_text("// spec: D1, S1\nexport const a = 1;\n\n// spec: S2\nexport const b = 2;\n", encoding="utf-8")
        (src / "ui" / "view.ts").write_text("export const v = 1;\n", encoding="utf-8")
        (src / "ledger.test.ts").write_text("// spec-guard: S1\ntest('x', () => {});\n", encoding="utf-8")
        (src / "stray.ts").write_text("// spec: S99\n", encoding="utf-8")
        return root


class CitationTests(CoversCase):
    def test_source_citations_parse(self):
        self.assertEqual(source_citations("# spec: G1, D2.1@abc123\n/* spec-guard : S1 */\nno cite"),
                         [(1, "serves", [("G1", None), ("D2.1", "abc123")]), (2, "verifies", [("S1", None)])])

    def test_guard_form_of_the_first_deployment(self):
        # space-separated, level-prefixed free kinds, @? for unread, bold markdown key
        text = " * spec-guard: S1@0c87308d51 L4-V2@? D2.1\n**spec-guard:** S2@?\nspec: S1 S2, S3\n"
        self.assertEqual(source_citations(text), [
            (1, "verifies", [("S1", "0c87308d51"), ("L4-V2", None), ("D2.1", None)]),
            (2, "verifies", [("S2", None)]),
            (3, "serves", [("S1", None), ("S2", None), ("S3", None)])])
        root = self.make({
            "L0-purpose.md": "## G1 — One\n",
            "L3-specs.md": "## S1 — S\nserves: G1\n",
            "L4-realization/v.md": "## V2 — guard row\nverifies: S1\n",
        }, manifest="name: t\nprofile: software\nrefs-root: ..\n")
        (self.tmp / "t.test.ts").write_text(" * spec-guard: S1@? V2@?  L4-V2@?\n", encoding="utf-8")
        spec = parse_spec(root)
        index, unresolved = scan_sources(spec, ".")
        self.assertEqual(unresolved, [])
        self.assertEqual([l["to"] for l in index["links"]], ["t:S1", "t:V2"])
        self.assertNotIn("accepted", index["links"][0])
        code, out, _ = run("scan", "t.test.ts", "--accept", str(root))
        self.assertEqual(code, 0)
        line = (self.tmp / "t.test.ts").read_text()
        self.assertRegex(line, r"^ \* spec-guard: S1@[0-9a-f]{10} V2@[0-9a-f]{10}  L4-V2@[0-9a-f]{10}\n$")

    def test_covers_lists_refs_citations_and_chain(self):
        root = self.build()
        code, out, _ = run("covers", "src/ledger.ts", str(root))
        self.assertEqual(code, 0)
        self.assertIn("D1 ", out); self.assertIn("S1 ", out)
        self.assertIn(":1 serves D1", out); self.assertIn(":4 serves S2", out)
        self.assertIn("up-chain", out); self.assertIn("G1 — One", out)
        self.assertNotIn("D2", out.split("up-chain")[0])

    def test_covers_line_narrows_to_nearest_citation(self):
        root = self.build()
        code, out, _ = run("covers", "src/ledger.ts:5", str(root))
        self.assertEqual(code, 0)
        self.assertIn(":4 serves S2", out)
        self.assertNotIn(":1 serves", out)

    def test_covers_matches_a_directory_ref(self):
        root = self.build()
        code, out, _ = run("covers", "src/ui/view.ts", str(root))
        self.assertEqual(code, 0)
        self.assertIn("D2 ", out)

    def test_covers_nothing(self):
        root = self.build()
        code, out, _ = run("covers", "src/nothing.ts", str(root))
        self.assertEqual(code, 1)
        self.assertIn("nothing names", out)

    def test_scan_builds_child_index_and_drift_sees_it(self):
        root = self.build()
        spec = parse_spec(root)
        index, unresolved = scan_sources(spec, "src")
        self.assertEqual(unresolved, [("src/stray.ts", 1, "S99")])
        self.assertEqual(sorted(index["items"]), ["src/ledger.test.ts", "src/ledger.ts", "src/stray.ts"])
        links = {(l["from"], l["relation"], l["to"]) for l in index["links"]}
        self.assertEqual(links, {("src/ledger.ts", "serves", "t:D1"), ("src/ledger.ts", "serves", "t:S1"),
                                 ("src/ledger.ts", "serves", "t:S2"), ("src/ledger.test.ts", "verifies", "t:S1")})
        # write it, declare it as an index child, refresh the fingerprints in the source, then change S2
        code, out, err = run("scan", "src", "-o", str(self.tmp / "code-index.json"), str(root))
        self.assertEqual(code, 1); self.assertIn("S99", err); self.assertIn("declare it", out)
        (root / "spec.yaml").write_text("name: t\nprofile: software\nrefs-root: ..\nchildren:\n  - index: ../code-index.json\n", encoding="utf-8")
        spec = parse_spec(root)
        self.assertEqual(run_checks(spec) and [x for x in run_checks(spec) if x.severity == "error"], [])
        ext = externals(spec)
        self.assertEqual(sorted(ext), ["code"])
        code, out, _ = run("scan", "src/ledger.ts", "--accept", str(root))
        self.assertEqual(code, 0); self.assertIn("3 citation(s) updated", out)
        text = (self.tmp / "src/ledger.ts").read_text()
        self.assertRegex(text, r"// spec: D1@[0-9a-f]{10}, S1@[0-9a-f]{10}")
        run("scan", "src", "-o", str(self.tmp / "code-index.json"), str(root))
        code, out, _ = run("drift", str(root))
        self.assertEqual(code, 0)
        self.assertNotIn("in children", out)
        (root / "L3-specs.md").write_text((root / "L3-specs.md").read_text().replace("## S2 — T", "## S2 — T changed"), encoding="utf-8")
        code, out, _ = run("drift", str(root))
        self.assertEqual(code, 1)                       # drift only in a child still fails the gate
        self.assertIn("in children (1 link", out); self.assertIn("S2 — T changed", out)
        code, out, _ = run("covers", "src/ledger.ts", str(root))
        self.assertIn("ROW CHANGED", out)
        self.assertIn("fingerprint current", out)
        self.assertIn("code:src/ledger.ts", out)
        # D1 lies on S1's chain, so the chain is printed once, from S1
        chains = out.split("up-chain to the top:")[1]
        self.assertEqual(chains.count("\n  D1 — "), 0)
        self.assertIn("\n  S1 — ", chains)

    def test_orphans_suggested(self):
        root = self.build()
        spec = parse_spec(root)
        self.assertEqual([(it.id, ids) for it, ids in suggested_parents(spec)], [("S1", ["D2"]), ("S2", ["D9", "D1"])])
        code, out, _ = run("orphans", "--suggested", str(root))
        self.assertEqual(code, 0)
        self.assertIn("S1         -> D2", out)
        self.assertIn("S2         -> D1  (unknown: D9)", out)
        self.assertIn("2 rows", out)


class DiscoveryTests(SpecCase):
    def test_bare_commands_find_the_spec_like_git(self):
        import os
        root = self.make({"L0-purpose.md": "## G1 — One\n"}, subdir="proj/spec")
        deep = self.tmp / "proj" / "src" / "deep"
        deep.mkdir(parents=True)
        from explain.cli import locate_spec
        self.assertEqual(locate_spec(str(root)), root.resolve())
        self.assertEqual(locate_spec(str(self.tmp / "proj")), root.resolve())
        self.assertIsNone(locate_spec(str(deep)))            # an explicit path is not walked upward
        cwd = os.getcwd()
        os.chdir(deep)
        try:
            self.assertEqual(locate_spec(), root.resolve())
            code, out, _ = run("g1")
            self.assertEqual(code, 0)
            self.assertIn("G1 — One", out)
        finally:
            os.chdir(cwd)
