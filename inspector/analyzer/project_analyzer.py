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
            'size': FileAnalyzer.estimate_file_size(self.project.get_file(path)),
        })

    def get_data(self):
        return self.data
