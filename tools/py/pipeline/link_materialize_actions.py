#versa.pipeline.link_materialize_actions

import itertools

from amara3 import iri

from versa import I, VERSA_BASEIRI, ORIGIN, RELATIONSHIP, TARGET, ATTRIBUTES, VTYPE_REL
from versa import util
from versa.util import simple_lookup

from . import context, materialize_entity, create_resource, is_pipeline_action

__all__ = ['link', 'materialize']

# SKIP = object()
DEFAULT_ARG = object()


def link(origin=None, rel=None, target=None, value=None, attributes=None, source=None):
    '''
    Action function generator to create a link based on the context's current link, or on provided parameters

    :param origin: IRI/string, or list of same; origins for the created relationships.
    If None, the action context provides the parameter.

    :param rel: IRI/string, or list of same; IDs for the created relationships.
    If None, the action context provides the parameter.
    
    :param target: IRI/string, or list of same; values/targets for the created relationships.
    If None, the action context provides the parameter.

    :param value: Deprecated synonym for target
    
    :param source: pattern action to be executed, generating contexts to determine the output statements. If given, overrides specific origin, rel or value params

    :return: Versa action function to do the actual work
    '''
    # Separate defaulting from potential None returns from action functions
    if origin is None: origin = DEFAULT_ARG
    if rel is None: rel = DEFAULT_ARG
    if target is None: target = value or DEFAULT_ARG # Checking value covers deprecated legacy
    attributes = attributes or {}
    #rel = I(iri.absolutize(rel, ctx.base))
    def _link(ctx):
        if source:
            if not is_pipeline_action(source):
                raise ValueError('Link source must be a pattern action function')
            contexts = source(ctx)
            for ctx in contexts:
                ctx.output_model.add(ctx.current_link[ORIGIN], ctx.current_link[RELATIONSHIP], ctx.current_link[TARGET], attributes)
            return

        (o, r, t, a) = ctx.current_link
        _origin = origin(ctx) if is_pipeline_action(origin) else origin
        o_list = [o] if _origin is DEFAULT_ARG else (_origin if isinstance(_origin, list) else [_origin])
        #_origin = _origin if isinstance(_origin, set) else set([_origin])
        _rel = rel(ctx) if is_pipeline_action(rel) else rel
        r_list = [r] if _rel is DEFAULT_ARG else (_rel if isinstance(_rel, list) else [_rel])
        #_rel = _rel if isinstance(_rel, set) else set([_rel])
        _target = target(ctx) if is_pipeline_action(target) else target
        t_list = [t] if _target is DEFAULT_ARG else (_target if isinstance(_target, list) else [_target])
        #_target = _target if isinstance(_target, set) else set([_target])
        _attributes = attributes(ctx) if is_pipeline_action(attributes) else attributes

        #(ctx_o, ctx_r, ctx_t, ctx_a) = ctx.current_link

        #FIXME: Add test for IRI output via wrapper action function
        for (o, r, t, a) in [ (o, r, t, a) for o in o_list
                                            for r in r_list
                                            for t in t_list
                                            if None not in (o, r, t) ]:
            ctx.output_model.add(o, r, t, attributes)

        return
    _link.is_pipeline_action = True
    return _link


