import json

from explain.checks import export_index
from explain.parse import parse_spec
from tests.helpers import SpecCase

PARENT_L0 = "## G1 — Parent goal\n"
PARENT_L2 = "## D1 — The child component\nserves: G1\n## D2 — Altimeter\nserves: G1\n"


class CrossSpecTests(SpecCase):
    def parent(self):
        return self.make({"L0-purpose.md": PARENT_L0, "L2-architecture.md": PARENT_L2}, name="acft", subdir="acft")

    def test_child_resolves_parent_by_path(self):
        self.parent()
        child = self.make({
            "L0-purpose.md": (
                "## G1 — Issue advisories\nserves: acft:D1\n"
                "## G2 — Derived\n"
                "## A1 — Altitude is accurate\ndischarged-by: acft:D2\n"
                "## A2 — Nobody discharges\n"
            ),
            "L1-principles.md": "## P1 — P\nserves: [G1, acft:D1]\n",
        }, name="tcas", manifest="name: tcas\nparents:\n  acft:\n    path: ../acft\n", subdir="tcas")
        _, f = self.check(child)
        self.assertNoErrors(f)
        self.assertCode(f, "derived-from-parent", "report", count=1)
        self.assertCode(f, "undischarged-assumption", "report", count=1)
        self.assertCode(f, "cross-spec-serves-below-top", "report", count=1)
        self.assertNoCode(f, "unresolvable-namespace")

    def test_child_resolves_parent_by_index(self):
        p = self.parent()
        idx = export_index(parse_spec(p))
        child = self.make({
            "parents/acft.index.json": json.dumps(idx),
            "L0-purpose.md": "## G1 — Issue advisories\nserves: acft:D1\n## G2 — Bad\nserves: acft:D9\n",
        }, name="tcas", manifest="name: tcas\nparents:\n  acft:\n    index: parents/acft.index.json\n", subdir="tcas")
        _, f = self.check(child)
        hits = self.assertCode(f, "unknown-id", "error", count=1)
        self.assertIn("D9", hits[0].message)

    def test_unresolvable_parent_is_a_report(self):
        child = self.make({"L0-purpose.md": "## G1 — One\nserves: acft:D1\n"},
                          name="tcas", manifest="name: tcas\nparents:\n  acft:\n    path: ../nowhere\n  other:\n", subdir="tcas")
        _, f = self.check(child)
        self.assertCode(f, "unresolvable-namespace", "report", count=2)
        self.assertNoErrors(f)

    def test_parent_name_mismatch(self):
        self.parent()
        child = self.make({"L0-purpose.md": "## G1 — One\nserves: plane:D1\n"},
                          name="tcas", manifest="name: tcas\nparents:\n  plane:\n    path: ../acft\n", subdir="tcas")
        _, f = self.check(child)
        hits = self.assertCode(f, "unresolvable-namespace", "report", count=1)
        self.assertIn("calls itself 'acft'", hits[0].message)

    def test_parent_sees_child(self):
        self.make({"L0-purpose.md": "## G1 — Child goal\nserves: acft:D1\n"}, name="tcas", subdir="tcas")
        parent = self.make({"L0-purpose.md": PARENT_L0, "L2-architecture.md": PARENT_L2 + "depends-on: tcas:G1\n"},
                           name="acft", manifest="name: acft\nchildren:\n  - path: ../tcas\n", subdir="acft")
        _, f = self.check(parent)
        self.assertNoErrors(f)

    def test_export_shape(self):
        p = self.parent()
        idx = export_index(parse_spec(p))
        self.assertEqual(idx["name"], "acft")
        self.assertEqual(idx["items"]["D1"]["level"], 2)
        self.assertIn({"from": "D1", "relation": "serves", "to": "G1"}, idx["links"])


