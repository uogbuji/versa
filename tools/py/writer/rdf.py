#versa.writer.rdfs
"""
Render a Versa vocab model as RDFS
"""

import re
import sys
import os
from itertools import islice
import datetime

import rdflib
from rdflib import URIRef, Literal
from amara3 import iri

from rdflib import URIRef, Literal, RDF
from rdflib import BNode

from versa import I, VERSA_BASEIRI, ORIGIN, RELATIONSHIP, TARGET
from versa.driver import memory
from versa import VERSA_BASEIRI
from versa.reader.md import from_markdown

#Represent the blank node RDF-ism
class mock_bnode(I):
    '''
    Must be initialized with a string. Just use ''
    '''
    def __new__(cls, _):
        new_id = '__VERSABLANKNODE__' + str(hash(datetime.datetime.now().isoformat())) #str(id(object())) #Fake an ID
        self = super(mock_bnode, cls).__new__(cls, new_id)
        return self


VERSA_TYPE = I(VERSA_BASEIRI + 'type')
VNS = rdflib.Namespace(VERSA_BASEIRI)

RDF_NS = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'
RDFS_NS = 'http://www.w3.org/2000/01/rdf-schema#'

RDF_TYPE = I(RDF_NS + 'type')


def prep(s, p, o):
    '''
    Prepare a triple for rdflib
    '''
    def bnode_check(r):
        return isinstance(r, mock_bnode) or r.startswith('VERSABLANKNODE_')

    s = BNode() if bnode_check(s) else URIRef(s)
    p = URIRef(p)
    o = BNode() if bnode_check(o) else (URIRef(o) if isinstance(o, I) else Literal(o))
    return s, p, o


def prep(s, p, o):
    '''
    Prepare a triple for rdflib
    '''
    def bnode_check(r):
        return isinstance(r, mock_bnode) or r.startswith('VERSABLANKNODE_')

    s = URIRef(s)
    p = URIRef(p)
    o = URIRef(o) if isinstance(o, I) else Literal(o)
    return s, p, o


def fixup_jsonld(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, dict) and '@value' in v:
                obj[k] = v['@value']
            if isinstance(v, list):
                objlist = []
                for i in v:
                    if isinstance(i, dict) and '@value' in i:
                        objlist.append(i['@value'])
                obj[k] = objlist
            else:
                fixup_jsonld(v)
    elif isinstance(obj, list):
        for i in obj:
            fixup_jsonld(i)
    return

