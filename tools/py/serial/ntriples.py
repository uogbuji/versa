# versa.serial.ntriples
"""
Serialize and deserialize between a Versa model and NTriples

https://www.w3.org/TR/rdf-testcases/#ntriples
"""

import re

from amara3 import iri

from versa import I, VERSA_BASEIRI, ORIGIN, RELATIONSHIP, TARGET
from versa.terms import VERSA_BASEIRI, RDF_NS, RDFS_NS, VERSA_TYPE_REL, RDF_TYPE_REL
from versa.driver.memory import newmodel

RESOURCE_MAPPING = {
    VERSA_BASEIRI('Resource'): RDFS_NS('Class'),
    VERSA_BASEIRI('Property'): RDF_NS('Property'),
    VERSA_BASEIRI('description'): RDFS_NS('comment'),
    VERSA_BASEIRI('label'): RDFS_NS('label'),
}


__all__ = ['parse', 'parse_iter', 'write',
    # Non-standard
]


NT_LINE_PAT = re.compile(r'^((<([^>]+)>)|(_:\w+))\s+<([^>]+)>\s+((<([^>]+)>)|"([^"]*)"|(_:\w+))\s+\.\s*')

def parse(nt, model, encoding='utf-8'):
    '''
    >>> 
    '''
    nt_gen = nt
    if isinstance(nt, str):
        nt_gen = nt.splitlines()
    for line in nt_gen:
        m = NT_LINE_PAT.match(line.strip())
        if m:
            #print(list(enumerate(m.groups())))
            _, s, s_iri, s_blank, p_iri, o, _, o_iri, o_str, o_blank = tuple(m.groups())
            #print((s, s_iri, s_blank, p_iri, o, o_iri, o_str, o_blank))

            if o_blank or s_blank:
                raise NotImplementedError('Blank nodes not yet implemented')

            model.add(I(s_iri), I(p_iri), I(o_iri) if o_iri else o_str, {})


def parse_iter(nt_fp, model_fact=newmodel):
    raise NotImplementedError


def strconv(item):
    '''
    Prepare a statement into a triple ready for rdflib
    '''
    if isinstance(item, I):
        return('<' + str(item) + '>')
    else:
        return('"' + str(item) + '"')


def write(models, out=None, base=None):
    '''
    models - one or more input Versa models from which output is generated.
    '''
    assert out is not None #Output stream required
    if not isinstance(models, list): models = [models]
    for m in models:
        for link in m.match():
            s, p, o = link[:3]
            #Skip docheader statements
            if s == (base or '') + '@docheader': continue
            if p in RESOURCE_MAPPING: p = RESOURCE_MAPPING[p]
            if o in RESOURCE_MAPPING: o = RESOURCE_MAPPING[o]
            
            if p == VERSA_TYPE_REL: p = RDF_TYPE_REL
            print(strconv(s), strconv(p), strconv(o), '.', file=out)
    return

