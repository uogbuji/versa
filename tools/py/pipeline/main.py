# versa.pipeline
'''
Creating and processing descriptions of Versa resources

# Creation

Use `create_resource` for general-purpose resource creation (i.e. establishing
a resource ID based on fingerprint characteristics).

Use 

# Modification

Versa pipelines provide a system for modifying Versa resources and their descriptions
using patterns and declared rules.

'''

import json
import itertools
# import functools
from operator import itemgetter
# from enum import Enum #https://docs.python.org/3.4/library/enum.html
from collections import defaultdict, OrderedDict
from types import GeneratorType

from amara3 import iri

from versa import I, VERSA_BASEIRI, ORIGIN, RELATIONSHIP, TARGET, ATTRIBUTES, VTYPE_REL, VLABEL_REL
from versa.terms import VFPRINT_REL
from versa import util
from versa.util import simple_lookup, OrderedJsonEncoder
from versa.driver.memory import newmodel

from versa.contrib.datachefids import idgen as default_idgen, FROM_EMPTY_64BIT_HASH

# VERSA_PIPELINE_WILDCARD = 'https://github.com/uogbuji/versa/pipeline/wildcard'

__all__ = [
    'context', 'DUMMY_CONTEXT', 'resource_id', 'materialize_entity',
    'is_pipeline_action', 'create_resource', 'stage',
    'definition', 'generic_pipeline',
    # Upstream objects included to reduce imports needed by users
    'I', 'VERSA_BASEIRI', 'ORIGIN', 'RELATIONSHIP', 'TARGET', 'ATTRIBUTES',
    'VTYPE_REL', 'VLABEL_REL'
]


class context(object):
    #Default way to create a model for the transform output, if one is not provided
    transform_factory = newmodel

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
        self.output_model = context.transform_factory() if output_model is None else output_model
        self.base = base
        self.variables = variables or {}
        self.extras = extras or {}
        # FIXME: idgen requires a base IRI. Think this over.
        self.idgen = idgen or default_idgen(base)
        self.existing_ids = existing_ids or set()

    def copy(self, current_link=None, input_model=None, output_model=None, base=None, variables=None, extras=None, idgen=None, existing_ids=None):
        '''
        Shallow copy of context
        '''
        current_link = current_link if current_link else self.current_link
        input_model = self.input_model if input_model is None else input_model
        output_model = self.output_model if output_model is None else output_model
        base = base if base else self.base
        variables = variables if variables else self.variables
        extras = extras if extras else self.extras
        idgen = idgen if idgen else self.idgen
        existing_ids = existing_ids if existing_ids else self.existing_ids
        return context(current_link=current_link, input_model=input_model, output_model=output_model, base=base, variables=variables, extras=extras, idgen=idgen, existing_ids=existing_ids)


# Create a dummy context for anyone wanting to start off a chain of derived contexts
# If this leaks into actual use, there will be errors, e.g. from input_model == None
# FIXME: Establish clear error behavior for such cases
_link = (None, I('https://example.org/'), None, {})
DUMMY_CONTEXT = context(_link, None)


