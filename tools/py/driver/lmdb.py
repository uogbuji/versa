# Python-Diskcache driver https://github.com/grantjenks/python-diskcache
# Versa is a Web semi-structured metadata toolkit
'''

Key is origin

Value is list:

[
    {rel1: [
        (target11, {attrname1: attrval1, attrname2: attrval2})
        (target12, {attrname1: attrval1, attrname2: attrval2})
    ]}
    {rel2: [
        (target21, {attrname1: attrval1, attrname2: attrval2})
        (target22, {attrname1: attrval1, attrname2: attrval2})
    ]}
]

Re use of use_bin_type=True & raw=False it's as given in the msgpack docs:

>>> import msgpack
>>> msgpack.unpackb(msgpack.packb([b'spam', 'eggs']))
[b'spam', b'eggs']
>>> msgpack.unpackb(msgpack.packb([b'spam', 'eggs'], use_bin_type=True), raw=False)
[b'spam', 'eggs']

'''

import functools
#from itertools import groupby
#from operator import itemgetter

import lmdb
import msgpack

from amara3 import iri #for absolutize & matches_uri_syntax

from versa.driver import connection_base
from versa import I, ORIGIN, RELATIONSHIP, TARGET, ATTRIBUTES

#1GB
DEFAULT_MAP_SIZE = 1024 * 1024 * 1024


def newmodel(dbname, baseiri=None, map_size=DEFAULT_MAP_SIZE):
    '''
    Return a new, empty Versa model with lmdb back end
    Warning: if there is data already in this file, it will be erased.
    '''
    # XXX Mandate mapsize?
    model = connection(dbname=dbname, baseiri=baseiri, clear=True, map_size=map_size)
    return model


