"""One test per error and report code (ARCHITECTURE.md section 9)."""

from tests.helpers import SpecCase


def spec_kinds(root, iid):
    from explain.parse import parse_spec
    it = parse_spec(root).items[iid]
    return (it.level, it.kind)

L0 = "## G1 — One\n## G2 — Two\n## A1 — Ass\n## C1 — Con\n"


class ErrorTests(SpecCase):
    def test_no_manifest(self):
        root = self.make({"L0-purpose.md": L0}, manifest="")
        (root / "spec.yaml").unlink()
        _, f = self.check(root)
        self.assertCode(f, "no-manifest", "error")

    def test_bad_manifest(self):
        for text in ("name: Bad Name\n", "bogus: 1\nname: t\n", "name: t\nparents: [a]\n", "name: t\nchildren:\n  x: 1\n", "name: [\n"):
            root = self.make({"L0-purpose.md": L0}, manifest=text, subdir="s" + str(abs(hash(text))))
            _, f = self.check(root)
            self.assertCode(f, "bad-manifest", "error")

    def test_bad_profile(self):
        root = self.make({"L0-purpose.md": L0}, manifest="name: t\nprofile: nope\n")
        _, f = self.check(root)
        self.assertCode(f, "bad-profile", "error")
        root = self.make({"L0-purpose.md": L0, "profile.yaml": "name: x\nlevels:\n  - n: 0\n    kinds:\n      L: bad\n"}, subdir="s2")
        _, f = self.check(root)
        self.assertCode(f, "bad-profile", "error")

    def test_unknown_and_duplicate_level(self):
        root = self.make({"L0-purpose.md": L0, "L7-x.md": "## G9 — nine\n", "L0-again/a.md": "## G3 — dup level\n"})
        _, f = self.check(root)
        self.assertCode(f, "unknown-level", "error")
        self.assertCode(f, "duplicate-level", "error")

    def test_duplicate_id(self):
        root = self.make({"L0-purpose.md": L0 + "## G1 — again\n"})
        _, f = self.check(root)
        self.assertCode(f, "duplicate-id", "error", count=1)

    def test_bad_header_values(self):
        root = self.make({"L0-purpose.md": (
            "## G1 — One\nstatus: nope\n"
            "## G2 — Two\nderived: false\n"
            "## G3 — Three\nserves: [G1\n"
            "## G4 — Four\nserves: 42\n"
            "## G5 — Five\nstatus: draft\nstatus: draft\n"
            "## G6 — Six\nwas: [not an id]\n"
        )})
        _, f = self.check(root)
        self.assertCode(f, "bad-header", "error", count=6)

    def test_unknown_key_and_relation(self):
        root = self.make({"L0-purpose.md": "## G1 — One\nrationale: because\n\nSee [[fulfils G2]].\n## G2 — Two\n"})
        _, f = self.check(root)
        self.assertCode(f, "unknown-key", "error", count=1)
        self.assertCode(f, "unknown-relation", "error", count=1)

    def test_link_outside_item(self):
        root = self.make({"L0-purpose.md": "# Title\n\nIntro with [[serves G1]] before any item.\n\n## G1 — One\n"})
        _, f = self.check(root)
        self.assertCode(f, "link-outside-item", "error", count=1)

    def test_level_prefix_rules(self):
        root = self.make({
            "L0-purpose.md": L0 + "## V1 — no prefix\n## L1-V2 — wrong prefix\n## L0-G3 — prefix on fixed kind\n",
            "L4-realization.md": "## L4-V3 — fine\nverifies: G1\n",
        })
        _, f = self.check(root)
        self.assertNoCode(f, "missing-level-prefix")            # a free kind needs no prefix
        self.assertEqual(spec_kinds(root, "V1"), (0, "V"))       # V1 at L0 is fine
        self.assertCode(f, "wrong-level-prefix", "error", count=1)
        self.assertCode(f, "unexpected-level-prefix", "error", count=1)
        self.assertNoCode(f, "unknown-kind")

    def test_unknown_kind_and_wrong_level(self):
        root = self.make({"L0-purpose.md": L0 + "## Z1 — no such kind\n## P1 — principle at L0\n"})
        _, f = self.check(root)
        self.assertCode(f, "unknown-kind", "error", count=1)
        self.assertCode(f, "kind-at-wrong-level", "error", count=1)

    def test_refinement_of_unknown(self):
        root = self.make({"L0-purpose.md": "## G1 — One\n- G2.1 — orphan refinement\n"})
        _, f = self.check(root)
        self.assertCode(f, "refinement-of-unknown", "error", count=1)

    def test_unknown_id_and_self_link(self):
        root = self.make({"L0-purpose.md": L0, "L1-principles.md": "## P1 — P\nserves: [G1, G9]\ndepends-on: P1\n"})
        _, f = self.check(root)
        self.assertCode(f, "unknown-id", "error", count=1)
        self.assertCode(f, "self-link", "error", count=1)

    def test_unknown_namespace(self):
        root = self.make({"L0-purpose.md": "## G1 — One\nserves: nowhere:G1\n"})
        _, f = self.check(root)
        self.assertCode(f, "unknown-namespace", "error", count=1)

    def test_serves_downward(self):
        root = self.make({"L0-purpose.md": "## G1 — One\nserves: P1\n", "L1-principles.md": "## P1 — P\nserves: G1\n"})
        _, f = self.check(root)
        self.assertCode(f, "serves-downward", "error", count=1)

    def test_assumes_and_discharge_kind_rules(self):
        root = self.make({"L0-purpose.md": L0 + "## G3 — Three\nassumes: G1\ndischarged-by: G2\n"})
        _, f = self.check(root)
        self.assertCode(f, "assumes-non-assumption", "error", count=1)
        self.assertCode(f, "discharge-on-non-assumption", "error", count=1)


