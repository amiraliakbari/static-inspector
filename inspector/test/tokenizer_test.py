# -*- coding: utf-8 -*-
from tempfile import TemporaryFile
import unittest

from inspector.parser.file_tokenizer import FileTokenizer


class TestFileTokenizer(unittest.TestCase):
    SAMPLE_STRING_1 = 'abc\nabc1\n\n2\ng-h-i-j-k-lm.'

    def test_opening(self):
        # string
        tz = FileTokenizer(content_file=self.SAMPLE_STRING_1)
        self.assertEqual(tz.L, 25)

        # file
        f = TemporaryFile()
        f.write(self.SAMPLE_STRING_1)
        f.seek(0)
        tz = FileTokenizer(content_file=f)
        self.assertEqual(tz.L, 25)

        # other (invalid)
        self.assertRaises(ValueError, FileTokenizer, content_file=())

    def test_parse(self):
        tz = FileTokenizer(content_file=self.SAMPLE_STRING_1)
        self.assertTrue(tz.has_content())
        self.assertEqual(tz.L, 25)
        self.assertEqual(tz.token, None)
        self.assertEqual(tz.token_type, None)
        self.assertTrue(tz.can_read())
        self.assertEqual(tz.read_ahead(2), 'ab')
        self.assertEqual(tz.read(1), 'a')
        self.assertEqual(tz.find_ahead('\n'), 3)
        self.assertEqual(tz.find_ahead('ab'), 4)
        self.assertEqual(tz.read(to=3), 'bc')
        tz.skip_spaces()
        self.assertEqual(tz.next_char(), 'a')
        self.assertEqual(tz.read_ahead(3), 'bc1')
        self.assertEqual(tz.next_char(skip=2), '1')
        self.assertEqual(tz.read_ahead(2), '\n\n')
        tz.skip_spaces()
        self.assertEqual(tz.read_ahead(1), '2')
        self.assertEqual(tz.read(cond=lambda ch: ch != '\n'), '2')
        self.assertEqual(tz.read_ahead(1), '\n')
        tz.skip_spaces()
        self.assertEqual(tz.read(find='-i'), 'g-h')
        self.assertEqual(tz.read(find='.', beyond=1), '-i-j-k-lm.')
        self.assertEqual(tz.next_char(), None)
        self.assertEqual(tz.next_char(skip=1), None)
        self.assertFalse(tz.can_read())
        self.assertTrue(tz.has_content())

    def test_argument_checking(self):
        tz = FileTokenizer(content_file=self.SAMPLE_STRING_1)
        self.assertRaises(ValueError, tz.next_char, skip=-2)
