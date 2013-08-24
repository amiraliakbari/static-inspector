# -*- coding: utf-8 -*-
import os


def get_extension(filename):
    return os.path.splitext(filename)[1][1:].lower()
