#!/usr/bin/env python

from distutils.core import setup
#from lib import __version__

versionfile = 'tools/py/version.py'
exec(compile(open(versionfile, "rb").read(), versionfile, 'exec'), globals(), locals())
__version__ = '.'.join(version_info)

LONGDESC = '''Versa
=====

The Versa model for Web resources and relationships. Think of it as an
evolution of Resource Description Framework (RDF) that's at once simpler
and more expressive.

'''

try:
    import pypandoc
    long_description = pypandoc.convert('README.md', 'rst')
except (IOError, ImportError) as e:
    #long_description = open('README.md').read()
    long_description = LONGDESC

setup(
    name = "versa",
    version = __version__,
    description="Versa model for Web resources and relationships. Think of it as an evolution of Resource Description Framework (RDF) that's at once simpler and more expressive.",
    author='Uche Ogbuji',
    author_email='uche@ogbuji.net',
    url='https://github.com/uogbuji/versa',
    package_dir={'versa': 'tools/py'},
    packages=['versa', 'versa.driver', 'versa.reader', 'versa.writer', 'versa.pipeline', 'versa.contrib'],
    scripts=['tools/exec/build_model_site', 'tools/exec/parse_versa', 'tools/exec/parse_versa_model', 'tools/exec/atom2versa'],
    keywords = ["web", "data"],
    #scripts=['exec/exhibit_agg', 'exec/exhibit_lint'],
    classifiers = [
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Development Status :: 3 - Alpha",
        #"Environment :: Other Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP",
    ],
    long_description = long_description
    )