class DerivedFromParentKindsTests(SpecCase):
    def test_free_kinds_at_child_top_are_not_derived(self):
        self.make({"L0-purpose.md": "## G1 — Parent goal\n## D1 — Element\nserves: G1\n"}, name="biz", subdir="biz")
        child = self.make({"L0-purpose.md": (
            "## Q1 — Which partner owns the domain?\nstatus: proposed\n"
            "## A1 — The partner exists\n## X1 — No budget yet\n## H1 — A risk\n## E1 — A bar\n"
            "## C1 — A constraint\n## R1 — A requirement\n"
            "## G1 — Served\nserves: biz:D1\n## G2 — Derived goal\n"
        )}, name="screen", manifest="name: screen\nparents:\n  biz:\n    path: ../biz\n", subdir="screen")
        _, f = self.check(child)
        hits = self.assertCode(f, "derived-from-parent", "report", count=1)
        self.assertIn("G2", hits[0].message)


class IndexChildTests(SpecCase):
    def test_child_index_joins_sweep_and_drift(self):
        parent = self.make({"L0-purpose.md": "## G1 — One\n", "L3-specs.md": "## S1 — A rule\nserves: G1\n\nThe rule.\n"},
                           name="acft", manifest="name: acft\nchildren:\n  - index: children/guards.index.json\n", subdir="acft")
        spec = parse_spec(parent)
        fp = spec.fingerprint("S1")
        idx = {"name": "guards", "items": {"T1": {"level": 4, "kind": "V", "title": "rule.test.ts", "fingerprint": "abc"},
                                            "T2": {"level": 4, "kind": "V", "title": "review-rule §3", "fingerprint": "def"}},
               "links": [{"from": "T1", "relation": "verifies", "to": "acft:S1", "accepted": fp},
                         {"from": "T2", "relation": "verifies", "to": "acft:S1"}]}
        (parent / "children").mkdir()
        (parent / "children/guards.index.json").write_text(json.dumps(idx), encoding="utf-8")
        spec = parse_spec(parent)
        from explain.checks import child_suspects, downstream, externals
        ext = externals(spec)
        self.assertEqual(sorted(ext), ["guards"]); self.assertIsNone(ext["guards"].error)
        rows = downstream(spec, "S1", ext)
        self.assertEqual(sorted(getattr(i, "qualified", i.id) for i, *_ in rows), ["guards:T1", "guards:T2"])
        self.assertEqual(sorted(getattr(i, "qualified", i.id) for i, *_ in downstream(spec, "G1", ext)), ["S1", "guards:T1", "guards:T2"])
        _, f = self.check(parent)
        self.assertNoCode(f, "child-link-suspect")
        (parent / "L3-specs.md").write_text("## S1 — A rule\nserves: G1\n\nThe rule, overturned.\n", encoding="utf-8")
        _, f = self.check(parent)
        hits = self.assertCode(f, "child-link-suspect", "report", count=1)   # T1 accepted a fingerprint; T2 did not
        self.assertIn("guards:T1 verifies S1", hits[0].message)
        self.assertEqual([(c, frm) for c, frm, *_ in child_suspects(parse_spec(parent), externals(parse_spec(parent)))], [("guards", "T1")])

    def test_export_carries_accepted_fingerprints(self):
        from explain.checks import accept, export_index, externals
        from explain.parse import save_accepted
        root = self.make({"L0-purpose.md": "## G1 — One\n", "L1-principles.md": "## P1 — P\nserves: G1\n"})
        spec = parse_spec(root)
        self.assertNotIn("accepted", export_index(spec)["links"][0])
        accept(spec, externals(spec), None); save_accepted(root, spec.accepted)
        link = export_index(parse_spec(root))["links"][0]
        self.assertEqual(link["accepted"], parse_spec(root).fingerprint("G1"))

    def test_allocations_from_index_child(self):
        from explain.checks import allocations
        parent = self.make({"L0-purpose.md": "## G1 — One\n", "L2-architecture.md": "## D1 — Elem\nserves: G1\n"},
                           name="acft", manifest="name: acft\nchildren:\n  - index: kid.json\n", subdir="acft")
        (parent / "kid.json").write_text(json.dumps({"name": "kid", "items": {"G1": {"level": 0, "kind": "G", "title": "child goal"}},
                                                     "links": [{"from": "G1", "relation": "serves", "to": "acft:D1"}]}), encoding="utf-8")
        served, obligations, unresolved = allocations(parse_spec(parent))
        self.assertEqual(unresolved, [])
        self.assertEqual([(c, i.id) for c, i in served["D1"]], [("kid", "G1")])
