# -*- coding: utf-8 -*-
import copy


class FileCoverageReport(object):
    def __init__(self, filename, package=''):
        package = package.replace('.', '/').replace('\\', '/').strip()
        self.filename = package + ('/' if package else '') + filename
        self.covered_lines = set()
        self.exec_info = []

    def cover_line(self, line_number):
        self.covered_lines.add(line_number)

    def process_executation_summary(self, exec_summary):
        raise NotImplementedError

    def __sub__(self, other):
        if self.filename != other.filename:
            return NotImplemented
        result = copy.deepcopy(self)
        result.covered_lines -= other.covered_lines
        # TODO: also consider exec_info
        return result

    def __unicode__(self):
        blocks = []
        block_start = None
        last = None
        for ln in sorted(self.covered_lines):
            if last is None:
                block_start = ln
                last = ln - 1
            if ln > last + 1:
                blocks.append((block_start, last))
                block_start = ln
            last = ln
        if block_start is not None:
            blocks.append((block_start, last))
        if not blocks:
            return '-'
        return u', '.join((u'%d-%d' % b if b[0] != b[1] else unicode(b[0])) for b in blocks)

    def __str__(self):
        return unicode(self)


class ProjectCoverageReport(object):
    def __init__(self):
        self.files = {}

    def add_coverage_report(self, file_report):
        self.files[file_report.filename] = file_report

    def get_reports(self):
        return self.files.itervalues()

    def __sub__(self, other):
        result = copy.deepcopy(self)
        for filename, f in self.files.items():
            if filename in other.files:
                result.add_coverage_report(f - other.files[filename])
            else:
                result.add_coverage_report(copy.deepcopy(f))
        return result

    def __unicode__(self):
        s = u''
        for filename, report in self.files.items():
            s += u'%s: %s\n' % (filename, report)
        if not s:
            s = '<Empty>'
        return s

    def __str__(self):
        return unicode(self)
