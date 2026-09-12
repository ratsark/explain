import unittest

from explain.miniyaml import MiniYamlError, loads, parse_value


class MiniYamlTests(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(loads(""), {})
        self.assertEqual(loads("# only a comment\n"), {})

    def test_scalars(self):
        self.assertEqual(parse_value("hello world"), "hello world")
        self.assertEqual(parse_value('"quoted: yes"'), "quoted: yes")
        self.assertEqual(parse_value("'single'"), "single")
        self.assertEqual(parse_value("true"), True)
        self.assertEqual(parse_value("no"), False)
        self.assertEqual(parse_value("null"), None)
        self.assertEqual(parse_value("42"), 42)
        self.assertEqual(parse_value("-3"), -3)
        self.assertEqual(parse_value("G2"), "G2")
        self.assertEqual(parse_value("biz:G3"), "biz:G3")

    def test_flow_list(self):
        self.assertEqual(parse_value("[G2, G3, biz:G1]"), ["G2", "G3", "biz:G1"])
        self.assertEqual(parse_value("[]"), [])
        self.assertEqual(parse_value('["a, b", c]'), ["a, b", "c"])
        with self.assertRaises(MiniYamlError):
            parse_value("[a, b")
        with self.assertRaises(MiniYamlError):
            parse_value("[[a], b]")
        with self.assertRaises(MiniYamlError):
            parse_value("{a: 1}")

    def test_mapping_and_comments(self):
        data = loads("name: t   # trailing\ntitle: 'x # not a comment'\n# full line\nprofile: software\n")
        self.assertEqual(data, {"name": "t", "title": "x # not a comment", "profile": "software"})

    def test_nested_mapping(self):
        data = loads("parents:\n  biz:\n    path: ../biz\n    index: p.json\n  other:\nname: t\n")
        self.assertEqual(data, {"parents": {"biz": {"path": "../biz", "index": "p.json"}, "other": None}, "name": "t"})

    def test_block_list(self):
        data = loads("children:\n  - path: a\n  - path: b\n    name: bee\nsections:\n  - Mission\n  - Environment:\n      - Assumptions\n      - External\n")
        self.assertEqual(data["children"], [{"path": "a"}, {"path": "b", "name": "bee"}])
        self.assertEqual(data["sections"], ["Mission", {"Environment": ["Assumptions", "External"]}])

    def test_profile_shape(self):
        text = (
            "name: p\nper-level-kinds:\n  V: verification\nlevels:\n"
            "  - n: 0\n    name: purpose\n    kinds:\n      G: goal\n      C: constraint\n"
            "    sections: [Mission, Goals]\n"
            "  - n: 1\n    name: principles\n    kinds: {P: principle}\n"
        )
        with self.assertRaises(MiniYamlError):
            loads(text)  # flow mappings are not supported, by design
        text = text.replace("kinds: {P: principle}", "kinds:\n      P: principle")
        data = loads(text)
        self.assertEqual(data["levels"][0]["kinds"], {"G": "goal", "C": "constraint"})
        self.assertEqual(data["levels"][1], {"n": 1, "name": "principles", "kinds": {"P": "principle"}})

    def test_errors_carry_line_numbers(self):
        with self.assertRaises(MiniYamlError) as cm:
            loads("a: 1\n  b: 2\n")
        self.assertEqual(cm.exception.line, 2)
        with self.assertRaises(MiniYamlError):
            loads("a: 1\na: 2\n")
        with self.assertRaises(MiniYamlError):
            loads("\tkey: value\n")
        with self.assertRaises(MiniYamlError):
            loads("just text\n")


if __name__ == "__main__":
    unittest.main()
