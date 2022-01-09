import ivydb
from ivydb.ivy_trace import Export, Import, grammar

import unittest

class ParserTest(unittest.TestCase):
    def test_comments(self):
        input = "# Ignore me!\n"
        grammar.parse(input)
        input = """# Ignore me!\n\n
# And also me!\n"""
        grammar.parse(input)

    def test_export(self):
        input = "< module.action(1,a,[2,3])\n"
        out = grammar.parse(input)
        self.assertEqual(out, Export(["module", "action"], [1, 'a', [2,3]], None))

        input = "< module.action(1,a,[2,3])\n[1,2,3]\n"
        out = grammar.parse(input)
        self.assertEqual(out, Export(["module", "action"], [1, 'a', [2,3]], [1,2,3]))

        input = """< module.action(1,a,[2,3])
< module.action(1,a,[2,3])
< module.action(1,a,[2,3])
"""
        out = grammar.parse(input)
        for action in out.children:
            self.assertEqual(action, Export(["module", "action"], [1, 'a', [2,3]], None))

    def test_input(self):
        input = "> module.action(1,a,[2,3])\n"
        out = grammar.parse(input)
        self.assertEqual(out, Import(["module", "action"], [1, 'a', [2,3]]))

    def test_action_and_comment(self):
        with self.assertRaises(Exception) as context:
            input = "> module.action(1,a,[2,3]) # Can't comment an action on the same line like this\n"
            out = grammar.parse(input)

        input = """# This, however, should be okay:
> module.action(1,a,[2,3])
# As should this.
"""
        out = grammar.parse(input)

if __name__ == '__main__':
    unittest.main()
