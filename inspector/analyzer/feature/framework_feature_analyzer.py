# -*- coding: utf-8 -*-
import re

from networkx import Graph


class FrameworkFeatureAnalyzer(object):
    """ A class to do feature location analyses on a project written in a specific framework

        Project Graph Details:
        -----------------------
        Node Groups:
            1: Android package
            2: -
            3: Android imported indentifier
            4: Java class
            5: Java method
            6: XML file Category
            7: XML file

        Edge Groups:
            1: internal/hierarchical links
            2: Java---Android mappings
            3: Java---XML mappings
    """

    def __init__(self, framework, project):
        """
            :param inspector.models.base.Project project: the project to be analyzed
        """
        self.project = project

        self.framework_namespace = str(framework)
        self.graph = Graph()
        self.graph.add_node(self.framework_namespace)
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
                    self.graph.add_node(cn, **data)
                    if last:
                        self.graph.add_edge(last, cn, weight=1, group=1)
                    last = cn
                if last:
                    data['group'] = 3
                    self.graph.add_node(last, **data)

    def analyze_source(self, source_file):
        """
            :param inspector.models.base.SourceFile source_file: the file
        """
        for cl in source_file.classes:
            self.graph.add_node(cl.name, group=4)
            for fu in cl.methods:
                # print '[{0}-{1}]'.format(fu.starting_line, fu.ending_line), re.sub('\s*\n\s*', ' ', unicode(fu))
                fn = fu.qualified_name
                self.graph.add_node(fn, group=5)
                self.graph.add_edge(cl.name, fn, weight=1, group=1)
                for im, usages in self.import_usages:
                    w = 0
                    for ln in usages:
                        if fu.starting_line <= ln <= fu.ending_line:
                            w += 1
                    if w:
                        self.graph.add_edge(im.import_str, fn, weight=w, group=2)

    def add_xml_files(self):
        xml_sub_groups = {':layout', ':values', ':drawable', ':menu', ':xml', ':color'}
        self.graph.add_nodes_from([':XML'] + list(xml_sub_groups), group=6)
        self.graph.add_edges_from([(':XML', g) for g in xml_sub_groups], weight=1, group=1)
        for path in self.project.filter_files(extension='xml'):
            xml_file = self.project.get_file(path)

            if path.startswith('app/res/'):
                g = path.split('/')[2]
                name = '/'.join(path.split('/')[2:])
                self.graph.add_node(name, group=7)
            else:
                if not path.split('/')[-1] in ['pom.xml', 'AndroidManifest.xml']:  # is ignored?
                    print 'invalid path:', path
                continue

            valid_group = False
            if g == 'values':
                g = 'values-default'
            if g.startswith('values-'):
                g = g[7:]
                self.graph.add_edge(':values', ':' + g, weight=1, group=1)
                valid_group = True
            g = ':' + g
            if valid_group or g in xml_sub_groups:
                self.graph.add_edge(g, name, weight=1, group=1)
            else:
                print 'invalid subgroup:', g
