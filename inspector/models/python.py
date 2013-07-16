# -*- coding: utf-8 -*-
from inspector.models.base import Project, SourceFile


class PythonProject(Project):
    pass


class PythonSourceFile(SourceFile):
    def _parse(self):
        pass
