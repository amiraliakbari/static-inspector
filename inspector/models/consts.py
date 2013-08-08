# -*- coding: utf-8 -*-
from inspector.utils.lang import enum


Language = enum('UNKNOWN', 'JAVA', 'PYTHON', verbose_names=['Unknown', 'Java', 'Python'])
JavaFrameworks = enum('ANDROID', verbose_names=['Android'])
PythonFrameworks = enum('DJANGO', 'FLASK', verbose_names=['Django', 'Flask'])
