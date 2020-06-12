#versa.writer.rdfs
"""
Render a Versa vocab model as RDFS
"""

import re
import sys
import os
import glob
import time
from itertools import islice
import logging

import rdflib
from rdflib import URIRef, Literal
from amara3 import iri

from rdflib import URIRef, Literal, RDF

from versa import I, VERSA_BASEIRI, ORIGIN, RELATIONSHIP, TARGET
from versa.driver import memory
from versa import VERSA_BASEIRI
from versa.reader.md import from_markdown

TYPE_REL = I(iri.absolutize('type', VERSA_BASEIRI))
VNS = rdflib.Namespace(VERSA_BASEIRI)

RDF_NAMESPACE = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'
RDFS_NAMESPACE = 'http://www.w3.org/2000/01/rdf-schema#'

RESOURCE_MAPPING = {
    I(VERSA_BASEIRI + 'Resource'): I(RDFS_NAMESPACE + 'Class'),
    I(VERSA_BASEIRI + 'Property'): I(RDF_NAMESPACE + 'Property'),
    I(VERSA_BASEIRI + 'description'): I(RDFS_NAMESPACE + 'comment'),
    I(VERSA_BASEIRI + 'label'): I(RDFS_NAMESPACE + 'label'),
}


def prep(link):
    '''
    Prepare a statement into a triple ready for rdflib
    '''
    s, p, o = link[:3]
    s = URIRef(s)
    p = URIRef(p)
    o = URIRef(o) if isinstance(o, I) else Literal(o)
    return s, p, o


def process(source, target, rdfsonly, base=None, logger=logging):
    '''
    Prepare a statement into a triple ready for rdflib graph

    '''
    for link in source.match():
        s, p, o = link[:3]
        #SKip docheader statements
        if s == (base or '') + '@docheader': continue
        if p in RESOURCE_MAPPING: p = RESOURCE_MAPPING[p]
        if o in RESOURCE_MAPPING: o = RESOURCE_MAPPING[o]
        if p == VERSA_BASEIRI + 'refines':
            tlinks = list(source.match(s, TYPE_REL))
            if tlinks:
                if tlinks[0][TARGET] == VERSA_BASEIRI + 'Resource':
                    p = I(RDFS_NAMESPACE + 'subClassOf')
                elif tlinks[0][TARGET] == VERSA_BASEIRI + 'Property':
                    p = I(RDFS_NAMESPACE + 'subPropertyOf')
        if p == VERSA_BASEIRI + 'properties':
            suri = I(iri.absolutize(s, base)) if base else s
            target.add((URIRef(o), URIRef(RDFS_NAMESPACE + 'domain'), URIRef(suri)))
            continue
        if p == VERSA_BASEIRI + 'value':
            if o not in ['Literal', 'IRI']:
                ouri = I(iri.absolutize(o, base)) if base else o
                target.add((URIRef(s), URIRef(RDFS_NAMESPACE + 'range'), URIRef(ouri)))
                continue
        s = URIRef(s)
        #Translate v:type to rdf:type
        p = RDF.type if p == TYPE_REL else URIRef(p)
        o = URIRef(o) if isinstance(o, I) else Literal(o)
        if not rdfsonly or p.startswith(RDF_NAMESPACE) or p.startswith(RDFS_NAMESPACE):
            target.add((s, p, o))
    return


def write(model, base=None, graph=None, rdfsonly=False, prefixes=None, logger=logging):
    '''
    See the command line help
    '''
    prefixes = prefixes or {}
    g = graph or rdflib.Graph()
    #g.bind('bf', BFNS)
    #g.bind('bfc', BFCNS)
    #g.bind('bfd', BFDNS)
    g.bind('v', VNS)
    for k, v in prefixes.items():
        g.bind(k, v)
    base_out = model.base
    process(model, g, rdfsonly, base=base_out, logger=logger)
    return g
