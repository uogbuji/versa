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
    links = list(m.match(orig, rel))
    return links[0][TARGET] if links else None


def transitive_closure(m, orig, rel):
    '''
    Generate the closure over a transitive relationship in depth-first fashion
    '''
    #FIXME: Broken for now
    links = list(m.match(orig, rel))
    for link in links:
        yield link[0][TARGET]
        yield from transitive_closure(m, target, rel)


def all_origins(m):
    '''
    Generate all unique statement origins in the given model
    '''
    seen = set()
    for link in m.match():
        origin = link[ORIGIN]
        if origin not in seen:
            seen.add(origin)
            yield origin


def jsonload(model, fp):
    '''
    Load Versa model dumped into JSON form
    '''
    dumped_list = json.load(fp)
    for link in dumped_list:
        sid, (s, p, o, a) = link
        model.add(s, p, o, a)
    return


def jsondump(model, fp):
    '''
    Dump Versa model into JSON form
    '''
    fp.write('[')
    links_ser = []
    for link in model:
        links_ser.append(json.dumps(link))
    fp.write(',\n'.join(links_ser))
    fp.write(']')

