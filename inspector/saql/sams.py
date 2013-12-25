# -*- coding: utf-8 -*-
from inspector.saql.saql_parser import SaqlParser


class SAMS(object):
    def __init__(self):
        self.project = None

    def open_project(self, project_path):
        self.project = project_path

    def run_query(self, query):
        if not self.project:
            raise ValueError('No project selected!')

        q = SaqlParser.parse_query(query)
        if q.is_select_classes():
            pass
        elif q.is_select_methods():
            pass
        elif q.is_select_instances():
            pass
        elif q.is_select_lines():
            pass
        else:
            raise ValueError('Unsupported query type: {0}'.format(q.select_type))
        return []

    def run_action(self, action):
        if action.startswith(r'\c '):
            self.open_project(action[3:])
            return
        raise ValueError('Invalid Action: {0}'.format(action))

    def run(self, command):
        """
            :param str command: The user input, a query or a action
        """
        if command.startswith('\\'):
            return self.run_action(command)
        else:
            return self.run_query(command)