def resource_id(etype, fprint=None, idgen=default_idgen(None), vocabbase=None):
    '''
    Lowest level routine for generating a, ID value using the Versa comvention
    
    The Versa convention originated as the hash algorithm outlined by
    the Libhub initiative for for BIBFRAME Lite, and now codified in the document [Computing Versa Resource Hashes
](https://github.com/uogbuji/versa/wiki/Computing-Versa-Resource-Hashes).

    etype - type IRI for the new entity (if the entity has multiple types, this is the primary and additional types
    can be provided in the fingerprint set)
    fprint - fingerprint set. List of key/value tuples of data to use in generating its unique ID, or None in which
    case one is just randomly generated
    defaultvocabbase - for convenience, provided, use to resolve relative etype & fingerprint keys

    >>> from versa.pipeline import resource_id
    >>> resource_id("http://schema.org/Person", [("http://schema.org/name", "Jonathan Bruce Postel"), ("http://schema.org/birthDate", "1943-08-06")])
    '-7hP9d_Xo8M'
    >>> resource_id("http://schema.org/Person", [("http://schema.org/name", "Augusta Ada King")])
    'xjgOrUFiw_o'
    '''
    params = {}
    if vocabbase and not iri.is_absolute(etype):
        etype = vocabbase(etype)

    fprint_processed = []
    for k, v in fprint or []:
        if vocabbase and not iri.is_absolute(k):
            k = vocabbase(k)
        fprint_processed.append((k, v))

    if fprint_processed:
        if (VTYPE_REL, etype) not in fprint_processed:
            fprint_processed.append((VTYPE_REL, etype))
        fprint_processed.sort()
        plaintext = json.dumps(fprint_processed, separators=(',', ':'), cls=OrderedJsonEncoder)
        eid = idgen.send(plaintext)
    else:
        #We only have a type; no other distinguishing data. Generate a random hash
        eid = next(idgen)
    return I(eid)


def is_pipeline_action(f):
    return callable(f) and getattr(f, 'is_pipeline_action', False)


def materialize_entity(ctx, etype, fprint=None):
    '''
    Low-level routine for creating a resource. Takes the entity (resource) type
    and a data mapping according to the resource type. As a convenience, if a
    vocabulary base is provided in the context, concatenate it to etype and
    data keys

    ctx - context information governing creation of the new entity
    etype - type IRI for the new entity
    fprint - list of key/value tuples of data to use in generating
                unique ID, or None in which case one is randomly generated
    '''
    fprint_processed = []
    for ix, (k, v) in enumerate(fprint or []):
        fprint_processed.append((k, v(ctx) if is_pipeline_action(v) else v))
    return I(resource_id(etype, fprint=fprint_processed, idgen=ctx.idgen,
                vocabbase=ctx.base))


def create_resource(output_model, rtypes, fprint, links, existing_ids=None, id_helper=None, preserve_fprint=False):
    '''
    General-purpose routine to create a new resource in the output model, based on provided resource types and fingerprinting info

    output_model    - Versa connection to model to be updated
    rtypes          - Type IRIor list of IRIs for the new resource, used to give the object a Versa type relationship
    fprint          - list of key/value pairs for determining a unique hash for the new resource
    links           - list of key/value pairs for setting properties on the new resource
    id_helper       - If a string, a base URL for the generatd ID. If callable, a function used to return the entity. If None, set a default good enough for testing.
    existing_ids    - set of existing IDs to not recreate, or None, in which case a new resource will always be created
    '''
    rtypes = rtypes if isinstance(rtypes, list) else [rtypes]
    rtype, *moretypes = rtypes
    for t in moretypes:
        links.append([VTYPE_REL, t])

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
    rid = I(materialize_entity(ctx, rtype, fprint=fprint))
    if existing_ids is not None:
        if rid in existing_ids:
            return (False, rid)
        existing_ids.add(rid)
    output_model.add(rid, VTYPE_REL, rtype)

    if preserve_fprint:
        attrs = { k:v for (k,v) in fprint }
        attrs[VTYPE_REL] = rtypes
        output_model.add(rid, VFPRINT_REL, rtype, attrs)

    for r, t in links:
        output_model.add(rid, r, t)
    return (True, rid)


# iritype = object()
# force_iritype = object()

# phases: sequence of processing phase functions to be applied to the
# input record to generate the output, e.g. fingerprint then core mapping

# When to use the source record for direct input rather than a fully constructed Versa model?
# Convenience & optimization, for example if the source record
# were an object from JSON you could use this to rapidly access the
# field needed for fingerprinting rather than going thru Versa query


# FIXME: Should get this from sys, really
# MAX32LESS1 = 4294967295 #2**32-1

def stage(sortkey):
    if callable(sortkey):
        raise RuntimeError('Did you forget to use the decorator as @stage() rather than @stage?')
    def _stage(func):
        func.pipeline_sort_key = sortkey
        return func
    return _stage