class ProfileOverrideTests(SpecCase):
    PROFILE = (
        "name: custom\n"
        "free-kinds:\n  V: verification\n"
        "levels:\n"
        "  - n: 0\n    name: purpose\n    kinds:\n      G: goal\n      R: requirement\n      H: hazard\n"
        "  - n: 1\n    name: principles\n    kinds:\n      P: principle\n      LAW: design law\n      N: never rule\n"
        "  - n: 2\n    name: design\n    kinds:\n      D: design element\n"
    )

    def test_profile_yaml_in_spec_root_overrides(self):
        root = self.make({
            "profile.yaml": self.PROFILE,
            "L0-purpose.md": "## G1 — One\n## R3 — Req\nserves: G1\n## H1 — Hazard\n",
            "L1-principles.md": "## LAW16 — The band keeps itself\nserves: G1\n## N2 — Never nag\nserves: G1\n## P1 — P\nserves: G1\n",
            "L2-design.md": "## D1 — D\nserves: LAW16\n\nSee [[N2]] and [[serves P1]].\n## L2-V1 — guard\nverifies: LAW16\n",
        })
        spec, f = self.check(root)
        self.assertNoErrors(f)
        self.assertEqual(spec.profile.name, "custom")
        self.assertEqual(spec.items["LAW16"].kind, "LAW")
        self.assertEqual(spec.items["LAW16"].level, 1)
        self.assertEqual([l.target for l in spec.items["D1"].links_of("serves")], ["LAW16", "P1"])
        self.assertNoCode(f, "unknown-kind")
        self.assertNoCode(f, "kind-at-wrong-level")
        self.assertNoCode(f, "sections-absent")   # the custom profile declares no sections

    def test_reserved_and_wrong_level_with_override(self):
        root = self.make({"profile.yaml": self.PROFILE, "L0-purpose.md": "## LAW1 — law at L0\n## P1 — p at L0\n"})
        _, f = self.check(root)
        self.assertCode(f, "kind-at-wrong-level", "error", count=2)


