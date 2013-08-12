# -*- coding: utf-8 -*-
import sys

from inspector.coverage.parsers.ecl_emma_xml_parser import EclEmmaXmlParser


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print >> sys.stderr, 'usage: fl.py main_feature_file other_feature_file'
        exit(1)
    feature_a = sys.argv[1]
    feature_b = sys.argv[2]
    a = EclEmmaXmlParser(feature_a).get_report()
    b = EclEmmaXmlParser(feature_b).get_report()

    diff = a - b

    print '==========================='
    print ' Feature Detection Summary '
    print '==========================='

    for report in diff.get_reports():
        s = unicode(report)
        if s == '-':
            continue
        print 'File: `%s`' % report.filename
        print '   ==> lines: %s' % s
        print ''
