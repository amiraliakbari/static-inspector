# -*- coding: utf-8 -*-
import os

from inspector.analyzer.feature.framework_feature_analyzer import FrameworkFeatureAnalyzer
from inspector.utils.visualization.graph import generate_graph_html


def framework_features_analyze(project):
    """
        :param inspector.models.base.Project project: project to be analyzed
    """
    print '===================================='
    print ' Framework Feature Location Results '
    print '===================================='

    fa = FrameworkFeatureAnalyzer('android', project=project)
    # TODO: use package format:
    source_file = project.get_file('app/src/main/java/com/github/mobile/ui/issue/IssueFragment.java')
    fa.analyze_framework_imports(source_file)
    fa.analyze_source(source_file)

    current_dir = os.path.abspath(os.path.dirname(__file__))
    generate_graph_html(fa.framework_tree, os.path.join(current_dir, 'reports', 'report.html'))
