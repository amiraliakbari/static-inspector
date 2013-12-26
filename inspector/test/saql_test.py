# -*- coding: utf-8 -*-
import unittest
from inspector.saql.saql_parser import SaqlParser


class ParserTest(unittest.TestCase):
    def test_simple_parse_1(self):
        qs1 = 'SELECT classes FROM project WHERE isSubClass(class:package.TheParentClassName)'
        q1 = SaqlParser.parse_query(qs1)
        self.assertEqual(q1.select_type, 'classes')
        self.assertListEqual(q1.select_from, ['project'])
        self.assertListEqual(q1.where_conditions, ['isSubClass(class:package.TheParentClassName)'])
        self.assertEqual(q1.select_from_type, 'project')
        self.assertTrue(q1.is_project_level())
        self.assertEqual(unicode(q1), qs1)

    def test_simple_parse_2(self):
        qs1 = 'SELECT classes FROM project'
        q1 = SaqlParser.parse_query(qs1)
        self.assertEqual(q1.select_type, 'classes')
        self.assertListEqual(q1.select_from, ['project'])
        self.assertListEqual(q1.where_conditions, [])
        self.assertEqual(unicode(q1), qs1)
