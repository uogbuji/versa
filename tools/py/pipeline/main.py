#versa.pipeline
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

#FIXME: Use __all__

import json
import itertools
import functools
import logging
#from enum import Enum #https://docs.python.org/3.4/library/enum.html
from collections import defaultdict, OrderedDict
from types import GeneratorType

#import amara3
from amara3 import iri
#from amara3.util import coroutine

from versa import I, VERSA_BASEIRI, ORIGIN, RELATIONSHIP, TARGET, ATTRIBUTES, VTYPE_REL
from versa import util
from versa.util import simple_lookup, OrderedJsonEncoder
from versa.driver import memory

from versa.contrib.datachefids import idgen as default_idgen, FROM_EMPTY_64BIT_HASH


class context(object):
    #Default way to create a model for the transform output, if one is not provided
    transform_factory = memory.connection

    #Note: origin was eliminated; not really needed since the origin of current_link can be used
    def __init__(self, current_link, input_model, output_model=None, base=None, variables=None, extras=None, idgen=None, existing_ids=None):
        '''
        current_link - one of the links in input_model, a key reference for the transform
        input_model - Versa model treated as overall input to the transform
        output_model - Versa model treated as overall output to the transform; if None an empty model is created
        base - reference base IRI, e.g. used to resolve created resources
        '''
        self.current_link = current_link
        self.input_model = input_model
        self.output_model = output_model or context.transform_factory()
        self.base = base
        self.variables = variables or {}
        self.extras = extras or {}
        #FIXME: idgen requires a base IRI. Think this over.
        self.idgen = idgen or default_idgen(base)
        self.existing_ids = existing_ids or set()

    def copy(self, current_link=None, input_model=None, output_model=None, base=None, variables=None, extras=None, idgen=None, existing_ids=None):
        current_link = current_link if current_link else self.current_link
        input_model = input_model if input_model else self.input_model
        output_model = output_model if output_model else self.output_model
        base = base if base else self.base
        variables = variables if variables else self.variables
        extras = extras if extras else self.extras
        idgen = idgen if idgen else self.idgen
        existing_ids = existing_ids if existing_ids else self.existing_ids
        return context(current_link=current_link, input_model=input_model, output_model=output_model, base=base, extras=extras, idgen=idgen, existing_ids=existing_ids)


def materialize_entity(ctx, etype, unique=None):
    '''
    Low-level routine for creating a BIBFRAME resource. Takes the entity (resource) type and a data mapping
    according to the resource type. Implements the Libhub Resource Hash Convention
    As a convenience, if a vocabulary base is provided in the context, concatenate it to etype and the data keys

    ctx - context information governing creation of the new entity
    etype - type IRI for th enew entity
    unique - list of key/value tuples of data to use in generating its unique ID, or None in which case one is just randomly generated
    '''
    params = {}
    if ctx.base:
        etype = ctx.base + etype

    unique_computed = []
    for k, v in unique:
        k = k if iri.is_absolute(k) else iri.absolutize(k, ctx.base)
        v = v(ctx) if callable(v) else v
        unique_computed.append((k, v))

    if unique_computed:
        plaintext = json.dumps([etype, unique_computed], cls=OrderedJsonEncoder)
        eid = ctx.idgen.send(plaintext)
    else:
        #We only have a type; no other distinguishing data. Generate a random hash
        eid = next(ctx.idgen)
    return eid


def create_resource(output_model, rtype, unique, links, existing_ids=None, id_helper=None):
    '''
    General-purpose routine to create a new resource in the output model, based on data provided

    output_model    - Versa connection to model to be updated
    rtype           - Type IRI for the new resource, set with Versa type
    unique          - list of key/value pairs for determining a unique hash for the new resource
    links           - list of key/value pairs for setting properties on the new resource
    id_helper       - If a string, a base URL for the generatd ID. If callable, a function used to return the entity. If None, set a default good enough for testing.
    existing_ids    - set of existing IDs to not recreate, or None, in which case a new resource will always be created
    '''
    if isinstance(id_helper, str):
        idg = idgen(id_helper)
    elif isinstance(id_helper, GeneratorType):
        idg = id_helper
    elif id_helper is None:
        idg = default_idgen(None)
    else:
        #FIXME: G11N
        raise ValueError('id_helper must be string (URL), callable or None')
    ctx = context(None, None, output_model, base=None, idgen=idg, existing_ids=existing_ids, extras=None)
    rid = I(materialize_entity(ctx, rtype, unique=unique))
    if existing_ids is not None:
        if rid in existing_ids:
            return (False, rid)
        existing_ids.add(rid)
    output_model.add(rid, VTYPE_REL, rtype)
    for r, t in links:
        output_model.add(rid, r, t)
    return (True, rid)

#iritype = object()
#force_iritype = object()