class connection(connection_base):
    def __init__(self, dbname=None, baseiri=None, map_size=DEFAULT_MAP_SIZE, clear=False):
        '''
        Versa connection object built from DiskCache collection object
        '''
        self._dbname = dbname
        self._db_env = lmdb.open(dbname, map_size=map_size)
        #if clear: self._db.clear()
        with self._db_env.begin(write=True) as txn:
            self._ensure_abbreviations(txn)
        #self.create_model()
        self._baseiri = baseiri
        self._abbr_index = 0
        return

    def copy(self, contents=True):
        '''Create a copy of this model, optionally without contents (i.e. just configuration)'''
        cp = connection(dbname=self._dbname, baseiri=self._baseiri)
        # FIXME!!!!!
        if contents: cp.add_many(self._relationships)
        return cp

    def query(self, expr):
        '''Execute a Versa query'''
        raise NotImplementedError

    def size(self):
        '''Return the number of links in the model'''
        count = 0
        with self._db_env.begin() as txn:
            for origin_b, nodedata in txn.cursor():
                if origin_b.startswith(b'@'):
                    continue
                nodedata = msgpack.loads(nodedata, raw=False)
                for rel, targetplus in nodedata.items():
                    count += len(targetplus)
        return count
        #return  self._db_coll.count() - connection.META_ITEM_COUNT

    def __iter__(self):
        abbrevs = self._abbreviations()
        cursor = self._db_coll.find()
        index = 0
        for origin in self._db:
            if origin.startswith('@'):
                continue
            for rel, targetplus in self._db[origin].items():
                try:
                    rel = rel.format(**abbrevs)
                except (KeyError, ValueError):
                    pass
                count += len(targetplus)
                for target, attribs in targetplus:
                    try:
                        target = target.format(**abbrevs)
                    except (KeyError, ValueError):
                        pass
                    yield index, (origin, rel, target, attribs)
                    index += 1

    # FIXME: Statement indices don't work sensibly without some inefficient additions. Use e.g. match for delete instead
    def match(self, origin=None, rel=None, target=None, attrs=None, include_ids=False):
        '''
        Iterator over relationship IDs that match a pattern of components

        origin - (optional) origin of the relationship (similar to an RDF subject). If omitted any origin will be matched.
        rel - (optional) type IRI of the relationship (similar to an RDF predicate). If omitted any relationship will be matched.
        target - (optional) target of the relationship (similar to an RDF object), a boolean, floating point or unicode object. If omitted any target will be matched.
        attrs - (optional) attribute mapping of relationship metadata, i.e. {attrname1: attrval1, attrname2: attrval2}. If any attribute is specified, an exact match is made (i.e. the attribute name and value must match).
        include_ids - If true include statement IDs with yield values
        '''
        index = 0
        with self._db_env.begin() as txn:
            abbrevs = self._abbreviations(txn)
            if origin is None:
                extent = txn.cursor()
            else:
                origin_b = origin.encode('utf-8')
                extent = [(origin_b, txn.get(origin_b))]

            for origin_b, nodedata in extent:
                if origin_b.startswith(b'@') or nodedata is None:
                    continue
                xorigin = origin_b.decode('utf-8')
                nodedata = msgpack.loads(nodedata, raw=False)
                for xrel, xtargetplus in nodedata.items():
                    try:
                        xrel = xrel.format(**abbrevs)
                    except (KeyError, ValueError):
                        pass
                    if rel and rel != xrel:
                        continue
                    for xtarget, xattrs in xtargetplus:
                        index += 1
                        # FIXME: only expand target abbrevs if of resource type?
                        try:
                            xtarget = xtarget.format(**abbrevs)
                        except (KeyError, ValueError, IndexError):
                            pass
                        if target and target != xtarget:
                            continue
                        matches = True
                        if attrs:
                            for k, v in attrs.items():
                                if k not in xattrs or xattrs.get(k) != v:
                                    matches = False
                        if matches:
                            if include_ids:
                                yield index, (xorigin, xrel, xtarget, xattrs)
                            else:
                                yield xorigin, xrel, xtarget, xattrs

        return

    def multimatch(self, origin=None, rel=None, target=None, attrs=None, include_ids=False):
        '''
        Iterator over relationship IDs that match a pattern of components, with multiple options provided for each component

        origin - (optional) origin of the relationship (similar to an RDF subject), or set of values. If omitted any origin will be matched.
        rel - (optional) type IRI of the relationship (similar to an RDF predicate), or set of values. If omitted any relationship will be matched.
        target - (optional) target of the relationship (similar to an RDF object), a boolean, floating point or unicode object, or set of values. If omitted any target will be matched.
        attrs - (optional) attribute mapping of relationship metadata, i.e. {attrname1: attrval1, attrname2: attrval2}. If any attribute is specified, an exact match is made (i.e. the attribute name and value must match).
        include_ids - If true include statement IDs with yield values
        '''
        raise NotImplementedError
        origin = origin if origin is None or isinstance(origin, set) else set([origin])
        rel = rel if rel is None or isinstance(rel, set) else set([rel])
        target = target if target is None or isinstance(target, set) else set([target])
        for index, curr_rel in enumerate(self._relationships):
            matches = True
            if origin and curr_rel[ORIGIN] not in origin:
                matches = False
            if rel and curr_rel[RELATIONSHIP] not in rel:
                matches = False
            if target and curr_rel[TARGET] not in target:
                matches = False
            if attrs:
                for k, v in attrs.items():
                    if k not in curr_rel[ATTRIBUTES] or curr_rel[ATTRIBUTES].get(k) != v:
                        matches = False
            if matches:
                if include_ids:
                    yield index, (curr_rel[0], curr_rel[1], curr_rel[2], curr_rel[3].copy())
                else:
                    yield (curr_rel[0], curr_rel[1], curr_rel[2], curr_rel[3].copy())
        return

    def add(self, origin, rel, target, attrs=None):
        '''
        Add one relationship to the model

        origin - origin of the relationship (similar to an RDF subject)
        rel - type IRI of the relationship (similar to an RDF predicate)
        target - target of the relationship (similar to an RDF object), a boolean, floating point or unicode object
        attrs - optional attribute mapping of relationship metadata, i.e. {attrname1: attrval1, attrname2: attrval2}
        '''
        if not origin: 
            raise ValueError('Relationship origin cannot be null')
        if not rel: 
            raise ValueError('Relationship ID cannot be null')

        attrs = attrs or {}

        with self._db_env.begin(write=True) as txn:
            rel = self._abbreviate(rel, txn)
            target = self._abbreviate(target, txn)
            nodedata = txn.get(origin.encode('utf-8'))
            if nodedata is None:
                nodedata = {rel: [[target, attrs]]}
            else:
                nodedata = msgpack.loads(nodedata, raw=False)
                nodedata.setdefault(rel, []).append([target, attrs])
            txn.put(origin.encode('utf-8'), msgpack.dumps(nodedata, use_bin_type=True))
        return

    def add_many(self, rels):
        '''
        Add a list of relationships to the extent

        rels - a list of 0 or more relationship tuples, e.g.:
        [
            (origin, rel, target, {attrname1: attrval1, attrname2: attrval2}),
        ]

        origin - origin of the relationship (similar to an RDF subject)
        rel - type IRI of the relationship (similar to an RDF predicate)
        target - target of the relationship (similar to an RDF object), a boolean, floating point or unicode object
        attrs - optional attribute mapping of relationship metadata, i.e. {attrname1: attrval1, attrname2: attrval2}
        '''
        for curr_rel in rels:
            attrs = {}
            if len(curr_rel) == 3:
                origin, rel, target = curr_rel
            elif len(curr_rel) == 4:
                origin, rel, target, attrs = curr_rel
            else:
                raise ValueError
            self.add(origin, rel, target, attrs)
        return

    #FIXME: Replace with a match_to_remove method
    def remove(self, index):
        '''
        Delete one or more relationship, by index, from the extent

        index - either a single index or a list of indices
        '''
        raise NotImplementedError
        if hasattr(index, '__iter__'):
            ind = set(index)
        else:
            ind = [index]

        # Rebuild relationships, excluding the provided indices
        self._relationships = [r for i, r in enumerate(self._relationships) if i not in ind]

    def __getitem__(self, i):
        raise NotImplementedError

    def __eq__(self, other):
        return repr(other) == repr(self)

    def _abbreviations(self, txn):
        prefix_map = txn.get(b'@_abbreviations')
        prefix_map = msgpack.loads(prefix_map, raw=False)
        return prefix_map
        
    def _abbreviate(self, rid, txn):
        '''
        Abbreviate a relationship or resource ID target for efficient storage
        in the DB. Works only with a prefix/suffix split of hierarchical HTTP-like IRIs,
        e.g. 'http://example.org/spam/eggs' becomes something like '{a23}eggs'
        and afterward there will be an entry in the prefix map from 'a23' to 'http://example.org/spam/'
        The map can then easily be used with str.format
        '''
        if not isinstance(rid, str) or '/' not in rid or not iri.matches_uri_syntax(rid):
            return rid
        head, tail = rid.rsplit('/', 1)
        head += '/'
        prefix_map = txn.get(b'@_abbreviations')
        assert prefix_map is not None
        prefix_map = msgpack.loads(prefix_map, raw=False)
        #FIXME: probably called too often to do this every time
        inv_prefix_map = {v: k for k, v in prefix_map.items()}
        if head in inv_prefix_map:
            prefix = inv_prefix_map[head]
        else:
            prefix = f'a{self._abbr_index}'
            prefix_map[prefix] = head
            self._abbr_index += 1
            txn.put(b'@_abbreviations', msgpack.dumps(prefix_map, use_bin_type=True))
        post_rid = '{' + prefix + '}' + tail.replace('{', '{{').replace('}', '}}')
        return post_rid
        
    def _ensure_abbreviations(self, txn):
        txn.put(b'@_abbreviations', msgpack.dumps({}))
        return

    def __del__(self):
        #self._db_env.close()
        pass
