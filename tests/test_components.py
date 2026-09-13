"""Components, interfaces, boundaries (ARCHITECTURE.md section 13)."""

import contextlib
import io

from explain.cli import main
from explain.components import Components
from explain.parse import parse_spec
from tests.helpers import SpecCase

L0 = "## Mission\n\nA sentence nothing depends on.\n\n## Goals\n## G1 — One\n## G2 — Two\n## A1 — World fact\n"
L2 = (
    "## Components\n"
    "## D1 — Engine\nhides: how the day is simulated\nserves: G1\n\n"
    "### D1.1 — Interface: tick\ninterface: true\n\n"
    "### D1.2 — Internal scheduler\n\n"
    "## D2 — Server\nserves: G2\n\n"
    "### D2.1 — Interface: activity record\ninterface: true\n\n"
    "### D2.2 — Ingestion\ndepends-on: D1.1\n\n"
    "### D2.3 — Reaches into the engine\ndepends-on: D1.2\n\n"
    "## D3 — Web\npart-of: D2\ncomponent: true\n\n"
    "### D3.1 — View\ndepends-on: D2.2\n\n"
    "## D4 — Loose interface\ninterface: true\n"
)
L3 = "## S1 — Ruling inside engine\npart-of: D1\nserves: D1\n## S2 — Cross-cutting rule\nserves: G1\n"


class ComponentTests(SpecCase):
    def spec(self):
        return self.make({"L0-purpose.md": L0, "L2-architecture.md": L2, "L3-specs.md": L3})

    def test_membership_and_chain(self):
        spec = parse_spec(self.spec())
        c = Components(spec)
        self.assertEqual(sorted(c.nodes), ["D1", "D2", "D3"])
        self.assertEqual(c.of("D1.1"), "D1")           # sub-item of a component node
        self.assertEqual(c.of("S1"), "D1")             # explicit part-of
        self.assertEqual(c.of("D3"), "D2")             # nested component
        self.assertEqual(c.of("D3.1"), "D3")           # D3 declares component: true
        self.assertEqual(c.chain("D3"), ["D3", "D2"])
        self.assertEqual(c.src("D1"), "D1")             # a node's own links are the node's
        self.assertIsNone(c.of("S2"))                  # cross-cutting
        self.assertIsNone(c.of("G1"))
        self.assertEqual(c.of("D4"), None)

    def test_boundary_reports(self):
        _, f = self.check(self.spec())
        self.assertNoErrors(f)
        hits = self.assertCode(f, "boundary-crossing", "report")
        msgs = "\n".join(h.message for h in hits)
        self.assertIn("D2.3 (in D2) depends-on D1.2", msgs)      # sibling internals: crossing
        self.assertNotIn("D2.2", msgs)                              # via interface D1.1: fine
        self.assertNotIn("S1 ", msgs)                               # S1 serves its own component node
        self.assertNotIn("D3.1", msgs)                              # reaching up into the enclosing component: fine
        self.assertCode(f, "interface-without-component", "report", count=1)
        self.assertCode(f, "section-prose-only", "report", count=1)  # Mission holds prose only
        self.assertNoCode(f, "component-cycle")

    def test_component_cycle_and_part_of_errors(self):
        root = self.make({
            "L0-purpose.md": "## G1 — One\n",
            "L2-architecture.md": "## D1 — A\nhides: a\n### D1.1 — a1\ndepends-on: D2.1\n## D2 — B\nhides: b\n### D2.1 — b1\ndepends-on: D1.1\n"
                                  "## D5 — bad\npart-of: D9\n## D6 — self\npart-of: D6\n## D7 — x\npart-of: D8\n## D8 — y\npart-of: D7\n",
        })
        _, f = self.check(root)
        self.assertCode(f, "component-cycle", "report", count=1)
        self.assertCode(f, "unknown-id", "error", count=1)
        self.assertCode(f, "self-link", "error", count=1)
        self.assertCode(f, "part-of-cycle", "error", count=2)   # D7 <-> D8; D6's self part-of is a self-link only

    def test_stats_and_queries(self):
        spec = parse_spec(self.spec())
        c = Components(spec)
        rows = c.stats()
        self.assertEqual(rows["D2"]["out_crossing"], 1)
        self.assertGreaterEqual(rows["D2"]["out_ok"], 1)
        ifaces, assumptions = c.interfaces("D1")
        self.assertEqual([i.id for i, _ in ifaces], ["D1.1"])
        self.assertEqual(ifaces[0][1], ["D2.2"])
        cc = c.cross_cutting()
        self.assertIn("G1", [t for t, _ in cc])
        self.assertEqual(sorted(c.component_edges()), [("D2", "D1")])   # D3 -> D2 is reaching up, not an edge

    def test_cli(self):
        root = self.spec()
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = main(["coupling", str(root)])
        self.assertEqual(code, 0)
        self.assertIn("boundary crossings: 1", out.getvalue())
        self.assertIn("D2.3 depends-on D1.2", out.getvalue())
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = main(["interfaces", "D1", str(root)])
        self.assertEqual(code, 0)
        self.assertIn("hides: how the day is simulated", out.getvalue())
        self.assertIn("D1.1", out.getvalue())
        self.assertIn("<- D2.2", out.getvalue())
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = main(["coupling", str(self.make({"L0-purpose.md": "## G1 — One\n"}, subdir="empty"))])
        self.assertEqual(code, 1)
