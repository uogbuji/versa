#versa.pipeline.other_actions

import itertools

from amara3 import iri

from versa import I, VERSA_BASEIRI, ORIGIN, RELATIONSHIP, TARGET, ATTRIBUTES, VTYPE_REL
#from versa.terms import VFPRINT_REL
#from versa import util
#from versa.util import simple_lookup

from . import context, materialize_entity, create_resource, is_pipeline_action

__all__ = [ 'var', 'extra', 'attr', 'origin', 'rel', 'target', 'values',
            'ifexists', 'if_', 'foreach', 'follow', 'toiri', 'lookup',
            'regex_match_modify', 'compose', 'ignore', 'replace_from',
            'action_template', 'contains', 'SKIP'
            ]


SKIP = object()
# DEFAULT_ARG = object()


def var(name):
    '''
    Action function generator to retrieve a variable from context
    '''
    def _var(ctx):
        _name = name(ctx) if is_pipeline_action(name) else name
        return ctx.variables.get(_name)
    _var.is_pipeline_action = True
    return _var


def extra(key, default=None):
    '''
    Action function generator to retrieve an extra value from context
    '''
    def _extra(ctx):
        _key = key(ctx) if is_pipeline_action(key) else key
        _default = default(ctx) if is_pipeline_action(default) else default
        return ctx.extras.get(_key, _default)
    _extra.is_pipeline_action = True
    return _extra


def attr(aid):
    '''
    Action function generator to retrieve an attribute from the current link
    '''
    def _attr(ctx):
        _aid = aid(ctx) if is_pipeline_action(aid) else aid
        return ctx.current_link[ATTRIBUTES].get(_aid)
    _attr.is_pipeline_action = True
    return _attr


def contains(l, val):
    '''
    Action function generator to check that a list contains a value
    '''
    def _contains(ctx):
        _l = l(ctx) if is_pipeline_action(l) else l
        vlist = val if isinstance(val, list) else [val]
        for v in vlist:
            if v in _l:
                return True
        else:
            return False 
    _contains.is_pipeline_action = True
    return _contains