# Copied from datachef. Move to amara3 core
def make_list(lvalue, *items):
    new_lvalue = lvalue if isinstance(lvalue, list) else [lvalue]
    new_lvalue.extend(items)
    return new_lvalue


class definition:
    '''
    Definition of a pipeline for transforming one Versa model to another
    through the action of functions executing the various stages of the transform,
    often by applying a system of mappings and rules. Also manages the entity mapping,
    how key entities in the input are mapped to the output.
    '''
    def __init__(self):
        self._stages = []
        self._stages_hash = None

    def check_update_stages(self):
        stage_func_names = [ k for k in dir(self) if hasattr(getattr(self, k), 'pipeline_sort_key') ]
        if hash(tuple(stage_func_names)) != self._stages_hash:
            self._stages = [ getattr(self, k) for k in dir(self) if hasattr(getattr(self, k), 'pipeline_sort_key') ]
            self._stages = [ (int(getattr(s, 'pipeline_sort_key')), s) for s in self._stages ]
            # Python sorts are guaranteed to be stable, so all with default sortkey will come
            # last, but in original declaration order
            self._stages.sort(key=itemgetter(0))
            self._stages_hash = hash(tuple(stage_func_names))
        return

    def run(self, input_model=None, raw_source=None, output_model=None, **kwargs):
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
        self.check_update_stages()

        self.input_model = newmodel() if input_model is None else input_model
        self.output_model = newmodel() if output_model is None else output_model

        self._raw_source = raw_source
        self.fingerprints = {}

        # First tuple item is just sortkey, so discarded 
        for _, stage in self._stages:
            retval = stage(**kwargs)
            if retval is False:
                #Signal to abort
                break
        return self.output_model

    def fingerprint_helper(self, rules, root_context=DUMMY_CONTEXT):
        '''
        Implements a common fingerprinting strategy where the input model
        is scanned for resources and each one is matched by type to the passed-in rules
        If any type is matched that corresponding action is run to determine
        the new resource ID & type
        '''
        # All output resources, whether or not from a direct fingerprint of an input resource
        new_rids = set()

        resources = list(util.all_origins(self.input_model))
        for rid in resources:
            for typ in util.resourcetypes(self.input_model, rid):
                if typ in rules:
                    rule_tup = rules[typ]
                    rule_tup = (rule_tup
                        if isinstance(rule_tup, list)
                            or isinstance(rule_tup, tuple)
                        else
                            (rule_tup,))
                    for rule in rule_tup:
                        out_rids = set()
                        def new_entity(eid):
                            '''
                            Called on Versa pipeline materialization of new entity
                            Ensures we capture additional entities created by
                            pipeline actions during this fingerprint phase
                            '''
                            if out_rids is not None:
                                out_rids.add(eid)

                        # None relationship here acts as a signal to actions
                        # such as materialize to not try to attach the newly created
                        # resource anywhere in the output, since this is just the
                        # fingerprinting stage
                        link = (rid, None, typ, {})
                        ctx = root_context.copy(current_link=link, input_model=self.input_model,
                            output_model=self.output_model)
                        ne_hook = ctx.extras.setdefault('@new-entity-hook', [])
                        ctx.extras['@new-entity-hook'] = make_list(ne_hook, new_entity)
                        main_ridouts = rule(ctx)
                        main_ridouts = set(main_ridouts) if isinstance(main_ridouts, list) else {main_ridouts}
                        mains, others = self.fingerprints.setdefault(rid, (set(), set()))
                        mains.update(main_ridouts), others.update(out_rids)
                        others -= mains
                        new_rids.update(out_rids)
                        out_rids = None
        return new_rids

    def transform_by_rel_helper(self, rules, origins=None, handle_misses=None,
                                    root_context=DUMMY_CONTEXT):
        '''
        Implements a common transform strategy where each fingerprinted
        input model resource is examined for outbound links, and each one matched
        by relationship to the passed-in rules. If matched the corresponding action
        is run to update the output model
        '''
        origins = origins or self.fingerprints
        # Really just for lightweight sanity checks
        applied_rules_count = 0
        types_cache = {}
        for rid in origins:
            (mains, others) = origins[rid]
            # import pprint; pprint.pprint([mains, others])

            # Go over all the links for the input resource
            for o, r, t, attribs in self.input_model.match(rid):
                # Match input resource against the rules mapping keys.
                # The mains can match on just rel if it's a simple, scalar key
                # Either mains or others can match on a (rel, T1, T2...) tuple key
                # whether a main or other if TN is one of the output resource's types

                # Collect node/match pairs
                match_sets = set()
                for out_rid in itertools.chain(mains, others):
                    for (rspec, rule) in rules.items():
                        if (out_rid in mains) and rspec == r:
                            match_sets.add((rule, out_rid))
                        elif rspec[0] == r:
                            if out_rid in types_cache:
                                out_rid_types = types_cache[out_rid]
                            else:
                                out_rid_types = frozenset(util.resourcetypes(self.output_model, out_rid))
                                types_cache[out_rid] = out_rid_types
                            _, *typs = rspec
                            for typ in typs:
                                if typ in out_rid_types:
                                    match_sets.add((rule, out_rid))
                                    break

                # If nothing matched, trigger caller's miss handler, if any
                if not match_sets:
                    if handle_misses:
                        handle_misses((rid, r, t, attribs))
                    continue

                for (rule, out_rid) in match_sets:
                    # At the heart of the Versa pipeline context is a prototype link,
                    # which looks like the link that triggered the current tule, but with the
                    # origin changed to the output resource
                    link = (out_rid, r, t, attribs)
                    # Build the rest of the context
                    variables = root_context.variables.copy()
                    variables.update({'input-resource': rid})
                    extras = root_context.extras.copy()
                    extras.update({'@resource': { k: list(m) for (k, (m, o)) in self.fingerprints.items() }})
                    ctx = root_context.copy(current_link=link, input_model=self.input_model,
                                                output_model=self.output_model, variables=variables,
                                                extras=extras)
                    # Run the rule, expecting the side effect of data added to the output model
                    rule(ctx)
                    applied_rules_count += 1
        return applied_rules_count

    def labelize_helper(self, rules, label_rel=VLABEL_REL, origins=None,
                            handle_misses=None, root_context=DUMMY_CONTEXT):
        '''
        Implements a common label making strategy where output
        resources are put through pattern/action according to type in order
        to determine the output label
        '''
        new_labels = {}
        # Anything with a Versa type is an output resource
        # FIXME weid, redundant logic
        for out_rid in util.all_origins(self.output_model, of_types='*'):
            for typ in util.resourcetypes(self.output_model, out_rid):
                if typ in rules:
                    rule = rules[typ]
                    link = (out_rid, VTYPE_REL, typ, {})
                    # Notice that it reads from the output model and also updates same
                    ctx = root_context.copy(current_link=link, input_model=self.output_model,
                                            output_model=self.output_model)
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


class generic_pipeline(definition):
    def __init__(self, fingerprint_rules, transform_rules, labelize_rules, root_ctx=DUMMY_CONTEXT):
        self.fingerprint_rules = fingerprint_rules
        self.transform_rules = transform_rules
        self.labelize_rules = labelize_rules
        self._root_ctx = root_ctx
        super().__init__()

    @stage(1)
    def fingerprint(self):
        '''
        Generates fingerprints from the source model
        '''
        new_rids = self.fingerprint_helper(self.fingerprint_rules,
                        root_context=self._root_ctx) # Delegate
        return bool(new_rids)

    @stage(2)
    def main_transform(self):
        '''
        Executes main transform rules to go from input to output model
        '''
        new_rids = self.transform_by_rel_helper(self.transform_rules,
                        root_context=self._root_ctx) # Delegate
        return True

    @stage(3)
    def labelize(self):
        '''
        Executes a utility rule to create labels in output model for new (fingerprinted) resources
        '''
        labels = self.labelize_helper(self.labelize_rules,
                        root_context=self._root_ctx) # Delegate
        return True

