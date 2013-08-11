# -*- coding: utf-8 -*-


def find(iterable, accept):
    for x in iterable:
        if accept(x):
            return x
    return None
