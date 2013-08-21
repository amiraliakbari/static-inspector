# -*- coding: utf-8 -*-
import sys

from inspector.models.android import AndroidProject
from inspector.models.base import Project
from inspector.models.java import JavaProject

from feature_location.dynamic_fl import dynamic_analyze
from feature_location.framework_fl import framework_features_analyze


if __name__ == '__main__':
    if len(sys.argv) < 4:
        project_dir = str(raw_input('Please enter project\'s path (base directory): '))
        project_type = str(raw_input('What is the project type? [java/android/auto] '))
        analysis_type = str(raw_input('Select the analysis to perform on this project: [dynamic/framework-features] '))
    else:
        project_dir = sys.argv[1]
        project_type = sys.argv[2]
        analysis_type = sys.argv[3]

    if project_type == 'java':
        project_class = JavaProject
    elif project_type == 'android':
        project_class = AndroidProject
    elif project_type == 'auto':
        # TODO: really auto-detect type
        project_class = Project
    else:
        print '[ERROR] Unknown project type: "{0}"'.format(project_type)
        sys.exit(1)

    try:
        p = project_class(project_dir)
    except ValueError:
        print '[ERROR] Invalid directory: "{0}"'.format(project_dir)
        sys.exit(1)
    p.rescan_files()

    if analysis_type == 'dynamic':
        dynamic_analyze(p)
    elif analysis_type == 'framework-features':
        framework_features_analyze(p)
    else:
        print '[ERROR] Invalid analysis type: "{0}"'.format(analysis_type)
        sys.exit(1)
