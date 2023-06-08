import unittest

from cjw.aistory.utilities.StringOps import parse_first_top_level_parentheses


class MyTestCase(unittest.TestCase):
    def test_parse_first_top_level_parentheses(self):
        s = "Hello (a <very{[]()}> nice) world (with blue sky and ocean)"
        before, between, after = parse_first_top_level_parentheses(s, "<[{(", ">]})")
        print(f"Before: {before}\nBetween: {between}\nAfter: {after}")
        self.assertEqual(before, "Hello ")
        self.assertEqual(between, "(a <very{[]()}> nice)")
        self.assertEqual(after, " world (with blue sky and ocean)")

        s = "No matching ) parentheses ("
        before, between, after = parse_first_top_level_parentheses(s)
        print(f"Before: {before}\nBetween: {between}\nAfter: {after}")
        self.assertEqual(before, s)
        self.assertIsNone(between)
        self.assertIsNone(after)

        s = "(incomplete parenthesis [ in parentheses) there ]"
        before, between, after = parse_first_top_level_parentheses(s)
        print(f"Before: {before}\nBetween: {between}\nAfter: {after}")
        self.assertEqual(before, "")
        self.assertEqual(between, "(incomplete parenthesis [ in parentheses)")
        self.assertEqual(after, " there ]")

        s = "I said, \"Hey, this works for quotes (\') too!\""
        before, between, after = parse_first_top_level_parentheses(s, "\"\'", "\"\'")
        print(f"Before: {before}\nBetween: {between}\nAfter: {after}")
        self.assertEqual(before, "I said, ")
        self.assertEqual(between, "\"Hey, this works for quotes (\') too!\"")
        self.assertEqual(after, "")

        s = "\'How about \"double quotes\" (\"lots of\" them)?\', I said."
        before, between, after = parse_first_top_level_parentheses(s, "\"\'", "\"\'")
        print(f"Before: {before}\nBetween: {between}\nAfter: {after}")
        self.assertEqual(before, "")
        self.assertEqual(between, "\'How about \"double quotes\" (\"lots of\" them)?\'")
        self.assertEqual(after, ", I said.")


if __name__ == '__main__':
    unittest.main()
