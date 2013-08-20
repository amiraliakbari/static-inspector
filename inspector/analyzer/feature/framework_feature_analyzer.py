# -*- coding: utf-8 -*-


class FrameworkFeatureAnalyzer(object):
    def __init__(self, framework, project):
        """
            :param inspector.models.base.Project project: the project to be analyzed
        """
        self.framework_namespace = framework
        self.project = project

    def analyze_file_imports(self, source_file):
        """
            :param inspector.models.base.SourceFile source_file: the file
        """
        for im in source_file.imports:
            if im.import_str.startswith(self.framework_namespace):
                print im
