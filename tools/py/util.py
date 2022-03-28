#versa.util
'''
Utilities to help deal with constructs expressed in Versa
'''

#from amara.lib import iri
#import logging

import re
import sys
import json
from collections import OrderedDict

from amara3 import iri

from versa import I, ORIGIN, RELATIONSHIP, TARGET, ATTRIBUTES
from versa import init_localization
init_localization()
from versa import VERSA_BASEIRI, VTYPE_REL, VLABEL_REL

def versa_list_to_pylist(m, vlistid):
    return [ s[TARGET] for s in m.match(vlistid, VERSA_BASEIRI + 'item') ]


def simple_lookup(m, orig, rel):
    links = list(m.match(orig, rel))
    return links[0][TARGET] if links else None


def simple_lookup_byvalue(m, rel, target):
    links = list(m.match(None, rel, target))
    return links[0][ORIGIN] if links else None


def lookup(m, orig, rel):
    for link in m.match(orig, rel):
        yield link[TARGET]


def lookup_byvalue(m, rel, target):
    links = list(m.match(None, rel, target))
    return [ l[ORIGIN] for l in links]


def transitive_closure(m, orig, rel):
    '''
    Generate the closure over a transitive relationship in depth-first fashion
    '''
    #FIXME: Broken for now
    links = list(m.match(orig, rel))
    for link in links:
        yield link[0][TARGET]
        yield from transitive_closure(m, target, rel)


def all_origins(m, of_types=None, only_types=None):
    '''
    Generate all unique statement origins in the given model
    '''
    seen = set()
    if not of_types: of_types = only_types
    # Undocumented, defensive coding against common error
    if isinstance(of_types, I): of_types = {of_types}
    of_types = set(of_types) if of_types else set()
    if '*' in of_types: of_types = {'*'}
    for link in m.match():
        origin = link[ORIGIN]
        if origin not in seen:
            seen.add(origin)
            if not of_types:
                yield origin
                continue
            otypes = set(resourcetypes(m, origin))
            if ('*' in of_types and otypes) or (of_types & otypes):
                yield origin


def column(m, linkpart):
    '''
    Generate all parts of links according to the parameter
    '''
    assert linkpart in (0, 1, 2, 3)
    seen = set()
    for link in m.match():
        val = link[linkpart]
        if val not in seen:
            seen.add(val)
            yield val


def resourcetypes(m, rid):
    '''
    Yield a list of Versa types for a resource
    '''
    for o, r, t, a in m.match(rid, VTYPE_REL):
        yield t


def labels(m, rid):
    '''
    Yield a list of Versa labels for a resource
    '''
    for o, r, t, a in m.match(rid, VLABEL_REL):
        yield t


def static_index(m, rel, setvals=False, include_attrs=True, intern=False):
    '''
    Create a static index for a relationship, a mapping from origin to
    targets and attributes of all matching relations from that origin
    
    Args:
        m - model from which to create the index
        rel - relationship to match in creating the index
        setvals - optional. If false (the default) values in the mapping
            might be target, attribute tuples or might be a list of such tuples.
            If true all values are a tuple of such tuples, even if there
            is only one matching relationship
        intern - use string interning for speedup & memory savings
    
    Return:
        the created index (mapping)
    '''
    index = {}
    for o, r, t, a in m.match(None, rel):
        if intern: o, t = sys.intern(str(o)), sys.intern(str(t))
        val = (t, a) if include_attrs else t
        curr = index.get(o)
        if curr is None:
            if setvals:
                index[o] = set((val,))
            else:
                index[o] = val
        else:
            if setvals:
                index[o].add(val)
            elif isinstance(curr, list):
                curr.append(val)
            else:
                index[o] = [curr, val]
    return index    
    

def origin_view(m):
    '''
    Materialize a view of all origina, mapping from origin to a list
    of rel/target/attribute tuples, covering all rels in the model
    
    Args:
        m - model from which to create the index
    
    Return:
        the created index (mapping)
    '''
    index = {}
    for o, r, t, a in m.match():
        index.setdefault(o, []).append((r,t,a))
    return index    
    

#XXX Could use a factory defined on in_m to create out_m, or do we want to use this approach to support append?
def replace_values(in_m, out_m, map_from=(), map_to=()):
    '''
    Make a copy of a model with one value replaced with another
    '''
    for link in in_m.match():
        new_link = list(link)
        if map_from:
            if link[ORIGIN] in map_from: new_link[ORIGIN] = map_to[map_from.index(link[ORIGIN])]
        new_link[ATTRIBUTES] = link[ATTRIBUTES].copy()
        out_m.add(*new_link)
    return


