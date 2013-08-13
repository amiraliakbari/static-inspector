# -*- coding: utf-8 -*-
import xml.sax

from ..raw_coverage_report import ProjectCoverageReport, FileCoverageReport


class HandleXml(xml.sax.ContentHandler):
    def __init__(self, report):
        self.report = report
        self.package = None
        self.cur_file = None

    def startElement(self, name, attributes):
        if name == 'package':
            self.package = attributes['name']
        elif self.package is not None and name == 'sourcefile':
            package = self.package.replace('.', '/').replace('\\', '/').strip()
            path = package + ('/' if package else '') + attributes['name']
            self.cur_file = FileCoverageReport(source_file=path)
        elif self.cur_file and name == 'line':
            if int(attributes['ci']) > 0:
                self.cur_file.cover_line(int(attributes['nr']))

    def endElement(self, name):
        if name == 'package':
            self.package = None
        elif name == 'sourcefile':
            self.report.add_coverage_report(self.cur_file)
            self.cur_file = None


class EclEmmaXmlParser(object):
    def __init__(self, xml_file):
        self.report = ProjectCoverageReport()
        self.xml_file = xml_file
        self.parser = xml.sax.make_parser()
        self.parser.setContentHandler(HandleXml(self.report))
        self.parse()

    def parse(self):
        self.parser.parse(self.xml_file)

    def get_report(self):
        return self.report
