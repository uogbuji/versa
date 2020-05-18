import os
import logging

from versa import I
from versa.driver import memory
from versa.reader.md import from_markdown


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


def test_versa_syntax1(testresourcepath):
    config = {
        'autotype-h1': 'http://example.org/r1',
        'autotype-h2': 'http://example.org/r2',
        'interpretations': {
            VERSA_BASEIRI + 'refines': VERSA_BASEIRI + 'resourceset',
            VERSA_BASEIRI + 'properties': VERSA_BASEIRI + 'resourceset',
            VERSA_BASEIRI + 'synonyms': VERSA_BASEIRI + 'resourceset'
        }
    }

    m = memory.connection(baseiri='http://example.org/')
    #from_markdown(VERSA_LITERATE1, m, encoding='utf-8')
    doc = open(os.path.join(testresourcepath, 'doc1.abbr.md')).read()
    from_markdown(doc, m, config=config)
    logging.debug('VERSA LITERATE EXAMPLE 1')
    results = list(m.match())
    assert len(results) == 6
    assert (I('http://uche.ogbuji.net/ndewo/'), I('http://bibfra.me/purl/versa/type'), 'http://example.org/r1', {}) in results
    assert (I('http://uche.ogbuji.net/ndewo/'), I('http://www.w3.org/TR/html5/title'), 'Ndewo, Colorado', {'@lang': None}) in results
    assert (I('http://uche.ogbuji.net/ndewo/'), I('http://www.w3.org/TR/html5/link-type/author'), '', {I('http://www.w3.org/TR/html5/link/description'): 'Uche Ogbuji'}) in results
    assert (I('http://uche.ogbuji.net/ndewo/'), I('http://www.w3.org/TR/html5/link-type/see-also'), '', {I('http://www.w3.org/TR/html5/link/label'): 'Goodreads'}) in results
    assert (I('http://uche.ogbuji.net/'), I('http://bibfra.me/purl/versa/type'), 'http://example.org/r1', {}) in results
    assert (I('http://uche.ogbuji.net/'), I('http://www.w3.org/TR/html5/link-type/see-also'), '', {}) in results

    # assert False, "Boo! "
