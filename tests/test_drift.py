"""Drift detection: fingerprints, accepted links, suspect and untracked reports."""

import json

from explain.checks import accept, export_index, externals, run_checks, suspects
from explain.parse import ACCEPTED_FILE, parse_spec, save_accepted
from tests.helpers import SpecCase

L0 = "## G1 — One\nstatus: draft\n\nThe first goal.\n\n## G2 — Two\n\n- G2.1 — part: detail\n## A1 — Ass\n"
L1 = "## P1 — P\nserves: [G1, G2]\nassumes: A1\n"


class DriftTests(SpecCase):
    def accept_all(self, root):
        spec = parse_spec(root)
        counts = accept(spec, externals(spec), None)
        save_accepted(root, spec.accepted)
        return spec, counts

    def test_untracked_then_accept(self):
        root = self.make({"L0-purpose.md": L0, "L1-principles.md": L1})
        _, f = self.check(root)
        hits = self.assertCode(f, "untracked-links", "report", count=1)
        self.assertIn("3 link(s)", hits[0].message)
        spec, (new, updated, unchanged, unresolved) = self.accept_all(root)
        self.assertEqual((new, updated, unchanged, unresolved), (3, 0, 0, 0))
        self.assertTrue((root / ACCEPTED_FILE).is_file())
        _, f = self.check(root)
        self.assertNoCode(f, "untracked-links")
        self.assertNoCode(f, "suspect-link")
        self.assertNoCode(f, "bad-accepted-line")

    def test_target_change_makes_link_suspect(self):
        root = self.make({"L0-purpose.md": L0, "L1-principles.md": L1})
        self.accept_all(root)
        (root / "L0-purpose.md").write_text(L0.replace("The first goal.", "The first goal, reworded."), encoding="utf-8")
        _, f = self.check(root)
        hits = self.assertCode(f, "suspect-link", "report", count=1)
        self.assertIn("P1 serves G1", hits[0].message)
        self.assertEqual(hits[0].line, 2)
        spec = parse_spec(root)
        rows = suspects(spec, externals(spec))
        self.assertEqual([(i.id, l.target) for i, l, _, _ in rows], [("P1", "G1")])
        # accept only P1: clears it
        accept(spec, externals(spec), {"P1"})
        save_accepted(root, spec.accepted)
        _, f = self.check(root)
        self.assertNoCode(f, "suspect-link")

    def test_status_change_is_not_drift_but_refinement_change_is(self):
        root = self.make({"L0-purpose.md": L0, "L1-principles.md": L1})
        self.accept_all(root)
        (root / "L0-purpose.md").write_text(L0.replace("status: draft", "status: adopted"), encoding="utf-8")
        _, f = self.check(root)
        self.assertNoCode(f, "suspect-link")
        (root / "L0-purpose.md").write_text(L0.replace("part: detail", "part: new detail"), encoding="utf-8")
        _, f = self.check(root)
        hits = self.assertCode(f, "suspect-link", "report", count=1)
        self.assertIn("P1 serves G2", hits[0].message)

    def test_title_change_is_drift(self):
        root = self.make({"L0-purpose.md": L0, "L1-principles.md": L1})
        self.accept_all(root)
        (root / "L0-purpose.md").write_text(L0.replace("## A1 — Ass", "## A1 — Assumption, renamed"), encoding="utf-8")
        _, f = self.check(root)
        hits = self.assertCode(f, "suspect-link", "report", count=1)
        self.assertIn("P1 assumes A1", hits[0].message)

    def test_bad_accepted_line_is_error(self):
        root = self.make({"L0-purpose.md": L0, "L1-principles.md": L1, ACCEPTED_FILE: "# ok\nP1 serves G1 abc123\nnonsense line\n"})
        _, f = self.check(root)
        self.assertCode(f, "bad-accepted-line", "error", count=1)

    def test_cross_spec_drift_via_index_and_staleness(self):
        parent = self.make({"L0-purpose.md": "## G1 — Parent goal\n\nOriginal.\n"}, name="acft", subdir="acft")
        idx = export_index(parse_spec(parent))
        self.assertIn("fingerprint", idx["items"]["G1"])
        child = self.make({
            "parents/acft.index.json": json.dumps(idx),
            "L0-purpose.md": "## G1 — Child goal\nserves: acft:G1\n",
        }, name="tcas", manifest="name: tcas\nparents:\n  acft:\n    path: ../acft\n    index: parents/acft.index.json\n", subdir="tcas")
        spec, counts = self.accept_all(child)
        self.assertEqual(counts[0], 1)
        _, f = self.check(child)
        self.assertNoCode(f, "suspect-link")
        self.assertNoCode(f, "index-stale")
        # parent changes wording: live resolution sees it (suspect) and the snapshot is now stale
        (parent / "L0-purpose.md").write_text("## G1 — Parent goal\n\nReworded.\n", encoding="utf-8")
        _, f = self.check(child)
        self.assertCode(f, "suspect-link", "report", count=1)
        hits = self.assertCode(f, "index-stale", "report", count=1)
        self.assertIn("G1", hits[0].message)
        # index-only child: frozen snapshot, so no suspect until the snapshot is refreshed
        child2 = self.make({
            "parents/acft.index.json": json.dumps(idx),
            "L0-purpose.md": "## G1 — Child goal\nserves: acft:G1\n",
        }, name="tcas2", manifest="name: tcas2\nparents:\n  acft:\n    index: parents/acft.index.json\n", subdir="tcas2")
        self.accept_all(child2)
        _, f = self.check(child2)
        self.assertNoCode(f, "suspect-link")
        (child2 / "parents/acft.index.json").write_text(json.dumps(export_index(parse_spec(parent))), encoding="utf-8")
        _, f = self.check(child2)
        self.assertCode(f, "suspect-link", "report", count=1)
