# -*- coding: utf-8 -*-
import json
import os
import sys

from inspector.analyzer.project_analyzer import LocCounter, LocCounter2
from inspector.models.base import Project


if __name__ == '__main__':
    if len(sys.argv) == 3:
        project_dir = sys.argv[1]
        plot_type = sys.argv[2]
    else:
        if len(sys.argv) > 1:
            print 'Invalid arguments!'
        project_dir = str(raw_input('Please enter project path: '))
        plot_type = str(raw_input('Please select output format [pie/tree]: '))

    current_dir = os.path.abspath(os.path.dirname(__file__))
    p = Project(project_dir)
    p.ignored_dirs = [
        '.git',
        '.settings', '.idea',
        '.classpath', 'bin',
        'media/uploads', 'media/serve',
        'lib/debug_toolbar', 'static/tiny_mce', 'static/js/tiny_mce', 'static/admin'
    ]

    params = {
        'width': 600,
        'height': 600,
        'pname': p.name,
        'data': '{}',
    }

    if plot_type == 'pie':
        hnd = LocCounter2()
        p.rescan_files(hnd)
        data = hnd.get_data()
        params['data'] = json.dumps(data)
        params['initial_description'] = '{0} characters, {1} lines of code.'.format(data[1], data[2])
        html_template = 'pie_report.html'
    elif plot_type == 'tree':
        hnd = LocCounter()
        p.rescan_files(hnd)
        params['data'] = json.dumps(hnd.get_data())
        html_template = 'tree_report.html'
    else:
        print 'Error: Invalid output type.'
        sys.exit(1)

    with open(os.path.join(current_dir, 'report_templates', html_template), 'r') as f:
        html = f.read()
    for k, v in params.iteritems():
        html = html.replace('{{ ' + k + ' }}', unicode(v))
    with open(os.path.join(current_dir, 'reports', 'report.html'), 'w') as f:
        f.write(html)
