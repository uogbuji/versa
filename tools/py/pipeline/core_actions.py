#versa.pipeline
#FIXME: Use __all__

import itertools
import re

from amara3 import iri

from versa import I, VERSA_BASEIRI, ORIGIN, RELATIONSHIP, TARGET, ATTRIBUTES, VTYPE_REL
from versa.terms import VFPRINT_REL
from versa import util
from versa.util import simple_lookup

from . import context, materialize_entity, create_resource

#FIXME: Use __all__

SKIP = object()
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
            if not callable(source):
                raise ValueError('Link source must be a pattern action function')
            contexts = source(ctx)
            for ctx in contexts:
                ctx.output_model.add(ctx.current_link[ORIGIN], ctx.current_link[RELATIONSHIP], ctx.current_link[TARGET], attributes)
            return

        (o, r, t, a) = ctx.current_link
        _origin = origin(ctx) if callable(origin) else origin
        o_list = [o] if _origin is DEFAULT_ARG else (_origin if isinstance(_origin, list) else [_origin])
        #_origin = _origin if isinstance(_origin, set) else set([_origin])
        _rel = rel(ctx) if callable(rel) else rel
        r_list = [r] if _rel is DEFAULT_ARG else (_rel if isinstance(_rel, list) else [_rel])
        #_rel = _rel if isinstance(_rel, set) else set([_rel])
        _target = target(ctx) if callable(target) else target
        t_list = [t] if _target is DEFAULT_ARG else (_target if isinstance(_target, list) else [_target])
        #_target = _target if isinstance(_target, set) else set([_target])
        _attributes = attributes(ctx) if callable(attributes) else attributes

        #(ctx_o, ctx_r, ctx_t, ctx_a) = ctx.current_link

        #FIXME: Add test for IRI output via wrapper action function
        for (o, r, t, a) in [ (o, r, t, a) for o in o_list
                                            for r in r_list
                                            for t in t_list
                                            if None not in (o, r, t) ]:
            ctx.output_model.add(o, r, t, attributes)

        return
    return _link


def var(name):
    '''
    Action function generator to retrieve a variable from context
    '''
    def _var(ctx):
        _name = name(ctx) if callable(name) else name
        return ctx.variables.get(_name)
    return _var


def extra(key, default=None):
    '''
    Action function generator to retrieve an extra value from context
    '''
    def _extra(ctx):
        _key = key(ctx) if callable(key) else key
        _default = default(ctx) if callable(default) else default
        return ctx.extras.get(_key, _default)
    return _extra


def attr(aid):
    '''
    Action function generator to retrieve an attribute from the current link
    '''
    def _attr(ctx):
        _aid = aid(ctx) if callable(aid) else aid
        return ctx.current_link[ATTRIBUTES].get(_aid)
    return _attr


def origin(unique=None):
    '''
    Action function generator to return the origin of the context's current link

    Arguments:
        unique - Used to derive a unique hash key input for the materialized resource,
        May be a list of key, value pairs, from which the ID is derived through
        the Versa hash convention, or may be an action function that returns the ID
        If a list of key, value pairs, the key of the first value must be the Versa type relationship
        And the first value is used in the hash generation

    Returns:
        origin of the context's current link, or origin computed from provided unique arg
    '''
    def _origin(ctx):
        '''
        Versa action function Utility to return the origin of the context's current link

        :param ctx: Versa context used in processing (e.g. includes the prototype link
        :return: origin of the context's current link
        '''
        o = ctx.current_link[ORIGIN]
        if callable(unique):
            o = unique(ctx)
        elif unique:
            # strip None values from computed unique list, including pairs where v is None
            typ = None
            computed_unique = []
            for k, v in unique:
                if typ is None:
                    if k != VTYPE_REL:
                        raise ValueError('Key of the first unique list pair must be the Versa type relationship')
                    typ = v
                if None in (k, v): continue
                v = v if isinstance(v, list) else [v]
                for subitem in v:
                    subval = subitem(ctx) if callable(subitem) else subitem
                    if subval:
                        subval = subval if isinstance(subval, list) else [subval]
                        computed_unique.extend([(k, s) for s in subval])

            o = materialize_entity(ctx, typ, unique=computed_unique)
            # print(o, ctx.extras)
        return o
    return _origin


