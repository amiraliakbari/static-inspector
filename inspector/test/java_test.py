# -*- coding: utf-8 -*-
import os
import unittest
from inspector.models.base import SourceFile


# TODO: test details!
class TestJavaParse(unittest.TestCase):
    def setUp(self):
        self.data_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data', 'java')

    def test_parse_1(self):
        sf = SourceFile.build_source_file(os.path.join(self.data_path, 'sample_sources', '1.java'))
        self.assertEqual(unicode(sf), u'Java SourceFile: 1 imports, 1 classes')
        self.assertEqual(sf.next_token(), None)

    def test_parse_2(self):
        sf = SourceFile.build_source_file(os.path.join(self.data_path, 'sample_sources', '2.java'))
        self.assertEqual(unicode(sf), u'Java SourceFile: 1 classes')
        self.assertEqual(sf.next_token(), None)

    def test_parse_3(self):
        sf = SourceFile.build_source_file(os.path.join(self.data_path, 'sample_sources', '3.java'))
        self.assertEqual(unicode(sf), u'Java SourceFile: 2 classes')
        self.assertEqual(sf.next_token(), None)

    def test_parse_4(self):
        sf = SourceFile.build_source_file(os.path.join(self.data_path, 'sample_sources', '4.java'))
        self.assertEqual(unicode(sf), u'Java SourceFile: 1 classes, 1 interfaces')
        self.assertEqual(sf.next_token(), None)

    def test_parse_5(self):
        sf = SourceFile.build_source_file(os.path.join(self.data_path, 'sample_sources', '5.java'))
        self.assertEqual(unicode(sf), u'Java SourceFile: 1 classes')
        self.assertEqual(sf.next_token(), None)

    def test_parse_6(self):
        sf = SourceFile.build_source_file(os.path.join(self.data_path, 'sample_sources', '6.java'))
        self.assertEqual(unicode(sf), u'Java SourceFile: 1 classes')
        self.assertEqual(sf.next_token(), None)


if __name__ == '__main__':
    unittest.main()
