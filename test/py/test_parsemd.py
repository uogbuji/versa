import logging

from versa.driver.sqlite import connection

#logging.basicConfig(level=logging.DEBUG)

#Move to a test utils module
import os, inspect
def module_path(local_function):
   ''' returns the module path without the use of __file__.  Requires a function defined 
   locally in the module.
   from http://stackoverflow.com/questions/729583/getting-file-path-of-imported-module'''
   return os.path.abspath(inspect.getsourcefile(local_function))

#hack to locate test resource (data) files regardless of from where nose was run
RESOURCEPATH = os.path.normpath(os.path.join(module_path(lambda _: None), '../../resource/'))

VERSA_LITERATE1 = """<!--
Test Versa literate model
-->

# @docheader

* @base: http://bibfra.me/vocab/
* @property-base: http://bibfra.me/purl/versa/support

# Resource

* synonyms: http://bibframe.org/vocab/Resource http://schema.org/Thing
* label: Resource
* description: Conceptual Resource
* properties: label description image link

"""

def test_versa_syntax1():
    import os
    from versa.mdsyntax import from_markdown

    #logging.debug(recs)
    m = connection()
    m.create_space()
    #from_markdown(VERSA_LITERATE1, m, encoding='utf-8')
    from_markdown(VERSA_LITERATE1, m)
    logging.debug('VERSA LITERATE EXAMPLE 1')
    for stmt in m.match():
        logging.debug('Result: {0}'.format(repr(stmt)))
        #assert result == ()
    #assert results == None, "Boo! "