def replace_entity_resource(model, oldres, newres):
    '''
    Replace one entity in the model with another with the same links

    :param model: Versa model to be updated
    :param oldres: old/former resource IRI to be replaced
    :param newres: new/replacement resource IRI
    :return: None
    '''
    oldrids = set()
    for rid, link in model:
        if link[ORIGIN] == oldres or link[TARGET] == oldres or oldres in link[ATTRIBUTES].values():
            oldrids.add(rid)
            new_link = (newres if o == oldres else o, r, newres if t == oldres else t, dict((k, newres if v == oldres else v) for k, v in a.items()))
            model.add(*new_link)
    model.delete(oldrids)
    return


def duplicate_statements(model, oldorigin, neworigin, rfilter=None):
    '''
    Take links with a given origin, and create duplicate links with the same information but a new origin

    :param model: Versa model to be updated
    :param oldres: resource IRI to be duplicated
    :param newres: origin resource IRI for duplication
    :return: None
    '''
    for o, r, t, a in model.match(oldorigin):
        if rfilter is None or rfilter(o, r, t, a):
            model.add(I(neworigin), r, t, a)
    return


def uniquify(model):
    '''
    Remove all duplicate relationships
    '''
    seen = set()
    to_remove = set()
    for ix, (o, r, t, a) in model:
        hashable_link = (o, r, t) + tuple(sorted(a.items()))
        #print(hashable_link)
        if hashable_link in seen:
            to_remove.add(ix)
        seen.add(hashable_link)

    model.remove(to_remove)
    return


def zoom_in(model, focus, depth=1, model_fact=None, max_rels=0):
    '''
    Given a model and a resource within it to focus on, create a new model
    with only relationships originating with the focus resource, or N
    rels removed therefrom, up to the specified depth

    max_rels - if non-zero set a maximum number of relationships to be copied
        into the output model
    '''
    model_fact = model_fact or model.factory
    zoomed = model_fact()

    def zoom_in_(m, f, d, relcount):
        for o, r, t, a in m.match(f):
            relcount += 1
            if max_rels and relcount > max_rels:
                return False, relcount
            zoomed.add(o, r, t, a)
            # XXX For now the Versa dump does not differentiate IRI targets
            # So we have to use an IRI ref syntax check, which is a bit awkward
            # if d and isinstance(t, I):
            if d and isinstance(t, str) and iri.matches_uri_ref_syntax(t):
                c, rc = zoom_in_(m, t, d-1, relcount)
                relcount += rc
        return True, relcount

    completed, _ = zoom_in_(model, focus, depth, 0)
    return zoomed, completed


def jsonload(model, fp):
    '''
    Load Versa model dumped into JSON form, either raw or canonical
    '''
    dumped_list = json.load(fp)
    for link in dumped_list:
        if len(link) == 2:
            sid, (s, p, o, a) = link
        elif len(link) == 4: #canonical
            (s, p, o, a) = link
            tt = a.get('@target-type')
            if tt == '@iri-ref':
                o = I(o)
            a.pop('@target-type', None)
        else:
            continue
        model.add(s, p, o, a)
    return


def jsondump(model, fp):
    '''
    Dump Versa model into JSON form
    '''
    fp.write('[')
    links_ser = []
    for link in model:
        links_ser.append(json.dumps(link))
    fp.write(',\n'.join(links_ser))
    fp.write(']')


class OrderedJsonEncoder(json.JSONEncoder):
    '''
    JSON-serialize OrderedDicts... in order

    Derived from http://stackoverflow.com/questions/10844064/items-in-json-object-are-out-of-order-using-json-dumps

    Used for generating canonical representations of Versa models
    '''
    def encode(self, o):
        if isinstance(o, OrderedDict):
            return '{'+','.join(( self.encode(k)+':'+self.encode(v) for (k,v) in o.items() ))+'}'
        else:
            return json.JSONEncoder.encode(self, o)


# Helper for slightly friendlier (non-crypto) hashes
HASHMASK = (1 << sys.hash_info.width) - 1


def make_immutable(obj):
    if isinstance(obj, list) or isinstance(obj, set):
        out = []
        for elem in obj:
            v = make_immutable(elem)
            out.append(v)
        return tuple(out)
        # XXX Maybe frozenset(out) instead if obj is set?
    if isinstance(obj, dict):
        out = []
        for k, v in obj.items():
            vv = make_immutable(v)
            out.append((k, vv))
        return tuple(out)
    return obj
    # FIXME: Think about handling instances
    # elif hasattr(obj, '__dict__'):
    #     out = []
    #     for k, v in obj.items():
    #         vv = make_immutable(v)
    #         out.append((k, vv))
    #     return tuple(out)


