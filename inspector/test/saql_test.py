# -*- coding: utf-8 -*-
import unittest
from inspector.saql.saql_parser import SaqlParser


class ParserTest(unittest.TestCase):
    def test_simple_parse(self):
        qs1 = 'SELECT classes FROM project WHERE isSubClass(class:package.TheParentClassName)'
        q1 = SaqlParser.parse_query(qs1)
        self.assertEqual(q1.select_type, 'classes')
        self.assertListEqual(q1.select_from, ['project'])
        self.assertListEqual(q1.where_conditions, ['isSubClass(class:package.TheParentClassName)'])
        self.assertEqual(unicode(q1), qs1)
