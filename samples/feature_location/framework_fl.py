# -*- coding: utf-8 -*-
from inspector.analyzer.feature.framework_feature_analyzer import FrameworkFeatureAnalyzer


def framework_features_analyze(project):
    """
        :param inspector.models.base.Project project: project to be analyzed
    """
    print '===================================='
    print ' Framework Feature Location Results '
    print '===================================='

    fa = FrameworkFeatureAnalyzer('android', project=project)
    # TODO: use package format
    fa.analyze_file_imports(project.get_file('app/src/main/java/com/github/mobile/ui/issue/IssueFragment.java'))
