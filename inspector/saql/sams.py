# -*- coding: utf-8 -*-
from inspector.models.android import AndroidProject
from inspector.models.base import Method
from inspector.saql.saql_parser import SaqlParser


class SAMS(object):
    QUERY_DEF = {
        'SELECT': {
            'class': ['file', 'project'],
            'method': ['class', 'file', 'project'],
            'file': ['project'],
        },
        'FUNCTIONS': {
            'class': [
                ('isSubClass', lambda c, parent: issubclass(c, parent)),
            ],
            'method': [
                ('isAbstract', lambda m: m.abstract),
                ('isPrivate', lambda m: m.access == Method.ACCESS.PRIVATE),
                ('isProtected', lambda m: m.access == Method.ACCESS.PROTECTED),
                ('isPackage', lambda m: m.access == Method.ACCESS.PACKAGE),
                ('isPublic', lambda m: m.access == Method.ACCESS.PUBLIC),
            ],
        }
    }

    def __init__(self):
        self.project = None

    def open_project(self, project_path):
        self.project = AndroidProject(project_path)

    def parse_identifier(self, identifier):
        if identifier == ['project'] or identifier == 'project':
            return self.project.all_files()
        if isinstance(identifier, list) or isinstance(identifier, tuple):
            return (self.project.find(iden) for iden in identifier)
        return self.project.find(identifier)

    def verify_query(self, query_def, query_type='SELECT'):
        if not query_def[1] in self.QUERY_DEF[query_type][query_def[0]]:
            raise ValueError('Query not applicable on these types: {0}'.format(query_def))

    def run_query(self, query):
        if not self.project:
            raise ValueError('No project selected!')

        q = SaqlParser.parse_query(query)
        if q.is_select_classes():
            classes = []
            sel = ('class', q.select_from_type)
            self.verify_query(sel)
            for obj in self.parse_identifier(q.select_from):
                classes += obj.classes
            return classes
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
            return "Project loaded"
        raise ValueError('Invalid Action: {0}'.format(action))

    def run(self, command):
        """
            :param str command: The user input, a query or a action
        """
        if command.startswith('\\'):
            return self.run_action(command)
        else:
            return self.run_query(command)
