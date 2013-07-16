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
    def __init__(self, filename):
        self.file_content = None
        self.filename = filename

    def get_abs_path(self):
        return self.filename

    def load_content(self):
        with open(self.get_abs_path(), 'r') as f:
            self.file_content = f.read()

    def detect_language(self):
        ext = os.path.splitext(self.filename)[1]
        if ext == '.java':
            return Language.JAVA
        elif ext == '.py':
            return Language.PYTHON
        return Language.UNKNOWN


class SourceFile(File):
    def __init__(self, filename, package=None, language=None):
        super(SourceFile, self).__init__(filename)
        self.package = package
        self.language = language if language is not None else self.detect_language()

        # parse info:
        self.imports = []
        self.classes = []
        self.functions = []

        self.load_content()

    def __unicode__(self):
        msg = u'%s SourceFile: %d imports, %d classes, %d functions'
        lng = Language.get_display_name(self.language)
        return msg % (lng, len(self.imports), len(self.classes), len(self.functions))

    def __str__(self):
        return self.__unicode__()

    @property
    def project(self):
        return self.package.project if self.package else None

    def get_abs_path(self):
        pkg_abs = self.package.get_abs_path() if self.package else ''
        return os.path.join(pkg_abs, self.filename)

    def load_content(self):
        super(SourceFile, self).load_content()
        self._parse()

    def _parse(self):
        """ Extract SourceFile data by parsing the code, result is saved in object's attributes.
        """
        raise NotImplementedError

    @staticmethod
    def build_source_file(filename):
        """ Create a parsed SourceFile, given the full filename.
        """
        package = None  # TODO: auto-detect package
        lng = File(filename).detect_language()
        if lng == Language.JAVA:
            from inspector.models import java
            return java.JavaSourceFile(filename, package=package, language=lng)
        elif lng == Language.PYTHON:
            from inspector.models import python
            return python.PythonSourceFile(filename, package=package, language=lng)
        raise ValueError('Unknown language')


class Class(object):
    pass


class Function(object):
    pass


class Method(Function):
    pass
