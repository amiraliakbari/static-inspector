# -*- coding: utf-8 -*-
import os
import re

from inspector.models.consts import Language
from inspector.parser.file_tokenizer import FileTokenizer
from inspector.utils.arrays import find
from inspector.utils.lang import enum
from inspector.utils.strings import summarize


class LocatableInterface(object):
    def get_abs_path(self):
        raise NotImplementedError


class Project(LocatableInterface):
    def __init__(self, path, name=None):
        if not path[-1] in ['/', '\\']:
            path = os.path.join(path, '')  # append /
        self.abs_path = path
        self.name = name if name is not None else re.split(r'[/\\]', self.abs_path)[-1]

        # files
        self._files = {}  # loaded files cache
        self._file_groups = {}

    #########################
    #  File System Related  #
    #########################
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

    ###################
    #  File Handling  #
    ###################
    def rescan_files(self):
        for r, d, files in os.walk(self.get_abs_path()):
            for f in files:
                path = self.build_relative_path(os.path.join(r, f))
                ext = os.path.splitext(path)[1][1:]
                self._files[path] = None
                if not ext in self._file_groups:
                    self._file_groups[ext] = []
                self._file_groups[ext].append(path)

    def filter_files(self, cond):
        """ Return filenames of files in this project that satisfy the condition function
        """
        return (f for f in self._files.iterkeys() if cond(f))

    def get_file(self, path):
        """
            :param str path: source file path, can be relative, abstract, or in java dotted format
        """
        #if re.match(r'[a-zA-Z0-9._]+', path):
        #    # java dotted format
        #    rel_path = os.path.join(*path.split('.'))
        #else:
        #    rel_path = self.build_relative_path(path)
        rel_path = self.build_relative_path(path)

        # file cache
        f = self._files[rel_path]
        if f is None:
            f = self._files[rel_path] = self.load_file(rel_path)
            f.project_path = rel_path
        return f

    def get_files(self, filenames):
        return (self.get_file(filename) for filename in filenames)

    ############################
    #  File Loading & Parsing  #
    ############################
    def load_file(self, rel_path):
        return File(self.build_path(rel_path))


class Package(LocatableInterface):
    def __init__(self, project):
        self.project = project
        self.name = None

    def get_abs_path(self):
        return self.project.get_abs_path() if self.project else None


