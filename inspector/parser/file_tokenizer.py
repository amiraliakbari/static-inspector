# -*- coding: utf-8 -*-


class FileTokenizer(object):
    def __init__(self, content_file=None):
        self.set_content(content_file)

        # public fields
        self.token = None
        self.token_type = None

    def set_content(self, content_file):
        # resetting heads
        self._parse_head = 0
        self._cur_line = 1

        # loading content from file
        if content_file is not None:
            if isinstance(content_file, basestring):
                self.file_content = content_file
            else:
                with open(content_file, 'r') as f:
                    self.file_content = f.read()
            self.L = len(self.file_content)
        else:
            self.file_content = None
            self.L = 0

    def has_content(self):
        return self.file_content is not None

    def can_read(self):
        return self._parse_head < self.L

    def next_char(self, skip=0):
        # TODO: optimize for skip > 0
        if skip < 0:
            raise ValueError('skip can not be negative')
        for _ in range(skip + 1):
            if not self.can_read():
                return None
            if self.file_content[self._parse_head] == '\n':
                self._cur_line += 1
            self._parse_head += 1
        return self.file_content[self._parse_head - 1]

    def skip_spaces(self):
        while self.can_read() and self.read_ahead_char().isspace():
            self.next_char()

    def read(self, length=None, to=None, cond=None, find=None, beyond=0):
        if length is not None:
            length += beyond
            self.next_char(skip=length - 1)
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

    def read_ahead_char(self):
        return self.file_content[self._parse_head]

    def find_ahead(self, sub):
        return self.file_content.find(sub, self._parse_head)
