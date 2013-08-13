# -*- coding: utf-8 -*-
import copy

from inspector.models.base import SourceFile


class FileCoverageReport(object):
    def __init__(self, source_file=None):
        """
            :type source_file: str or SourceFile or None
        """
        self.covered_lines = set()
        self.exec_info = []
        self.source_file = None

        self.set_source_file(source_file)

    def set_source_file(self, source_file):
        if isinstance(self.source_file, SourceFile):
            self.source_file.attach_coverage_report(None)
        self.source_file = source_file
        if isinstance(self.source_file, SourceFile):
            self.source_file.attach_coverage_report(self)

    @property
    def covered_lines_count(self):
        return len(self.covered_lines)

    def cover_line(self, line_number):
        """
            :type line_number: list of int or set of int or int or str
        """
        if isinstance(line_number, list) or isinstance(line_number, set):
            for l in line_number:
                self.covered_lines.add(l)
        elif isinstance(line_number, int):
            self.covered_lines.add(line_number)
        elif isinstance(line_number, str):
            self.cover_line(self.parse_line_range(line_number))
        else:
            raise ValueError('Line number must be an integer.')

    def process_execution_summary(self, exec_summary):
        raise NotImplementedError

    def __sub__(self, other):
        """
            :type other: FileCoverageReport
        """
        if self.source_file != other.source_file:
            return NotImplemented
        result = copy.deepcopy(self)
        result.covered_lines -= other.covered_lines
        # TODO: also consider exec_info
        return result

    def __getitem__(self, item):
        """
            :type item: slice
        """
        if not isinstance(item, slice):  # TODO: also check step to be 1
            raise TypeError
        r = FileCoverageReport(source_file=self.source_file)
        r.covered_lines = set(x for x in self.covered_lines if item.start <= x < item.stop)
        return r

    def __unicode__(self):
        return self.format_line_range(self.covered_lines)

    def __str__(self):
        return unicode(self)

    @classmethod
    def format_line_range(cls, a):
        """
            :param set or list a: iterable containing line numbers
            :rtype: str
        """
        blocks = []
        block_start = None
        last = None
        for ln in sorted(a):
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
        return ', '.join(('%d-%d' % b if b[0] != b[1] else unicode(b[0])) for b in blocks)

    @classmethod
    def parse_line_range(cls, s):
        """
            :param str s: string having the line range
            :rtype: set of int
        """
        lines = set()
        rr = s.split(',')
        for r in rr:
            i = r.find('-')
            if i == -1:
                lines.add(int(r.strip()))
            else:
                for l in range(int(r[:i].strip()), int(r[i+1:].strip()) + 1):
                    lines.add(l)
        return lines


class ProjectCoverageReport(object):
    def __init__(self):
        self.files = {}

    def add_coverage_report(self, file_report):
        if not file_report.source_file:
            raise ValueError('Project coverage reports must have a valid filename.')
        self.files[file_report.source_file] = file_report

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
