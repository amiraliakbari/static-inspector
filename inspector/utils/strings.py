# -*- coding: utf-8 -*-


def summarize(string, max_len=10):
    """
        :param str or unicode string: string to be summarized
    """
    if len(string) > max_len:
        string = string[:max_len] + u'...'
    return string


def quoted(string):
    """
        :param unicode string: string to be quoted
    """
    return u'"{0}"'.format(string)