class File(LocatableInterface):
    def __init__(self, filename, preload=False):
        self.file_content = None
        self._lines = None
        self.filename = filename
        self.project_path = None

        # setup
        if preload:
            self.load_content()

    def get_abs_path(self):
        return self.filename

    @property
    def loaded(self):
        return self.file_content is not None

    # noinspection PyShadowingBuiltins
    def load_content(self, reload=True):
        if not reload and self.loaded:
            return
        with open(self.get_abs_path(), 'r') as f:
            self.file_content = f.read()

    def detect_language(self):
        ext = os.path.splitext(self.filename)[1]
        if ext == '.java':
            return Language.JAVA
        elif ext == '.py':
            return Language.PYTHON
        return Language.UNKNOWN

    #####################
    #  Line Processing  #
    #####################
    def get_line(self, line_number):
        if self._lines is None:
            self.load_content(reload=False)
            self._lines = self.file_content.split('\n')
        ln = self._lines[line_number - 1]
        if ln.endswith('\r'):
            ln = ln[:-1]
        return ln

    @property
    def lines_count(self):
        if self._lines:
            return len(self._lines)
        self.load_content(reload=False)
        return self.file_content.count('\n') + 1


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
        self._language = language if language is not None else self.detect_language()

        # parse results
        self.parsed = False
        self.imports = []
        self.globals = []
        self.classes = []
        self.functions = []

        # coverage
        self.coverage = None

        # loading and parsing
        self.load_content()

    def __unicode__(self):
        msg = u'{lang} SourceFile: {content}'
        lng = Language.display_name[self.language]
        contents = []
        if self.imports:
            contents.append(u'{0} imports'.format(len(self.imports)))
        if self.globals:
            contents.append(u'{0} globals'.format(len(self.globals)))
        if self.functions:
            contents.append(u'{0} functions'.format(len(self.functions)))
        if self.classes:
            contents.append(u'{0} classes'.format(len(self.classes)))
        contents = u', '.join(contents) if contents else u'empty'
        return msg.format(lang=lng, content=contents)

    def __str__(self):
        return unicode(self)

    @property
    def project(self):
        return self.package.project if self.package else None

    @property
    def language(self):
        return self._language

    @language.setter
    def language(self, value):
        if self._language == value:
            return
        self._language = value
        if self.language_detected:
            # TODO: this does not change this class parser, so _parse() is useless
            self._parse()

    def get_abs_path(self):
        pkg_abs = self.package.get_abs_path() if self.package else ''
        return os.path.join(pkg_abs, self.filename)

    # noinspection PyShadowingBuiltins
    def load_content(self, reload=True):
        if not reload and self.loaded:
            return
        super(SourceFile, self).load_content(reload=reload)
        self.set_content(self.file_content)
        if self.language_detected:
            self._parse()

    ##########################
    #  Model Access Helpers  #
    ##########################
    def get_class(self, name):
        """
            :rtype: Class
        """
        return find(self.classes, lambda m: m.name == name)

    #######################
    #  Parsing Utilities  #
    #######################
    @property
    def language_detected(self):
        return self.language and self.language != Language.UNKNOWN

    def find_context_top(self, cond=None, default=None):
        """
            :rtype : inspector.parser.base.Token
        """
        if cond is None:
            return self._context[-1] if self._context else default
        for c in reversed(self._context):
            if cond(c):
                return c
        return default

    def context_pop(self):
        """
            :rtype: inspector.parser.base.Token
        """
        self._last_popped = self._context.pop()
        return self._last_popped

    def next_token(self):
        raise NotImplementedError()

    def _save_model(self, token_model):
        if isinstance(token_model, Import):
            self.imports.append(token_model)
        elif isinstance(token_model, Class):
            self.classes.append(token_model)
        elif isinstance(token_model, Function):
            self.functions.append(token_model)
        else:
            self.globals.append(token_model)

    def _parse(self):
        """ Extract SourceFile data by parsing the code, result is saved in object's attributes.
        """
        self._context = []
        self._last_popped = None
        while self.can_read():
            token = self.next_token()
            if token.model is None:
                continue
            if self.find_context_top(cond=lambda x: x != token and x.isinstance(CodeBlock)) is None:
                # this token model has no parents, we must save it separately
                self._save_model(token.model)
        self.parsed = True

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
    def covered_ratio(self):
        return 1. * self.coverage.covered_lines_count / self.lines_count

    def attach_coverage_report(self, report):
        """
            :param report: coverage report to be attached
            :type report: inspector.coverage.raw_coverage_report.FileCoverageReport or None
        """
        self.coverage = report


class Import(object):
    def __init__(self, import_str):
        self.import_str = import_str

    def __unicode__(self):
        return 'Import: {0}'.format(self.import_str)

    def __str__(self):
        return unicode(self)


class CodeBlock(object):
    def __init__(self):
        self.statements = []  # array of Statement
        self.starting_line = None
        self.ending_line = None

    def add_statement(self, statement):
        """
            :param Statement statement: statement to be added
        """
        self.statements.append(statement)

    @property
    def line_count(self):
        if self.ending_line is None or self.starting_line is None:
            return None
        return self.ending_line - self.starting_line + 1


class Class(CodeBlock):
    def __init__(self, name, source_file=None, package=None, parent_class=None, extends=None):
        super(Class, self).__init__()
        self.name = name
        self.parent_class = parent_class
        self.source_file = source_file
        self.package = package
        self.methods = []
        self.fields = []
        if not extends:
            self.extends = []
        else:
            if not isinstance(extends, list):
                extends = [extends]
            self.extends = extends  # TODO: set real Class reference

    def __unicode__(self):
        q_name = u'{0}.{1}'.format(self.parent_class.name, self.name) if self.parent_class else self.name
        return u'Class {0}'.format(q_name)

    def __str__(self):
        return unicode(self)

    def add_statement(self, statement):
        # TODO: model and check fields
        self.fields.append(statement)

    def get_method(self, name):
        """
            :rtype: Method
        """
        return find(self.methods, lambda m: m.name == name)


