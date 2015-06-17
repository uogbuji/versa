'''

Note: to see DEBUG log even if the tests pass do:

nosetests test/py/test_memory.py --tc=debug:y --nologcapture

'''

import logging

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
    results = model.match(origin='http://copia.ogbuji.net')
    logging.debug('BASICS PART 1')
    for result in results:
        logging.debug('Result: {0}'.format(repr(result)))
        #assert result == ()
    #assert results == None, "Boo! "

    results = model.match(origin='http://uche.ogbuji.net', attrs={u'@lang': u'ig'})
    logging.debug('BASICS PART 2')
    results = tuple(list(results))
    import pprint; pprint.pprint(results)
    for result in results:
        logging.debug('Result: {0}'.format(repr(result)))
        #assert result == ()
    expected = (('http://uche.ogbuji.net', 'http://purl.org/dc/elements/1.1/title', 'Ulo Uche', {'@context': 'http://uche.ogbuji.net#_metadata', '@lang': 'ig'}),)
    assert results == expected, (results, expected)

def test_ordering_insertion():
    model = memory.connection()
    model.add('s1','p1','lit1',{})
    model.add('s1','p2','lit2',{})
    model.add('s1','p0','lit0',{},index=1)
    model.add('s2','p3','lit3',{})

    assert list(model)[0][1][1] == 'p1'
    assert list(model)[1][1][1] == 'p0'
    assert list(model)[2][1][1] == 'p2'
    assert list(model)[3][1][1] == 'p3'

def test_removal():
    model = memory.connection()
    model.add('s1','p0','lit0',{})
    model.add('s1','p1','lit1',{})
    model.add('s1','p2','lit2',{})
    model.add('s2','p3','lit3',{})
    model.remove([3,0])

    assert list(model)[0][1][2] == 'lit1'
    assert list(model)[1][1][2] == 'lit2'
    assert model.size() == 2

    model.remove(0)
    assert list(model)[0][1][2] == 'lit2'
    assert model.size() == 1


RELS_1 = [
    ("http://copia.ogbuji.net", "http://purl.org/dc/elements/1.1/creator", "Uche Ogbuji", {"@context": "http://copia.ogbuji.net#_metadata"}),
    ("http://copia.ogbuji.net", "http://purl.org/dc/elements/1.1/title", "Copia", {"@context": "http://copia.ogbuji.net#_metadata", '@lang': 'en'}),
    ("http://uche.ogbuji.net", "http://purl.org/dc/elements/1.1/creator", "Uche Ogbuji", {"@context": "http://uche.ogbuji.net#_metadata"}),
    ("http://uche.ogbuji.net", "http://purl.org/dc/elements/1.1/title", "Uche's home", {"@context": "http://uche.ogbuji.net#_metadata", '@lang': 'en'}),
    ("http://uche.ogbuji.net", "http://purl.org/dc/elements/1.1/title", "Ulo Uche", {"@context": "http://uche.ogbuji.net#_metadata", '@lang': 'ig'}),
]

if __name__ == '__main__':
    raise SystemExit("use py.test")

