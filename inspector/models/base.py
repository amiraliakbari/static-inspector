# -*- coding: utf-8 -*-
import os
import re
import logging

from inspector.models.consts import Language
from inspector.parser.file_tokenizer import FileTokenizer
from inspector.utils.arrays import find
from inspector.utils.files import get_extension
from inspector.utils.lang import enum
from inspector.utils.strings import summarize, has_word


logging.basicConfig(filename='logs.log', filemode='w', level=logging.DEBUG)
logger = logging.getLogger('models_base')


class LocatableInterface(object):
    @property
    def abs_path(self):
        raise NotImplementedError


class Project(LocatableInterface):
    def __init__(self, path, name=None):
        """ Create a project from a filesystem's path
            loading of files is done later, on demand (by calling methods)

        """
        self._path = ''
        self.name = ''
        self.source_roots = []
        self.ignored_dirs = []  # TODO: load this from .gitignore file

        # files
        self._files = {}  # loaded files cache
        self.file_extensions = set()

        # initial configuration
        self.abs_path = path
        self.name = name if name is not None else re.split(r'[/\\]', self.abs_path)[-2]
        self.auto_detect_roots()

    #########################
    #  File System Related  #
    #########################
    @property
    def abs_path(self):
        return self._path

    @abs_path.setter
    def abs_path(self, path):
        if not path[-1] in ['/', '\\']:
            path = os.path.join(path, '')  # append /
        if not os.path.exists(path):
            raise ValueError('Invalid directory: "{0}".'.format(path))
        self._path = path

    def build_path(self, path):
        return os.path.join(self.abs_path, path)

    def build_relative_path(self, abs_path):
        """ Return relative form of the path, returning path only contains / (and not \) on any platform

            :rtype: str
        """
        if not os.path.isabs(abs_path):
            path = abs_path
        elif not abs_path.startswith(self.abs_path):
            raise ValueError('The path is not in project directory.')
        else:
            path = abs_path[len(self.abs_path):]
        return path.replace('\\', '/')

    ###################
    #  File Handling  #
    ###################
    @property
    def files(self):
        """ Cache layer over self._files, returning all filenames in the project
        """
        if not self._files:
            self.rescan_files()
        return self._files

    class FileDfsHandler(object):
        def __init__(self):
            self.project = None

        def setup(self):
            pass

        def tear_down(self):
            pass

        def handle_file(self, path):
            pass

        def enter_dir(self, path):
            pass

        def exit_dir(self, path):
            pass

    def rescan_files(self, handler=None):
        """
            :type handler: FileDfsHandler or None
        """
        dir_stack = []
        if handler:
            handler.project = self
            handler.setup()

        project_root = self.abs_path
        for r, d, files in os.walk(project_root):
            dir_path = self.build_relative_path(r)
            ignored = False
            for ignored_dir in self.ignored_dirs:
                if dir_path.startswith(ignored_dir):
                    ignored = True
                    break
            if ignored:
                continue
            if handler:
                while dir_stack and not dir_path.startswith(dir_stack[-1]):
                    handler.exit_dir(dir_stack.pop())
                dir_stack.append(dir_path)
                handler.enter_dir(dir_path)
            for f in files:
                path = self.build_relative_path(os.path.join(r, f))
                self.file_extensions.add(get_extension(path))
                self._files[path] = None
                if handler:
                    handler.handle_file(path)

        if handler:
            while dir_stack:
                handler.exit_dir(dir_stack.pop())
            handler.tear_down()

    def filter_files(self, cond=None, extension=None):
        """ Return filenames of files in this project that satisfy the condition function

            :param str or None extension: the file extensions to filter, e.g. 'java' or 'java,xml'
        """
        if cond is not None:
            return (f for f in self.files.iterkeys() if cond(f))

        if extension is not None:
            return self.filter_files(cond=lambda f: get_extension(f) in [e.strip() for e in extension.split(',')])

        #TODO: other cases?

    def get_file(self, path, is_qualified=None):
        """
            :param str path: source file path, can be relative, abstract, or in java dotted format
            :rtype: File or SourceFile or JavaSourceFile
        """
        if is_qualified is None:
            is_qualified = not ('/' in path or '\\' in path)

        if is_qualified:
           # java dotted format
            found = False
            rel_path = os.path.join(*path.split('.'))
            for sr in self.source_roots:
                if os.path.join(sr, rel_path) + '.java' in self.files:
                    rel_path = os.path.join(sr, rel_path) + '.java'
                    found = True
                    break
            if not found:
                raise KeyError('File not found in project source roots: {0}'.format(path))
        else:
            rel_path = self.build_relative_path(path)

        # file cache
        f = self.files[rel_path]
        if f is None:
            f = self.files[rel_path] = self.load_file(rel_path)
            f.project_path = rel_path
        return f

    def get_files(self, filenames):
        return (self.get_file(filename) for filename in filenames)

    def all_files(self):
        """ Return an iterator of all files in the project
            note: returned files are parsed, so this may take a while for large projects
            note: use filter_files or get_files for returning a subset of all project files
        """
        return self.get_files(self.files)

    def dfs_files(self, handler):
        """
            :type handler: FileDfsHandler
        """

        self.rescan_files(handler)
        handler.tear_down()

    ####################
    #  Find Utilities  #
    ####################
    def find_class(self, qualified_name):
        p = qualified_name.split('.')
        class_name = p[-1]
        try:
            class_file = self.get_file('.'.join(p[:-1]))
        except KeyError:
            # the user can omit the class_name if class_name == filename (e.g. a.b.ClassName.ClassName)
            # TODO: consider other languages like python! they maybe need camel case conversion
            class_file = self.get_file('.'.join(p))
        return class_file.get_class(class_name)

    def find(self, identifier):
        """ Find the code object (file/class/method/etc.) specified by the
             identifier in this project.

            :param str identifier: object to find, e.g. 'class:a.b.X', 'file:a.b.f'
        """
        try:
            id_type, id_val = identifier.split(':', 1)
        except ValueError:
            raise ValueError('Invalid identifer: {0}'.format(identifier))
        if id_type == 'file':
            return self.get_file(id_val)
        if id_type == 'class':
            return self.find_class(id_val)
        if id_type == 'method':
            ind = id_val.rfind('.')
            method_class = self.find_class(id_val[:ind])
            return method_class.get_method(id_val[ind+1:])
        raise ValueError('Invalid identifier: {0}'.format(id_type))

    ############################
    #  File Loading & Parsing  #
    ############################
    def load_file(self, rel_path):
        return File(self.build_path(rel_path))

    def auto_detect_roots(self):
        if os.path.isdir(self.build_path('src')):
            self.source_roots.append('src')
        else:
            self.source_roots.append('')


