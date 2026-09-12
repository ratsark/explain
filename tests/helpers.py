"""Build tiny specs in a temp dir and run the checks on them."""

import tempfile
import unittest
from pathlib import Path

from explain.checks import run_checks
from explain.parse import parse_spec

MANIFEST = "name: t\nprofile: software\n"


class SpecCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def make(self, files, name="t", manifest=None, subdir="spec"):
        """files: {relative path: content}. Returns the spec root."""
        root = self.tmp / subdir
        root.mkdir(parents=True, exist_ok=True)
        if manifest is None and "spec.yaml" not in files:
            files = dict(files)
            files["spec.yaml"] = f"name: {name}\nprofile: software\n"
        elif manifest is not None:
            files = dict(files)
            files["spec.yaml"] = manifest
        for rel, content in files.items():
            p = root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
        return root

    def check(self, root):
        spec = parse_spec(root)
        return spec, run_checks(spec)

    def codes(self, findings, severity=None):
        return sorted(f.code for f in findings if severity is None or f.severity == severity)

    def assertCode(self, findings, code, severity, count=None):
        hits = [f for f in findings if f.code == code]
        self.assertTrue(hits, f"expected a finding with code {code!r}; got {[f.format() for f in findings]}")
        for h in hits:
            self.assertEqual(h.severity, severity, h.format())
        if count is not None:
            self.assertEqual(len(hits), count, [h.format() for h in hits])
        return hits

    def assertNoCode(self, findings, code):
        hits = [f.format() for f in findings if f.code == code]
        self.assertFalse(hits, hits)

    def assertNoErrors(self, findings):
        errs = [f.format() for f in findings if f.severity == "error"]
        self.assertFalse(errs, errs)
