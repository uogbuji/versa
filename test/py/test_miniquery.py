'''


'''

import logging

from versa.query import miniparse, context
from versa.driver import memory

def test_basics():
    "Basic query test"
    m = memory.connection()
    [ m.add(*l) for l in RELS_1 ]
    variables = {'DC': DC, 'H5': H5, 'H5L': H5L}
    ctx = context(tuple(RELS_1[0]), m, U + 'uo', base=None, extras=None, variables=variables)
    parsed = miniparse("?($a, H5 'title', *) and ?($b, H5L 'see-also', $a)")
    result = parsed.evaluate(ctx)
    assert result == {'a': set(['http://uche.ogbuji.net/ndewo/']), 'b': set(['http://uche.ogbuji.net/'])}

    parsed = miniparse("?($a, H5L 'see-also', *)")
    result = parsed.evaluate(ctx)
    assert result == {'a': set(['http://uche.ogbuji.net/', 'http://uche.ogbuji.net/ndewo/'])}

    parsed = miniparse("?($a, H5 'title', *)")
    result = parsed.evaluate(ctx)
    assert result == {'a': set(['http://uche.ogbuji.net/ndewo/'])}
    return


DC = 'http://purl.org/dc/elements/1.1/'
H5 = 'http://www.w3.org/TR/html5/'
H5L = 'http://www.w3.org/TR/html5/link-type/'
U = 'http://uche.ogbuji.net#'

RELS_1 = [
    ("http://uche.ogbuji.net/ndewo/", "http://www.w3.org/TR/html5/title", "Ndewo, Colorado", {"@lang": "en"}),
    ("http://uche.ogbuji.net/ndewo/", "http://www.w3.org/TR/html5/link-type/author", "http://uche.ogbuji.net/", {"link/description": "Uche Ogbuji"}),
    ("http://uche.ogbuji.net/ndewo/", "http://www.w3.org/TR/html5/link-type/see-also", "https://www.goodreads.com/book/show/18714145-ndewo-colorado", {"@label": "Goodreads"}),
    ("http://uche.ogbuji.net/", "http://www.w3.org/TR/html5/link-type/see-also", "http://uche.ogbuji.net/ndewo/", {})
]

RELS_2 = [
    ("http://copia.ogbuji.net", "http://purl.org/dc/elements/1.1/creator", "Uche Ogbuji", {"@context": "http://copia.ogbuji.net#_metadata"}),
    ("http://copia.ogbuji.net", "http://purl.org/dc/elements/1.1/title", "Copia", {"@context": "http://copia.ogbuji.net#_metadata", '@lang': 'en'}),
    ("http://uche.ogbuji.net", "http://purl.org/dc/elements/1.1/creator", "Uche Ogbuji", {"@context": "http://uche.ogbuji.net#_metadata"}),
    ("http://uche.ogbuji.net", "http://purl.org/dc/elements/1.1/title", "Uche's home", {"@context": "http://uche.ogbuji.net#_metadata", '@lang': 'en'}),
    ("http://uche.ogbuji.net", "http://purl.org/dc/elements/1.1/title", "Ulo Uche", {"@context": "http://uche.ogbuji.net#_metadata", '@lang': 'ig'}),
]

if __name__ == '__main__':
    raise SystemExit("use py.test")


'''
from versa.query import miniparse, context
from versa.driver import memory
DC = 'http://purl.org/dc/elements/1.1/'
H5 = 'http://www.w3.org/TR/html5/'
H5L = 'http://www.w3.org/TR/html5/link-type/'
U = 'http://uche.ogbuji.net#'
m = memory.connection()
LINKS = [
["http://uche.ogbuji.net/ndewo/", "http://www.w3.org/TR/html5/title", "Ndewo, Colorado", {"@lang": "en"}],
["http://uche.ogbuji.net/ndewo/", "http://www.w3.org/TR/html5/link-type/author", "http://uche.ogbuji.net/", {"link/description": "Uche Ogbuji"}],
["http://uche.ogbuji.net/ndewo/", "http://www.w3.org/TR/html5/link-type/see-also", "https://www.goodreads.com/book/show/18714145-ndewo-colorado", {"@label": "Goodreads"}],
["http://uche.ogbuji.net/", "http://www.w3.org/TR/html5/link-type/see-also", "http://uche.ogbuji.net/ndewo/", {}]
]
[ m.add(*l) for l in LINKS ]
variables = {'DC': DC, 'H5': H5, 'H5L': H5L}
ctx = context(tuple(LINKS[0]), m, U + 'uo', base=None, extras=None, variables=variables)
parsed = miniparse("?($a, H5 'title', *) and ?($b, H5L 'see-also', $a)")
parsed.evaluate(ctx)
parsed = miniparse("?($a, H5 'title', *)")
parsed.evaluate(ctx)
'''
