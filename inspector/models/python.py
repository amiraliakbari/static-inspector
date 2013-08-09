# -*- coding: utf-8 -*-
from inspector.models.base import Project, SourceFile


class PythonProject(Project):
    pass


class PythonSourceFile(SourceFile):
    def __init__(self, filename, package=None):
        super(PythonSourceFile, self).__init__(filename, package=package)

    def _parse(self):
        pass
