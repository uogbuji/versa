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

from versa import I, VERSA_BASEIRI, ORIGIN, RELATIONSHIP, TARGET, ATTRIBUTES
from versa import util
from versa.util import simple_lookup, OrderedJsonEncoder
from versa.driver import memory

from versa.contrib.datachefids import idgen as default_idgen, FROM_EMPTY_64BIT_HASH

VTYPE_REL = I(iri.absolutize('type', VERSA_BASEIRI))


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


def link(origin=None, rel=None, value=None, attributes=None, source=None):
    '''
    Action function generator to create a link based on the context's current link, or on provided parameters

    :param origin: IRI/string, or list of same; origins for the created relationships.
    If None, the action context provides the parameter.

    :param rel: IRI/string, or list of same; IDs for the created relationships.
    If None, the action context provides the parameter.
    
    :param value: IRI/string, or list of same; values/targets for the created relationships.
    If None, the action context provides the parameter.
    
    :param source: pattern action to be executed, generating contexts to determine the output statements. If given, overrides specific origin, rel or value params

    :return: Versa action function to do the actual work
    '''
    attributes = attributes or {}
    #rel = I(iri.absolutize(rel, ctx.base))
    def _link(ctx):
        if source:
            if not callable(source):
                raise ValueError('Link source must be a pattern action function')
            contexts = source(ctx)
            for ctx in contexts:
                ctx.output_model.add(ctx.current_link[ORIGIN], ctx.current_link[RELATIONSHIP], ctx.current_link[TARGET], attributes)
            return

        (o, r, v, a) = ctx.current_link
        _origin = origin(ctx) if callable(origin) else origin
        o_list = [o] if _origin is None else (_origin if isinstance(_origin, list) else [_origin])
        #_origin = _origin if isinstance(_origin, set) else set([_origin])
        _rel = rel(ctx) if callable(rel) else rel
        r_list = [r] if _rel is None else (_rel if isinstance(_rel, list) else [_rel])
        #_rel = _rel if isinstance(_rel, set) else set([_rel])
        _value = value(ctx) if callable(value) else value
        v_list = [v] if _value is None else (_value if isinstance(_value, list) else [_value])
        #_target = _target if isinstance(_target, set) else set([_target])
        _attributes = attributes(ctx) if callable(attributes) else attributes

        #(ctx_o, ctx_r, ctx_t, ctx_a) = ctx.current_link

        #FIXME: Add test for IRI output via wrapper action function
        for (o, r, v, a) in [ (o, r, v, a) for o in o_list for r in r_list for v in v_list ]:
            ctx.output_model.add(o, r, v, attributes)

        return
    return _link


def links(origin, rel, target, attributes=None):
    '''
    '''
    raise NotImplementedError('You can just use link() for this now.')


def var(name):
    '''
    Action function generator to retrieve a variable from context
    '''
    def _var(ctx):
        return ctx.variables.get(name)
    return _var


def target():
    '''
    Action function generator to return the target of the context's current link

    :return: target of the context's current link
    '''
    #Action function generator to multiplex a relationship at processing time
    def _target(ctx):
        '''
        Versa action function Utility to return the target of the context's current link

        :param ctx: Versa context used in processing (e.g. includes the prototype link
        :return: Target of the context's current link
        '''
        return ctx.current_link[TARGET]
    return _target


def values(*rels):
    '''
    Action function generator to compute a set of relationships from criteria

    :param rels: List of relationships to compute
    :return: Versa action function to do the actual work
    '''
    #Action function generator to multiplex a relationship at processing time
    def _values(ctx):
        '''
        Versa action function Utility to specify a list of relationships

        :param ctx: Versa context used in processing (e.g. includes the prototype link
        :return: Tuple of key/value tuples from the attributes; suitable for hashing
        '''
        computed_rels = [ rel(ctx) if callable(rel) else rel for rel in rels ]
        return computed_rels
    return _values


def ifexists(test, value, alt=None):
    '''
    Action function generator providing an if/then/else type primitive
    :param test: Expression to be tested to determine the branch path
    :param value: Expression providing the result if test is true
    :param alt: Expression providing the result if test is false
    :return: Versa action function to do the actual work
    '''
    def _ifexists(ctx):
        '''
        Versa action function Utility to specify a list of relationships

        :param ctx: Versa context used in processing (e.g. includes the prototype link)
        :return: Value computed according to the test expression result
        '''
        _test = test(ctx) if callable(test) else test
        if _test:
            return value(ctx) if callable(value) else value
        else:
            return alt(ctx) if callable(alt) else alt
    return _ifexists


