# -*- coding: utf-8 -*-
import re


def summarize(string, max_len=10):
    """
        :param str or unicode string: string to be summarized
    """
    if len(string) > max_len:
        string = string[:max_len] + u'...'
    return string


def quoted(string):
    """
        :param str or unicode string: string to be quoted
    """
    return u'"{0}"'.format(string)


def has_word(string, sub):
    """ Determine if the string has the given sub string as a whole word in it
    """
    return re.search(r"\b" + re.escape(sub) + r"\b", string) is not None


def render_template(template_string, params):
    """ Replace all {{ vars }} with their values given in a dictionary

        :param str template_string: string to render
        :param dict params: a dictionary containing template parameters
        :rtype: str
    """

    for k, v in params.iteritems():
        template_string = template_string.replace('{{ ' + k + ' }}', unicode(v))
    return template_string
