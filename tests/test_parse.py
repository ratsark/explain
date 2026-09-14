from explain.parse import parse_spec, split_qid
from tests.helpers import SpecCase


class IdTests(SpecCase):
    def test_split_qid(self):
        self.assertEqual(split_qid("G2"), (None, "G2"))
        self.assertEqual(split_qid("G06.2"), (None, "G6.2"))
        self.assertEqual(split_qid("biz:G3"), ("biz", "G3"))
        self.assertEqual(split_qid("L4-V1.2"), (None, "L4-V1.2"))
        self.assertIsNone(split_qid("L0"))          # reserved: level prefix, not a kind
        self.assertIsNone(split_qid("g2"))
        self.assertIsNone(split_qid("G"))
        self.assertIsNone(split_qid("2"))
        self.assertIsNone(split_qid("law 16"))


class ParseTests(SpecCase):
    def test_levels_from_paths(self):
        root = self.make({
            "L0-purpose.md": "# L0 — Purpose\n\n## G1 — One\n",
            "L1-principles/a.md": "## P1 — A\nserves: G1\n",
            "L1-principles/deep/b.md": "## P2 — B\nserves: G1\n",
            "notes.md": "## G9 — not a level file\n",
            "L0-notes.txt": "## G8 — wrong extension\n",
        })
        spec = parse_spec(root)
        self.assertEqual(sorted(spec.levels), [0, 1])
        self.assertEqual({i.id: i.level for i in spec.items.values()}, {"G1": 0, "P1": 1, "P2": 1})
        self.assertEqual(spec.levels[1].name, "principles")
        self.assertEqual([str(f) for f in spec.levels[1].files], ["L1-principles/a.md", "L1-principles/deep/b.md"])

    def test_heading_forms(self):
        root = self.make({"L0-purpose.md": (
            "## G1 — em dash\n"
            "### G2 – en dash ###\n"
            "#### G3 - hyphen\n"
            "## G4: colon\n"
            "## G5—tight\n"
            "## Goals\n"
            "## 2. Not an item\n"
            "## GX — letters only, not an item\n"
        )})
        spec = parse_spec(root)
        self.assertEqual(sorted(spec.items), ["G1", "G2", "G3", "G4", "G5"])
        self.assertEqual(spec.items["G2"].title, "en dash")
        self.assertEqual(spec.items["G5"].title, "tight")
        self.assertEqual(spec.items["G2"].depth, 3)

    def test_header_body_and_links(self):
        root = self.make({"L0-purpose.md": (
            "## G1 — One\n"
            "status: adopted\n"
            "source: owner, 2026-09-05\n"
            "refs: [a.md, b.md]\n"
            "\n"
            "Body line one [[G2]] and a typed [[depends-on G2]].\n"
            "\n"
            "### Rationale\n"
            "Deeper non-id heading stays in the body.\n"
            "\n"
            "## G2 — Two\n"
            "First body line right after the heading is not a header line: it has spaces.\n"
        )})
        spec = parse_spec(root)
        g1 = spec.items["G1"]
        self.assertEqual(g1.header, {"status": "adopted", "source": "owner, 2026-09-05", "refs": ["a.md", "b.md"]})
        self.assertEqual([(l.relation, l.target, l.inline) for l in g1.links], [("depends-on", "G2", True)])
        self.assertEqual([m.target for m in g1.mentions], ["G2"])
        self.assertIn("### Rationale", g1.body)
        self.assertNotIn("G2 — Two", g1.body)
        self.assertEqual(spec.items["G2"].header, {})
        self.assertTrue(spec.items["G2"].body.startswith("First body line"))
        self.assertNoErrors(spec.findings)

    def test_header_relations_single_and_list(self):
        root = self.make({
            "L0-purpose.md": "## G1 — One\n## G2 — Two\n## A1 — Ass\n",
            "L1-principles.md": "## P1 — P\nserves: [G1, G2]\nassumes: A1\n",
        })
        spec = parse_spec(root)
        self.assertEqual([(l.relation, l.target) for l in spec.items["P1"].links],
                         [("serves", "G1"), ("serves", "G2"), ("assumes", "A1")])

    def test_bullets_and_refinement(self):
        root = self.make({"L0-purpose.md": (
            "## G6 — Social\n"
            "status: adopted\n"
            "\n"
            "Intro.\n"
            "- G6.1 — Collaboration: together [[depends-on G1]]\n"
            "  continuation line with [[G1]]\n"
            "  - G6.1.1 — Nested: deeper\n"
            "- G6.2 — Helping\n"
            "- plain bullet, not an item, belongs to G6\n"
            "\n"
            "## G1 — One\n"
        )})
        spec = parse_spec(root)
        self.assertEqual(sorted(spec.items), ["G1", "G6", "G6.1", "G6.1.1", "G6.2"])
        self.assertEqual(spec.items["G6.1"].parent_id, "G6")
        self.assertEqual(spec.items["G6.1.1"].parent_id, "G6.1")
        self.assertTrue(spec.items["G6.1"].is_bullet)
        self.assertEqual([(l.relation, l.target) for l in spec.items["G6.1"].links], [("depends-on", "G1")])
        self.assertEqual([m.target for m in spec.items["G6.1"].mentions], ["G1"])
        self.assertEqual(spec.items["G6.1"].title, "Collaboration: together [[depends-on G1]]")
        self.assertEqual(spec.items["G6.1"].body, "continuation line with [[G1]]")
        self.assertIn("plain bullet", spec.items["G6"].body)
        self.assertEqual(spec.items["G6.2"].title, "Helping")

    def test_fenced_blocks_are_ignored(self):
        root = self.make({"L0-purpose.md": (
            "## G1 — One\n\n```markdown\n## G2 — inside a fence\n[[serves G9]]\n```\n\nAfter [[G3]].\n## G3 — Three\n"
        )})
        spec = parse_spec(root)
        self.assertEqual(sorted(spec.items), ["G1", "G3"])
        self.assertEqual(spec.items["G1"].links, [])
        self.assertEqual([m.target for m in spec.items["G1"].mentions], ["G3"])

    def test_sections_collected_per_level(self):
        root = self.make({"L0-purpose.md": "# L0 — Purpose\n\n## Mission\ntext\n## Goals\n## G1 — One\n### Environment\n"})
        spec = parse_spec(root)
        self.assertEqual([t for t, _, _, _ in spec.sections[0]], ["L0 — Purpose", "Mission", "Goals", "Environment"])

    def test_was_and_derived(self):
        root = self.make({
            "L0-purpose.md": "## G1 — One\n",
            "L1-principles.md": "## P1 — P\nwas: [G1, G7]\nderived: true\n",
        })
        spec = parse_spec(root)
        self.assertEqual(spec.items["P1"].header["was"], ["G1", "G7"])
        self.assertIs(spec.items["P1"].header["derived"], True)