def origin(fprint=None):
    '''
    Action function generator to return the origin of the context's current link

    Arguments:
        fprint - Used to derive a unique hash key input for the materialized resource,
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
        if is_pipeline_action(fprint):
            o = fprint(ctx)
        elif fprint:
            # strip None values from computed unique list, including pairs where v is None
            typ = None
            computed_fprint = []
            for k, v in fprint:
                if typ is None:
                    if k != VTYPE_REL:
                        raise ValueError('Key of the first unique list pair must be the Versa type relationship')
                    typ = v
                if None in (k, v): continue
                v = v if isinstance(v, list) else [v]
                for subitem in v:
                    subval = subitem(ctx) if is_pipeline_action(subitem) else subitem
                    if subval:
                        subval = subval if isinstance(subval, list) else [subval]
                        computed_fprint.extend([(k, s) for s in subval])

            o = materialize_entity(ctx, typ, fprint=computed_fprint)
            # print(o, ctx.extras)
        return o
    _origin.is_pipeline_action = True
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
    _rel.is_pipeline_action = True
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
    _target.is_pipeline_action = True
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
            if is_pipeline_action(rel):
                rel = rel(ctx)

            if isinstance(rel, list):
                computed_rels.extend(rel)
            else:
                computed_rels.append(rel)

        return computed_rels
    _values.is_pipeline_action = True
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
        _test = test(ctx) if is_pipeline_action(test) else test
        if _test:
            return value(ctx) if is_pipeline_action(value) else value
        else:
            return alt(ctx) if is_pipeline_action(alt) else alt
    _ifexists.is_pipeline_action = True
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
                _v = v(ctx) if is_pipeline_action(v) else v
                out_vars[k] = _v

            _test = eval(test, out_vars, out_vars)
            #Test is an expression to be dynamically computed
            #for m in ACTION_FUNCTION_PAT.findall(test):
            #    func_name = m.group(1)
        else:
            _test = test(ctx) if is_pipeline_action(test) else test
        if _test:
            return iftrue(ctx) if is_pipeline_action(iftrue) else iftrue
        elif iffalse:
            return iffalse(ctx) if is_pipeline_action(iffalse) else iffalse
    _if_.is_pipeline_action = True
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
        _origin = origin(ctx) if is_pipeline_action(origin) else origin
        _rel = rel(ctx) if is_pipeline_action(rel) else rel
        _target = target(ctx) if is_pipeline_action(target) else target
        _attributes = attributes(ctx) if is_pipeline_action(attributes) else attributes
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
            if not(is_pipeline_action(action)):
                raise TypeError('foreach() action arg must be callable')
            for subctx in subcontexts:
                action(subctx)
        else:
            return subcontexts
        #for (curr_o, curr_r, curr_t, curr_a) in product(origin or [o], rel or [r], target or [t], attributes or [a]):
        #    newctx = ctx.copy(current_link=(curr_o, curr_r, curr_t, curr_a))
            #ctx.output_model.add(I(objid), VTYPE_REL, I(iri.absolutize(_typ, ctx.base)), {})
    _foreach.is_pipeline_action = True
    return _foreach


def follow(*rels, origin=None, action=None):
    '''
    Action function generator to retrieve a variable from context
    '''
    def _follow(ctx):
        assert ctx.input_model
        _origin = origin(ctx) if is_pipeline_action(origin) else origin
        _rels = [ (r(ctx) if is_pipeline_action(r) else r) for r in rels ]
        (o, in_rel, t, a) = ctx.current_link
        computed_o = o if _origin is None else _origin
        pre_traverse = [(computed_o, a)]
        post_traverse = []
        for rel in _rels:
            for o, a in pre_traverse:
                for _, r, t, a in ctx.input_model.match(o, rel):
                    post_traverse.append((t, a))
            pre_traverse, post_traverse = post_traverse, []
        # Since we already swapped them out above, we have to get the final from pre
        final = pre_traverse

        if action:
            results = []
            if not(is_pipeline_action(action)):
                raise TypeError('follow() action arg must be callable')
            for t, a in final:
                subctx = ctx.copy(current_link=(computed_o, in_rel, t, a))
                res = action(subctx)
                res = [] if res is None else (res if isinstance(res, list) else [res])
                for r in res:
                    results.append(r)
            return results
        else:
            return [ t for (t, a) in final ]
    _follow.is_pipeline_action = True
    return _follow


def toiri(arg, base=None, ignore_refs=True):
    '''
    Convert the argument into an IRI ref or list thereof

    :param base: base IRI to resolve relative references against
    :param ignore_refs: if True, make no attempt to convert would-be IRI refs to IRI type
    '''
    def _toiri(ctx):
        _arg = arg(ctx) if is_pipeline_action(arg) else arg
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
    _toiri.is_pipeline_action = True
    return _toiri


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
        (origin, _, t, a) = ctx.current_link
        _key = key(ctx) if is_pipeline_action(key) else (t if key is None else key)
        if isinstance(mapping, str):
            _mapping = ctx.extras['lookups'][mapping] if 'lookups' in ctx.extras else ctx.extras[mapping]
        else:
            _mapping = mapping

        _onmiss = onmiss
        if onmiss == None:
            _onmiss = key
        elif onmiss == SKIP:
            _onmiss = None
        if isinstance(_key, list):
            _key = next(iter(_key), None)
        result = _mapping.get(_key, _onmiss)
        return result
    _lookup.is_pipeline_action = True
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
        _value = value(ctx) if is_pipeline_action(value) else (t if value is None else value)
        match = _pattern.match(_value)
        if not match: return _value
        if is_pipeline_action(group_or_func):
            return group_or_func(match)
        else:
            return match.groupdict().get(group_or_func, '')
    _regex_modify.is_pipeline_action = True
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
    _compose.is_pipeline_action = True
    return _compose


def ignore():
    '''
    Action function generator that's pretty much a no-op/ignore input

    :return: None
    '''
    def _ignore(ctx): return
    _ignore.is_pipeline_action = True
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
        _old_text = old_text(ctx) if is_pipeline_action(old_text) else old_text
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
    _replace_from.is_pipeline_action = True
    return _replace_from


def action_template(proto):
    '''
    Action function template wrapper. Allows definition of reusable template actions for pipelines
    '''
    def _action_template_prep(**terms):
        def _action_wrapper(ctx):
            for term, val in terms.items():
                val = val(ctx) if is_pipeline_action(val) else val
                ctx.variables[term] = val
            return proto(ctx)
        _action_wrapper.is_pipeline_action = True
        return _action_wrapper
    return _action_template_prep


