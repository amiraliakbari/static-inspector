# -*- coding: utf-8 -*-
import os
import unittest

from inspector.models.base import SourceFile
from inspector.models.consts import Language
from inspector.models.java import JavaClass


# TODO: test details!
class TestJavaParse(unittest.TestCase):
    def setUp(self):
        self.data_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data', 'java')

    def test_parse_1(self):
        sf = SourceFile.build_source_file(os.path.join(self.data_path, 'sample_sources', '1.java'))
        self.assertTrue(sf.language_detected)
        self.assertEqual(sf.language, Language.JAVA)
        self.assertTrue(sf.parsed)
        self.assertEqual(unicode(sf), u'Java SourceFile: 1 imports, 1 classes')
        self.assertEqual(sf.next_token(), None)
        c1 = sf.get_class('MyFirstProgram')
        self.assertEqual(c1.starting_line, 2)
        self.assertEqual(c1.ending_line, 23)
        self.assertEqual(len(c1.methods), 1)
        self.assertEqual(c1.get_method('main').lines_count, 19)

    def test_parse_2(self):
        sf = SourceFile.build_source_file(os.path.join(self.data_path, 'sample_sources', '2.java'))
        self.assertEqual(unicode(sf), u'Java SourceFile: 1 classes')
        self.assertEqual(sf.get_class('Fibonacci').get_method('main').lines_count, 11)
        self.assertEqual(sf.next_token(), None)

    def test_parse_3(self):
        sf = SourceFile.build_source_file(os.path.join(self.data_path, 'sample_sources', '3.java'))
        self.assertEqual(unicode(sf), u'Java SourceFile: 2 classes')
        point = sf.get_class('Point')
        pixel = sf.get_class('Pixel')
        self.assertEqual(point.get_method('clear').lines_count, 5)
        self.assertEqual(pixel.get_method('clear').lines_count, 4)
        self.assertEqual(len(point.fields), 3)
        self.assertEqual(len(pixel.fields), 1)
        self.assertEqual(sf.next_token(), None)

    def test_parse_4(self):
        sf = SourceFile.build_source_file(os.path.join(self.data_path, 'sample_sources', '4.java'))
        self.assertEqual(unicode(sf), u'Java SourceFile: 1 classes, 1 interfaces')
        simple_lookup = sf.get_class('SimpleLookup')
        lookup = sf.get_interface('Lookup')
        self.assertEqual(simple_lookup.get_method('processValues').lines_count, 7)
        self.assertEqual(len(simple_lookup.fields), 2)
        self.assertEqual(len(lookup.fields), 0)
        self.assertEqual(len(lookup.abstract_methods), 1)
        self.assertEqual(sf.next_token(), None)

    def test_parse_5(self):
        sf = SourceFile.build_source_file(os.path.join(self.data_path, 'sample_sources', '5.java'))
        self.assertEqual(unicode(sf), u'Java SourceFile: 1 classes')
        mc = sf.get_class('PingPONG').get_method('PingPONG')
        self.assertEqual(mc.lines_count, 4)
        self.assertTrue(mc.is_constructor())
        self.assertFalse(sf.get_class('PingPONG').get_method('run').is_constructor())
        self.assertEqual(sf.next_token(), None)

    def test_parse_6(self):
        sf = SourceFile.build_source_file(os.path.join(self.data_path, 'sample_sources', '6.java'))
        self.assertEqual(unicode(sf), u'Java SourceFile: 1 classes')
        account = sf.get_class('Account')
        self.assertEqual(len(account.methods), 4)
        self.assertEqual(len(account.fields), 1)
        self.assertEqual(account.get_method('abs').lines_count, 8)
        self.assertEqual(sf.next_token(), None)


class TestParseInternals(unittest.TestCase):
    def test_visibility_parse(self):
        self.assertEqual(JavaClass.parse_access('private'), JavaClass.ACCESS.PRIVATE)
        self.assertEqual(JavaClass.parse_access(None), JavaClass.ACCESS.PACKAGE)
        self.assertEqual(JavaClass.parse_access(''), JavaClass.ACCESS.PACKAGE)
        self.assertEqual(JavaClass.parse_access(' '), JavaClass.ACCESS.PACKAGE)
        self.assertEqual(JavaClass.parse_access('package'), JavaClass.ACCESS.PACKAGE)
        self.assertEqual(JavaClass.parse_access('protected'), JavaClass.ACCESS.PROTECTED)
        self.assertEqual(JavaClass.parse_access('public'), JavaClass.ACCESS.PUBLIC)
        self.assertEqual(JavaClass.parse_access('public '), JavaClass.ACCESS.PUBLIC)
        self.assertEqual(JavaClass.parse_access('published'), JavaClass.ACCESS.UNKNOWN)
