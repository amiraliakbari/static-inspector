# -*- coding: utf-8 -*-
import unittest
from inspector.utils.strings import has_word, quoted, summarize


class StringsTest(unittest.TestCase):
    def test_summarize(self):
        sample_str = 'Short String'
        self.assertEqual(summarize(sample_str, max_len=20), sample_str)
        self.assertEqual(summarize(sample_str, max_len=len(sample_str)), sample_str)
        self.assertEqual(summarize(sample_str, max_len=5), 'Short...')

        # Word breaking
        self.assertEqual(summarize(sample_str, max_len=6), 'Short ...')
        self.assertEqual(summarize(sample_str, max_len=8), 'Short St...')
        # TODO: this is the correct behavior:
        #self.assertEqual(summarize(sample_str, max_len=6), 'Short...')
        #self.assertEqual(summarize(sample_str, max_len=8), 'Short ...')

        # unicode
        self.assertEqual(summarize(u'رشته‌ی مثال', max_len=6), u'رشته‌ی...')

    def test_quoted(self):
        self.assertEqual(quoted('string'), '"string"')
        self.assertEqual(quoted('first second third'), '"first second third"')
        self.assertEqual(quoted(u'رشته'), u'"رشته"')

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
