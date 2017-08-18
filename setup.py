#!/usr/bin/env python3
from setuptools import setup

setup(
    name='contemplate',
    py_modules=['contemplate'],
    install_requires=[
        'jinja2',
        'pyyaml',
    ],
    entry_points={
        'console_scripts': [
            'contemplate = contemplate:main',
        ],
    },
)
