'''
Structured Data Validators Structured Data Linter http://linter.structured-data.org/ Open Graph Debugger https://developers.facebook.com/tools/debug Schema Validator http://validator.nu/ Twitter Card Preview https://dev.twitter.com/docs/cards/preview Google Structured Data Testing Tool http://www.google.com/webmasters/tools/richsnippets
'''

import logging
import functools

import pytest

from amara3 import iri
from versa import I, VERSA_BASEIRI, ORIGIN, RELATIONSHIP, TARGET
from versa.driver import memory
from versa.pipeline import *
from versa.contrib.datachefids import idgen, FROM_EMPTY_64BIT_HASH
from versa.util import jsondump, jsonload


# FIXME: Move to a test utils module
import os, inspect
def module_path(local_function):
    '''
    returns the module path without the use of __file__.  Requires a function defined 
    locally in the module.
    from http://stackoverflow.com/questions/729583/getting-file-path-of-imported-module
    '''
    return os.path.abspath(inspect.getsourcefile(local_function))

# Hack to locate test resource (data) files regardless of from where nose was run
RESOURCEPATH = os.path.normpath(os.path.join(module_path(lambda _: None), '../../resource/'))

SIMPLE_BOOK = {
    'id': 'http://example.org/book/catcher-in-the-rye',
    'title': 'The Catcher in the Rye',
    'type': 'http://ogp.me/ns/books#books.book',
    'link': 'https://en.wikipedia.org/wiki/The_Catcher_in_the_Rye',
    'author': 'J.D. Salinger',
    'cover': 'http://example.org/book/catcher-in-the-rye-book-cover.jpg',
}

BOOK_TYPE = 'http://schema.org/Book'
SCH = SCHEMA_ORG = 'http://schema.org/'
EXAMPLE_ORG = 'http://example.org/'

BOOK_ID = 'http://example.org/book/catcher-in-the-rye'
SCHEMA_NAME = I(iri.absolutize('name', SCHEMA_ORG))
SCHEMA_AUTHOR = I(iri.absolutize('author', SCHEMA_ORG))
XXX_WROTE = 'http://example.org/wrote'

# Not really needed.
IN_M = memory.connection(baseiri='http://example.org/')

BOOK_CASES = []

transforms = {
    'id': ignore(),
    'title': link(rel=SCH+'name'),
    'author': materialize(SCH+'Person', rel=SCH+'author', unique=[(SCH+'name', target())], links=[(SCH+'name', target())]),
    'link': link(rel=SCH+'link'),
    'cover': link(rel=SCH+'cover'),
}

def asserter(out_m):
    assert out_m.size() == 7, repr(out_m)
    assert next(out_m.match(BOOK_ID, VTYPE_REL))[TARGET] == BOOK_TYPE
    assert next(out_m.match(BOOK_ID, SCHEMA_NAME))[TARGET] == 'The Catcher in the Rye'
    author = next(out_m.match(BOOK_ID, SCHEMA_AUTHOR, None))[TARGET]
    assert next(out_m.match(author, SCHEMA_NAME), None)[TARGET] == 'J.D. Salinger'

BOOK_CASES.append(('simple1', transforms, asserter))

# Inverted form
transforms = {
    'id': ignore(),
    'title': link(rel=SCH+'name'),
    #For testing; doesn't make much sense, really, otherwise 
    'author': link(
        origin=materialize(
            SCH+'Person',
            unique=[(SCH+'name', target())],
            links=[(SCH+'name', target())],
            attach=False),
        rel=XXX_WROTE,
        target=origin()),
    'link': link(rel=SCH+'link'),
    'cover': link(rel=SCH+'cover'),
}

def asserter(out_m):
    #import pprint; pprint.pprint(out_m)
    assert out_m.size() == 7, repr(out_m)
    assert next(out_m.match(BOOK_ID, VTYPE_REL))[TARGET] == BOOK_TYPE
    assert next(out_m.match(BOOK_ID, SCHEMA_NAME))[TARGET] == 'The Catcher in the Rye'
    author = next(out_m.match(None, XXX_WROTE), BOOK_ID)[ORIGIN]
    assert next(out_m.match(author, SCHEMA_NAME), None)[TARGET] == 'J.D. Salinger'


BOOK_CASES.append(('inverted1', transforms, asserter))

#    'author': link(rel=SCH+'author') materialize(SCH+'Person', unique=[(SCH+'name', run('target'))], links=[(SCH+'name', target()), (None, SCH+'wrote', origin())]),


@pytest.mark.parametrize('label,transforms,asserter', BOOK_CASES)
def test_book_cases(label, transforms, asserter):
    idg = idgen(EXAMPLE_ORG)
    existing_ids = set()
    out_m = memory.connection(baseiri='http://example.org/')

    rid = SIMPLE_BOOK['id']
    out_m.add(rid, VTYPE_REL, BOOK_TYPE)

    for k, v in SIMPLE_BOOK.items():
        ctxlink = (rid, k, v, {})
        func = transforms.get(k)
        if func:
            ctx = context(ctxlink, IN_M, out_m, base=SCHEMA_ORG, idgen=idg)
            func(ctx)

    asserter(out_m)


if __name__ == '__main__':
    raise SystemExit("use py.test")
