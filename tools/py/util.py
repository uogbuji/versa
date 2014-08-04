#versa.util
'''
Utilities to help deal with constructs expressed in Versa
'''

#from amara.lib import iri
#import logging

import json

from versa import ORIGIN, RELATIONSHIP, TARGET, VERSA_BASEIRI
from versa import init_localization
init_localization()

def versa_list_to_pylist(m, vlistid):
    return [ s[TARGET] for s in m.match(vlistid, VERSA_BASEIRI + 'item') ]


def simple_lookup(m, orig, rel):
    stmts = list(m.match(orig, rel))
    return stmts[0][TARGET] if stmts else None


def transitive_closure(m, orig, rel):
    '''
    Generate the closure over a transitive relationship in depth-first fashion
    '''
    #FIXME: Broken for now
    stmts = list(m.match(orig, rel))
    for stmt in stmts:
        yield stmt[0][TARGET]
        yield from transitive_closure(m, target, rel)


def all_origins(m):
    '''
    Generate all unique statement origins in the given model
    '''
    seen = set()
    for stmt in m.match():
        origin = stmt[ORIGIN]
        if origin not in seen:
            seen.add(origin)
            yield origin


def jsonload(model, fp):
    '''
    Load Versa model dumped into JSON form
    '''
    dumped_list = json.load(fp)
    for stmt in dumped_list:
        sid, (s, p, o, a) = stmt
        model.add(s, p, o, a)
    return


def jsondump(model, fp):
    '''
    Dump Versa model into JSON form
    '''
    fp.write('[')
    stmts_ser = []
    for stmt in model:
        stmts_ser.append(json.dumps(stmt))
    fp.write(',\n'.join(stmts_ser))
    fp.write(']')

