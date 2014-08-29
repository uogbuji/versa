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

from datachef.ids import simple_hashstring, FROM_EMPTY_HASH

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
    properties = properties or {}
    newlinkset = []
    #Just work with the first provided statement, for now
    (o, r, t) = ctx.linkset[0]
    if unique:
        objid = hashidgen.send(unique(ctx))
    else:
        objid = next(hashidgen)
    if objid != FROM_EMPTY_HASH:
        newlinkset.append((I(o), I(iri.absolutize(new_rel, ctx.base)), I(objid), {}))
        if objid not in existing_ids:
            if typ: newlinkset.append((I(objid), VTYPE_REL, I(iri.absolutize(typ, ctx.base)), {}))
            for k, v in properties.items():
                if callable(v):
                    v = v(ctx)
                newlinkset.append((I(objid), I(iri.absolutize(k, ctx.base)), v, {}))
    return newlinkset


def inverse_materialize(ctx, hashidgen=None, existing_ids=None, unique=None, typ=None, new_rel=None, properties=None):
    '''
    Create a new resource related to the origin
    '''
    properties = properties or {}
    newlinkset = []
    #Just work with the first provided statement, for now
    (o, r, t) = ctx.linkset[0]
    if unique:
        objid = hashidgen.send(unique(ctx))
    else:
        objid = next(hashidgen)
    if objid != FROM_EMPTY_HASH:
        newlinkset.append((I(objid), I(iri.absolutize(new_rel, ctx.base)), I(o), {}))
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
        link = ctx.linkset[0]
        gdict = {
            'origin': resource(ctx),
            #'origin': resource(link[ORIGIN], ctx),
            'target': link[TARGET],
        }
        result = eval(pycmds, gdict)
        return result
    return _run

