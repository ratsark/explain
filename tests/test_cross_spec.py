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
