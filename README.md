Static Inspector
================
[![Build Status](https://travis-ci.org/amiraliakbari/static-inspector.png?branch=master)](https://travis-ci.org/amiraliakbari/static-inspector)
[![Coverage Status](https://coveralls.io/repos/amiraliakbari/static-inspector/badge.png?branch=master)](https://coveralls.io/r/amiraliakbari/static-inspector?branch=master)

Static Inspector is a Python library to parse, model, inspect, and modify source codes of a variety
of programming languages.

It can be used to construct an OO model of a project to do further inspections and modifications. The
modelling is not limited to files or packages, and can be done up to project or repository level.
The model is intended to be as general-purpose as possible, to consider all aspects of modern
projects (repositories, code frameworks, required libraries, paths, static content, projects with
multiple languages, etc.), as well as being simple to use.

Parsers for some popular languages and frameworks are included in the library (currently Python,
Java, Django, and Android), which can construct project models without needing any extra configuration.
The library's architecture separates the parsing from other parts of the system to allow use of a
common codebase for inspecting different languages, frameworks, and project types.

There are many inspection and parsing tools available for python, inculding standard `inspect` or `ast`,
and many other third party libraries (see
[Ned Batchelder's overview](http://nedbatchelder.com/text/python-parsers.html)).
Static Inspector tries to provide extra features like project-level parsing, inspection without needing
to import the code to be inspected, OO modeling of the parsing results, and out of the box support for
major languages and frameworks.

Another feature of Static Inspector parser is preserving the real code structure (including comments,
indentation, definition order, and code line number) to enable use cases like code quality inspection,
source code modification (like a human programmer), and maybe more detailed coverage reports.
