#versa.pipeline.link_materialize_actions

import warnings

from amara3 import iri

from versa import I, VERSA_BASEIRI, ORIGIN, RELATIONSHIP, TARGET, ATTRIBUTES, VTYPE_REL
from versa import util
from versa.util import simple_lookup
from versa.terms import VFPRINT_REL

from . import context, materialize_entity, create_resource, is_pipeline_action

__all__ = ['link', 'materialize', 'COPY']

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


# XXX: Could generalize this with some sort of session object for the entire pipeline op
def _smart_add(model, origin, rel, target, attrs, already_added):
    '''
    Add link to a model, with a simple safeguard to avoid re-adding the same link

    model - model to which the link should be added
    origin, rel, target - parts of the link
    attrs - tuple of key/value pairs for the link
    already_added - set of previously added link hashes
    '''
    attr_dict = {}
    newhash = hash(util.make_immutable((origin, rel, target, attrs))) & util.HASHMASK

    if newhash not in already_added:
        for (k, v) in attrs:
            if k not in attr_dict:
                attr_dict[k] = v
            elif isinstance(attr_dict[k], list):
                attr_dict[k].append(v)
            else:
                attr_dict[k] = [attr_dict[k], v]
        model.add(origin, rel, target, attr_dict)
        already_added.add(newhash)
    return