class Package(LocatableInterface):
    def __init__(self, project):
        self.project = project
        self.name = None

    @property
    def abs_path(self):
        return self.project.abs_path if self.project else None


class File(LocatableInterface):
    def __init__(self, filename, preload=False):
        self.file_content = None
        self._file_size = None
        self._lines = None
        self.filename = filename
        self.project_path = None  # project relative path

        # setup
        if preload:
            self.load_content()

    def get_abs_path(self):
        return self.filename

    @property
    def loaded(self):
        return self.file_content is not None

    @property
    def file_size(self):
        if self._file_size is None:
            self._file_size = os.path.getsize(self.get_abs_path())
        return self._file_size

    # noinspection PyShadowingBuiltins
    def load_content(self, reload=True):
        if not reload and self.loaded:
            return
        # TODO: this is 2X memory!
        with open(self.get_abs_path(), 'r') as f:
            self.file_content = f.read()
        with open(self.get_abs_path(), 'r') as f:
            self._lines = f.readlines()

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
        ln = self.lines[line_number - 1]
        if ln.endswith('\r'):
            ln = ln[:-1]
        return ln

    @property
    def lines(self):
        if self._lines is None:
            self.load_content(reload=False)
        return self._lines

    @property
    def lines_count(self):
        # TODO: this functions returns 1 extra line for some files
        return len(self.lines)

    @property
    def chars_count(self):
        self.load_content(reload=False)
        return len(self.file_content)


class Directory(LocatableInterface):
    def __init__(self, path):
        self.path = path

    def get_abs_path(self):
        return self.path


class Coverable(object):
    def __init__(self):
        self._coverage = None

    @property
    def coverage(self):
        if self._coverage is None:
            self.autoload_coverage_report()
        if self._coverage is None:
            raise ValueError('No coverage data attached.')
        return self._coverage

    @coverage.setter
    def coverage(self, value):
        self._coverage = value

    @property
    def lines_count(self):
        """
            :rtype: int
        """
        raise NotImplementedError

    def covered_ratio(self):
        return 1. * self.coverage.covered_lines_count / self.lines_count

    def attach_coverage_report(self, report):
        """
            :param report: coverage report to be attached
            :type report: inspector.coverage.raw_coverage_report.FileCoverageReport or None
        """
        self.coverage = report

    def autoload_coverage_report(self):
        pass


