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


'''

import functools
#from itertools import groupby
#from operator import itemgetter

from diskcache import Index #pip install diskcache

from amara3 import iri #for absolutize & matches_uri_syntax

from versa.driver import connection_base
from versa import I, ORIGIN, RELATIONSHIP, TARGET, ATTRIBUTES


def newmodel(dbdir, baseiri=None):
    '''
    Return a new, empty Versa model with DiskCache back end
    Warning: if there is DiskCache data already in dbdir, it will be erased.
    '''
    model = connection(dbdir=dbdir, baseiri=baseiri, clear=True)
    return model


class connection(connection_base):
    def __init__(self, dbdir=None, baseiri=None, clear=False):
        '''
        Versa connection object built from DiskCache collection object
        '''
        self._dbdir = dbdir
        self._db = Index(dbdir)
        if clear: self._db.clear()
        self._ensure_abbreviations()
        #self.create_model()
        self._baseiri = baseiri
        self._abbr_index = 0
        return

    def copy(self, contents=True):
        '''Create a copy of this model, optionally without contents (i.e. just configuration)'''
        cp = connection(dbdir=self._dbdir, baseiri=self._baseiri)
        # FIXME!!!!!
        if contents: cp.add_many(self._relationships)
        return cp

    def query(self, expr):
        '''Execute a Versa query'''
        raise NotImplementedError

    def size(self):
        '''Return the number of links in the model'''
        count = 0
        for origin in self._db:
            if origin.startswith('@'):
                continue
            for rel, targetplus in self._db[origin].items():
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
        abbrevs = self._abbreviations()
        index = 0
        if origin is None:
            extent = self._db
        else:
            extent = [origin]

        for origin in extent:
            if origin.startswith('@'):
                continue
            for xrel, xtargetplus in self._db.get(origin, {}).items():
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
                    except (KeyError, ValueError):
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
                            yield index, (origin, xrel, xtarget, xattrs)
                        else:
                            yield origin, xrel, xtarget, xattrs

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

        origin_obj = self._db.get(origin)
        rel = self._abbreviate(rel)
        target = self._abbreviate(target)
        
        if origin_obj is None:
            self._db[origin] = {rel: [(target, attrs)]}
        else:
            origin_obj.setdefault(rel, []).append((target, attrs))
            self._db[origin] = origin_obj
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

    def _abbreviations(self):
        abbrev_obj = self._db['@_abbreviations']
        return abbrev_obj
        
    def _abbreviate(self, rid):
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
        pmap = self._db['@_abbreviations']
        assert pmap is not None
        #FIXME: probably called too often to do this every time
        inv_pmap = {v: k for k, v in pmap.items()}
        if head in inv_pmap:
            prefix = inv_pmap[head]
        else:
            prefix = f'a{self._abbr_index}'
            pmap[prefix] = head
            self._abbr_index += 1
            self._db['@_abbreviations'] = pmap
        post_rid = '{' + prefix + '}' + tail.replace('{', '{{').replace('}', '}}')
        return post_rid
        
    def _ensure_abbreviations(self):
        if '@_abbreviations' not in self._db:
            self._db['@_abbreviations'] = {}
        return
        
