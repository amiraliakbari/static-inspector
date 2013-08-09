# -*- coding: utf-8 -*-
import os
import re

from inspector.models.consts import Language
from inspector.parser.file_tokenizer import FileTokenizer
from inspector.utils.lang import enum


class LocatableInterface(object):
    def get_abs_path(self):
        raise NotImplementedError


class Project(LocatableInterface):
    def __init__(self, path, name=None):
        if not path[-1] in ['/', '\\']:
            path = os.path.join(path, '')  # append /
        self.abs_path = path
        self.name = name if name is not None else re.split(r'[/\\]', self.abs_path)[-1]

    def get_abs_path(self):
        return self.abs_path

    def build_path(self, path):
        return os.path.join(self.abs_path, path)

    def build_relative_path(self, abs_path):
        if not os.path.isabs(abs_path):
            return abs_path
        if not abs_path.startswith(self.abs_path):
            raise ValueError('The path is not in project directory.')
        return abs_path[len(self.abs_path):]


class Package(LocatableInterface):
    def __init__(self, project):
        self.project = project
        self.name = None

    def get_abs_path(self):
        return self.project.get_abs_path() if self.project else None


class File(LocatableInterface):
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


class Directory(LocatableInterface):
    def __init__(self, path):
        self.path = path

    def get_abs_path(self):
        return self.path


class SourceFile(File, FileTokenizer):
    def __init__(self, filename, package=None, language=None):
        super(SourceFile, self).__init__(filename)
        FileTokenizer.__init__(self)
        self.package = package
        self.language = language if language is not None else self.detect_language()

        # internals
        self._tokens = []
        self._tokens_data = []
        self._context = []

        # parse results
        self.imports = []
        self.globals = []
        self.classes = []
        self.functions = []

        # coverage
        self.coverage = None

        # loading and parsing
        self.load_content()

    def __unicode__(self):
        msg = u'%s SourceFile: %d imports, %d classes, %d functions'
        lng = Language.display_name[self.language]
        return msg % (lng, len(self.imports), len(self.classes), len(self.functions))

    def __str__(self):
        return unicode(self)

    @property
    def project(self):
        return self.package.project if self.package else None

    def get_abs_path(self):
        pkg_abs = self.package.get_abs_path() if self.package else ''
        return os.path.join(pkg_abs, self.filename)

    def load_content(self):
        super(SourceFile, self).load_content()
        self.set_content(self.file_content)
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
            return java.JavaSourceFile(filename, package=package)
        elif lng == Language.PYTHON:
            from inspector.models import python
            return python.PythonSourceFile(filename, package=package)
        raise ValueError('Unknown language')

    ##############
    #  Coverage  #
    ##############
    def attach_coverage_report(self, report):
        """
            :param inspector.coverage.raw_coverage_report.FileCoverageReport: coverage report to be attached
        """
        self.coverage = report


class Import(object):
    def __init__(self, import_str):
        self.import_str = import_str

    def __unicode__(self):
        return 'Import {0}'.format(self.import_str)

    def __str__(self):
        return unicode(self)


class Class(object):
    def __init__(self, name, source_file=None, package=None, parent_class=None):
        self.name = name
        self.parent_class = parent_class
        self.source_file = source_file
        self.package = package
        self.methods = []

    def __unicode__(self):
        q_name = u'{0}.{1}'.format(self.parent_class.name, self.name) if self.parent_class else self.name
        return u'Class {0}'.format(q_name)

    def __str__(self):
        return unicode(self)


class Function(object):
    def __init__(self, name, return_type=None, arguments=None):
        self.name = name
        self.arguments = arguments or []
        self.return_type = return_type or ''
        self.binding = Method.BINDING.UNBOUND

        # code location
        self.starting_line = None
        self.ending_line = None

    def __unicode__(self):
        args_rep = u', '.join([u'{0} {1}'.format(x, y) for x, y in self.arguments])
        return u'Function {0}({1}): {2}'.format(self.name, args_rep, self.return_type)

    def __str__(self):
        return unicode(self)


class Method(Function):
    ACCESS = enum('UNKNOWN', 'PRIVATE', 'PROTECTED', 'PACKAGE', 'PUBLIC', 'PUBLISHED',
                  verbose_names=['unknown', 'private', 'protected', 'package', 'public', 'published'])
    BINDING = enum('UNKNOWN', 'UNBOUND', 'STATIC', 'CLASS', 'INSTANCE',
                   verbose_names=['unknown', 'unbound', 'static', 'class', 'instance'])

    def __init__(self, parent_class, name, return_type=None, arguments=None, access=None, binding=None, abstract=False):
        super(Method, self).__init__(name, return_type=return_type, arguments=arguments)
        self.parent_class = None
        self.set_parent_class(parent_class)
        self.access = access or self.ACCESS.UNKNOWN
        self.binding = binding or self.BINDING.UNKNOWN
        self.abstract = abstract

    def __unicode__(self):
        args_rep = u', '.join([u'{0} {1}'.format(x, y) for x, y in self.arguments])
        acc_rep = self.ACCESS.display_name[self.access]
        abs_rep = u' Abstract' if self.abstract else ''
        bin_rep = (u' ' + self.BINDING.display_name[self.binding]) if self.binding != self.BINDING.INSTANCE else u''
        fmt = u'{acc}{abs}{bin} Method {name}({args}): {ret}'
        return fmt.format(acc=acc_rep, abs=abs_rep, bin=bin_rep, name=self.name, args=args_rep, ret=self.return_type)

    def set_parent_class(self, parent_class):
        """
            :type parent_class: Class
        """
        if self.parent_class is not None:
            self.parent_class.methods.remove(self)
        self.parent_class = parent_class
        parent_class.methods.append(self)

    @classmethod
    def parse_access(cls, access_str, default=None):
        if access_str is not None:
            access_str = access_str.strip()
        if not access_str:
            return default or cls.ACCESS.PACKAGE
        for k, v in cls.ACCESS.display_name.items():
            if v == access_str:
                return k
        return None

    @classmethod
    def parse_binding(cls, binding_str, default=None):
        if binding_str is not None:
            binding_str = binding_str.strip()
        if not binding_str:
            return default or cls.BINDING.INSTANCE
        for k, v in cls.BINDING.display_name.items():
            if v == binding_str:
                return k
        return None
