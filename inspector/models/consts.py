# -*- coding: utf-8 -*-


class Language:
    UNKNOWN = 0
    JAVA = 1
    PYTHON = 2

    @classmethod
    def get_display_name(cls, lng):
        if lng == cls.JAVA:
            return 'Java'
        if lng == cls.PYTHON:
            return 'Python'
        return 'Unknown'


class JavaFrameworks:
    ANDROID = 11


class PythonFrameworks:
    DJANGO = 21
    FLASK = 22
