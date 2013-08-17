# -*- coding: utf-8 -*-
from inspector.analyzer.file_analyzer import FileAnalyzer
from inspector.models.base import Project


class LocCounter(Project.FileDfsHandler):
    def setup(self):
        self.data = {}
        self.node_stack = []

    def enter_dir(self, path):
        if self.node_stack:
            node = {'name': path.split('/')[-1], 'children': []}
            self.node_stack[-1]['children'].append(node)
        else:
            node = self.data = {'name': 'Project: ' + self.project.name, 'children': []}
        self.node_stack.append(node)

    def exit_dir(self, path):
        self.node_stack.pop()

    def handle_file(self, path):
        self.node_stack[-1]['children'].append({
            'name': path.split('/')[-1],
            'size': FileAnalyzer.estimate_file_size(self.project.get_file(path))[0],
        })

    def get_data(self):
        return self.data


class LocCounter2(Project.FileDfsHandler):
    def setup(self):
        self.data = None
        self.node_stack = []

    def enter_dir(self, path):
        if self.node_stack:
            name = path.split('/')[-1]
            node = self.node_stack[-1][-1][name.replace('.', '-')] = [
                name,
                0,
                0,
                {},
            ]
        else:
            node = self.data = ['Project: ' + self.project.name, 100, 10, {}]
        self.node_stack.append(node)

    def exit_dir(self, path):
        node = self.node_stack.pop()
        x, y = 0, 0
        for _, f in node[-1].iteritems():
            x += f[1]
            y += f[2]
        node[1] = x
        node[2] = y

    def handle_file(self, path):
        name = path.split('/')[-1]
        file_obj = self.project.get_file(path)
        sz, loc = FileAnalyzer.estimate_file_size(file_obj)
        self.node_stack[-1][-1][name.replace('.', '-')] = [name, sz, loc, {}]

    def get_data(self):
        return self.data
