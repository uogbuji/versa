#versa.writer.ntriples
"""
Render a Versa vocab model as NTriples

https://www.w3.org/TR/rdf-testcases/#ntriples
"""

from amara3 import iri

from versa import I, VERSA_BASEIRI, ORIGIN, RELATIONSHIP, TARGET
from versa.terms import VERSA_BASEIRI, RDF_NS, RDFS_NS, VERSA_TYPE_REL, RDF_TYPE_REL
from versa.driver import memory
from versa import VERSA_BASEIRI

RESOURCE_MAPPING = {
    I(VERSA_BASEIRI + 'Resource'): I(RDFS_NAMESPACE + 'Class'),
    I(VERSA_BASEIRI + 'Property'): I(RDF_NAMESPACE + 'Property'),
    I(VERSA_BASEIRI + 'description'): I(RDFS_NAMESPACE + 'comment'),
    I(VERSA_BASEIRI + 'label'): I(RDFS_NAMESPACE + 'label'),
}


def strconv(item):
    '''
    Prepare a statement into a triple ready for rdflib
    '''
    if isinstance(item, I):
        return('<' + str(item) + '>')
    else:
        return('"' + str(item) + '"')


def write(models, out=None, base=None, logger=logging):
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

