import unittest

from envfile import ParseError, parse


class Basics(unittest.TestCase):
    def test_simple_pairs(self):
        self.assertEqual(parse("A=1\nB=hello\n", {}), {"A": "1", "B": "hello"})

    def test_blank_lines_and_comments(self):
        self.assertEqual(parse("\n# a comment\n   # indented comment\nA=1\n\n", {}), {"A": "1"})

    def test_export_prefix(self):
        self.assertEqual(parse("export A=1", {}), {"A": "1"})

    def test_quoted_values(self):
        self.assertEqual(parse("A='x y'\nB=\"z\"", {}), {"A": "x y", "B": "z"})

    def test_last_definition_wins(self):
        self.assertEqual(parse("A=1\nA=2", {}), {"A": "2"})

    def test_missing_equals(self):
        with self.assertRaises(ParseError) as cm:
            parse("A=1\nB\n", {})
        self.assertEqual(cm.exception.line, 2)


if __name__ == "__main__":
    unittest.main()
