# test_diskcache.py (use py.test)
'''

Note: to see stdout, stderr, ets:

py.test -s test/py/test_diskcache.py

'''

#import logging

import pytest
#from testconfig import config

from versa.driver.diskcache import newmodel
from versa import I, ORIGIN, RELATIONSHIP, TARGET, ATTRIBUTES

##If you do this you also need --nologcapture
##Handle  --tc=debug:y option
#if config.get('debug', 'n').startswith('y'):
#    logging.basicConfig(level=logging.DEBUG)

@pytest.fixture
def rels_1():
    return [
        ("http://copia.ogbuji.net", "http://purl.org/dc/elements/1.1/creator", "Uche Ogbuji", {"@context": "http://copia.ogbuji.net#_metadata"}),
        ("http://copia.ogbuji.net", "http://purl.org/dc/elements/1.1/title", "Copia", {"@context": "http://copia.ogbuji.net#_metadata", '@lang': 'en'}),
        ("http://uche.ogbuji.net", "http://purl.org/dc/elements/1.1/creator", "Uche Ogbuji", {"@context": "http://uche.ogbuji.net#_metadata"}),
        ("http://uche.ogbuji.net", "http://purl.org/dc/elements/1.1/title", "Uche's home", {"@context": "http://uche.ogbuji.net#_metadata", '@lang': 'en'}),
        ("http://uche.ogbuji.net", "http://purl.org/dc/elements/1.1/title", "Ulo Uche", {"@context": "http://uche.ogbuji.net#_metadata", '@lang': 'ig'}),
    ]

def test_basics_1(tmp_path, rels_1):
    model = newmodel(dbdir=tmp_path.name)
    for (subj, pred, obj, attrs) in rels_1:
        model.add(subj, pred, obj, attrs)
    assert model.size() == 5

    results = list(model.match(origin='http://copia.ogbuji.net'))
    assert len(results) == 2

    results = list(model.match(origin='http://uche.ogbuji.net'))
    assert len(results) == 3

    # Does it behave properly on non-matches?
    results = list(model.match(origin='SPAM'))
    assert len(results) == 0

    results = list(model.match(rel='SPAM'))
    assert len(results) == 0

    results = list(model.match(target='SPAM'))
    assert len(results) == 0

    results = list(model.match(attrs={'SPAM': 'EGGS'}))
    assert len(results) == 0


def test_attribute_basics_1(tmp_path, rels_1):
    model = newmodel(dbdir=tmp_path.name)
    for (subj, pred, obj, attrs) in rels_1:
        model.add(subj, pred, obj, attrs)
    assert model.size() == 5

    results = list(model.match(origin='http://uche.ogbuji.net', attrs={u'@lang': u'ig'}))
    assert len(results) == 1
    assert results[0][TARGET] == 'Ulo Uche'

    results = list(model.match(origin='http://uche.ogbuji.net', attrs={u'@lang': u'ig'}, include_ids=True))
    assert len(results) == 1
    results = [r[1] for r in results]
    assert results[0][TARGET] == 'Ulo Uche'

    results = list(model.match(origin='http://uche.ogbuji.net', attrs={u'@lang': u'en'}))
    assert len(results) == 1
    assert results[0][TARGET] == 'Uche\'s home'

    results = list(model.match(origin='http://uche.ogbuji.net', attrs={u'@lang': u'en'}, include_ids=True))
    assert len(results) == 1
    results = [r[1] for r in results]
    assert results[0][TARGET] == 'Uche\'s home'


if __name__ == '__main__':
    raise SystemExit("use pytest command line")
