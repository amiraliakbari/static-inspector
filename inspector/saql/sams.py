# -*- coding: utf-8 -*-
import re
from inspector.models.android import AndroidProject
from inspector.models.base import Method
from inspector.saql.saql_parser import SaqlParser


class SAMS(object):
    FN = {
        'nameIs': lambda o, p: o.name == p,
        'nameIsLike': lambda o, p: re.match(p, o.name) is not None,
    }
    QUERY_DEF = {
        'SELECT': {
            'class': ['file', 'project'],
            'method': ['class', 'file', 'project'],
            'file': ['project'],
            'line': [],
            'instance': [],
        },
        'FUNCTIONS': {
            'class': {
                'isSubclassOf': lambda c, parent: c.is_subclass_of(parent),
                'nameIs': FN['nameIs'],
                'nameIsLike': FN['nameIsLike'],
            },
            'method': {
                'nameIs': FN['nameIs'],
                'nameIsLike': FN['nameIsLike'],
                'isAbstract': lambda m: m.abstract,
                'isPrivate': lambda m: m.access == Method.ACCESS.PRIVATE,
                'isProtected': lambda m: m.access == Method.ACCESS.PROTECTED,
                'isPackage': lambda m: m.access == Method.ACCESS.PACKAGE,
                'isPublic': lambda m: m.access == Method.ACCESS.PUBLIC,
            },
            'file': {},
            'line': {},
            'instance': {},
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

    def parse_token(self, token):
        token = token.strip()
        candidate_types = [int, float]
        for tp in candidate_types:
            try:
                return tp(token)
            except ValueError:
                pass
        if len(token) > 1 and token[0] == "'" and token[-1] == "'":
            return str(token[1:-1])
        return self.parse_identifier(token)

    def verify_query(self, query_def, query_type='SELECT'):
        if not query_def[1] in self.QUERY_DEF[query_type][query_def[0]]:
            raise ValueError('Query not applicable on these types: {0}'.format(query_def))

    def select_candidate_classes(self, query):
        """ Give all classes that match queries FROM clause

            :param SaqlQuery query: the query
            :rtype: list of inspector.models.base.Class
        """
        classes = []
        for obj in self.parse_identifier(query.select_from):
            classes += obj.classes
        return classes

    def select_candidate_methods(self, query):
        """ Give all methods that match queries FROM clause

            :param SaqlQuery query: the query
            :rtype: list of inspector.models.base.Method
        """
        methods = []
        if query.select_from_type != 'class':
            candidate_classes = self.select_candidate_classes(query)
        else:
            candidate_classes = self.parse_identifier(query.select_from)
        for cc in candidate_classes:
            methods += cc.methods
        return methods

    def run_query(self, query):
        if not self.project:
            raise ValueError('No project selected!')

        q = SaqlParser.parse_query(query)

        if q.is_select():
            # first gathering all candidates
            sel = ['?', q.select_from_type]
            objects = []
            if q.is_select_classes():
                sel[0] = 'class'
                self.verify_query(sel)
                objects = self.select_candidate_classes(q)
            elif q.is_select_methods():
                sel[0] = 'method'
                self.verify_query(sel)
                objects = self.select_candidate_methods(q)
            elif q.is_select_lines():
                sel[0] = 'line'
                self.verify_query(sel)
            elif q.is_select_instances():
                sel[0] = 'instance'
                self.verify_query(sel)
            else:
                raise ValueError('Unsupported query type: {0}'.format(q.select_type))

            # filtering by WHERE conditions
            for wcl in q.where_conditions:
                # TODO: support operators on functions too
                m = re.match(r'^\s*(\w+)\s*\((.*?)\)\s*$', wcl)
                if not m:
                    raise ValueError('Invalid WHERE condition: {0}'.format(wcl))
                fn_name = m.group(1)
                fn_params = [self.parse_token(s) for s in m.group(2).split(',')] if m.group(2) else []
                try:
                    fn_callable = self.QUERY_DEF['FUNCTIONS'][sel[0]][fn_name]
                except KeyError:
                    raise ValueError('Invalid function for {1} object: {0}'.format(fn_name, sel[0]))
                objects = filter(lambda o: fn_callable(o, *fn_params), objects)

            return objects

        raise ValueError('Unsupported query')

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
