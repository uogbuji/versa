#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Highly recommend installing using `pip install -U .` not `python setup.py install`

Uses pkgutil-style namespace package (Working on figuring out PEP 420)

Note: careful not to conflate install_requires with requirements.txt

https://packaging.python.org/discussions/install-requires-vs-requirements/

Reluctantly use setuptools for now to get install_requires & long_description_content_type

$ python -c "import amara3; import amara3.iri; import amara3.uxml; import amara3.uxml.version; print(amara3.uxml.version.version_info)"
('3', '0', '1')
'''

import sys
from setuptools import setup, Extension
#from distutils.core import setup, Extension

PROJECT_NAME = 'versa'
PROJECT_DESCRIPTION = "Versa model for Web resources and relationships. Think of it as an evolution of Resource Description Framework (RDF) that's at once simpler and more expressive."
PROJECT_LICENSE = 'License :: OSI Approved :: Apache Software License'
PROJECT_AUTHOR = 'Uche Ogbuji'
PROJECT_AUTHOR_EMAIL = 'uche@ogbuji.net'
PROJECT_URL = 'https://github.com/uogbuji/versa'
PACKAGE_DIR = {'versa': 'tools/py'}
PACKAGES = ['versa', 'versa.driver', 'versa.serial', 'versa.query',
            'versa.pipeline', 'versa.contrib']
SCRIPTS = [
        'tools/exec/build_model_site',
        'tools/exec/parse_versa',
        'tools/exec/parse_versa_model',
        'tools/exec/atom2versa',
        'tools/exec/parse_rdfa',
        'tools/exec/versa',
]

CORE_REQUIREMENTS = [
    'amara3.xml',
    'Markdown',
    'python-slugify',
    'click',
    'pyparsing==3.0.4'
]

EXTRA_REQUIREMENTS = [
    'pytest-mock',  # For testing
]

# From http://pypi.python.org/pypi?%3Aaction=list_classifiers
CLASSIFIERS = [
    "Programming Language :: Python",
    "Programming Language :: Python :: 3",
    "Development Status :: 4 - Beta",
    #"Environment :: Other Environment",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: Apache Software License",
    "Operating System :: OS Independent",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Topic :: Internet :: WWW/HTTP",
]

KEYWORDS=['web', 'data']

versionfile = 'tools/py/version.py'
exec(compile(open(versionfile, "rb").read(), versionfile, 'exec'), globals(), locals())
__version__ = '.'.join(version_info)

LONGDESC = '''Versa
=====

The Versa model for Web resources and relationships. Think of it as an
evolution of Resource Description Framework (RDF) that's at once simpler
and more expressive.

'''

LONGDESC_CTYPE = 'text/markdown'

setup(
    name=PROJECT_NAME,
    version=__version__,
    description=PROJECT_DESCRIPTION,
    license=PROJECT_LICENSE,
    author=PROJECT_AUTHOR,
    author_email=PROJECT_AUTHOR_EMAIL,
    #maintainer=PROJECT_MAINTAINER,
    #maintainer_email=PROJECT_MAINTAINER_EMAIL,
    url=PROJECT_URL,
    package_dir=PACKAGE_DIR,
    packages=PACKAGES,
    scripts=SCRIPTS,
    install_requires=CORE_REQUIREMENTS,
    classifiers=CLASSIFIERS,
    long_description=LONGDESC,
    long_description_content_type=LONGDESC_CTYPE,
    keywords=KEYWORDS,
)

