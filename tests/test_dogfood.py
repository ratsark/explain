"""explain's own spec (spec/) holds up under its own checker."""

import re
import unittest
from collections import Counter
from pathlib import Path

from explain.checks import run_checks
from explain.parse import parse_spec

ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "spec"


class DogfoodTests(unittest.TestCase):
    def setUp(self):
        self.spec = parse_spec(SPEC)
        self.findings = run_checks(self.spec)

    def test_no_errors(self):
        self.assertEqual([f.format() for f in self.findings if f.severity == "error"], [])

    def test_no_orphans_and_no_drift(self):
        codes = Counter(f.code for f in self.findings if f.severity == "report")
        self.assertEqual(codes["orphan"], 0, [f.format() for f in self.findings if f.code == "orphan"])
        self.assertEqual(codes["suspect-link"], 0, [f.format() for f in self.findings if f.code == "suspect-link"])
        self.assertEqual(codes["boundary-crossing"], 0)
        self.assertEqual(codes["component-cycle"], 0)
        self.assertEqual(codes["unresolved-mention"], 0)
        self.assertEqual(codes["missing-ref"], 0)

    def test_every_architecture_section_is_cited(self):
        text = (ROOT / "ARCHITECTURE.md").read_text(encoding="utf-8")
        sections = {int(m.group(1)) for m in re.finditer(r"^## (\d+)\. ", text, re.M)}
        cited = set()
        for it in self.spec.items.values():
            for m in re.finditer(r"ARCHITECTURE\.md[^\n]*?§ ?(\d+)", str(it.header.get("source", ""))):
                cited.add(int(m.group(1)))
            for m in re.finditer(r"§ ?(\d+)", str(it.header.get("source", ""))):
                if "ARCHITECTURE" in str(it.header.get("source", "")):
                    cited.add(int(m.group(1)))
        self.assertEqual(sorted(sections - cited), [], f"uncited ARCHITECTURE.md sections: {sorted(sections - cited)}")

    def test_every_test_file_is_a_guard(self):
        files = {p.name for p in (ROOT / "tests").glob("test_*.py")}
        guarded = set()
        for it in self.spec.items.values():
            if it.kind == "V":
                for r in it.header.get("refs", []) or []:
                    if str(r).startswith("tests/"):
                        guarded.add(Path(str(r)).name)
        self.assertEqual(sorted(files - guarded), [], f"test files with no guard row: {sorted(files - guarded)}")
