# -*- coding: utf-8 -*-
import os
import re

from inspector.parser.base import Token, LanguageSpecificParser
from inspector.models.base import Project, SourceFile, Class, Method, Import, Comment, Statement, ExceptionBlock, CodeBlock, ForBlock, WhileBlock, IfBlock, Function
from inspector.models.consts import Language
from inspector.models.exceptions import ParseError
from inspector.utils.lang import enum


class JavaProject(Project):
    def __init__(self, path, name=None):
        super(JavaProject, self).__init__(path, name=name)
        self.source_roots = []
        self._files = {}  # parsed SourceFile cache

        # initial configuration
        self.auto_detect_roots()
        self.rescan_files()

    def auto_detect_roots(self):
        if os.path.isdir(self.build_path('src')):
            self.source_roots.append('src')
        else:
            self.source_roots.append('')

    def rescan_files(self):
        for root in self.source_roots:
            for r, d, files in os.walk(self.build_path(root)):
                for f in files:
                    if f.endswith('.java'):
                        path = self.build_relative_path(os.path.join(r, f))
                        self._files[path] = None

    def get_source_file(self, path):
        """
            :param str path: source file path, can be relative, abstract, or in java dotted format
        """
        if re.match(r'[a-zA-Z0-9._]+', path):
            # java dotted format
            rel_path = os.path.join(*path.split('.'))
        else:
            rel_path = self.build_relative_path(path)

        # file cache
        f = self._files[rel_path]
        if f is None:
            f = self._files[rel_path] = JavaSourceFile(self.build_path(rel_path), package=None)  # TODO: package
        return f


class JavaSourceFile(SourceFile):
    def __init__(self, filename, package=None):
        super(JavaSourceFile, self).__init__(filename, package=package)
        self.language = Language.JAVA

    def next_token(self):
        """
            :return: next token, parsed
            :rtype: Token
        """
        t = Token()
        self.skip_spaces()

        prefix = self.read_ahead(2)  # to detect comments
        if prefix == '//':
            t.type = 'comment'
            t.content = self.read(cond=lambda ch: ch != '\n')
            t.model = Comment(t.content)
        elif prefix == '/*':
            t.type = 'comment'
            t.content = self.read(find='*/', beyond=2)
            t.model = Comment(t.content)

        else:
            t.content = self.read(cond=lambda c: c not in ['{', '}', ';'])  # TODO: count () here
            ch = self.next_char()
            if ch == '}':
                if t.content.strip():
                    raise ParseError(u'Unexpected token: } in "{0}".'.format(t.content))
                t.type = 'end-control'
                t.content = '}'

                # context
                try:
                    self._context.pop()
                except IndexError:
                    raise ParseError(u'Unmatched }.')

            elif ch == '{':
                t.type = 'control'
                t.content = t.content.strip()
                push = False

                # Exception
                if t.content == 'try':
                    t.model = ExceptionBlock()
                    push = True
                elif t.content.startswith('catch'):
                    t = self.find_context_top()
                    if isinstance(t, ExceptionBlock):
                        t.add_catch(t.content[5:].strip())  # TODO: remove (), etc.
                    else:
                        raise ParseError('catch not in a try block: {0}.'.format(t.content))

                # IfBlock
                elif t.content.startswith('if'):
                    t.model = IfBlock(t.content[2:].strip())  # TODO: remove (), etc.
                    push = True
                elif t.content.startswith('else'):
                    t = self.find_context_top()
                    if isinstance(t, IfBlock):
                        if t.content.startswith('else if'):  # TODO: is this ok for java?
                            t.add_elif(t.content[7:].strip())  # TODO: remove (), etc.
                        else:
                            t.activate_else()
                    else:
                        raise ParseError('else not in a if block: {0}.'.format(t.content))

                # ForBlock
                elif t.content.startswith('for'):
                    t.model = ForBlock()
                    push = True

                # WhileBlock
                elif t.content.startswith('while'):
                    t.model = WhileBlock()
                    push = True

                # More complex parts (class, method)
                else:
                    parent_class = self.find_context_top(lambda x: x.isinstance(Class))
                    t.model = JavaClass.try_parse(t.content, {u'parent_class': parent_class})
                    if not t.model:
                        t.model = JavaMethod.try_parse(t.content, {u'parent_class': parent_class})
                    if not t.model:
                        raise ParseError(u'Token can not be parsed: "{0}".'.format(t.content))
                    else:
                        push = True

                if push:
                    self._context.append(t)

            elif ch == ';':
                t.type = 'statement'
                t.content += ';'

                is_special_statement = False

                # package
                PACKAGE_RE = re.compile(r'package\s+([a-zA-Z0-9_.]+)\s*;')
                pm = PACKAGE_RE.match(t.content)
                if pm:
                    self.package = pm.group(1).strip()  # TODO: check with file path
                    is_special_statement = True

                # normal statement
                t.model = JavaImport.try_parse(t.content)
                if not t.model:
                    t.model = JavaStatement.try_parse(t.content)
                    if t.model and not is_special_statement:
                        ct = self.find_context_top()
                        if isinstance(ct, CodeBlock):
                            ct.add_statement(t.model)
                        else:
                            raise ParseError(u'Statement is not in a block: {0}.'.format(t.model))
                    else:
                        raise ParseError(u'Invalid statement: "{0}"'.format(t.content))

            elif ch is None:
                t = None

            else:
                assert False

        # final cares
        self.skip_spaces()
        t.normalize_content()
        return t


