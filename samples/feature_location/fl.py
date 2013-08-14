# -*- coding: utf-8 -*-
import sys

from inspector.coverage.parsers.ecl_emma_xml_parser import EclEmmaXmlParser
from inspector.models.java import JavaProject


if __name__ == '__main__':
    if len(sys.argv) < 2:
        project_dir = str(raw_input('Please enter project path: '))
    else:
        project_dir = sys.argv[1]

    p = JavaProject(project_dir)
    p.rescan_files()
    dyna_features = p.filter_files(cond=lambda s: s.startswith('fl_coverage/') and s.endswith('_a.xml'))

    print '==========================='
    print ' Feature Detection Summary '
    print '==========================='
    for df in dyna_features:
        feature_name = df[12:-6]
        feature_a = df
        feature_b = feature_a[:-6] + '_b.xml'
        a = EclEmmaXmlParser(p.build_path(feature_a)).get_report()
        b = EclEmmaXmlParser(p.build_path(feature_b)).get_report()
        diff = a - b

        print 'Feature: "{0}"'.format(feature_name)
        for report in diff.get_reports():
            s = unicode(report)
            if s == '-':
                continue

            methods = []
            classes = set()
            filename = report.source_file[:-5].replace('/', '.')

            sf = p.get_file(filename, is_qualified=True)
            sf.attach_coverage_report(report)
            for c in sf.classes:
                for m in c.methods:
                    if m.covered_ratio() > 0:
                        methods.append(m)
                        classes.add(m.parent_class)

            methods_rep = []
            for m in methods:
                methods_rep.append((int(m.covered_ratio() * 100), m.name))
            methods_rep = ', '.join(['{1}({0}%)'.format(*f) for f in sorted(methods_rep, reverse=True)])

            print '  File: `%s`' % report.source_file
            print '    > classes:', ', '.join([c.name for c in classes])
            print '    > methods:', methods_rep
            print '    > lines: %s' % s
            print ''