def foreach(origin=None, rel=None, target=None, attributes=None):
    '''
    Action function generator to compute a combination of links

    :return: Versa action function to do the actual work
    '''
    def _foreach(ctx):
        '''
        Versa action function utility to compute a list of values from a list of expressions

        :param ctx: Versa context used in processing (e.g. includes the prototype link)
        '''
        _origin = origin(ctx) if callable(origin) else origin
        _rel = rel(ctx) if callable(rel) else rel
        _target = target(ctx) if callable(target) else target
        _attributes = attributes(ctx) if callable(attributes) else attributes
        (o, r, t, a) = ctx.current_link
        o = [o] if _origin is None else (_origin if isinstance(_origin, list) else [_origin])
        r = [r] if _rel is None else (_rel if isinstance(_rel, list) else [_rel])
        t = [t] if _target is None else (_target if isinstance(_target, list) else [_target])
        #a = [a] if _attributes is None else _attributes
        a = [a] if _attributes is None else (_attributes if isinstance(_attributes, list) else [_attributes])
        #print([(curr_o, curr_r, curr_t, curr_a) for (curr_o, curr_r, curr_t, curr_a)
        #            in product(o, r, t, a)])
        return [ ctx.copy(current_link=(curr_o, curr_r, curr_t, curr_a))
                    for (curr_o, curr_r, curr_t, curr_a)
                    in itertools.product(o, r, t, a) ]
        #for (curr_o, curr_r, curr_t, curr_a) in product(origin or [o], rel or [r], target or [t], attributes or [a]):
        #    newctx = ctx.copy(current_link=(curr_o, curr_r, curr_t, curr_a))
            #ctx.output_model.add(I(objid), VTYPE_REL, I(iri.absolutize(_typ, ctx.base)), {})
    return _foreach


