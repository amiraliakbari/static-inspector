# -*- coding: utf-8 -*-
import os

from inspector.models.base import Project

if __name__ == '__main__':
    # configs
    PROJECTS_PATH = '/data/code/android'
    projects = ['github-android', 'linphone-android', 'vlc/vlc-android', 'mytracks/MyTracks']
    exts = ['java', 'xml', 'c']

    for project_dir in projects:
        project_dir = os.path.join(PROJECTS_PATH, project_dir)
        print '========================='
        print ' Project Analysis Report '
        print '========================='
        print '  path:', project_dir
        p = Project(project_dir)
        p.rescan_files()
        print '  Total number of files:', len(p._files)
        print '  File type breakdown:'
        TR = len(p._files) / 10
        for k, v in p._file_groups.iteritems():
            if not k:
                k = '""'
            loc = None
            if k in exts:
                loc = 0
                for f in v:
                    loc += p.get_file(f).lines_count
            if loc or len(v) >= TR:
                print '   ', k, '  \t', len(v), ' \t', loc if loc else 'N/A'
        print ""