class ReportTests(SpecCase):
    def test_clean_spec_has_no_errors(self):
        root = self.make({
            "L0-purpose.md": "## Mission\n## Goals\n## G1 — One\nstatus: adopted\n## Constraints\n## C1 — Con\nserves: G1\n",
            "L1-principles.md": "## Principles\n## P1 — P\nserves: G1\n",
            "L2-architecture.md": "## Components\n## D1 — D\nserves: P1\n",
        })
        _, f = self.check(root)
        self.assertNoErrors(f)
        # D1 is at the bottom of what exists, so it is unserved; all else is served.
        self.assertEqual([x.code for x in f if x.code == "unserved"], ["unserved"])
        self.assertNoCode(f, "orphan")

    def test_orphan_and_derived(self):
        root = self.make({
            "L0-purpose.md": "## G1 — One\n",
            "L1-principles.md": "## P1 — orphan\n## P2 — derived\nderived: true\n## P3 — both\nderived: true\nserves: G1\n## P4 — fine\nserves: G1\n",
        })
        _, f = self.check(root)
        hits = self.assertCode(f, "orphan", "report", count=1)
        self.assertIn("P1", hits[0].message)
        self.assertCode(f, "derived-but-serves", "report", count=1)

    def test_refinements_are_not_orphans(self):
        root = self.make({"L0-purpose.md": "## G1 — One\n", "L1-principles.md": "## P1 — P\nserves: G1\n- P1.1 — sub\n"})
        _, f = self.check(root)
        self.assertNoCode(f, "orphan")

    def test_unserved_and_undischarged(self):
        root = self.make({"L0-purpose.md": L0 + "## G3 — rejected\nstatus: rejected\n", "L1-principles.md": "## P1 — P\nserves: G1\nassumes: A1\n"})
        _, f = self.check(root)
        unserved = {x.message.split()[0] for x in f if x.code == "unserved"}
        self.assertEqual(unserved, {"G2", "P1"})   # G1 served by P1; G3 rejected; C1 and A1 are not goal-like
        self.assertCode(f, "undischarged-assumption", "report", count=1)

    def test_skip_level_and_same_level(self):
        root = self.make({
            "L0-purpose.md": L0 + "## G3 — Three\nserves: G1\n",
            "L2-architecture.md": "## D1 — D\nserves: G1\n",
        })
        _, f = self.check(root)
        self.assertCode(f, "skip-level", "report", count=1)
        hits = self.assertCode(f, "serves-same-level", "report", count=1)
        self.assertIn("G3", hits[0].message)
        self.assertNoErrors(f)

    def test_constraint_serving_goal_is_silent(self):
        root = self.make({"L0-purpose.md": "## G1 — One\n## C1 — Con\nserves: G1\n"})
        _, f = self.check(root)
        self.assertNoCode(f, "serves-same-level")

    def test_verifies_supersedes_mention_refs(self):
        root = self.make({
            "L0-purpose.md": "## G1 — One\nrefs: [exists.md, missing.md]\n\nSee [[G9]].\n## G2 — Old\nsupersedes: G1\n## G3 — verifier?\nverifies: G1\n",
            "exists.md": "x",
        })
        _, f = self.check(root)
        self.assertCode(f, "verifies-from-non-verification", "report", count=1)
        self.assertCode(f, "supersedes-unmarked", "report", count=1)
        self.assertCode(f, "unresolved-mention", "report", count=1)
        hits = self.assertCode(f, "missing-ref", "report", count=1)
        self.assertIn("missing.md", hits[0].message)

    def test_refs_root(self):
        root = self.make({"L0-purpose.md": "## G1 — One\nrefs: [spec/L0-purpose.md]\n"},
                         manifest="name: t\nrefs-root: ..\n")
        _, f = self.check(root)
        self.assertNoCode(f, "missing-ref")

    def test_sections_absent(self):
        root = self.make({"L0-purpose.md": "## Mission\n## G1 — One\n"})
        _, f = self.check(root)
        hits = self.assertCode(f, "sections-absent", "report", count=1)
        self.assertNotIn("Mission", hits[0].message)
        self.assertIn("Goals", hits[0].message)


