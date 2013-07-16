# -*- coding: utf-8 -*-
import os
import unittest
from inspector.models.base import SourceFile


class TestJavaParse(unittest.TestCase):
    def setUp(self):
        self.data_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data', 'java')

    def test_parse(self):
        sf = SourceFile.build_source_file(os.path.join(self.data_path, 'sample_sources', '1.java'))
        self.assertEqual(unicode(sf), 'Java SourceFile: 0 imports, 0 classes, 0 functions')


if __name__ == '__main__':
    unittest.main()
