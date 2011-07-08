#!/usr/bin/env python
import sys
from setuptools import setup, find_packages

import staples

long_description = """
Staples is a simple static site generator based on the idea of processors
mapped to types of files. It includes a basic server for development, and
has no external requirements itself, beyond the Python Standard Library.
Specific processors, such as the included Django template renderer, will
have their own requirements.

Info and source: https://github.com/typeish/staples
"""

setup(
    name                = 'Staples',
    version             = staples.__version__,
    long_description    = '',
    long_description    = long_description,
    author              = staples.__author__,
    author_email        = 'contact@typeish.net',
    url                 = 'https://github.com/typeish/staples',
    py_modules          = ['staples'],
    test_suite          = '',
    tests_require       = [],
    install_requires    = [],
    license             = staples.__license__
    entry_points        = {
        'console_scripts': [
            'staples = staples:main',
        ]
    },
    classifiers         =[
    ],
)