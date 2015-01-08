'''
Framework for expressing transforms from one pattern of Versa links to another
This is especially useful if you've used a tool to extract Versa from some data
source but would like to tweak the interpretation of that data. It's also useful
for mapping from one vocabulary to another.

The concept is similar to XProc (http://en.wikipedia.org/wiki/XProc). You define
the overall transform in terms of transform steps or stages, implemented as
Python functions. Each function can have inputs, which might be simple Versa
scalars or even functions in themselves. The outputs are Versa scalars.

There is also a shared environment across the steps, called the context (`versa.context`).
The context includes a resource which is considered the origin for purposes
of linking, an input Versa model considered to be an overall input to the transform
and an output Versa model considered to be an overall output.
'''

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

try:
    from datachef.ids import simple_hashstring, FROM_EMPTY_HASH
except ImportError:
    #datachef not installed, but proceed anyway
    #Note: if so they must be providing a different hash key generator, so we might want to provide a way to override this marker
    FROM_EMPTY_HASH = 'AAAAAAAA'

VTYPE_REL = I(iri.absolutize('type', VERSA_BASEIRI))


#FIXME: Use __all__

class resource(object):
    def __init__(self, ctx):
        self._origin = ctx.current_link[ORIGIN]
        self._input_model = ctx.input_model
        self._base = ctx.base
        return

    def follow(self, rel):
        return simple_lookup(self._input_model, self._origin, I(iri.absolutize(rel, self._base)))


#def vtype():
#    return TYPE_REL


def origin(ctx):
    return resource(ctx.current_link[ORIGIN], ctx.input_model)


def res(arg):
    '''
    Render the argument as an IRI reference
    '''
    def _res(ctx):
        _arg = arg(ctx) if callable(arg) else arg
        return I(arg)
    return _res


#Functions that take a prototype link set and generates a transformed link set

def materialize(ctx, hashidgen=None, existing_ids=None, unique=None, typ=None, new_rel=None, properties=None):
    '''
    Create a new resource related to the origin, with optional, additional links created in the output model
    '''
    properties = properties or {}
    (o, r, t, a) = ctx.current_link
    if unique:
        objid = hashidgen.send(unique(ctx))
    else:
        objid = next(hashidgen)
    if objid != I(iri.absolutize(FROM_EMPTY_HASH, ctx.base)):
        ctx.output_model.add(I(o), I(iri.absolutize(new_rel, ctx.base)), I(objid), {})
        if objid not in existing_ids:
            if typ: ctx.output_model.add(I(objid), VTYPE_REL, I(iri.absolutize(typ, ctx.base)), {})
            for k, v in properties.items():
                if callable(v):
                    v = v(ctx)
                ctx.output_model.add(I(objid), I(iri.absolutize(k, ctx.base)), v, {})
    return objid


def inverse_materialize(ctx, hashidgen=None, existing_ids=None, unique=None, typ=None, new_rel=None, properties=None):
    '''
    Create a new resource related to the origin
    '''
    properties = properties or {}
    #Just work with the first provided statement, for now
    (o, r, t, a) = ctx.current_link
    if unique:
        objid = hashidgen.send(unique(ctx))
    else:
        objid = next(hashidgen)
    if objid != I(iri.absolutize(FROM_EMPTY_HASH, ctx.base)):
        ctx.output_model.add(I(objid), I(iri.absolutize(new_rel, ctx.base)), I(o), {})
        if objid not in existing_ids:
            if typ: ctx.output_model.add(I(objid), VTYPE_REL, I(iri.absolutize(typ, ctx.base)), {})
            for k, v in properties.items():
                if callable(v):
                    v = v(ctx)
                ctx.output_model.add(I(objid), I(iri.absolutize(k, ctx.base)), v, {})
    return objid


def relabel(ctx, new_rel=None, res=False):
    '''
    Update the label of the relationship to be added to the link space
    '''
    #Just work with the first provided statement, for now
    (o, r, t, a) = ctx.current_link
    if res: t = I(t)
    ctx.output_model.add(I(o), I(iri.absolutize(new_rel, ctx.base)), t, {})
    return None


def discard(ctx):
    #No op. Just ignore the proposed link set
    return None


def run(pycmds):
    def _run(ctx):
        gdict = {
            'origin': resource(ctx),
            #'origin': resource(link[ORIGIN], ctx),
            'target': ctx.current_link[TARGET],
        }
        result = eval(pycmds, gdict)
        return result
    return _run