class AliasTests(SpecCase):
    def test_aka_resolves_and_must_be_unique(self):
        root = self.make({
            "L0-purpose.md": "## G1 — One\n",
            "L1-principles.md": "## P1 — P\nserves: G1\naka: [law 16, the automaticity doctrine]\n## P2 — Q\nserves: G1\naka: Law 16\n## P3 — R\nserves: G1\naka: G1\n",
        })
        spec, f = self.check(root)
        self.assertCode(f, "duplicate-alias", "error", count=1)
        self.assertCode(f, "alias-is-an-id", "error", count=1)
        from explain.checks import find_alias
        self.assertEqual(find_alias(spec, "  LAW  16 ").id, "P1")
        self.assertEqual(find_alias(spec, "The Automaticity Doctrine").id, "P1")
        self.assertIsNone(find_alias(spec, "law 17"))


class BuildStateTests(SpecCase):
    def test_built_values_and_reports(self):
        root = self.make({
            "L0-purpose.md": "## G1 — One\n",
            "L1-principles.md": "## P1 — P\nserves: G1\n",
            "L2-architecture.md": (
                "## D1 — unstated\nserves: P1\n"
                "## D2 — roadmap\nserves: P1\nbuilt: unbuilt\n"
                "## D3 — shipped, unrealized and unguarded\nserves: P1\nbuilt: shipped\n"
                "## D4 — shipped, realized, guarded\nserves: P1\nbuilt: shipped\n"
                "## D5 — bad\nserves: P1\nbuilt: done\n"
                "## D6 — removed\nserves: P1\nbuilt: removed\n"
            ),
            "L4-realization.md": "## I1 — impl\nserves: D4\n## L4-V1 — guard\nverifies: D4\n",
        })
        _, f = self.check(root)
        self.assertCode(f, "bad-header", "error", count=1)
        unserved = sorted(x.message.split()[0] for x in f if x.code == "unserved")
        self.assertEqual(unserved, ["D1", "D5"])           # unstated build state keeps the old report (D5's built line was rejected)
        self.assertEqual([x.message.split()[0] for x in f if x.code == "unrealized"], ["D3"])
        self.assertEqual([x.message.split()[0] for x in f if x.code == "unguarded"], ["D3"])
        # D2 (unbuilt) and D6 (removed) are neither unserved nor unrealized

    def test_isolated(self):
        from explain.checks import connectivity
        from explain.parse import parse_spec
        root = self.make({
            "L0-purpose.md": "## G1 — linked\n## G2 — lonely\n## G3 — has a child\n- G3.1 — part\n## G4 — only mentioned\n\nSee [[G4]] from G5.\n## G5 — mentions only\n\nSee [[G4]].\n",
            "L1-principles.md": "## P1 — P\nserves: G1\n",
        })
        spec = parse_spec(root)
        isolated, built = connectivity(spec)
        self.assertEqual(sorted(i.id for i in isolated), ["G2", "G4", "G5"])
        self.assertEqual(built, {"unstated": 7})


class QuestionTests(SpecCase):
    def test_questions_and_until(self):
        from explain.checks import questions
        from explain.parse import parse_spec
        root = self.make({
            "L0-purpose.md": "## G1 — One\n",
            "L2-architecture.md": (
                "## Q1 — Does the valley pause during sleep?\nstatus: proposed\nowner: the owner\n\n- Q1.1 — and the herd?\n"
                "## Q2 — Answered one\nstatus: superseded\n"
                "## Q3 — Wrongly adopted\nstatus: adopted\n"
                "## D1 — Sleep\nserves: G1\ndepends-on: Q1\nuntil: the band ever needs a night shift\n"
                "## D2 — The answer\nserves: G1\nsupersedes: Q2\n"
            ),
        })
        spec, f = self.check(root)
        self.assertNoErrors(f)
        self.assertCode(f, "question-adopted", "report", count=1)
        open_, answered = questions(spec)
        self.assertEqual([(it.id, b, s) for it, b, _, s in open_], [("Q1", ["D1"], ["Q1.1"]), ("Q3", [], [])])
        self.assertEqual([(it.id, ans) for it, _, ans, _ in answered], [("Q2", ["D2"])])
        self.assertEqual(spec.items["D1"].header["until"], "the band ever needs a night shift")