class Function(CodeBlock):
    def __init__(self, name, return_type=None, arguments=None):
        super(Function, self).__init__()
        self.name = name
        self.arguments = arguments or []
        self.return_type = return_type or None
        self.binding = Method.BINDING.UNBOUND

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

    def __init__(self, parent_class, name, return_type=None, arguments=None, access=None, binding=None, abstract=False,
                 throws=None):
        super(Method, self).__init__(name, return_type=return_type, arguments=arguments)
        self.parent_class = None
        self.set_parent_class(parent_class)
        self.access = access or self.ACCESS.UNKNOWN
        self.binding = binding or self.BINDING.UNKNOWN
        self.abstract = abstract
        self.throws = throws or []

    def __unicode__(self):
        args_rep = u', '.join([u'{0} {1}'.format(x, y) for x, y in self.arguments])
        acc_rep = self.ACCESS.display_name[self.access]
        abs_rep = u' Abstract' if self.abstract else ''
        bin_rep = (u' ' + self.BINDING.display_name[self.binding]) if self.binding != self.BINDING.INSTANCE else u''
        thr_rep = (u', throws ' + u', '.join(self.throws)) if self.throws else u''
        ret_name = u': ' + self.return_type if not self.is_constructor() else u''
        method_name = u'Method' if not self.is_constructor() else u'Constructor'
        fmt = u'{acc}{abs}{bin} {method_name} {name}({args}){ret} {thr}'
        return fmt.format(acc=acc_rep, abs=abs_rep, bin=bin_rep, name=self.name, args=args_rep, ret=ret_name,
                          thr=thr_rep, method_name=method_name)

    def set_parent_class(self, parent_class):
        """
            :type parent_class: Class
        """
        if self.parent_class is not None:
            self.parent_class.methods.remove(self)
        self.parent_class = parent_class
        parent_class.methods.append(self)

    def is_constructor(self):
        return self.return_type is None

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


class Comment(object):
    def __init__(self, content):
        """
            :param str or unicode content: comment content, including // or /* */
        """
        self.content = content
        self.doc_comment = self.content.startswith(u'/**')
        self.starting_line = None
        self.ending_line = None

        if self.content.startswith('//'):
            self.multiline = False
            pat = r'^//(/|\s)*'
        elif self.content.startswith('/*'):
            self.multiline = True
            pat = r'(^/\*(\*|\s)*|(\*|\s)*\*/$)'
        else:
            raise ValueError(u'Invalid comment start.')
        self.content = re.sub(pat, '', self.content)

    def __unicode__(self):
        u = u'Comment: {0}'.format(summarize(self.content, max_len=10))
        if self.doc_comment:
            u += u' (docstring)'
        return u

    def __str__(self):
        return unicode(self)


class Statement(object):
    def __init__(self, code):
        self.code = code

    def __unicode__(self):
        return u'Statement: {0}'.format(summarize(self.code, max_len=30))

    def __str__(self):
        return unicode(self)


class IfBlock(CodeBlock):
    def __init__(self, condition):
        super(IfBlock, self).__init__()
        self.condition = condition
        self.mode = None
        self.elifs = []
        self.else_block = CodeBlock()

    def add_elif(self, condition):
        self.elifs.append((condition, CodeBlock()))
        self.mode = u'elif'

    def activate_else(self):
        self.mode = u'else'

    def add_statement(self, statement):
        if self.mode == u'elif':
            self.elifs[-1][1].append(statement)
        elif self.mode == u'else':
            self.else_block.add_statement(statement)
        else:
            super(IfBlock, self).add_statement(statement)


class ExceptionBlock(CodeBlock):
    def __init__(self):
        super(ExceptionBlock, self).__init__()
        self.catches = {}
        self.active_catch = None
        self.finally_block = CodeBlock()
        self.else_block = CodeBlock()  # python specific

    def add_catch(self, catch):
        if catch in self.catches:
            raise ValueError(u'Catch already exists.')
        self.catches[catch] = CodeBlock()
        self.active_catch = catch

    def add_statement(self, statement):
        if self.active_catch is not None:
            self.catches[self.active_catch].add_statement(statement)
        else:
            super(ExceptionBlock, self).add_statement(statement)

    def __unicode__(self):
        catches = u','.join(self.catches.keys())
        if not catches:
            catches = u'nothing'
        return u'ExceptionBlock: {0} statements, catching {1}.'.format(len(self.statements), catches)

    def __str__(self):
        return unicode(self)


class ForBlock(CodeBlock):
    pass


class WhileBlock(CodeBlock):
    pass


class DoWhileBlock(WhileBlock):
    pass


class WithBlock(CodeBlock):
    pass
