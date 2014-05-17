#versa.util
'''
Utilities to help deal with constructs expressed in Versa
'''

#from amara.lib import iri
#import logging

from versa import ORIGIN, RELATIONSHIP, TARGET, VERSA_BASEIRI
from versa import init_localization
init_localization()

def versa_list_to_pylist(m, vlistid):
    return [ s[TARGET] for s in m.match(vlistid, VERSA_BASEIRI + 'item') ]


def simple_lookup(m, orig, rel):
    stmts = list(m.match(orig, rel))
    return stmts[0][TARGET] if stmts else None


