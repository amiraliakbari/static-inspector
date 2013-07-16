# -*- coding: utf-8 -*-
from inspector.models.base import Project, SourceFile
from inspector.models.exceptions import ParseError


class JavaProject(Project):
    pass


class JavaSourceFile(SourceFile):
    def __init__(self, *args, **kwargs):
        super(JavaSourceFile, self).__init__(*args, **kwargs)
        self._parse_head = 0
        self._cur_line = 1
        self.L = len(self.file_content)
        self.token = None
        self.token_type = None

    def can_read(self):
        return self._parse_head < self.L

    def next_char(self, length=1):
        # TODO: optimize for length > 1
        for _ in range(length):
            if not self.can_read():
                return None
            if self.file_content[self._parse_head] == '\n':
                self._cur_line += 1
            self._parse_head += 1
        return self.file_content[self._parse_head - 1]

    def skip_spaces(self):
        while self.file_content[self._parse_head].isspace():
            self.next_char()

    def read(self, length=None, to=None, cond=None, find=None, beyond=0):
        if length is not None:
            length += beyond
            self.next_char(length)
            return self.file_content[self._parse_head - length:self._parse_head]
        elif to is not None:
            return self.read(length=to - self._parse_head, beyond=beyond)
        elif cond is not None:
            s = ''
            while self.can_read() and cond(self.file_content[self._parse_head]):
                s += self.next_char()
            for _ in range(beyond):
                s += self.next_char()
            return s
        elif find is not None:
            return self.read(to=self.find_ahead(find), beyond=beyond)
        raise ValueError

    def read_ahead(self, length):
        return self.file_content[self._parse_head:self._parse_head + length]

    def find_ahead(self, sub):
        return self.file_content.find(sub, self._parse_head)

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
                self.token_type = '}'
            elif ch == '{':
                self.token_type = 'control'
            elif ch == ';':
                self.token_type = 'statement'
            else:
                self.token = None
                self.token_type = None
                raise ParseError
        return self.token_type, self.token

    def _parse(self):
        pass