def rel():
    '''
    Action function generator to return the relationship of the context's current link

    :return: origin of the context's current link
    '''
    def _rel(ctx):
        '''
        Versa action function Utility to return the relationship of the context's current link

        :param ctx: Versa context used in processing (e.g. includes the prototype link
        :return: relationship of the context's current link
        '''
        return ctx.current_link[RELATIONSHIP]
    return _rel


def target():
    '''
    Action function generator to return the target of the context's current link

    :return: target of the context's current link
    '''
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
        computed_rels = []
        for rel in rels:
            if callable(rel):
                rel = rel(ctx)

            if isinstance(rel, list):
                computed_rels.extend(rel)
            else:
                computed_rels.append(rel)

        return computed_rels
    return _values


def ifexists(test, value, alt=None):
    '''
    Action function generator providing a limited if/then/else type primitive
    :param test: Expression to be tested to determine the branch path
    :param value: Expression providing the result if test is true
    :param alt: Expression providing the result if test is false
    :return: Action representing the actual work
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


def if_(test, iftrue, iffalse=None, vars_=None):
    '''
    Action function generator providing a fuller if/then/else type primitive
    :param test: Expression to be tested to determine the branch path
    :param iftrue: Expression to be executed (perhaps for side effects) if test is true
    :param iffalse: Expression to be executed (perhaps for side effects) if test is false
    :param vars: Optional dictionary of variables to be used in computing string test
    :return: Action representing the actual work. This function returns the value computed from iftrue if the test computes to true, otherwise iffalse
    '''
    vars_ = vars_ or {}
    def _if_(ctx):
        '''
        Versa action function utility to execute an if/then/else type primitive

        :param ctx: Versa context used in processing (e.g. includes the prototype link)
        :return: Value computed according to the test expression result
        '''
        out_vars = {'target': ctx.current_link[TARGET]}
        if isinstance(test, str):
            for k, v in vars_.items():
                #FIXME: Less crude test
                assert isinstance(k, str)
                _v = v(ctx) if callable(v) else v
                out_vars[k] = _v

            _test = eval(test, out_vars, out_vars)
            #Test is an expression to be dynamically computed
            #for m in ACTION_FUNCTION_PAT.findall(test):
            #    func_name = m.group(1)
        else:
            _test = test(ctx) if callable(test) else test
        if _test:
            return iftrue(ctx) if callable(iftrue) else iftrue
        elif iffalse:
            return iffalse(ctx) if callable(iffalse) else iffalse
    return _if_


# XXX: Top-level Target function is shadowed in here
def foreach(origin=None, rel=None, target=None, attributes=None, action=None):
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
        # print([(curr_o, curr_r, curr_t, curr_a) for (curr_o, curr_r, curr_t, curr_a)
        #            in product(o, r, t, a)])
        # Assemble the possible context links, ignoring those with blank or None origins
        subcontexts = [ ctx.copy(current_link=(curr_o, curr_r, curr_t, curr_a))
                    for (curr_o, curr_r, curr_t, curr_a)
                    in itertools.product(o, r, t, a) if curr_o ]
        if action:
            if not(callable(action)):
                raise TypeError('foreach() action arg must be callable')
            for subctx in subcontexts:
                action(subctx)
        else:
            return subcontexts
        #for (curr_o, curr_r, curr_t, curr_a) in product(origin or [o], rel or [r], target or [t], attributes or [a]):
        #    newctx = ctx.copy(current_link=(curr_o, curr_r, curr_t, curr_a))
            #ctx.output_model.add(I(objid), VTYPE_REL, I(iri.absolutize(_typ, ctx.base)), {})
    return _foreach


def materialize(typ, rel=None, origin=None, unique=None, fprint=None, links=None, split=None, attributes=None, attach=True, preserve_fprint=False, inverse=False):
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

        fprint (unique is the deprecated name): Used to derive a unique hash key input for the materialized
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

        preserve_fprint - if True record the fingerprint (from the fprint param) in a new relationship

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
        #FIXME: Part of the datachef sorting out
        if not ctx.idgen: ctx.idgen = idgen
        _typ = typ(ctx) if callable(typ) else typ
        _unique = unique(ctx) if callable(unique) else unique
        (o, r, t, a) = ctx.current_link
        #FIXME: On redesign implement split using function composition instead
        targets = [ sub_t.strip() for sub_t in t.split(split) if sub_t.strip() ] if split else [t]
        #Make sure we end up with a list
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
                        subval = subitem(ctx_stem) if callable(subitem) else subitem
                        if subval:
                            subval = subval if isinstance(subval, list) else [subval]
                            computed_unique.extend([(k, s) for s in subval])

            objid = materialize_entity(ctx_stem, _typ, unique=computed_unique)
            objids.append(objid)
            #rels = [ ('_' + curr_rel if curr_rel.isdigit() else curr_rel) for curr_rel in rels if curr_rel ]
            computed_rels = []
            for curr_relobj in rels:
                #e.g. scenario if passed in rel=ifexists(...)
                curr_rels = curr_relobj(ctx_stem) if callable(curr_relobj) else curr_relobj
                curr_rels = curr_rels if isinstance(curr_rels, list) else [curr_rels]
                for curr_rel in curr_rels:
                    if not curr_rel: continue
                    # FIXME: Fix properly, by slugifying & making sure slugify handles  all numeric case (prepend '_')
                    curr_rel = '_' + curr_rel if curr_rel.isdigit() else curr_rel
                    # Shotgun hack to restore inverse until we move to pipeline_uni
                    if inverse:
                        ctx_stem.output_model.add(I(objid), I(iri.absolutize(curr_rel, ctx_stem.base)), I(o), {})
                    elif attach:
                        ctx_stem.output_model.add(I(o), I(iri.absolutize(curr_rel, ctx_stem.base)), I(objid), {})
                    computed_rels.append(curr_rel)
            # print((objid, ctx_.existing_ids))
            # XXX: Means links are only processed on new objects! This needs some thought
            if objid not in ctx_stem.existing_ids:
                if _typ: ctx_stem.output_model.add(I(objid), VTYPE_REL, I(iri.absolutize(_typ, ctx_stem.base)), {})
                computed_unique.sort()
                if preserve_fprint:
                    attr_dict = {}
                    for (k, v) in computed_unique:
                        if k not in attr_dict:
                            attr_dict[k] = v
                        elif isinstance(attr_dict[k], list):
                            attr_dict[k].append(v)
                        else:
                            attr_dict[k] = [attr_dict[k], v]
                    ctx_stem.output_model.add(I(objid), VFPRINT_REL, _typ, attr_dict)
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

                    lo = lo(ctx_stem) if callable(lo) else lo
                    # Update contexts as we go along
                    ctx_vein = ctx_stem.copy(current_link=(lo, ctx_stem.current_link[RELATIONSHIP],
                                                            ctx_stem.current_link[TARGET],
                                                            ctx_stem.current_link[ATTRIBUTES]))
                    lr = lr(ctx_vein) if callable(lr) else lr
                    ctx_vein = ctx_vein.copy(current_link=(lo, lr, ctx_stem.current_link[TARGET],
                                                            ctx_stem.current_link[ATTRIBUTES]))
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
                        lt = lt(ctx_vein) if callable(lt) else lt

                        # If k or v come from pipeline functions as None it signals to skip generating anything else for this link item
                        if lt is not None:
                            # FIXME: Fix properly, by slugifying & making sure slugify handles all-numeric case
                            if lr.isdigit(): lr = '_' + lr
                            if isinstance(lt, list):
                                for valitems in lt:
                                    if valitems:
                                        ctx_vein.output_model.add(lo, I(iri.absolutize(lr, ctx_vein.base)), valitems, {})
                            else:
                                ctx_vein.output_model.add(lo, I(iri.absolutize(lr, ctx_vein.base)), lt, {})
                ctx_stem.existing_ids.add(objid)
                if '@new-entity-hook' in ctx.extras:
                    ctx.extras['@new-entity-hook'](objid)
            
        return objids

    return _materialize


def toiri(arg, base=None, ignore_refs=True):
    '''
    Convert the argument into an IRI ref or list thereof

    :param base: base IRI to resolve relative references against
    :param ignore_refs: if True, make no attempt to convert would-be IRI refs to IRI type
    '''
    def _toiri(ctx):
        _arg = arg(ctx) if callable(arg) else arg
        _arg = [_arg] if not isinstance(_arg, list) else _arg
        ret = []
        for u in _arg:
            iu = u
            if not (ignore_refs and not iri.is_absolute(iu)):
                # coerce into an IRIref, but fallout as untyped text otherwise
                try:
                    iu = I(iu)
                except ValueError as e:
                    # attempt to recover by percent encoding
                    try:
                        iu = I(iri.percent_encode(iu))
                    except ValueError as e:
                        ctx.extras['logger'].warn('Unable to convert "{}" to IRI reference:\n{}'.format(iu, e))

                if base is not None and isinstance(iu, I):
                    iu = I(iri.absolutize(iu, base))

            ret.append(iu)

        return ret
    return _toiri

# Legacy aliases
res = url = toiri


def lookup(mapping, key=None, onmiss=None):
    '''
    Action function generator to look up a value from a mapping provided inline or in context
    (either as ctx.extras[mapping-name] or ctx.extras['lookups'][mapping-name]) if that special,
    reserved item 'lookups' is found in extras

    Args:
        mapping: dictionary for the lookup, or string key of such a mapping in ctx.extras or in ctx.extras['lookups']
        key: value to look up instead of the current link target
        onmiss: value to be returned in case of a miss (lookup value not found in mapping)

    Return:
        Versa action function to do the actual work
    '''
    def _lookup(ctx):
        '''
        Versa action function Utility to do the text replacement

        :param ctx: Versa context used in processing (e.g. includes the prototype link)
        :return: Replacement text, or input text if not found
        '''
        if isinstance(mapping, str):
            _mapping = ctx.extras['lookups'][mapping] if 'lookups' in ctx.extras else ctx.extras[mapping]
        else:
            _mapping = mapping
        (origin, _, t, a) = ctx.current_link
        _key = key(ctx) if callable(key) else (t if key is None else key)

        _onmiss = onmiss
        if onmiss == None:
            _onmiss = key
        elif onmiss == SKIP:
            _onmiss = None
        result = _mapping.get(_key, _onmiss)
        return result
    return _lookup


def regex_match_modify(pattern, group_or_func, value=None):
    '''
    Action function generator to take some text and modify it either according to a named group or a modification function for the match

    :param pattern: regex string or compiled pattern
    :param group_or_func: string or function that takes a regex match. If string, a named group to use for the result. If a function, executed to return the result
    :param pattern: value to use instead of the current link target
    :return: Versa action function to do the actual work
    '''
    def _regex_modify(ctx):
        '''
        Versa action function Utility to do the text replacement

        :param ctx: Versa context used in processing (e.g. includes the prototype link)
        :return: Replacement text
        '''
        _pattern = re.compile(pattern) if isinstance(pattern, str) else pattern
        (origin, _, t, a) = ctx.current_link
        _value = value(ctx) if callable(value) else (t if value is None else value)
        match = _pattern.match(_value)
        if not match: return _value
        if callable(group_or_func):
            return group_or_func(match)
        else:
            return match.groupdict().get(group_or_func, '')
    return _regex_modify


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


def ignore():
    '''
    Action function generator that's pretty much a no-op/ignore input

    :return: None
    '''
    def _ignore(ctx): return
    return _ignore


def replace_from(patterns, old_text):
    '''
    Action function generator to take some text and replace it with another value based on a regular expression pattern

    :param specs: List of replacement specifications to use, each one a (pattern, replacement) tuple
    :param old_text: Source text for the value to be created. If this is a list, the return value will be a list processed from each item
    :return: Versa action function to do the actual work
    '''
    def _replace_from(ctx):
        '''
        Versa action function Utility to do the text replacement

        :param ctx: Versa context used in processing (e.g. includes the prototype link)
        :return: Replacement text
        '''
        #If we get a list arg, take the first
        _old_text = old_text(ctx) if callable(old_text) else old_text
        _old_text = [] if _old_text is None else _old_text
        old_text_list = isinstance(_old_text, list)
        _old_text = _old_text if old_text_list else [_old_text]
        # print(old_text_list, _old_text)
        new_text_list = set()
        for text in _old_text:
            new_text = text #So just return the original string, if a replacement is not processed
            for pat, repl in patterns:
                m = pat.match(text)
                if not m: continue
                new_text = pat.sub(repl, text)

            new_text_list.add(new_text)
        # print(new_text_list)
        return list(new_text_list) if old_text_list else list(new_text_list)[0]
    return _replace_from


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

