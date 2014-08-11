import itertools
import functools
import logging

#import amara3
from amara3 import iri
#from amara3.util import coroutine

from versa import I, VERSA_BASEIRI, ORIGIN, RELATIONSHIP, TARGET
from versa import util
from versa.util import simple_lookup
from versa import context

from datachef.ids import simple_hashstring

VTYPE_REL = I(iri.absolutize('type', VERSA_BASEIRI))

#FIXME: Use __all__

class resource(object):
    def __init__(self, ctx):
        self._origin = ctx.origin
        self._linkspace = ctx.linkspace
        self._base = ctx.base
        return

    def follow(self, rel):
        return simple_lookup(self._linkspace, self._origin, I(iri.absolutize(rel, self._base)))


#def vtype():
#    return TYPE_REL


def origin(ctx):
    return resource(ctx.linkset[0][ORIGIN], ctx.linkspace)

#Functions that take a prototype link set and generates a transformed link set

def materialize(ctx, hashidgen=None, existing_ids=None, unique=None, typ=None, new_rel=None, properties=None):
    '''
    Create a new resource related to the origin
    '''
    newlinkset = []
    #Just work with the first provided statement, for now
    (o, r, t) = ctx.linkset[0]
    if unique:
        objid = hashidgen.send(unique(ctx))
    else:
        objid = next(hashidgen)
    newlinkset.append((I(o), I(iri.absolutize(new_rel, ctx.base)), I(objid), {}))
    if objid not in existing_ids:
        if typ: newlinkset.append((I(objid), VTYPE_REL, I(iri.absolutize(typ, ctx.base)), {}))
        for k, v in properties.items():
            if callable(v):
                v = v(ctx)
            newlinkset.append((I(objid), I(iri.absolutize(k, ctx.base)), v, {}))
    return newlinkset


def relabel(ctx, new_rel=None):
    '''
    Update the label of the relationship to be added to the link space
    '''
    newlinkset = []
    #Just work with the first provided statement, for now
    (o, r, t) = ctx.linkset[0]
    newlinkset.append((I(o), I(iri.absolutize(new_rel, ctx.base)), t, {}))
    return newlinkset


def discard(ctx):
    #No op. Just ignore the proposed link set
    return []


def run(pycmds):
    def _run(ctx):
        stmt = ctx.linkset[0]
        gdict = {
            'origin': resource(ctx),
            #'origin': resource(stmt[ORIGIN], ctx),
            'target': stmt[TARGET],
        }
        result = eval(pycmds, gdict)
        return result
    return _run

'''
with open(sys.argv[1], 'rb') as inf:
    existing_ids = []
    indata = dict_from_xls(inf)
    #for row in itertools.islice(indata, None):
    for row in indata:
        for k, v in row.items():
            sid = next(idg)
            stmt = (sid, k, v)
            existing_ids.append(sid)
            func = ACTIONS[k]
            ctx = context(stmt[ORIGIN], [stmt], m, base=BFZ)
            new_stmts = func(context)

            #FIXME: Use add
            for s in new_stmts: m.add(*s)
        print('.', end='')

with open(sys.argv[2], 'wb') as outf:
    rdf.process(m, g, logger=logging)
    outf.write(g.serialize(format="turtle"))
'''