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
        for ext in p.file_extensions:
            files = p.filter_files(extension=ext)
            ext_name = ext if ext else '""'
            loc = 0
            if ext in exts:
                for f in files:
                    loc += p.get_file(f).lines_count
            if loc or len(files) >= TR:
                print '   ', ext_name, '  \t', len(files), ' \t', loc if loc else 'N/A'
        print ""
