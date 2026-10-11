import unittest

from envfile import ParseError, parse


def p(text, env=None):
    return parse(text, env or {})


class Unquoted(unittest.TestCase):
    def test_inner_spaces_kept_trailing_stripped(self):
        self.assertEqual(p("A=  a b c   \n"), {"A": "a b c"})

    def test_hash_without_space_is_literal(self):
        self.assertEqual(p("A=a#b"), {"A": "a#b"})

    def test_hash_at_start_of_value_is_comment(self):
        self.assertEqual(p("A=#x\nB=   #y"), {"A": "", "B": ""})

    def test_hash_after_space_or_tab_is_comment(self):
        self.assertEqual(p("A=a #b\nB=x\t# c\nC= # only comment"), {"A": "a", "B": "x", "C": ""})

    def test_empty_value(self):
        self.assertEqual(p("A=\nB="), {"A": "", "B": ""})

    def test_spaces_around_equals_and_leading_whitespace(self):
        self.assertEqual(p("   A  =  1\n\tB\t=2"), {"A": "1", "B": "2"})

    def test_quotes_inside_unquoted_are_literal(self):
        self.assertEqual(p("A=it's \"ok\""), {"A": "it's \"ok\""})

    def test_crlf(self):
        self.assertEqual(p("A=1\r\nB='x'\r\nC=\"y\"\r\n"), {"A": "1", "B": "x", "C": "y"})


class Keys(unittest.TestCase):
    def test_export_with_several_spaces_or_tab(self):
        self.assertEqual(p("export   A=1\nexport\tB=2"), {"A": "1", "B": "2"})

    def test_export_as_key(self):
        self.assertEqual(p("export=1\nexportX=2"), {"export": "1", "exportX": "2"})

    def test_invalid_keys(self):
        for bad in ("1A=x", "A-B=x", "A B=x", "=x", "export A B=x"):
            with self.subTest(bad=bad):
                with self.assertRaises(ParseError) as cm:
                    p("OK=1\n" + bad)
                self.assertEqual(cm.exception.line, 2)


class SingleQuoted(unittest.TestCase):
    def test_literal(self):
        self.assertEqual(p("B=x\nA='a $B ${B} \\n \\' "), {"B": "x", "A": "a $B ${B} \\n \\"})

    def test_hash_inside_and_comment_after(self):
        self.assertEqual(p("A='a #b' # c"), {"A": "a #b"})

    def test_multiline(self):
        self.assertEqual(p("A='l1\nl2'\nB=2"), {"A": "l1\nl2", "B": "2"})


class DoubleQuoted(unittest.TestCase):
    def test_escapes(self):
        self.assertEqual(p(r'A="a\nb\tc\"d\"\\e"'), {"A": 'a\nb\tc"d"\\e'})

    def test_unknown_escape_kept(self):
        self.assertEqual(p(r'A="C:\data\x"'), {"A": "C:\\data\\x"})

    def test_escaped_dollar_is_not_expanded(self):
        self.assertEqual(p(r'B=x' + "\n" + r'A="\$B and ${B}"'), {"B": "x", "A": "$B and x"})

    def test_hash_inside_and_comment_after(self):
        self.assertEqual(p('A="a # b"   # comment'), {"A": "a # b"})

    def test_empty(self):
        self.assertEqual(p('A=""\nB=\'\''), {"A": "", "B": ""})

    def test_multiline_keeps_newlines_and_expands(self):
        self.assertEqual(p('X=1\nA="first $X\n  second\n"\nB=2'), {"X": "1", "A": "first 1\n  second\n", "B": "2"})

    def test_escaped_backslash_then_quote_closes(self):
        self.assertEqual(p(r'A="a\\" # c'), {"A": "a\\"})


class Errors(unittest.TestCase):
    def assertLine(self, text, line):
        with self.assertRaises(ParseError) as cm:
            p(text)
        self.assertEqual(cm.exception.line, line)

    def test_text_after_closing_quote(self):
        self.assertLine('A=1\nB="x" y', 2)
        self.assertLine("A='x'y", 1)

    def test_text_after_multiline_closing_quote_reports_closing_line(self):
        self.assertLine('A="one\ntwo" junk', 2)

    def test_unterminated_quote_reports_opening_line(self):
        self.assertLine('A=1\nB="never closed\nC=3\nD=4', 2)
        self.assertLine("A='open", 1)

    def test_line_numbers_after_multiline_value(self):
        self.assertLine('A="1\n2\n3"\nB=ok\nbroken', 5)

    def test_unterminated_brace(self):
        self.assertLine("A=1\nB=${A", 2)
        self.assertLine('B="${A"', 1)

    def test_invalid_name_in_braces(self):
        self.assertLine("A=${1X}", 1)
        self.assertLine("A=${}", 1)
        self.assertLine("A=${X-y}", 1)


class References(unittest.TestCase):
    def test_forms(self):
        self.assertEqual(p("A=x\nB=$A\nC=${A}\nD=pre${A}post\nE=\"$A $A\""),
                         {"A": "x", "B": "x", "C": "x", "D": "prexpost", "E": "x x"})

    def test_longest_name(self):
        self.assertEqual(p("A=x\nB=$A_1\nC=${A}_1"), {"A": "x", "B": "", "C": "x_1"})

    def test_literal_dollar(self):
        self.assertEqual(p("A=$\nB=5$\nC=$1\nD=\"$ $-\"\nE=a$ b"),
                         {"A": "$", "B": "5$", "C": "$1", "D": "$ $-", "E": "a$ b"})

    def test_default(self):
        self.assertEqual(p("E=\nA=${U:-dflt}\nB=${E:-dflt}\nC=${A:-other}\nD=${U:-}"),
                         {"E": "", "A": "dflt", "B": "dflt", "C": "dflt", "D": ""})

    def test_default_is_literal(self):
        self.assertEqual(p("X=1\nA=${U:-$X}\nB=${U:-a b}"), {"X": "1", "A": "$X", "B": "a b"})

    def test_environ_used_when_not_in_file(self):
        self.assertEqual(p("A=$HOME/x", {"HOME": "/h"}), {"A": "/h/x"})

    def test_file_shadows_environ_even_when_empty(self):
        self.assertEqual(p("HOME=\nA=[$HOME]", {"HOME": "/h"}), {"HOME": "", "A": "[]"})

    def test_later_definitions_not_visible(self):
        self.assertEqual(p("A=$B\nB=1", {"B": "env"}), {"A": "env", "B": "1"})
        self.assertEqual(p("A=$B\nB=1"), {"A": "", "B": "1"})

    def test_value_at_that_point(self):
        self.assertEqual(p("A=1\nB=$A\nA=2\nC=$A"), {"A": "2", "B": "1", "C": "2"})

    def test_self_reference_appends(self):
        self.assertEqual(p("PATH=$PATH:/x", {"PATH": "/bin"}), {"PATH": "/bin:/x"})

    def test_reference_then_comment(self):
        self.assertEqual(p("A=x\nB=$A #c"), {"A": "x", "B": "x"})


if __name__ == "__main__":
    unittest.main()
