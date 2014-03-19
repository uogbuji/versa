'''

Note: to see DEBUG log even if the tests pass do:

nosetests test/py/test_memory.py --tc=debug:y --nologcapture

'''

import logging

from nose import with_setup
from testconfig import config

from versa.driver import memory

#If you do this you also need --nologcapture
#Handle  --tc=debug:y option
if config.get('debug', 'n').startswith('y'):
    logging.basicConfig(level=logging.DEBUG)


def test_basics():
    "test ..."
    model = memory.connection()
    for (subj, pred, obj, attrs) in RELS_1:
        model.add(subj, pred, obj, attrs)
    results = model.match(subj='http://copia.ogbuji.net')
    logging.debug('BASICS PART 1')
    for result in results:
        logging.debug('Result: {0}'.format(repr(result)))
        #assert result == ()
    #assert results == None, "Boo! "

    results = model.match(subj='http://uche.ogbuji.net', attrs={u'@lang': u'ig'})
    logging.debug('BASICS PART 2')
    results = tuple(list(results))
    import pprint; pprint.pprint(results)
    for result in results:
        logging.debug('Result: {0}'.format(repr(result)))
        #assert result == ()
    expected = (('http://uche.ogbuji.net', 'http://purl.org/dc/elements/1.1/title', 'Ulo Uche', {'@context': 'http://uche.ogbuji.net#_metadata', '@lang': 'ig'}),)
    assert results == expected, (results, expected)


RELS_1 = [
    ("http://copia.ogbuji.net", "http://purl.org/dc/elements/1.1/creator", "Uche Ogbuji", {"@context": "http://copia.ogbuji.net#_metadata"}),
    ("http://copia.ogbuji.net", "http://purl.org/dc/elements/1.1/title", "Copia", {"@context": "http://copia.ogbuji.net#_metadata", '@lang': 'en'}),
    ("http://uche.ogbuji.net", "http://purl.org/dc/elements/1.1/creator", "Uche Ogbuji", {"@context": "http://uche.ogbuji.net#_metadata"}),
    ("http://uche.ogbuji.net", "http://purl.org/dc/elements/1.1/title", "Uche's home", {"@context": "http://uche.ogbuji.net#_metadata", '@lang': 'en'}),
    ("http://uche.ogbuji.net", "http://purl.org/dc/elements/1.1/title", "Ulo Uche", {"@context": "http://uche.ogbuji.net#_metadata", '@lang': 'ig'}),
]

if __name__ == '__main__':
    raise SystemExit("use nosetests")

