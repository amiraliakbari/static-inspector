# -*- coding: utf-8 -*-
import os
import unittest
from inspector.saql.sams import SAMS
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


class SAMSTest(unittest.TestCase):
    def setUp(self):
        path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data', 'projects', 'gissue')
        self.sams = SAMS()
        self.sams.open_project(path)

    def test_select_classes(self):
        q1 = 'SELECT classes FROM project'
        r = self.sams.run_query(q1)
        self.assertItemsEqual([c.qualified_name for c in r],
                              ['com.g.issue.IssueFragment', 'com.g.issue.IssuesFragment'])

        q2 = 'SELECT classes FROM file:com.g.issue.IssueFragment'
        r = self.sams.run_query(q2)
        self.assertItemsEqual([c.qualified_name for c in r],
                              ['com.g.issue.IssueFragment'])

        q3 = 'SELECT classes FROM file:com.g.issue.IssueFragment, file:com.g.issue.IssuesFragment'
        r = self.sams.run_query(q3)
        self.assertItemsEqual([c.qualified_name for c in r],
                              ['com.g.issue.IssueFragment', 'com.g.issue.IssuesFragment'])

        q4 = 'SELECT classes FROM class:com.g.issue.IssueFragment'
        self.assertRaises(ValueError, self.sams.run_query, q4)

        q5 = "SELECT classes FROM project WHERE isSubclassOf('DialogFragment')"
        r = self.sams.run_query(q5)
        self.assertItemsEqual([c.qualified_name for c in r],
                              ['com.g.issue.IssueFragment'])