class JavaClass(Class, LanguageSpecificParser):
    CLASS_RE = re.compile(r'^(\w+\s+)?class\s*(\w+)(?:\s*extends\s*([a-zA-Z0-9_.]+))?(?:\s+implements\s*(.+?)\s*)?$')
    ACCESS = enum('UNKNOWN', 'PRIVATE', 'PROTECTED', 'PACKAGE', 'PUBLIC',
                  verbose_names=['unknown', 'private', 'protected', 'package', 'public'])

    def __init__(self, name, source_file=None, package=None, parent_class=None, extends=None, access=None,
                 implements=None):
        super(JavaClass, self).__init__(name, source_file=source_file, package=package, parent_class=parent_class,
                                        extends=extends)
        if len(self.extends) > 1:
            raise ParseError(u'Multiple inheritance is not supported in Java.')
        self.access = access or self.ACCESS.PACKAGE
        self.implements = implements or []  # TODO: set real Interface reference

    @classmethod
    def parse_access(cls, access_str):
        if not access_str:
            return cls.ACCESS.PACKAGE

        for k, v in cls.ACCESS.display_name.items():
            if v == access_str:
                return k
        return None

    @classmethod
    def try_parse(cls, string, opts=None):
        opts = opts or {}
        cm = cls.CLASS_RE.match(string)
        if not cm:
            return None

        acc_str = cm.group(1)
        ext_str = cm.group(3)
        imp_str = cm.group(4)
        return JavaClass(name=cm.group(2),
                         parent_class=opts.get(u'parent_class'),
                         extends=ext_str,
                         implements=[s.strip() for s in imp_str.split(',')] if imp_str else [],
                         access=JavaClass.parse_access(acc_str.strip() if acc_str else None))


class JavaMethod(Method, LanguageSpecificParser):
    METHOD_RE = re.compile(r'^([a-z]+\s+)?(static\s+)?([a-zA-Z0-9_]+\s+)?(\w+)\s*\((.*)\)(?:\s*throws ([a-zA-Z0-9_.,]+))?$')

    @classmethod
    def try_parse(cls, string, opts=None):
        opts = opts or {}
        fm = cls.METHOD_RE.match(string)
        if not fm:
            return None

        parent_class = opts.get(u'parent_class')
        if parent_class is None:
            raise ParseError(u'Functions must be in a class in Java.')

        def split_arg(s):
            si = s.strip().rfind(' ')
            if si == -1:
                return '?', s
            return s[:si], s[si + 1:]

        throw_str = fm.group(6)
        args_str = fm.group(5)
        return Method(parent_class,
                      name=fm.group(4),
                      arguments=[split_arg(s) for s in args_str.split(',')] if args_str else [],
                      return_type=fm.group(3),
                      binding=Method.parse_binding(fm.group(2)),
                      access=Method.parse_access(fm.group(1), default=Method.ACCESS.PACKAGE),
                      throws=[s.strip() for s in throw_str.split(',')] if throw_str else None)


class JavaImport(Import, LanguageSpecificParser):
    IMPORT_RE = re.compile(r'^import\s*([a-zA-Z0-9._*]+);$')

    @classmethod
    def try_parse(cls, string, opts=None):
        """
            :param str or unicode string: code to be parsed
            :rtype: Import
        """
        im = cls.IMPORT_RE.match(string)
        if im:
            return Import(im.group(1))
        return None


class JavaStatement(Statement, LanguageSpecificParser):
    @classmethod
    def try_parse(cls, string, opts=None):
        """
            :param str or unicode string: code to be parsed
            :rtype: Statement
        """
        # TODO: any checks required?
        return Statement(string)
