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

from versa import I, VERSA_BASEIRI, ORIGIN, RELATIONSHIP, TARGET, ATTRIBUTES, VTYPE_REL, VLABEL_REL
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
        unique_computed.insert(0, [VTYPE_REL, etype])
        plaintext = json.dumps(unique_computed, separators=(',', ':'), cls=OrderedJsonEncoder)
        eid = idgen.send(plaintext)
    else:
        #We only have a type; no other distinguishing data. Generate a random hash
        eid = next(idgen)
    return eid


def is_pipeline_action(f):
    return callable(f) and getattr(f, 'is_pipeline_action', False)


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
        if is_pipeline_action(v):
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


# iritype = object()
# force_iritype = object()

# phases: sequence of processing phase functions to be applied to the
# input record to generate the output, e.g. fingerprint then core mapping

# When to use the source record for direct input rather than a fully constructed Versa model?
# Convenience & optimization, for example if the source record
# were an object from JSON you could use this to rapidly access the
# field needed for fingerprinting rather than going thru Versa query


class definition:
    '''
    Definition of a pipeline for transforming one Versa model to another
    through the action of functions executing the various stages of the transform,
    often by applying a system of mappings and rules. Also manages the entity mapping,
    how key entities in the input are mapped to the output.
    '''
    def __init__(self):
        self._stages = []
        self.fingerprints = {}

    def transform(self, input_model=None, raw_source=None, output_model=None, **kwargs):
        '''
        Process an input, either an input Versa model or in some raw record format
        through a sequence of transform stages, to generate a versa model of output resources

        Caller must provide either an input_model or a raw_source, but can provide
        any combination of these, depending on the expectations of the defined stages
        
        Args:
            input_model: Versa model which serves as the starting point
            raw_source: raw input data, a possible optimization if it's impractical to directly
                represent as a Versa model, but can be interpreted by the stages as if it were
            output_model: optional output model, which might be provided to add transform results
                to existing data, or to use a specialized Versa model implementation
            kwargs: any additional parameters which are passed as they are to all the stages

        Returns:
            output_model: Same reference as the input output_model, if provided, otherwise a new
                model containing the results of the transform
        '''
        self.input_model = input_model or memory.connection()
        self.output_model = output_model or memory.connection()

        self._raw_source = raw_source
        # interphase['fingerprints'] = []

        for stage in self._stages:
            retval = stage(self, **kwargs)
            if retval is False:
                #Signal to abort
                break
        return self.output_model

    # FIXME: Add position/priority sort key arg, to not be dependent on definition order
    def stage(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Remember that retval will be expected to be boolean
            retval = func(*args, **kwargs)
            return retval
        self._stages.append(wrapper)
        return wrapper

    def fingerprint_helper(self, rules):
        '''
        Implements a common fingerprinting strategy where the input model
        is scanned for resources and each one is matched by type to the passed-in rules
        If any type is matched that corresponding action is run to determine
        the new resource ID & type
        '''
        new_rids = []
        resources = list(util.all_origins(self.input_model))
        for rid in resources:
            for typ in util.resourcetypes(self.input_model, rid):
                if typ in rules:
                    rule = rules[typ]
                    link = (rid, VTYPE_REL, typ, {})
                    ctx = context(link, self.input_model, self.output_model)
                    out_rid = rule(ctx)
                    out_rid = out_rid if isinstance(out_rid, list) else [out_rid]
                    self.fingerprints.setdefault(rid, []).extend(out_rid)
                    new_rids.append(new_rids)
        return new_rids

    def transform_by_rel_helper(self, rules, origins=None, handle_misses=None):
        '''
        Implements a common transform strategy where each fingerprinted
        input model resource is examined for outbound links, and each one matched
        by relationship to the passed-in rules. If matched the corresponding action
        is run to update the output model
        '''
        origins = origins or self.fingerprints
        # Really just for lightweight sanity checks
        applied_rules_count = 0
        for rid in origins:
            for out_rid in origins[rid]:
                # Go over all the links for the resource
                for o, r, t, attribs in self.input_model.match(rid):
                    rule = rules.get(r)
                    if not rule:
                        if handle_misses:
                            handle_misses((rid, r, t, attribs))
                        continue
                    # At the heart of the Versa pipeline context is a prototype link,
                    # which looks like the link that triggered the current tule, but with the
                    # origin changed to the output resource
                    link = (out_rid, r, t, attribs)
                    # Build the rest of the context
                    ctx = context(link, self.input_model, self.output_model)
                    # Run the rule, expecting the side effect of data added to the output model
                    rule(ctx)
                    applied_rules_count += 1
        return applied_rules_count

    def labelize_helper(self, rules, label_rel=VLABEL_REL, origins=None, handle_misses=None):
        '''
        Implements a common label making strategy where the fingerprinted
        resources are put through pattern/action according to type in order
        to determine the output label
        '''
        origins = origins or self.fingerprints
        new_labels = {}
        for rid in origins:
            out_rid = origins[rid]
            for typ in util.resourcetypes(self.output_model, out_rid):
                if typ in rules:
                    rule = rules[typ]
                    link = (out_rid, VTYPE_REL, typ, {})
                    # Notice that it reads from the output model and also updates same
                    ctx = context(link, self.output_model, self.output_model)
                    out_labels = rule(ctx)
                    if not out_labels: continue
                    for label in out_labels:
                        if not label or not str(label).strip():
                            if handle_misses:
                                handle_misses(out_rid, typ)
                        # Stripped because labels are for human reading so conventional not to differentiate by whitespace
                        # FIXME: fully normalize
                        label = str(label).strip()
                        new_labels[out_rid] = label
                        self.output_model.add(out_rid, label_rel, label)
        return new_labels

