# -*- coding: utf-8 -*-


class Token(object):
    def __init__(self):
        self.content = None
        self.type = None
        self.model = None

    def normalize_content(self):
        if self.content:
            self.content = self.content.strip()

    def isinstance(self, cls):
        return isinstance(self.model, cls)


class LanguageSpecificParser(object):
    @classmethod
    def try_parse(cls, string, opts=None):
        """
            :param str or unicode string: code to be parsed
        """
        raise NotImplementedError