def materialize(typ, rel=None, origin=None, unique=None, links=None, split=None, attributes=None, attach=True):
    '''
    Create a new resource related to the origin

    Args:

        typ: IRI of the type for the resource to be materialized,
            which becomes the target of the main link, and the origin of any
            additional links given in the links param

        rel: relationship between the origin and the materialized target,
            added to the output model if attach=True. Can be an IRI,
            or a list of relationship IRIs, each of which will be used
            to create a separate link, or a versa action to derive
            this relationship or list of relationships at run time,
            or None, in which case use the relationship from the action
            context link.

        origin: Literal IRI or Versa action function for origin of the
            main generated link. If none, use the action context.

        unique: Used to derive a unique hash key input for the materialized
            resource. May be a list of key, value pairs, from which the ID
            is derived through the Versa hash convention, or may be an action
            function that returns the ID

        links: List of links to create with the newly materialized resource
            as origin. Each can be a rel/target pair or an origin/rel/target
            triple. Each rel can be a simple IRIs, a Versa action function
            returning and IRI, a Versa action function returning a list of
            Versa contexts used to generate links, or a Versa action function
            returning None, which signals that a particular link is skipped entirely.

        attach: if True (the default) attach the newly materialized resource
            to the context origin

    Return:
        Versa action function to do the actual work
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
        # FIXME: Part of the datachef sorting out
        if not ctx.idgen: ctx.idgen = idgen
        _typ = typ(ctx) if is_pipeline_action(typ) else typ
        _unique = unique(ctx) if is_pipeline_action(unique) else unique
        (o, r, t, a) = ctx.current_link
        # FIXME: On redesign implement split using function composition instead
        targets = [ sub_t.strip() for sub_t in t.split(split) if sub_t.strip() ] if split else [t]

        # Especially useful signal in a pipeline's fingerprinting stage
        attach_ = False if rel is None and r is None else attach

        # Make sure we end up with a list or None
        rels = rel if isinstance(rel, list) else ([rel] if rel else [r])
        objids = []

        # Botanical analogy: stem context is from the caller (e.g. connection point of newly materialized resource)
        # vein comtexts derive from the stem
        for target in targets:
            ctx_stem = ctx.copy(current_link=(ctx.current_link[ORIGIN], ctx.current_link[RELATIONSHIP], target, ctx.current_link[ATTRIBUTES]))
            if origin:
                #Have been given enough info to derive the origin from context. Ignore origin in current link
                o = origin(ctx_stem)
            if not o: #Defensive coding
                continue

            computed_unique = [] if _unique else None
            if _unique:
                # strip None values from computed unique list, including pairs where v is None
                for k, v in _unique:
                    if None in (k, v): continue
                    v = v if isinstance(v, list) else [v]
                    for subitem in v:
                        subval = subitem(ctx_stem) if is_pipeline_action(subitem) else subitem
                        if subval:
                            subval = subval if isinstance(subval, list) else [subval]
                            computed_unique.extend([(k, s) for s in subval])

            objid = materialize_entity(ctx_stem, _typ, unique=computed_unique)
            objids.append(objid)
            # rels = [ ('_' + curr_rel if curr_rel.isdigit() else curr_rel) for curr_rel in rels if curr_rel ]
            computed_rels = []
            for curr_relobj in rels:
                #e.g. scenario if passed in rel=ifexists(...)
                curr_rels = curr_relobj(ctx_stem) if is_pipeline_action(curr_relobj) else curr_relobj
                curr_rels = curr_rels if isinstance(curr_rels, list) else [curr_rels]
                for curr_rel in curr_rels:
                    if not curr_rel: continue
                    # FIXME: Fix properly, by slugifying & making sure slugify handles  all numeric case (prepend '_')
                    curr_rel = '_' + curr_rel if curr_rel.isdigit() else curr_rel
                    if attach_:
                        ctx_stem.output_model.add(I(o), I(iri.absolutize(curr_rel, ctx_stem.base)), I(objid), {})
                    computed_rels.append(curr_rel)
            # print((objid, ctx_.existing_ids))
            # XXX: Means links are only processed on new objects! This needs some thought
            if objid not in ctx_stem.existing_ids:
                if _typ: ctx_stem.output_model.add(I(objid), VTYPE_REL, I(iri.absolutize(_typ, ctx_stem.base)), {})
                # XXX: Use Nones to mark blanks, or should Versa define some sort of null resource?
                for l in links:
                    if len(l) == 2:
                        lo = I(objid)
                        lr, lt = l
                    elif len(l) == 3:
                        lo, lr, lt = l
                    # If explicitly None, use context 
                    lo = lo or ctx_stem.current_link[ORIGIN]
                    lr = lr or ctx_stem.current_link[RELATIONSHIP]
                    lt = lt or ctx_stem.current_link[TARGET]

                    lo = lo(ctx_stem) if is_pipeline_action(lo) else lo
                    # XXX: Do we need to use the new origin context?
                    # new_current_link = (lo, ctx_stem.current_link[RELATIONSHIP], ctx_stem.current_link[TARGET], ctx_stem.current_link[ATTRIBUTES])
                    # ctx_vein = ctx_stem.copy(current_link=new_current_link)
                    lr = lr(ctx_stem) if is_pipeline_action(lr) else lr
                    # If k is a list of contexts use it to dynamically execute functions
                    if isinstance(lr, list):
                        if lr and isinstance(lr[0], context):
                            for newctx in lr:
                                #The function in question will generate any needed links in the output model
                                lt(newctx)
                            continue

                    #import traceback; traceback.print_stack() #For looking up the call stack e.g. to debug nested materialize
                    #Check that the links key is not None, which is a signal not to
                    #generate the item. For example if the key is an ifexists and the
                    #test expression result is False, it will come back as None,
                    #and we don't want to run the v function
                    if lr:
                        lt = lt(ctx_stem) if is_pipeline_action(lt) else lt

                        # If k or v come from pipeline functions as None it signals to skip generating anything else for this link item
                        if lt is not None:
                            # FIXME: Fix properly, by slugifying & making sure slugify handles all-numeric case
                            if lr.isdigit(): lr = '_' + lr
                            if isinstance(lt, list):
                                for valitems in lt:
                                    if valitems:
                                        ctx_stem.output_model.add(lo, I(iri.absolutize(lr, ctx_stem.base)), valitems, {})
                            else:
                                ctx_stem.output_model.add(lo, I(iri.absolutize(lr, ctx_stem.base)), lt, {})
                ctx_stem.existing_ids.add(objid)
                if '@new-entity-hook' in ctx.extras:
                    ctx.extras['@new-entity-hook'](objid)
            
        return objids

    _materialize.is_pipeline_action = True
    return _materialize
