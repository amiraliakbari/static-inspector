# -*- coding: utf-8 -*-
import os

from inspector.utils.strings import render_template


def generate_graph_html(graph, filename):
    """
        :type graph: networkx.Graph
        :param str filename: path to save the generated html file
    """

    params = {
        'nodes': [],
        'links': [],
    }
    ids = {}
    for i, (node, data) in enumerate(graph.nodes(data=True)):
        val = unicode(node)
        ids[val] = i
        params['nodes'].append('{name:"%s",group:%d}' % (node, data.get('group', 1)))
    for u, v, data in graph.edges(data=True):
        params['links'].append('{source:%d,target:%d,value:%d,group:%d}' % (ids[unicode(u)],
                                                                            ids[unicode(v)],
                                                                            data.get('weight', 1),
                                                                            data.get('group', 1)))
    params['nodes'] = ','.join(params['nodes'])
    params['links'] = ','.join(params['links'])

    # generating output
    current_dir = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(current_dir, 'templates', 'force_directed_graph.html'), 'r') as f:
        html = f.read()
    html = render_template(html, params)
    with open(filename, 'w') as f:
        f.write(html)
