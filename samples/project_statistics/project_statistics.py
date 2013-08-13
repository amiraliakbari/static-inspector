# -*- coding: utf-8 -*-
from inspector.models.base import Project

if __name__ == '__main__':

    projects = [
        '/data/code/android/github-android',
        '/data/code/android/linphone-android',
        '/data/code/android/vlc/vlc-android',
    ]
    exts = ['java', 'xml']
    for project_dir in projects:
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
