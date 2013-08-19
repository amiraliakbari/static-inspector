# -*- coding: utf-8 -*-
import unittest
from inspector.utils.strings import has_word


class StringsTest(unittest.TestCase):
    def test_has_word(self):
        string = 'inspector.analyzer.func()'
        self.assertTrue(has_word(string, 'inspector'))
        self.assertTrue(has_word(string, 'analyzer'))
        self.assertFalse(has_word(string, 'analyze'))
        self.assertFalse(has_word(string, 'alyzer'))
        self.assertTrue(has_word(string, 'func'))
        self.assertFalse(has_word(string, 'fun'))
        self.assertTrue(has_word(string, 'analyzer.func'))

if __name__ == '__main__':
    unittest.main()
