# versa.serial.util

from versa import I, VERSA_BASEIRI, ORIGIN, RELATIONSHIP, TARGET, ATTRIBUTES

#Helper routines for reader code

def statement_prep(link):
    '''
    Prepare a statement into a triple ready for rdflib
    '''
    from rdflib import URIRef, Literal
    from rdflib import BNode
    s, p, o = link[:3]
    if not isinstance(s, BNode): s = URIRef(s)
    p = URIRef(p)
    if not isinstance(o, BNode): o = URIRef(o) if isinstance(o, I) else Literal(o)
    return s, p, o


#Helper coroutines for reader code

#Coroutine to keep triples raw as they are
def dumb_triples(output):
    while True:
        triple = yield
        output.append(triple)
    return


#Coroutine to convert triples to RDF
def rdfize(g):
    while True:
        triple = yield
        (s, p, o) = statement_prep(triple)
        g.add((s, p, o))
    return


#Coroutine to add Versa links
def versalinks(model):
    while True:
        params = yield
        if len(params) == 4:
            s, p, o, a = params
        else:
            s, p, o = params
            a = {}
        model.add(s, p, o, a)
    return

