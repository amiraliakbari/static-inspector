# -*- coding: utf-8 -*-
import os
from inspector.models.consts import Language


class Project(object):
    def __init__(self):
        self.name = None
        self.abs_path = None


class Package(object):
    def __init__(self, project):
        self.project = project
        self.name = None

    def get_abs_path(self):
        return self.project.abs_path if self.project else None


class File(object):
    def __init__(self):
        self.file_content = None
        self.filename = None

    def get_abs_path(self):
        return self.filename

    def load_content(self):
        with open(self.get_abs_path(), 'r') as f:
            self.file_content = f.read()


class SourceFile(File):
    def __init__(self):
        super(SourceFile, self).__init__()
        self.language = Language.UNKNOWN
        self.package = None

    @property
    def project(self):
        return self.package.project

    def get_abs_path(self):
        pkg_abs = self.package.get_abs_path() if self.package else ''
        return os.path.join(pkg_abs, self.filename)


class Class(object):
    pass


class Function(object):
    pass


class Method(Function):
    pass
