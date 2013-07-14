# -*- coding: utf-8 -*-
import unittest

from inspector.coverage.raw_coverage_report import FileCoverageReport


class TestCoverageReport(unittest.TestCase):
    def test_file_coverage_report(self):
        fcr = FileCoverageReport('coverage_test.py', package='inspector.test')
        for x in [1, 4, 7, 5, 100, 200]:
            fcr.cover_line(x)
        for x in range(50, 75):
            fcr.cover_line(x)
        for x in range(90, 110):
            fcr.cover_line(x)
        self.assertEqual(unicode(fcr), '1, 4-5, 7, 50-74, 90-109, 200')

if __name__ == '__main__':
    unittest.main()