def materialize(typ, rel=None, origin=None, unique=None, links=None, inverse=False, split=None, attributes=None):
    '''
    Create a new resource related to the origin

    :param typ: IRI of the type for the resource to be materialized,
    which becomes the target of the main link, and the origin of any
    additional links given in the links param

    :param rel: IRI of the relationship between the origin and the materialized
    target, or a list of relationship IRIs, each of which will be used to create
    a separate link, or a versa action function to derive this relationship or
    list of relationships at run time, or None. If none, use the action context.

    :param origin: Literal IRI or Versa action function for origin of the
    main generated link. If none, use the action context.

    :param unique: Versa action function to be invoked in order to
    derive a unique hash key input for the materialized resource, in the form of
    multiple key, value pairs (or key, list-of-values)

    :param links: Dictionary of links from the newly materialized resource.
    Each keys can be a relationship IRIs, a Versa action function returning
    a relationship IRI, a Versa action function returning a list of Versa
    contexts, which can be used to guide a sequence pattern of generated
    links, or a Versa action function returning None, which signals that
    the particular link is skipped entirely.

    :param postprocess: IRI or list of IRI queueing up actiona to be postprocessed
    for this materialized resource. None, the default, signals no special postprocessing

    For examples of all these scenarios see marcpatterns.py

    :return: Versa action function to do the actual work
    '''
    links = links or []
    attributes = attributes or {}
    def _materialize(ctx):
        '''
        Inserts at least two main links in the context's output_model, one or more for
        the relationship from the origin to the materialized resource, one for the
        type of the materialized resource, and links according to the links parameter

        :param ctx: Runtime Versa context used in processing (e.g. includes the prototype link)
        :return: None

        This function is intricate in its use and shifting of Versa context, but the
        intricacies are all designed to make the marcpatterns mini language more natural.
        '''
        #FIXME: Part of the datachef sorting out
        if not ctx.idgen: ctx.idgen = idgen
        _typ = typ(ctx) if callable(typ) else typ
        _rel = rel(ctx) if callable(rel) else rel
        _unique = unique(ctx) if callable(unique) else unique
        (o, r, t, a) = ctx.current_link
        #FIXME: On redesign implement split using function composition instead
        targets = [ sub_t.strip() for sub_t in t.split(split) ] if split else [t]
        #Conversions to make sure we end up with a list of relationships out of it all
        if _rel is None:
            _rel = [r]
        rels = _rel if isinstance(_rel, list) else ([_rel] if _rel else [])
        objids = []

        #Botanical analogy
        #The stem is the relationship from the original to the materialized resource 
        #The veins are any further relationships from materialized resource 
        for target in targets:
            ctx_stem = ctx.copy(current_link=(o, r, target, a))
            if origin:
                #Have been given enough info to derive the origin from context. Ignore origin in current link
                o = origin(ctx_stem)

            computed_unique = [] if _unique else None
            if _unique:
                # strip None values from computed unique list, including pairs where v is None
                for k, v in _unique:
                    if None in (k, v): continue
                    v = v if isinstance(v, list) else [v]
                    for subitem in v:
                        subval = subitem(ctx) if callable(subitem) else subitem
                        if subval:
                            subval = subval if isinstance(subval, list) else [subval]
                            computed_unique.extend([(k, s) for s in subval])

            objid = materialize_entity(ctx, _typ, unique=computed_unique)
            objids.append(objid)
            for curr_rel in rels:
                #e.g. scenario if passed in rel=ifexists(...)
                curr_rel = curr_rel(ctx) if callable(curr_rel) else curr_rel
                #FIXME: Fix this properly, by slugifying & making sure slugify handles all numeric case (prepend '_')
                curr_rel = '_' + curr_rel if curr_rel.isdigit() else curr_rel
                if curr_rel:
                    if inverse:
                        ctx.output_model.add(I(objid), I(iri.absolutize(curr_rel, ctx.base)), I(o), {})
                    else:
                        ctx.output_model.add(I(o), I(iri.absolutize(curr_rel, ctx.base)), I(objid), {})
            #print((objid, ctx_.existing_ids))
            if objid not in ctx.existing_ids:
                if _typ: ctx.output_model.add(I(objid), VTYPE_REL, I(iri.absolutize(_typ, ctx.base)), {})
                #FIXME: Should we be using Python Nones to mark blanks, or should Versa define some sort of null resource?
                #XXX: Note, links are only processed on new objects! This needs some thought
                for k, v in links:
                    new_current_link = (I(objid), k, ctx.current_link[TARGET], ctx.current_link[ATTRIBUTES])
                    ctx_vein = ctx_stem.copy(current_link=new_current_link)
                    k = k(ctx_vein) if callable(k) else k
                    #If k is a list of contexts use it to dynamically execute functions
                    if isinstance(k, list):
                        if k and isinstance(k[0], context):
                            for newctx in k:
                                #The function in question will generate any needed links in the output model
                                v(newctx)
                            continue

                    #import traceback; traceback.print_stack() #For looking up the call stack e.g. to debug nested materialize
                    #Check that the links key is not None, which is a signal not to
                    #generate the item. For example if the key is an ifexists and the
                    #test expression result is False, it will come back as None,
                    #and we don't want to run the v function
                    if k:
                        v = v(ctx_vein) if callable(v) else v

                        #If k or v come from pipeline functions as None it signals to skip generating anything else for this link item
                        if v is not None:
                            v = v(ctx_vein) if callable(v) else v
                            #FIXME: Fix properly, by slugifying & making sure slugify handles all-numeric case
                            if k.isdigit(): k = '_' + k
                            if isinstance(v, list):
                                for valitems in v:
                                    if valitems:
                                        ctx.output_model.add(I(objid), I(iri.absolutize(k, ctx_vein.base)), valitems, {})
                            else:
                                ctx.output_model.add(I(objid), I(iri.absolutize(k, ctx_vein.base)), v, {})
                ctx.existing_ids.add(objid)
        return objids

    return _materialize


def res(arg):
    '''
    Convert the argument into an IRI ref
    '''
    def _res(ctx):
        _arg = arg(ctx) if callable(arg) else arg
        return I(arg)
    return _res


def compose(*funcs):
    '''
    Compose an ordered list of functions. Args of a,b,c,d evaluates as a(b(c(d(ctx))))
    '''
    def _compose(ctx):
        # last func gets context, rest get result of previous func
        _result = funcs[-1](ctx)
        for f in reversed(funcs[:-1]):
            _result = f(_result)

        return _result
    return _compose


def discard():
    '''
    Action function generator that's pretty much a no-op. Just ignore the proposed link set

    :return: None
    '''
    def _discard(ctx): return
    return _discard

# ----
# Still needed?


class resource(object):
    def __init__(self, ctx):
        self._origin = ctx.current_link[ORIGIN]
        self._input_model = ctx.input_model
        self._base = ctx.base
        return

    def follow(self, rel):
        return simple_lookup(self._input_model, self._origin, I(iri.absolutize(rel, self._base)))


def origin(ctx):
    return resource(ctx.current_link[ORIGIN], ctx.input_model)


def run(pycmds):
    def _run(ctx):
        gdict = {
            'origin': ctx.current_link[ORIGIN],
            #'origin': resource(ctx),
            #'origin': resource(link[ORIGIN], ctx),
            'target': ctx.current_link[TARGET],
        }
        result = eval(pycmds, gdict)
        return result
    return _run
