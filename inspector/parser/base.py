# -*- coding: utf-8 -*-
from inspector.utils.strings import quoted


class Token(object):
    def __init__(self, content=None, t_type=None, model=None):
        self.content = content
        self.type = t_type
        self.model = model

    def normalize_content(self):
        if self.content:
            self.content = self.content.strip()

    def isinstance(self, cls):
        return isinstance(self.model, cls)

    def __unicode__(self):
        return unicode(self.model) if self.model is not None else quoted(unicode(self.content))

    def __str__(self):
        return unicode(self)


class LanguageSpecificParser(object):
    @classmethod
    def try_parse(cls, string, opts=None):
        """
            :param str or unicode string: code to be parsed
        """
        raise NotImplementedError
