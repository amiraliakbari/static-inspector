# -*- coding: utf-8 -*-
import os
import re

from inspector.utils.lang import enum
from inspector.models.base import Project, SourceFile, Class, Method, Import
from inspector.models.exceptions import ParseError


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

    def next_token(self):
        self.skip_spaces()
        prefix = self.read_ahead(2)
        if prefix == '//':
            self.token_type = 'comment'
            self.token = self.read(cond=lambda ch: ch != '\n')
            self.next_char()
        elif prefix == '/*':
            self.token_type = 'comment'
            self.token = self.read(find='*/', beyond=2)
        else:
            self.token = self.read(cond=lambda c: c not in ['{', '}', ';'])
            ch = self.next_char()
            if ch == '}':
                self.token += ch
                self.token_type = 'end-control'
            elif ch == '{':
                self.token_type = 'control'
            elif ch == ';':
                self.token_type = 'statement'
                self.token += ';'
            elif ch is None:
                self.token = None
                self.token_type = None
                return None, None
            else:
                self.token = None
                self.token_type = None
                raise ParseError
        self.token = self.token.strip()
        self.skip_spaces()
        return self.token_type, self.token

    def extract_token_data(self, token_type, token):
        """
            :type token: str
        """
        def split_arg(s):
            si = s.strip().rfind(' ')
            if si == -1:
                return '?', s
            return s[:si], s[si + 1:]

        # print '@', token
        d = {}
        if token_type == 'statement':
            im = re.match(r'^import\s*([a-zA-Z0-9._*]+);$', token)
            if im:
                d = Import(im.group(1))

            # TODO: consider package

            if isinstance(d, dict):
                d['code'] = token

        elif token_type == 'control':
            # TODO: also specify line number for if/for/...
            if token == 'try':
                d['type'] = 'try'
            elif token.startswith('catch'):
                d['type'] = 'catch'
            elif token.startswith('if'):
                d['type'] = 'if'
            elif token.startswith('else if'):
                d['type'] = 'else if'
            elif token.startswith('else'):
                d['type'] = 'else'
            elif token.startswith('for'):
                d['type'] = 'for'
            elif token.startswith('while'):
                d['type'] = 'while'
            else:
                parent_class = None
                for c, _, _ in reversed(self._context):
                    if isinstance(c, Class):
                        parent_class = c
                        break

                cm = re.match(r'^(\w+\s+)?class\s*(\w+)$', token)
                if cm:
                    acc_str = cm.group(1)
                    d = JavaClass(name=cm.group(2),
                                  parent_class=parent_class,
                                  access=JavaClass.parse_access(acc_str.strip() if acc_str else None))

                fm = re.match(r'^([a-z]+\s+)?(static\s+)?([a-z]+\s+)?(\w+)\s*\((.*)\)$', token)
                if fm:
                    if parent_class is None:
                        raise ParseError('Functions must be in a class in Java.')
                    d = Method(parent_class,
                               name=fm.group(4),
                               arguments=[split_arg(s) for s in fm.group(5).split(',')],
                               return_type=fm.group(3),
                               binding=Method.parse_binding(fm.group(2)),
                               access=Method.parse_access(fm.group(1), default=Method.ACCESS.PACKAGE))

                if not d:
                    raise ParseError('Unknown token: "{0}".'.format(token))

            p = []
            for _, name, _ in self._context:
                if name is not None:
                    p.append(name)
            p.append(d.get('name', d['type']) if isinstance(d, dict) else d.name)
            if isinstance(d, dict):
                d['code_path'] = '.'.join(p)
            self._context.append((d, d.get('name', '') if isinstance(d, dict) else d.name, token))

        elif token_type == 'end-control':
            try:
                self._context.pop()
            except IndexError:
                raise ParseError

        elif token_type == 'comment':
            pass  # why?

        else:
            print 'Unknown token: "{0}".'.format(token)
            return None

        return d

    def _parse(self):
        while self.can_read():
            tp, tok = self.next_token()
            self._tokens.append((tp, tok))
            d = self.extract_token_data(tp, tok)
            if isinstance(d, Import):
                self.imports.append(d)
            elif isinstance(d, Class):
                self.classes.append(d)
            self._tokens_data.append(d)


class JavaClass(Class):
    ACCESS = enum('UNKNOWN', 'PRIVATE', 'PROTECTED', 'PACKAGE', 'PUBLIC',
                  verbose_names=['unknown', 'private', 'protected', 'package', 'public'])

    def __init__(self, name, source_file=None, package=None, parent_class=None, access=None):
        super(JavaClass, self).__init__(name, source_file=source_file, package=package, parent_class=parent_class)
        self.access = access or self.ACCESS.PACKAGE

    @classmethod
    def parse_access(cls, access_str):
        if not access_str:
            return cls.ACCESS.PACKAGE

        for k, v in cls.ACCESS.display_name.items():
            if v == access_str:
                return k
        return None
