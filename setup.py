#!/usr/bin/env python

from setuptools import setup, find_packages

VERSION = '0.1.10'
DESCRIPTION = 'aws server list in ncurses - select your server/s and ssh to them'

setup(
    name='assh',
    version=VERSION,
    description=DESCRIPTION,
    author='ybrs',
    license='MIT',
    url="http://github.com/ybrs/assh",
    author_email='aybars.badur@gmail.com',
    packages=['assh'],
    install_requires=['hst', 'boto', 'plotly==1.9.6'],
    scripts=['./assh/bin/assh'],
    classifiers = [
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Database',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)