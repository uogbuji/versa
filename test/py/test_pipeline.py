'''
Structured Data Validators Structured Data Linter http://linter.structured-data.org/ Open Graph Debugger https://developers.facebook.com/tools/debug Schema Validator http://validator.nu/ Twitter Card Preview https://dev.twitter.com/docs/cards/preview Google Structured Data Testing Tool http://www.google.com/webmasters/tools/richsnippets
'''

import logging
import functools

from versa import I, VERSA_BASEIRI, ORIGIN, RELATIONSHIP, TARGET
from versa.driver import memory
from versa.pipeline import *
from versa.contrib.datachefids import idgen, FROM_EMPTY_HASH
from versa.util import jsondump, jsonload


#Move to a test utils module
import os, inspect
def module_path(local_function):
    '''
    returns the module path without the use of __file__.  Requires a function defined 
    locally in the module.
    from http://stackoverflow.com/questions/729583/getting-file-path-of-imported-module
    '''
    return os.path.abspath(inspect.getsourcefile(local_function))

#hack to locate test resource (data) files regardless of from where nose was run
RESOURCEPATH = os.path.normpath(os.path.join(module_path(lambda _: None), '../../resource/'))

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

def test_pipeline1():
    idg = idgen(EXAMPLE_ORG)
    existing_ids = set()

    TRANSFORMS = {
        'id': discard(),
        'title': rename(rel='name'),
        'author': materialize('Person', rel='author', unique=run('target'), links={'name': run('target')}),
        'link': rename(rel='link'),
        'cover': rename(rel='cover'),
    }
    #'type': functools.partial(relabel, rel=VTYPE_REL),

    out_m = memory.connection(baseiri='http://example.org/')

    rid = SIMPLE_BOOK['id']
    out_m.add(rid, VTYPE_REL, BOOK_TYPE)
    for k, v in SIMPLE_BOOK.items():
        link = (rid, k, v, {})
        func = TRANSFORMS.get(k)
        if func:
            in_m = memory.connection(baseiri='http://example.org/')
            ctx = context(link, in_m, out_m, base=SCHEMA_ORG, idgen=idg)
            func(ctx)
    
    assert out_m.size() == 7, repr(out_m)
    assert next(out_m.match('http://example.org/book/catcher-in-the-rye', VTYPE_REL))[TARGET] == BOOK_TYPE
    assert next(out_m.match('http://example.org/book/catcher-in-the-rye', I(iri.absolutize('name', SCHEMA_ORG))))[TARGET] == 'The Catcher in the Rye'


def test_pipeline2():
    idg = idgen(EXAMPLE_ORG)
    existing_ids = set()

    TRANSFORMS = [
        ('id', discard()),
        ('title', rename(rel='name')),
        #For testing; doesn't make much sense, really, otherwise 
        ('author', materialize('Person', rel='author', unique=run('target'), links={'name': run('target')}, inverse=True)),
        ('link', rename(rel='link')),
        ('cover', rename(rel='cover')),
    ]

    out_m = memory.connection(baseiri='http://example.org/')

    rid = SIMPLE_BOOK['id']
    out_m.add(rid, VTYPE_REL, BOOK_TYPE)
    for k, v in SIMPLE_BOOK.items():
        link = (rid, k, v, {})
        for rel, func in TRANSFORMS:
            if k == rel:
                in_m = memory.connection(baseiri='http://example.org/')
                ctx = context(link, in_m, out_m, base=SCHEMA_ORG, idgen=idg)
                func(ctx)
    
    assert out_m.size() == 7, repr(out_m)
    assert next(out_m.match('http://example.org/book/catcher-in-the-rye', VTYPE_REL))[TARGET] == BOOK_TYPE
    assert next(out_m.match('http://example.org/book/catcher-in-the-rye', I(iri.absolutize('name', SCHEMA_ORG))))[TARGET] == 'The Catcher in the Rye'
    author = next(out_m.match(None, I(iri.absolutize('author', SCHEMA_ORG))), 'http://example.org/book/catcher-in-the-rye')[ORIGIN]
    assert next(out_m.match(author, I(iri.absolutize('name', SCHEMA_ORG))), None)[TARGET] == 'J.D. Salinger'


if __name__ == '__main__':
    raise SystemExit("use py.test")
