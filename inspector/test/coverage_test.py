# -*- coding: utf-8 -*-
import os
import unittest

from inspector.coverage.raw_coverage_report import FileCoverageReport
from inspector.models.java import JavaSourceFile


class TestCoverageReport(unittest.TestCase):
    def test_file_coverage_report(self):
        fcr = FileCoverageReport()
        for x in [1, 4, 7, 5, 100, 200]:
            fcr.cover_line(x)
        for x in range(50, 75):
            fcr.cover_line(x)
        for x in range(90, 110):
            fcr.cover_line(x)
        self.assertEqual(unicode(fcr), '1, 4-5, 7, 50-74, 90-109, 200')


class TestJavaCoverage(unittest.TestCase):
    def setUp(self):
        self.data_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data', 'java')

    def test_whole_file_coverage(self):
        sf = JavaSourceFile(os.path.join(self.data_path, 'sample_sources', '1.java'))
        r1 = FileCoverageReport(source_file=sf)
        self.assertAlmostEqual(sf.covered_ratio(), 0)
        r1.cover_line([5, 6, 7, 8])
        self.assertEqual(sf.coverage.covered_lines_count, 4)
        self.assertEqual(sf.lines_count, 23)
        self.assertAlmostEqual(sf.covered_ratio(), .174, places=3)
        r1.cover_line('14-20')
        self.assertEqual(sf.coverage.covered_lines_count, 11)
        self.assertAlmostEqual(sf.covered_ratio(), .478, places=3)
        self.assertAlmostEqual(sf.get_class('MyFirstProgram').get_method('main').covered_ratio(), .579, places=3)
