# -*- coding: utf-8 -*-
import os
import unittest

from inspector.models.android import AndroidProject
from inspector.models.base import Method
from inspector.models.consts import Language
from inspector.utils.strings import has_word


class TestAndroid(unittest.TestCase):
    def setUp(self):
        path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data', 'android', 'github-android')
        self.project = AndroidProject(path)

    # noinspection PyPep8Naming
    def assertFilenameEqual(self, filename1, filename2):
        return filename1.replace('\\', '/').endswith('/github-android/' + filename2)

    def test_import_detection(self):
        sf = self.project.get_file('sample_files/IssuesFragment.java')
        self.assertTrue(sf.language_detected)
        self.assertEqual(sf.language, Language.JAVA)
        self.assertTrue(sf.parsed)
        self.assertEqual(len(sf.imports), 43)

        # specific check for one import
        im = sf.imports[13]
        known_usages = [31, 87, 126]
        self.assertEqual(im.imported_identifier, 'ImageView')
        self.assertListEqual(im.find_usages(), known_usages)
        for i in range(len(sf.lines)):
            ln = i + 1
            self.assertEqual(has_word(sf.get_line(ln), 'ImageView'), ln in known_usages)

        # general check for other imports
        for im in sf.imports:
            identifier = im.imported_identifier
            if identifier == '*':
                continue
            usages = im.find_usages()
            for l in usages:
                self.assertTrue(sf.get_line(l).find(identifier) > -1)

    def test_find(self):
        sf = self.project.find('file:sample_files.IssueFragment')
        self.assertFilenameEqual(sf.filename, 'sample_files/IssueFragment.java')

        cls = self.project.find('class:sample_files.IssueFragment.IssueFragment')
        self.assertEqual(cls.name, 'IssueFragment')
        self.assertFilenameEqual(sf.filename, 'sample_files/IssueFragment.java')

        # alternative (shortcut) way for the same action
        cls = self.project.find('class:sample_files.IssueFragment')
        self.assertEqual(cls.name, 'IssueFragment')
        self.assertFilenameEqual(sf.filename, 'sample_files/IssueFragment.java')

        mt = self.project.find('method:sample_files.IssueFragment.openPullRequestCommits')
        self.assertEqual(mt.name, 'openPullRequestCommits')
        self.assertEqual(mt.access, Method.ACCESS.PRIVATE)

    def test_java_parse_1(self):
        sf = self.project.get_file('sample_files/IssueFragment.java')
        cls = sf.get_class('IssueFragment')
        self.assertEqual(len(cls.fields), 34)
