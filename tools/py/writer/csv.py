#versa.writer.ntriples
"""
Render a Versa vocab model as CSV, using a given set of ruls to flatten

Import as:

from versa.writer import csv as vcsv

"""

import logging
import operator

from amara3 import iri

from versa import I, VERSA_BASEIRI, ORIGIN, RELATIONSHIP, TARGET
from versa.terms import VERSA_BASEIRI, RDF_NS, RDFS_NS, VERSA_TYPE_REL, RDF_TYPE_REL
from versa.util import all_origins, lookup, resourcetypes


def fromlist(l):
    return '|'.join(l)


def omap(m):
    '''
    Create a nested mapping from origin to property to values/attributes covering an entire Versa model
    '''
    om = {}
    for s, p, o, a in m.match():
        om.setdefault(s, {})
        om[s].setdefault(p, []).append((o, a))
    return om
        

def write(models, csvout, rulelist, write_header, base=None, logger=logging):
    '''
    models - one or more input Versa models from which output is generated.
    '''
    properties = [ k for (k, v) in rulelist ]
    numprops = len(properties)
    headers = [ v for (k, v) in rulelist ]
    if write_header:
        csvout.writerow(['id', 'type'] + headers)

    rules = { k: v for (k, v) in rulelist }

    if not isinstance(models, list): models = [models]
    for m in models:
        mapped = omap(m)
        for o, props in mapped.items():
            rtypes = list(map(operator.itemgetter(0), props.get(RDF_TYPE_REL, [])))
            if not rtypes: continue
            #print('RES TYPES:', rtypes)
            row = [o, fromlist(rtypes)] + [None] * numprops
            for ix, p in enumerate(properties):
                v = list(map(operator.itemgetter(0), props.get(p, [])))
                if v:
                    row[ix + 2] = fromlist(v)
                    csvout.writerow(row)

    return


def IGNORE():
    if False:
        for rid in all_origins(m):
            #print(rid, list(m.match(rid, RDF_TYPE_REL)))
            rtypes = list(lookup(m, rid, RDF_TYPE_REL))
            #if not rtypes: rtypes = list(lookup(m, rid, VERSA_TYPE_REL))
            #Ignore if no type
            if not rtypes: continue
            row = [rid, fromlist(rtypes)] + [None] * numprops
            for ix, p in enumerate(properties):
                #v = next(lookup(m, rid, RDF_TYPE_REL), None)
                v = list(lookup(m, rid, p))
                if v:
                    row[ix + 2] = fromlist(v)
                    csvout.writerow(row)
            
    return

