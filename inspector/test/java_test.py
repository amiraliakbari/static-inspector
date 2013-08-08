# -*- coding: utf-8 -*-
import os
import unittest
from inspector.models.base import SourceFile


class TestJavaParse(unittest.TestCase):
    def setUp(self):
        self.data_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data', 'java')

    def test_parse(self):
        sf = SourceFile.build_source_file(os.path.join(self.data_path, 'sample_sources', '1.java'))
        tokens = [
            ('statement', 'import java.io.*;'),
            ('control', 'class MyFirstProgram'),
            ('comment', '/** Print a hello message */'),
            ('control', 'public static void main(String[] args)'),
            ('statement', 'BufferedReader in =\n        new BufferedReader(new InputStreamReader(System.in));'),
            ('statement', 'String name = "Instructor";'),
            ('statement', 'System.out.print("Give your name: ");'),
            ('comment', '// Ask from user'),
            ('control', 'try'),
            ('statement', 'name = in.readLine();'),
            ('end-control', '}'),
            ('control', 'catch(Exception e)'),
            ('statement', 'System.out.println("Caught an exception!");'),
            ('end-control', '}'),
            ('statement', 'System.out.println("Hello " + name + "!");'),
            ('end-control', '}'),
            ('end-control', '}'),
        ]
        self.assertEqual(sf._tokens, tokens)
        self.assertEqual(sf.next_token(), None)
        self.assertEqual(sf.next_token(), None)

    def test_modelling(self):
        sf = SourceFile.build_source_file(os.path.join(self.data_path, 'sample_sources', '1.java'))
        self.assertEqual(unicode(sf), u'Java SourceFile: 1 imports, 1 classes, 0 functions')

if __name__ == '__main__':
    unittest.main()
