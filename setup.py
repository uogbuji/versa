#!/usr/bin/env python

from distutils.core import setup
#from lib import __version__

setup(name = "versa",
      #version = __version__,
      version = "0.2",
      description="Versa model for Web resources and relationships. Think of it as an evolution of Resource Description Framework (RDF) that's at once simpler and more expressive.",
      author='Uche Ogbuji',
      author_email='uche@ogbuji.net',
      url='http://uche.ogbuji.net',
      package_dir={'versa': 'tools/py'},
      packages=['versa', 'versa.driver'],
      scripts=['tools/exec/build_model_site'],
      #package_data={'akara': ["akara.conf"]},
      )
