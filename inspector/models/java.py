# -*- coding: utf-8 -*-
import re

from inspector.models.base import Project, SourceFile, Class, Method, Import
from inspector.models.exceptions import ParseError


class JavaProject(Project):
    pass


class JavaSourceFile(SourceFile):
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
                return None
            else:
                self.token = None
                self.token_type = None
                raise ParseError
        self.token = self.token.strip()
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

        d = {}
        if token_type == 'statement':
            im = re.match(r'^import\s*([a-zA-Z0-9._*]+);$', token)
            if im:
                d = Import(im.group(1))
        elif token_type == 'control':
            # TODO: also specify line number for if/for/...
            if token == 'try':
                d['type'] = 'try'
            elif token.startswith('catch'):
                d['type'] = 'catch'
            elif token.startswith('if'):
                d['type'] = 'if'
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

                cm = re.match(r'^class\s*(\w+)$', token)
                if cm:
                    d = Class(name=cm.group(1), parent_class=parent_class)

                fm = re.match(r'^(\w*\s*?)\s(\w*\s*?)\s(\w*)\s*(\w+)\s*\((.*)\)$', token)
                if fm:
                    if parent_class is None:
                        raise ParseError('Functions must be in a class in Java.')
                    d = Method(parent_class,
                               name=fm.group(4),
                               arguments=[split_arg(s) for s in fm.group(5).split(',')],
                               return_type=fm.group(3),
                               binding=Method.parse_binding(fm.group(2)),
                               access=Method.parse_access(fm.group(1)))

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
            pass
        else:
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
