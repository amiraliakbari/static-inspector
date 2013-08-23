# -*- coding: utf-8 -*-
import re
from networkx import Graph


class FrameworkFeatureAnalyzer(object):
    def __init__(self, framework, project):
        """
            :param inspector.models.base.Project project: the project to be analyzed
        """
        self.project = project

        self.framework_namespace = str(framework)
        self.framework_tree = Graph()
        self.framework_tree.add_node(self.framework_namespace)
        self.import_usages = []

    def add_source_file(self, source_file):
        """
            :param inspector.models.base.SourceFile source_file: the file
        """
        self.analyze_framework_imports(source_file)
        self.analyze_source(source_file)

    def analyze_framework_imports(self, source_file):
        """
            :param inspector.models.base.SourceFile source_file: the file
        """
        for im in source_file.imports:
            if im.import_str.startswith(self.framework_namespace):
                self.import_usages.append((im, im.find_usages()))

                components = im.import_str.split('.')

                data = {'group': 1}
                if re.match(r'^[A-Z]+(_[A-Z]+)*$', components[-1]):
                    data['group'] = 3

                last = None
                for i in range(len(components)):
                    cn = '.'.join(components[:i + 1])
                    self.framework_tree.add_node(cn, **data)
                    if last:
                        self.framework_tree.add_edge(last, cn, weight=1, group=1)
                    last = cn
                if last:
                    data['group'] = 3
                    self.framework_tree.add_node(last, **data)

    def analyze_source(self, source_file):
        """
            :param inspector.models.base.SourceFile source_file: the file
        """
        for cl in source_file.classes:
            self.framework_tree.add_node(cl.name, group=4)
            for fu in cl.methods:
                # print '[{0}-{1}]'.format(fu.starting_line, fu.ending_line), re.sub('\s*\n\s*', ' ', unicode(fu))
                fn = fu.qualified_name
                self.framework_tree.add_node(fn, group=5)
                self.framework_tree.add_edge(cl.name, fn, weight=1, group=2)
                for im, usages in self.import_usages:
                    w = 0
                    for ln in usages:
                        if fu.starting_line <= ln <= fu.ending_line:
                            w += 1
                    if w:
                        self.framework_tree.add_edge(im.import_str, fn, weight=w, group=3)
