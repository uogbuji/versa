# versa.pipeline
'''
'''

# FIXME: Use __all__

import json
import itertools
import functools
import logging
# from enum import Enum #https://docs.python.org/3.4/library/enum.html
from collections import defaultdict, OrderedDict
from types import GeneratorType

from amara3 import iri

from versa import I, VERSA_BASEIRI, ORIGIN, RELATIONSHIP, TARGET, ATTRIBUTES, VTYPE_REL
from versa import util
from versa.util import simple_lookup, OrderedJsonEncoder
from versa.driver import memory

from versa.contrib.datachefids import idgen as default_idgen, FROM_EMPTY_64BIT_HASH

# VERSA_PIPELINE_WILDCARD = 'https://github.com/uogbuji/versa/pipeline/wildcard'


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
        # FIXME: idgen requires a base IRI. Think this over.
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
        return context(current_link=current_link, input_model=input_model, output_model=output_model, base=base, variables=variables, extras=extras, idgen=idgen, existing_ids=existing_ids)


def resource_id(etype, unique=None, idgen=default_idgen(None), vocabbase=None):
    '''
    Lowest level routine for generating a, ID value using the Versa comvention
    
    The Versa convention originated as the hash algorithm outlined by
    the Libhub initiative for for BIBFRAME Lite (Libhub Resource Hash Convention).
    https://github.com/zepheira/pybibframe/wiki/From-Records-to-Resources:-the-Library.Link-resource-ID-generation-algorithm
    
    Takes the entity (resource) type and an ordered data mapping.

    etype - type IRI for th enew entity
    unique - list of key/value tuples of data to use in generating its unique ID, or None in which case one is just randomly generated
    defaultvocabbase - for convenience, provided, use to resolve relative etype & data keys

    >>> from versa.pipeline import resource_id
    >>> resource_id("http://schema.org/Person", [("http://schema.org/name", "Jonathan Bruce Postel"), ("http://schema.org/birthDate", "1943-08-06")])
    '-7hP9d_Xo8M'
    >>> resource_id("http://schema.org/Person", [("http://schema.org/name", "Augusta Ada King")])
    'xjgOrUFiw_o'
    '''
    params = {}
    #XXX: Use proper URI normalization? Have a philosophical discussion with Mark about this :)
    if vocabbase and not iri.is_absolute(etype):
        etype = vocabbase + etype

    unique_computed = []
    for k, v in unique:
        if vocabbase:
            #XXX OK absolutize used here. Go figure
            k = k if iri.is_absolute(k) else iri.absolutize(k, vocabbase)
        unique_computed.append((k, v))

    if unique_computed:
        unique_computed.append((VTYPE_REL, etype))
        unique_computed.sort()
        plaintext = json.dumps(unique_computed, separators=(',', ':'), cls=OrderedJsonEncoder)
        eid = idgen.send(plaintext)
    else:
        #We only have a type; no other distinguishing data. Generate a random hash
        eid = next(idgen)
    return eid


def materialize_entity(ctx, etype, unique=None):
    '''
    Low-level routine for creating a resource. Takes the entity (resource) type
    and a data mapping according to the resource type. As a convenience, if a
    vocabulary base is provided in the context, concatenate it to etype and
    data keys

    ctx - context information governing creation of the new entity
    etype - type IRI for the new entity
    unique - list of key/value tuples of data to use in generating
                unique ID, or None in which case one is randomly generated
    '''
    for ix, (k, v) in enumerate(unique):
        if callable(v):
            unique[ix] = v(ctx)
    return I(resource_id(etype, unique=unique, idgen=ctx.idgen, vocabbase=ctx.base))


def create_resource(output_model, rtype, unique, links, existing_ids=None, id_helper=None):
    '''
    General-purpose routine to create a new resource in the output model, based on data provided

    output_model    - Versa connection to model to be updated
    rtype           - Type IRI for the new resource, set with Versa type. If you need multiple types, see create_resource_mt
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


def create_resource_mt(output_model, rtypes, unique, links, existing_ids=None, id_helper=None):
    '''
    Convenience variation of create_resource which supports multiple entity types.
    The first is taken as primary

    output_model    - Versa connection to model to be updated
    rtypes          - Type IRIor list of IRIs for the new resource, set with Versa type
    unique          - list of key/value pairs for determining a unique hash for the new resource
    links           - list of key/value pairs for setting properties on the new resource
    id_helper       - If a string, a base URL for the generatd ID. If callable, a function used to return the entity. If None, set a default good enough for testing.
    existing_ids    - set of existing IDs to not recreate, or None, in which case a new resource will always be created
    '''
    rtypes = rtypes if isinstance(rtypes, list) else [rtypes]
    rtype, *moretypes = rtypes
    for t in moretypes:
        links.append([VTYPE_REL, t])
    return create_resource(output_model, rtype, unique, links, existing_ids=None, id_helper=None)

#iritype = object()
#force_iritype = object()

#Generic entry point for pipeline tools
def transform(record, phases, config, interphase=None, postprocess=None, **kwargs):
    #Google-style doctrings. Anything but ReST!
    '''
    Process an input record in some raw format through a defined sequence of transforms,
    generating a versa model of output resources
    
    Args:
        record: unit of input to be processed independently into resource output,
            according to conventions established in the process phases
        phases: sequence of processing phase functions to be applied to the
            input record to generate the output, e.g. fingerprint then core mapping
        interphase: shared dictionary for cooperative data sharing across phases
        postprocess: optional final transform of the output Versa model,
            usually to a different format

    Returns:
        list: Resource objects constructed from the post-transform Versa model
    '''
    #FIXME: Convert config into more kwargs?
    input_model = memory.connection()#baseiri=BFZ)
    output_model = memory.connection()
    kwargs['record'] = record
    #kwargs['logger'] = logger

    resources = []

    #Interphase. One POV: Michael Jackson would have a hernia here. Another POV: This is just basically a heap used by coroutines; not yet quite implemented in coroutine form, but it could be soon
    if interphase is None: interphase = {}
    kwargs['interphase'] = interphase
    for phase in phases:
        retval = phase(input_model, output_model, **kwargs)
        if retval is False:
            #Signal to abort
            return None
    if postprocess:
        return(postprocess(output_model))
    else:
        return output_model

