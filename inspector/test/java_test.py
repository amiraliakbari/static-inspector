# -*- coding: utf-8 -*-
import os
import unittest
from inspector.models.base import SourceFile


class TestJavaParse(unittest.TestCase):
    def setUp(self):
        self.data_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data', 'java')

    def test_parse_1(self):
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
        self.assertEqual(sf.next_token(), (None, None))
        self.assertEqual(sf.next_token(), (None, None))

    def test_parse_2(self):
        sf = SourceFile.build_source_file(os.path.join(self.data_path, 'sample_sources', '2.java'))
        tokens = [
            ('control', 'class Fibonacci'),
            ('comment', '// Print out the Fibonacci sequence for values < 50'),
            ('control', 'public static void main(String[] args)'),
            ('statement', 'int lo = 1;'),
            ('statement', 'int hi = 1;'),
            ('statement', 'System.out.println(lo);'),
            ('control', 'while (hi < 50)'),
            ('statement', 'System.out.print(hi);'),
            ('statement', 'hi = lo + hi;'),
            ('comment', '// new hi'),
            ('statement', 'lo = hi - lo;'),
            ('comment', '/* new lo is (sum - old lo)\n                       i.e., the old hi */'),
            ('end-control', '}'),
            ('end-control', '}')
        ]
        self.assertEqual(sf._tokens, tokens)
        self.assertEqual(sf.next_token(), (None, None))

    def test_parse_3(self):
        sf = SourceFile.build_source_file(os.path.join(self.data_path, 'sample_sources', '3.java'))
        tokens = [
            ('control', 'class Point'),
            ('statement', 'public double x, y;'),
            ('statement', 'public static Point origin = new Point(0,0);'),
            ('comment', '// This always refers to an object at (0,0)'),
            ('control', 'Point(double x_value, double y_value)'),
            ('statement', 'x = x_value;'),
            ('statement', 'y = y_value;'),
            ('end-control', '}'),
            ('control', 'public void clear()'),
            ('statement', 'this.x = 0;'),
            ('statement', 'this.y = 0;'),
            ('end-control', '}'),
            ('control', 'public double distance(Point that)'),
            ('statement', 'double xDiff = x - that.x;'),
            ('statement', 'double yDiff = y - that.y;'),
            ('statement', 'return Math.sqrt(xDiff * xDiff + yDiff * yDiff);'), ('end-control', '}'),
            ('end-control', '}'),
            ('control', 'class Pixel extends Point'),
            ('statement', 'Color color;'),
            ('control', 'public void clear()'),
            ('statement', 'super.clear();'), ('statement', 'color = null;'),
            ('end-control', '}'),
            ('end-control', '}')
        ]
        self.assertEqual(sf._tokens, tokens)
        self.assertEqual(sf.next_token(), (None, None))

    def test_modelling(self):
        sf = SourceFile.build_source_file(os.path.join(self.data_path, 'sample_sources', '1.java'))
        self.assertEqual(unicode(sf), u'Java SourceFile: 1 imports, 1 classes, 0 functions')


if __name__ == '__main__':
    unittest.main()
