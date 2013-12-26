# -*- coding: utf-8 -*-
import os
import unittest
from inspector.analyzer.file_analyzer import FileAnalyzer
from inspector.models.base import File


class TestFileAnalyzer(unittest.TestCase):
    def setUp(self):
        self.data_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data', 'files')

    def test_is_binary(self):
        f1 = File(os.path.join(self.data_path, 'hello_world.out'))
        self.assertTrue(FileAnalyzer.is_binary(f1))

        f2 = File(os.path.join(self.data_path, 'hello_world.cpp'))
        self.assertFalse(FileAnalyzer.is_binary(f2))

    def test_estimate_file_size(self):
        f1 = File(os.path.join(self.data_path, 'hello_world.out'))
        self.assertEqual(FileAnalyzer.estimate_file_size(f1), (8, 8))

        f2 = File(os.path.join(self.data_path, 'hello_world.cpp'))
        self.assertEqual(FileAnalyzer.estimate_file_size(f2), (107, 7))
