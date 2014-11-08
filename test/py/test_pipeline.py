'''
Structured Data Validators Structured Data Linter http://linter.structured-data.org/ Open Graph Debugger https://developers.facebook.com/tools/debug Schema Validator http://validator.nu/ Twitter Card Preview https://dev.twitter.com/docs/cards/preview Google Structured Data Testing Tool http://www.google.com/webmasters/tools/richsnippets
'''

import logging
import functools

from datachef.ids import idgen, simple_hashstring, FROM_EMPTY_HASH

from versa import I, VERSA_BASEIRI, ORIGIN, RELATIONSHIP, TARGET
from versa.driver import memory
from versa.pipeline import *

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
VTYPE_REL = I(iri.absolutize('type', VERSA_BASEIRI))

SIMPLE_BOOK = {
    'id': 'http://example.org/book/catcher-in-the-rye',
    'title': 'The Catcher in the Rye',
    'type': 'http://ogp.me/ns/books#books.book',
    'link': 'http://example.org/book/catcher-in-the-rye.html',
    'author': 'J.D. Salinger',
    'cover': 'http://example.org/book/catcher-in-the-rye-book-cover.jpg',
}

#logging.basicConfig(level=logging.DEBUG)
BOOK_TYPE = 'http://schema.org/Book'
SCHEMA_ORG = 'http://schema.org/'
EXAMPLE_ORG = 'http://example.org/'

def test_pipeline():
    idg = idgen(EXAMPLE_ORG)
    existing_ids = []
    mat = functools.partial(materialize, hashidgen=idg, existing_ids=existing_ids)

    TRANSFORMS = {
        'id': functools.partial(discard),
        'title': functools.partial(relabel, new_rel='name'),
        'author': functools.partial(mat, new_rel='author', unique=run('target'), typ='Person', properties={'name': run('target')}),
        'link': functools.partial(relabel, new_rel='link'),
        'cover': functools.partial(relabel, new_rel='cover'),
    }
    #'type': functools.partial(relabel, new_rel=VTYPE_REL),

    out_m = memory.connection(baseiri='http://example.org/')

    rid = SIMPLE_BOOK['id']
    out_m.add(rid, VTYPE_REL, BOOK_TYPE)
    for k, v in SIMPLE_BOOK.items():
        link = (rid, k, v)
        func = TRANSFORMS.get(k)
        if func:
            in_m = memory.connection(baseiri='http://example.org/')
            ctx = context(link, in_m, out_m, base=SCHEMA_ORG)
            func(ctx)
    
    assert out_m.size() == 7
    assert next(out_m.match('http://example.org/book/catcher-in-the-rye', VTYPE_REL))[TARGET] == BOOK_TYPE
    assert next(out_m.match('http://example.org/book/catcher-in-the-rye', I(iri.absolutize('name', SCHEMA_ORG))))[TARGET] == 'The Catcher in the Rye'

    #logging.debug('Result: {0}'.format(repr(link)))
    #assert results == None, "Boo! "

if __name__ == '__main__':
    raise SystemExit("use py.test")
