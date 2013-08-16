# -*- coding: utf-8 -*-
from inspector.models.base import Project, SourceFile
from inspector.models.consts import Language


class PythonProject(Project):
    pass


class PythonSourceFile(SourceFile):
    def __init__(self, filename, package=None):
        super(PythonSourceFile, self).__init__(filename, package=package)

    @property
    def language(self):
        return Language.PYTHON