def materialize(typ, rel=None, origin=None, unique=None, fprint=None, links=None,
                split=None, attributes=None, attach=True, preserve_fprint=False,
                vars=None, debug=None):
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
            or None (the default), in which case use the relationship
            from the action context link.

        origin: Literal IRI or Versa action function for origin of the
            main generated link. Default is None, i.e. use the action context.

        fprint (unique is the deprecated name): Used to derive a unique hash
            key input for the materialized resource. May be a list of key,
            value pairs, from which the ID is derived through the Versa hash
            convention, or may be an action function that returns the ID.
            Default is None, i.e. a random hash is used.

        links: List of links to create with the newly materialized resource
            as origin. Each can be a rel/target pair or an origin/rel/target
            triple. Each rel can be a simple IRIs, a Versa action function
            returning and IRI, a Versa action function returning a list of
            Versa contexts used to generate links, or a Versa action function
            returning None, which signals that a particular link is skipped
            entirely. Default is None, i.e. no such links are created.

        attach: if True (the default) attach the newly materialized resource
            to the context origin. 

        preserve_fprint: if True record the fingerprint (from the fprint param) in a
            new relationship. Default is False, i.e. this special rel is not created.

        vars: list of 2-tuples, each of which is used to add a variable mapping
            to the top-level context for the materialize action. Default is None,
            i.e. no variables are mapped.

        debug: optional file-like object to which debug/tracing info is written.
            Default is None, i.e. no debug info is written.

    Returns:
        Versa action function to do the actual work
    '''
    links = links or []
    attributes = attributes or {}
    if unique and not fprint: fprint = unique
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
        if debug is None:
            def log_debug(msg): return
        elif not hasattr(debug, 'write'):
            raise TypeError('debug argument to materialize must be file-like object or None')
        else:
            def log_debug(msg):
                print(msg, file=debug)

        # Set up variables to be made available in any derived contexts
        vars_items = list((vars or {}).items())
        if vars_items:
            # First make sure we're not tainting the passed-in context
            ctx = ctx.copy(variables=ctx.variables.copy())
            for k, v in vars_items:
                if None in (k, v): continue
                #v = v if isinstance(v, list) else [v]
                v = v(ctx) if is_pipeline_action(v) else v
                if v:
                    # v = v[0] if isinstance(v, list) else v
                    ctx.variables[k] = v

        (o, r, t, a) = ctx.current_link
        if typ is None:
            raise ValueError('typ (type) argument to materialize cannot be None')
        if isinstance(typ, COPY):
            object_copy = typ
            object_copy.id = o
            _typ = next(util.resourcetypes(ctx.input_model, o), None)
            object_copy.links = []
            for stmt in ctx.input_model.match(o):
                if object_copy.rels is None or stmt[RELATIONSHIP] in typ.rels:
                    # FIXME: Attributes?
                    object_copy.links.append((stmt[RELATIONSHIP], stmt[TARGET]))
        else:
            _typ = typ(ctx) if is_pipeline_action(typ) else typ
            object_copy = None
        _fprint = fprint(ctx) if is_pipeline_action(fprint) else fprint
        # FIXME: On redesign implement split using function composition instead
        targets = [ sub_t.strip() for sub_t in t.split(split) if sub_t.strip() ] if split else [t]

        # If the rel in the incoming context is null and there is no rel passed in, nothing to attach
        # Especially useful signal in a pipeline's fingerprinting stage
        attach_ = False if rel is None and r is None else attach

        if '@added-links' not in ctx.extras: ctx.extras['@added-links'] = set()

        # Make sure we end up with a list or None
        rels = rel if isinstance(rel, list) else ([rel] if rel else [r])
        log_debug(f'materialize action. Type: {_typ}. Anchoring rels: {rels} Initial context current link: {ctx.current_link}')
        log_debug(f'Variables (including from vars= arg): {ctx.variables}')
        objids = []

        # Botanical analogy: stem context is from the caller (e.g. connection point of newly materialized resource)
        # vein comtexts derive from the stem
        for target in targets:
            ctx_stem = ctx.copy(current_link=(ctx.current_link[ORIGIN], ctx.current_link[RELATIONSHIP], target, ctx.current_link[ATTRIBUTES]))
            if origin:
                # Have been given enough info to derive the origin from context. Ignore origin in current link
                o = origin(ctx_stem)
            if not o: #Defensive coding
                continue

            computed_fprint = set()
            first_type = _typ[0] if isinstance(_typ, list) else _typ
            rtypes = set(_typ if isinstance(_typ, list) else [_typ])
            if _fprint:
                # strip None values from computed unique list, including pairs where v is None
                for k, v in _fprint:
                    if None in (k, v): continue
                    for subitem in (v if isinstance(v, list) else [v]):
                        subval = subitem(ctx_stem) if is_pipeline_action(subitem) else subitem
                        if subval:
                            subval = subval if isinstance(subval, list) else [subval]
                            if k == VTYPE_REL: rtypes.update(set(subval))
                            computed_fprint.update(set([(k, s) for s in subval]))
            for t in rtypes:
                if t != first_type:
                    computed_fprint.add((VTYPE_REL, t))
            log_debug(f'Provided fingerprinting info: {computed_fprint}')

            non_type_fprints = [ (k, v) for (k, v) in computed_fprint if k != VTYPE_REL ]
            if not non_type_fprints:
                warnings.warn("Only type information was provided for fingerprinting. Unexpected output resource IDs might result.")

            if object_copy:
                objid = object_copy.id
            else:
                objid = materialize_entity(ctx_stem, first_type, fprint=computed_fprint)
            objids.append(objid)
            log_debug(f'Newly materialized object: {objid}')
            # rels = [ ('_' + curr_rel if curr_rel.isdigit() else curr_rel) for curr_rel in rels if curr_rel ]
            computed_rels = []
            for curr_relobj in rels:
                # e.g. scenario if passed in rel=ifexists(...)
                curr_rels = curr_relobj(ctx_stem) if is_pipeline_action(curr_relobj) else curr_relobj
                curr_rels = curr_rels if isinstance(curr_rels, list) else [curr_rels]
                for curr_rel in curr_rels:
                    if not curr_rel: continue
                    # FIXME: Fix properly, by slugifying & making sure slugify handles all numeric case (prepend '_')
                    curr_rel = '_' + curr_rel if curr_rel.isdigit() else curr_rel
                    if attach_:
                        _smart_add(ctx_stem.output_model, I(o), I(iri.absolutize(curr_rel, ctx_stem.base)), I(objid), (), ctx.extras['@added-links'])
                    computed_rels.append(curr_rel)
            # print((objid, ctx_.existing_ids))
            # XXX: Means links are only processed on new objects! This needs some thought
            if objid not in ctx_stem.existing_ids:
                if first_type:
                    _smart_add(ctx_stem.output_model, I(objid), VTYPE_REL, I(iri.absolutize(first_type, ctx_stem.base)), (), ctx.extras['@added-links'])
                if preserve_fprint:
                    # Consolidate types
                    computed_fprint = [ (k, v) for (k, v) in computed_fprint if k != VTYPE_REL ]
                    # computed_fprint += 
                    attrs = tuple(computed_fprint + [(VTYPE_REL, r) for r in rtypes])
                    _smart_add(ctx_stem.output_model, I(objid), VFPRINT_REL, first_type, attrs, ctx.extras['@added-links'])

                # XXX: Use Nones to mark blanks, or should Versa define some sort of null resource?
                all_links = object_copy.links + links if object_copy else links
                for l in all_links:
                    if len(l) == 2:
                        lo = I(objid)
                        lr, lt = l
                    elif len(l) == 3:
                        lo, lr, lt = l
                    # This context is in effect 

                    # First of all, hold on to the inbound origin so that it can be accessed in embedded actions
                    vein_vars = ctx_stem.variables.copy()
                    vein_vars['@stem'] = ctx_stem.current_link[ORIGIN]

                    # Newly materialized resource is the origin. The overall context target for embedded actions
                    ctx_vein = ctx_stem.copy(current_link=(objid, ctx_stem.current_link[RELATIONSHIP], ctx_stem.current_link[TARGET], ctx_stem.current_link[ATTRIBUTES]), variables=vein_vars)

                    lo = lo or ctx_vein.current_link[ORIGIN]
                    lr = lr or ctx_vein.current_link[RELATIONSHIP]
                    lt = lt or ctx_vein.current_link[TARGET]

                    lo = lo(ctx_vein) if is_pipeline_action(lo) else lo
                    lo = lo if isinstance(lo, list) else [lo]
                    lr = lr(ctx_vein) if is_pipeline_action(lr) else lr

                    # Update lr
                    # XXX This needs cleaning up
                    ctx_vein = ctx_stem.copy(current_link=(ctx_vein.current_link[ORIGIN], lr, ctx_vein.current_link[TARGET], ctx_stem.current_link[ATTRIBUTES]), variables=vein_vars)

                    # If k is a list of contexts use it to dynamically execute functions
                    if isinstance(lr, list):
                        if lr and isinstance(lr[0], context):
                            for newctx in lr:
                                #The function in question will generate any needed links in the output model
                                lt(newctx)
                            continue

                    # import traceback; traceback.print_stack() #For looking up the call stack e.g. to debug nested materialize
                    # Check that the links key is not None, which is a signal not to
                    # generate the item. For example if the key is an ifexists and the
                    # test expression result is False, it will come back as None,
                    # and we don't want to run the v function
                    if lr:
                        lt = lt(ctx_vein) if is_pipeline_action(lt) else lt

                        # If k or v come from pipeline functions as None it signals to skip generating anything else for this link item
                        if lt is not None:
                            # FIXME: Fix properly, by slugifying & making sure slugify handles all-numeric case
                            if lr.isdigit(): lr = '_' + lr
                            _lr = I(iri.absolutize(lr, ctx_vein.base))
                            log_debug(f'Generated link: {lo, _lr, lt}')
                            if isinstance(lt, list):
                                for valitems in lt:
                                    if valitems:
                                        for loi in lo:
                                            _smart_add(ctx_vein.output_model, loi, _lr, valitems, (), ctx.extras['@added-links'])
                            else:
                                for loi in lo:
                                    _smart_add(ctx_vein.output_model, loi, _lr, lt, (), ctx.extras['@added-links'])
                ctx_stem.existing_ids.add(objid)
                for func in ctx.extras.get('@new-entity-hook', []):
                    func(objid)
        log_debug(f'End materialize')
            
        return objids

    _materialize.is_pipeline_action = True
    return _materialize


class COPY:
    '''
    Signal object for materialize action function to copy the context origin
    resource from the input to the output graph. The copied object has the
    identical ID, and is a shallow copy, with rel and target for selected,
    or for all links.
    '''
    def __init__(self, rels=None):
        '''
        rels - if None (the default), copy all rels from the input graph
        '''
        self.rels = rels

