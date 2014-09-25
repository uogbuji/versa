import logging
from amara.lib import U, inputsource

from versa.driver import memory
from versa.reader.md import from_markdown

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

VERSA_BASEIRI = 'http://bibfra.me/purl/versa/'

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


def Xtest_versa_syntax1():
    #logging.debug(recs)
    m = connection()
    m.create_space()
    #from_markdown(VERSA_LITERATE1, m, encoding='utf-8')
    from_markdown(VERSA_LITERATE1, m)
    logging.debug('VERSA LITERATE EXAMPLE 1')
    for link in m.match():
        logging.debug('Result: {0}'.format(repr(link)))
        #assert result == ()
    #assert results == None, "Boo! "


def test_versa_syntax1():
    config = {
        'autotype-h1': 'http://example.org/r1',
        'autotype-h2': 'http://example.org/r2',
        'interpretations': {
            VERSA_BASEIRI + 'refines': VERSA_BASEIRI + 'resourceset',
            VERSA_BASEIRI + 'properties': VERSA_BASEIRI + 'resourceset',
            VERSA_BASEIRI + 'synonyms': VERSA_BASEIRI + 'resourceset'
        }
    }

    m = memory.connection(baseuri='http://example.org/')
    #from_markdown(VERSA_LITERATE1, m, encoding='utf-8')
    doc = open(os.path.join(RESOURCEPATH, 'ubibframe.md')).read()
    from_markdown(doc, m, config=config)
    logging.debug('VERSA LITERATE EXAMPLE 1')
    for link in m.match():
        logging.debug('Result: {0}'.format(repr(link)))
        #assert result == ()
    assert results == None, "Boo! "


    #expected_statements = [(u'http://uche.ogbuji.net/data#uche.ogbuji', u'http://purl.org/xml3k/dendrite/test1/name', u'Uche Ogbuji', {u'@context': u'http://purl.org/xml3k/dendrite/test1/', u'http://purl.org/xml3k/dendrite/test1/form': u'familiar'}),
    #    (u'http://uche.ogbuji.net/data#uche.ogbuji', u'http://purl.org/xml3k/dendrite/test1/works-at', u'http://uche.ogbuji.net/data#zepheira', {u'http://purl.org/xml3k/dendrite/test1/temporal-assertion': u'2007-', u'@context': u'http://purl.org/xml3k/dendrite/test1/'}),
    #    (u'http://uche.ogbuji.net/data#zepheira', u'http://purl.org/xml3k/dendrite/test1/name', u'Zepheira', {u'@context': u'http://purl.org/xml3k/dendrite/test1/', u'http://purl.org/xml3k/dendrite/test1/form': u'familiar'}),
    #    (u'http://uche.ogbuji.net/data#zepheira', u'http://purl.org/xml3k/dendrite/test1/name', u'Zepheira LLC', {u'@context': u'http://purl.org/xml3k/dendrite/test1/', u'http://purl.org/xml3k/dendrite/test1/form': u'legal'}),
    #    (u'http://uche.ogbuji.net/data#zepheira', u'http://purl.org/xml3k/dendrite/test1/webaddress', u'http://zepheira.com', {u'@context': u'http://purl.org/xml3k/dendrite/test1/'})]

