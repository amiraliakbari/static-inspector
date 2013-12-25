# -*- coding: utf-8 -*-
import re


class SaqlQuery(object):
    def __init__(self):
        self.select_type = None
        self.select_from = []
        self.where_conditions = []

    def __unicode__(self):
        qs = u'SELECT {0} FROM {1}'.format(self.select_type, u','.join(self.select_from))
        if self.where_conditions:
            qs += u' WHERE ' + u' AND '.join(self.where_conditions)
        return qs

    def is_select_classes(self):
        return self.select_type == 'classes'

    def is_select_methods(self):
        return self.select_type == 'methods'

    def is_select_instances(self):
        return self.select_type == 'instances'

    def is_select_lines(self):
        return self.select_type == 'lines'


class SaqlParser(object):
    @classmethod
    def parse_query(cls, query):
        """
            :rtype: SaqlQuery
        """
        m = re.match(r'^SELECT\s+(.*?)\s+FROM\s+(.*?)(?:\s+WHERE\s+(.*?))?$', query)
        if not m:
            raise ValueError('Invalid Query!')

        q = SaqlQuery()
        q.select_type = m.group(1).strip()
        q.select_from = [s.strip() for s in m.group(2).split(',')]
        q.where_conditions = [s.strip() for s in m.group(3).split(' AND ')]
        return q
