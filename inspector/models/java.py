# -*- coding: utf-8 -*-
import re

from inspector.models.base import Project, SourceFile
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
            if token.startswith('import '):
                d['type'] = 'import'
        elif token_type == 'control':
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
                cm = re.match(r'^class\s*(\w+)$', token)
                if cm:
                    d['type'] = 'class'
                    d['name'] = cm.group(1)

                fm = re.match(r'^(\w*\s*?)\s(\w*\s*?)\s(\w*)\s*(\w+)\s*\((.*)\)$', token)
                if fm:
                    d['type'] = 'function'
                    d['access'] = fm.group(1)
                    d['binding'] = fm.group(2)
                    d['return_type'] = fm.group(3)
                    d['name'] = fm.group(4)
                    d['arguments'] = [split_arg(s) for s in fm.group(5).split(',')]

            p = []
            for _, name, _ in self._context:
                if name is not None:
                    p.append(name)
            p.append(d.get('name', d['type']))  # TODO: also specify line number for if/for/...
            d['code_path'] = '.'.join(p)

            self._context.append((d['type'], d.get('name', ''), token))
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
            self._tokens_data.append(self.extract_token_data(tp, tok))
