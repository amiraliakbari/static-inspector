# -*- coding: utf-8 -*-
import unittest

from inspector.models.base import Comment


class BaseModelTest(unittest.TestCase):
    def test_comment(self):
        c1 = Comment(u'// comment 1')
        self.assertEqual(c1.content, u'comment 1')
        self.assertFalse(c1.doc_comment)
        self.assertFalse(c1.multiline)
        self.assertEqual(unicode(c1), u'Comment: comment 1')
        self.assertEqual(str(c1), 'Comment: comment 1')

        c2 = Comment(u'/*******************\n * Comment2 _ \n****/')
        self.assertEqual(c2.content, u'Comment2 _')
        self.assertTrue(c2.doc_comment)
        self.assertTrue(c2.multiline)
        self.assertEqual(unicode(c2), u'Comment: Comment2 _ (docstring)')

        self.assertRaises(ValueError, Comment, u'int x = 2;')


if __name__ == '__main__':
    unittest.main()
