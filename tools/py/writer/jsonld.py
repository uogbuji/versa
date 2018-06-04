#versa.writer.ntriples
"""
Render a Versa vocab model as JSON-LD

"""

import logging

from amara3 import iri

from versa import I, VERSA_BASEIRI, ORIGIN, RELATIONSHIP, TARGET
from versa.terms import VERSA_BASEIRI, RDF_NS, RDFS_NS, VERSA_TYPE, RDF_TYPE
from versa.driver import memory
from versa import VERSA_BASEIRI
from versa.util import all_origins, lookup

def bind(models, context=None, ignore_oftypes=None, logger=logging):
    if not isinstance(models, list): models = [models]
    vocab = context.get('@vocab')
    non_top_ids = set()
    obj_pool = {} #Mapping from resource id to object and list of referring ids
    used_objects = set() #Track multiple instance of docs to prevent data structure recursion
    #typed_origins = set()
    for m in models:
        #Everything with a type
        for origin in all_origins(m):
            typ = next(lookup(m, origin, RDF_TYPE), None)
            #if p == VERSA_TYPE: p = RDF_TYPE
            obj, referents = obj_pool.setdefault(origin, ({}, []))
            if vocab and typ:
                typ_rel = iri.relativize(typ, vocab)
                if typ_rel: typ = typ_rel
            if typ: obj['@type'] = typ
            if not origin.startswith('__VERSABLANKNODE__'): obj['@id'] = origin
            for o, r, t, a in m.match(origin):
                if r == RDF_TYPE: continue
                if isinstance(t, I) and o != t:
                    if vocab:
                        t_rel = iri.relativize(t, vocab)
                        if t_rel: t = t_rel
                    valobj, referents = obj_pool.setdefault(t, ({}, []))
                    if t in used_objects:
                        val = t
                    else:
                        val = valobj
                        if not t.startswith('__VERSABLANKNODE__') and '@id' not in val: val['@id'] = t
                        used_objects.add(t)

                        non_top_ids.add(t) #If something has an object as a value it does not appear at the top
                    referents.append(o)
                else:
                    val = t
                if vocab:
                    r_rel = iri.relativize(r, vocab)
                    if r_rel: r = r_rel
                if r in obj and isinstance(obj[r], list):
                    obj[r].append(val)
                elif r in obj:
                    obj[r] = [obj[r], val]
                else:
                    obj[r] = val

    #Eliminate objects of types to be ignored
    to_remove = []
    for (oid, (obj, referents)) in obj_pool.items():
        typ = obj.get('@type')
        if vocab and typ: typ = iri.absolutize(typ, vocab)
        if typ in ignore_oftypes:
            to_remove.append(oid)
            for ref in referents:
                refobj, _ = obj_pool[ref]
                for k in list(refobj.keys()):
                    v = refobj[k]
                    if isinstance(v, list) and obj in v:
                        v.remove(obj)
                        if len(v) == 1:
                            refobj[k] = v[0]
                    elif v == obj:
                        del refobj[k]
                        
    for k in to_remove:
        del obj_pool[k]

    #Handle @id only
    for (oid, (obj, referents)) in obj_pool.items():
        for k, v in obj.items():
            if len(v) == 1 and '@id' in v:
                obj[k] = v['@id']
    
    top_objs = [ obj for (k, (obj, refs)) in obj_pool.items() if k not in non_top_ids ]
    #Eliminate stranded top-level objects with no more than type
    to_remove = []
    #for ix, obj in enumerate(top_objs):
    for obj in top_objs:
        if len(obj) == 1 and '@type' in obj:
            to_remove.append(obj)
    for obj in to_remove:
        top_objs.remove(obj)
    #import pprint;pprint.pprint(top_objs)
    if context and context.get('@output', True):
        top = {'@context': context, '@graph': top_objs}
    else:
        return top_objs