class SourceFile(File, FileTokenizer, Coverable):
    def __init__(self, filename, package=None):
        """ Create a parsed SourceFile model from the file
             note: parsing is done in the constructor
             note: if file's language can not be detected, parsing is not done

            :param str filename: file to e read and parsed
            :param package: the containing package of this file
        """

        super(SourceFile, self).__init__(filename)
        Coverable.__init__(self)
        FileTokenizer.__init__(self)
        self.package = package

        # parse results
        self.parsed = False
        self.imports = []
        self.globals = []
        self.classes = []
        self.functions = []

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

    def get_abs_path(self):
        pkg_abs = self.package.abs_path if self.package else ''
        return os.path.join(pkg_abs, self.filename)

    # noinspection PyShadowingBuiltins
    def load_content(self, reload=True):
        """ Read the content of this SourceFile, and fully parse it if the
             programming language is detected

            :param bool reload: wheter to reload the content if it is already loaded before
        """
        if not reload and self.loaded:
            return
        super(SourceFile, self).load_content(reload=reload)
        self.set_content(self.file_content)
        if self.language_detected:
            # TODO: parse should be done only if content is not loaded yet or reload is True
            self._parse()

    ##########################
    #  Model Access Helpers  #
    ##########################
    def get_class(self, name):
        """ Return the class matching the given name from this SourceFile
             note: None is returned if there is no such class

            :param str name: name of the class
            :rtype: Class or None
        """
        return find(self.classes, lambda m: m.name == name)

    #######################
    #  Language Specific  #
    #######################
    @property
    def language(self):
        return self.detect_language()

    @property
    def language_detected(self):
        lng = self.language
        return lng and lng != Language.UNKNOWN

    #######################
    #  Parsing Utilities  #
    #######################
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
        p = self._context.pop()
        # print "poped:", p.model
        if p.isinstance(CodeBlock):
            self._last_popped = p
        return p

    def next_token(self):
        """ Get the next language-specific token of the file (relative to read head)
             This abstract method is where subclasses define language-specific parsing
             rules and grammar.
             Tokens are constructs like Class, Function, Method, IfBlock, Statement, etc.

            :return: next token, parsed
            :rtype: Token
        """
        raise NotImplementedError()

    def _save_model(self, token_model):
        if isinstance(token_model, Import):
            self.imports.append(token_model)
            token_model.source_file = self
        elif isinstance(token_model, Class):
            self.classes.append(token_model)
        elif isinstance(token_model, Function):
            self.functions.append(token_model)
        else:
            self.globals.append(token_model)

    def _parse(self):
        """ Extract SourceFile data by parsing the code, result is saved in object's attributes.
             General parsing algorithm is in this method, but the language specific (the main)
             part is done using the abstract self.next_token() method
        """
        logger.debug('Parsing file: %s', self.filename)
        self._context = []
        self._last_popped = None
        self.statement_pre_read = None
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
        """ Create a parsed SourceFile, given the full disk filename

            :param str filename: the disk filename of the target file
            :rtype: JavaSourceFile or PythonSourceFile
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


class Import(object):
    def __init__(self, import_str, source_file=None):
        """
            :param str or unicode import_str: the string used to import the identifier
            :param SourceFile source_file: the source file this import is located in
        """
        self.import_str = import_str
        self.source_file = source_file

    def __unicode__(self):
        return 'Import: {0}'.format(self.import_str)

    def __str__(self):
        return unicode(self)

    @property
    def imported_identifier(self):
        """ what identifier is made available with this import
        """
        return self.import_str

    def find_usages(self):
        if not self.source_file:
            return None

        identifier = self.imported_identifier
        usage_lines = []
        for i, l in enumerate(self.source_file._lines):
            if has_word(l, identifier):
                usage_lines.append(i + 1)
        return usage_lines


class CodeBlock(Coverable):
    def __init__(self):
        Coverable.__init__(self)
        self.parent_block = None
        self.statements = []  # array of Statement
        self.starting_line = None
        self.ending_line = None

    def add_statement(self, statement):
        """
            :param Statement statement: statement to be added
        """
        self.statements.append(statement)

    def __unicode__(self):
        return u'CodeBlock:\n\t' + u'\n\t'.join([unicode(s) for s in self.statements])

    def __str__(self):
        return str(unicode(self))

    @property
    def lines_count(self):
        if self.ending_line is None or self.starting_line is None:
            return None
        return self.ending_line - self.starting_line + 1

    def autoload_coverage_report(self):
        source = self.get_source_file()
        if source and source.coverage:
            self.attach_coverage_report(source.coverage[self.starting_line:self.ending_line + 1])

    def get_source_file(self):
        """ Return source file containing this block

            :rtype: SourceFile
        """
        if hasattr(self, 'source_file'):
            return self.source_file
        if isinstance(self.parent_block, CodeBlock):
            return self.parent_block.get_source_file()
        raise NotImplementedError


class Class(CodeBlock):
    def __init__(self, name, source_file=None, package=None, parent_class=None, extends=None):
        super(Class, self).__init__()
        self.name = name
        self.parent_block = self.parent_class = parent_class
        self.source_file = source_file
        self._package = package
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

    def __repr__(self):
        return 'class:{0}'.format(self.qualified_name)

    @property
    def qualified_name(self):
        # TODO: use self.package instead of self.source_file

        if not self.source_file.project_path:
            return self.name

        p = os.path.splitext(self.source_file.project_path)[0].split('/')
        # TODO: check project better!
        # project = self.source_file.project
        # if project and p[0] in project.source_roots:
        #     p = p[1:]
        if p[0] == 'src':
            # TODO: fix this hardcode!
            p = p[1:]
        p.append(self.name)
        return '.'.join(p)

    @property
    def package(self):
        if self._package:
            return self._package
        if self.source_file:
            return self.source_file.package
        return None

    def add_statement(self, statement):
        if isinstance(statement, Field):
            self.fields.append(statement)
        else:
            # TODO: support statics/etc.
            raise ValueError('Invalid statement inside a class: "{0}".'.format(unicode(statement)))

    def get_method(self, name):
        """ Return the method matching the given name from this Class
             note: None is returned if there is no such method

            :param str name: name of the method
            :rtype: Method or None
        """
        return find(self.methods, lambda m: m.name == name)

    def is_subclass_of(self, parent_class):
        # TODO: check better! its currently just by name (without even package)
        if isinstance(parent_class, Class):
            parent_class = parent_class.name
        return parent_class in self.extends


class Field(object):
    def __init__(self, name, field_type, parent_class, visibility=None, annotations=None, initializer=None,
                 is_static=False):
        self.name = name
        self.type = field_type
        self.parent_class = parent_class
        self.visibility = visibility
        self.is_static = is_static
        self.annotations = annotations
        self.initializer = initializer

    def __unicode__(self):
        return u'Field: {1} {0}'.format(self.name, self.type)

    def __str__(self):
        return str(unicode(self))


class Function(CodeBlock):
    def __init__(self, name, source_file=None, return_type=None, arguments=None):
        super(Function, self).__init__()
        self.name = name
        self.source_file = source_file
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
        self.nested_classes = []
        self.nested_functions = []

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

    def __repr__(self):
        return 'method:{0}'.format(self.qualified_name)

    def set_parent_class(self, parent_class):
        """
            :type parent_class: Class
        """
        if self.parent_class is not None:
            self.parent_class.methods.remove(self)
        self.parent_class = parent_class
        self.parent_block = self.parent_class
        self.source_file = parent_class.source_file
        parent_class.methods.append(self)

    def is_constructor(self):
        return self.return_type is None

    @property
    def qualified_name(self):
        name = self.name
        if self.parent_class:
            name = self.parent_class.qualified_name + '.' + name
        return name

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
        return u'Statement: {0}'.format(summarize(self.code, max_len=0))

    def __str__(self):
        return unicode(self)


class IfBlock(CodeBlock):
    def __init__(self, condition):
        super(IfBlock, self).__init__()
        self.condition = condition
        self.mode = None
        self.elifs = []
        self.else_block = CodeBlock()

    def __unicode__(self):
        return u'IfBlock:\n\t' + u'\n\t'.join([unicode(s) for s in self.statements])

    def add_elif(self, condition):
        self.elifs.append((condition, CodeBlock()))
        self.mode = u'elif'

    def activate_else(self):
        self.mode = u'else'

    def add_statement(self, statement):
        if self.mode == u'elif':
            self.elifs[-1][1].add_statement(statement)
        elif self.mode == u'else':
            self.else_block.add_statement(statement)
        else:
            super(IfBlock, self).add_statement(statement)


class SwitchBlock(CodeBlock):
    def __init__(self, condition):
        super(SwitchBlock, self).__init__()
        self.condition = condition
        self.cases = {}
        self.case_orders = []
        self.mode = ''
        self.default = CodeBlock()
        self.active_cases = []

    def add_case(self, case_expr):
        self.active_cases.append(case_expr)
        self.case_orders.append(case_expr)

    def add_break(self):
        self.active_cases = []

    def add_return(self):
        self.mode = 'return'

    def add_default(self):
        self.active_cases = 'default'

    def add_statement(self, statement):
        if not self.active_cases and not self.mode:
            raise ValueError('Statement not in a case: {0}.'.format(unicode(statement)))
        if self.active_cases == 'default':
            self.default.add_statement(statement)
        else:
            for case in self.active_cases:
                if not self.cases.get(case):
                    self.cases[case] = CodeBlock()
                self.cases[case].add_statement(statement)
            if self.mode == 'return':
                self.mode = ''
                self.active_cases = []


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