class EditorialAndRootTests(SpecCase):
    def test_editorial_paragraphs_and_files(self):
        root = self.make({
            "L0-purpose/00-goals.md": "## G1 — One\n\nThe design sentence.\n\nHistory: minted 2026-09-12; renamed once.\n\nMore design [[G2]].\n\nNote: the checker flags this on purpose.\n## G2 — Two\n",
            "L0-purpose/NOTES.md": "## G9 — would be an item if parsed\n",
            "L0-purpose/README.md": "editorial\n",
            "L0-purpose/old.notes.md": "## G8 — also skipped\n",
        })
        spec = parse_spec(root)
        self.assertEqual(sorted(spec.items), ["G1", "G2"])
        g1 = spec.items["G1"]
        self.assertEqual(g1.design_body, "The design sentence.\n\nMore design [[G2]].")
        self.assertIn("History:", g1.editorial_body); self.assertIn("Note:", g1.editorial_body)
        fp = spec.fingerprint("G1")
        (root / "L0-purpose/00-goals.md").write_text((root / "L0-purpose/00-goals.md").read_text().replace("renamed once", "renamed twice"), encoding="utf-8")
        self.assertEqual(parse_spec(root).fingerprint("G1"), fp)       # editorial change: no drift
        (root / "L0-purpose/00-goals.md").write_text((root / "L0-purpose/00-goals.md").read_text().replace("The design sentence", "The design sentence, changed"), encoding="utf-8")
        self.assertNotEqual(parse_spec(root).fingerprint("G1"), fp)    # design change: drift

    def test_root_implies_serves(self):
        root = self.make({"L0-purpose.md": "## G0 — The mission\n## G1 — One\n## G2 — Two\nserves: G0\n- G2.1 — part\n## C1 — Con\n## A1 — Ass\n"},
                         manifest="name: t\nroot: G0\n")
        spec, f = self.check(root)
        self.assertNoErrors(f)
        self.assertNoCode(f, "serves-same-level")
        self.assertEqual([(l.target, l.implied) for l in spec.items["G1"].links], [("G0", True)])
        self.assertEqual([(l.target, l.implied) for l in spec.items["G2"].links], [("G0", False)])
        self.assertEqual(spec.items["C1"].links, []); self.assertEqual(spec.items["G2.1"].links, [])
        unserved = [x.message.split()[0] for x in f if x.code == "unserved"]
        self.assertNotIn("G0", unserved)
        from explain.checks import connectivity
        self.assertEqual(sorted(i.id for i in connectivity(spec)[0]), ["A1", "C1"])

    def test_bad_root(self):
        root = self.make({"L0-purpose.md": "## G1 — One\n", "L1-principles.md": "## P1 — P\nserves: G1\n"}, manifest="name: t\nroot: P1\n")
        _, f = self.check(root)
        self.assertCode(f, "bad-manifest", "error", count=1)
