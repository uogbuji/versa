#MongoDB driver for Versa, a Web semi-structured metadata tool
'''

[
    (origin, rel, target, {attrname1: attrval1, attrname2: attrval2}),
]

The optional attributes are metadata bound to the statement itself


Example of use, assuming a DB named 'versademo' already exists with an empty collection named model1

connstr = mongodb://verser:password31337@localhost/versademo



Note:

On MongoDB cmdline

> use versademo
> use admin
> db.auth('admin', 'XXX')
> db.createUser({user: 'verser', pwd: 'password31337', roles : [{role: 'readWrite', db: 'versademo'}, {role: 'dbAdmin', db: 'versademo'}]});
> db.auth('verser', 'password31337')
> use versademo
> db.createCollection('model1')

Note: when you log in you'll need authSource (in URL) or --authenticationDatabase (on cmdline)

e.g.

mongo 'mongodb://verser:password31337@localhost/?authSource=admin'

'''

import functools
#from itertools import groupby
#from operator import itemgetter

from amara3 import iri #for absolutize & matches_uri_syntax
from pymongo import MongoClient

from versa.driver import connection_base
from versa import I, ORIGIN, RELATIONSHIP, TARGET, ATTRIBUTES


def newmodel(collection=None, baseiri=None):
    return connection(collection=collection, baseiri=baseiri)

class connection(connection_base):
    #Meta items, e.g. the abbreviations map, so as not to be included in size()
    META_ITEM_COUNT = 1

    def __init__(self, collection=None, baseiri=None):
        '''
        Versa connection object built from MongoDB collection object
        '''
        if collection:
            self._db_coll = collection
        else:
            raise NotImplementedError('For now construct only from collection object')
        #self._conn = MongoClient(connstr)
        #lllists = db.lllists #DB
        #author_wd = lllists.author_wikidata  #Collection
        #item_authors = lllists.item_authors  #Collection
        
        self._ensure_abbreviations()
        #self.create_model()
        self._baseiri = baseiri
        self._abbr_index = 0
        return

    def copy(self, contents=True):
        '''Create a copy of this model, optionally without contents (i.e. just configuration)'''
        cp = connection(collection=self._db_coll, baseiri=self._baseiri)
        if contents: cp.add_many(self._relationships)
        return cp

    def create_collection(self):
        '''Set up a new table space for the first time'''
        raise NotImplementedError
        self._relationships = []
        #self._id_counter = 1
        return

    def drop_collection(self):
        '''Dismantle an existing table space'''
        raise NotImplementedError
        return

    def query(self, expr):
        '''Execute a Versa query'''
        raise NotImplementedError

    def size(self):
        '''Return the number of links in the model'''
        count = 0
        cursor = self._db_coll.find()
        for item in cursor:
            if item['origin'] == '@_abbreviations':
                continue
            count += len(item['rels'])
        return count
        #return  self._db_coll.count() - connection.META_ITEM_COUNT

    def __iter__(self):
        abbrevs = self._abbreviations()
        cursor = self._db_coll.find()
        index = 0
        for item in cursor:
            if item['origin'] == '@_abbreviations':
                continue
            origin = item['origin']
            for rel in item['rels']:
                relid = rel['rid']
                for target, attribs in rel['instances']:
                    yield index, (origin, relid.format(**abbrevs), target.format(**abbrevs), attribs)
                    index += 1

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
            cursor = self._db_coll.find()
        else:
            cursor = self._db_coll.find({'origin': origin})
            
        for item in cursor:
            if item['origin'] == '@_abbreviations':
                continue
            if origin != item['origin']:
                continue
            for xrel_obj in item['rels']:
                xrelid = xrel_obj['rid'].format(**abbrevs)
                if rel and rel != xrelid:
                    continue
                for xtarget, xattrs in xrel_obj['instances']:
                    index += 1
                    xtarget = xtarget.format(**abbrevs)
                    if target and target != xtarget:
                        continue
                    matches = True
                    if attrs:
                        for k, v in attrs.items():
                            if k not in xattrs or xattrs.get(k) != v:
                                matches = False
                    if matches:
                        if include_ids:
                            yield index, (origin, xrelid, xtarget, xattrs)
                        else:
                            yield origin, xrelid, xtarget, xattrs

                    #if matches:
                    #    if include_ids:
                    #        yield index, (curr_rel[0], curr_rel[1], curr_rel[2], curr_rel[3].copy())
                    #    else:
                    #        yield (curr_rel[0], curr_rel[1], curr_rel[2], curr_rel[3].copy())
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

        origin_item = self._db_coll.find_one({'origin': origin})
        rel = self._abbreviate(rel)
        target = self._abbreviate(target)
        rel_info = {'rid': rel, 'instances': [[target, attrs]]}
        if origin_item is None:
            self._db_coll.insert_one(
                {
                    'origin': origin,
                    'rels': [rel_info],
                }
            )
        else:
            origin_item['rels'].append(rel_info)
            self._db_coll.replace_one(
                {'origin': origin}, origin_item
            )
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

    def add_iri_prefix(self, prefix):
        '''
        Add an IRI prefix, for efficiency of table scan searches

        XXX We might or might not need such a method, based on perf testing
        '''
        raise NotImplementedError

    def close(self):
        raise NotImplementedError

    def __getitem__(self, i):
        raise NotImplementedError

    def __eq__(self, other):
        return repr(other) == repr(self)

    def _abbreviations(self):
        abbrev_obj = self._db_coll.find_one({'origin': '@_abbreviations'})
        return abbrev_obj['map']
        
    def _abbreviate(self, rid):
        '''
        Abbreviate a relationship or resource ID target for efficient storage
        in the DB. Works only with a prefix/suffix split of hierarchical HTTP-like IRIs,
        e.g. 'http://example.org/spam/eggs' becomes something like '{a23}eggs'
        and afterward there will be an entry in the prefix map from 'a23' to 'http://example.org/spam/'
        The map can then easily be used with str.format
        '''
        if not isinstance(rid, str) or not iri.matches_uri_syntax(rid): return rid
        head, tail = rid.rsplit('/', 1)
        head += '/'
        abbrev_obj = self._db_coll.find_one({'origin': '@_abbreviations'})
        assert abbrev_obj is not None
        pmap = abbrev_obj['map']
        #FIXME: probably called too often to do this every time
        inv_pmap = {v: k for k, v in pmap.items()}
        if head in inv_pmap:
            prefix = inv_pmap[head]
        else:
            prefix = f'a{self._abbr_index}'
            pmap[prefix] = head
            self._abbr_index += 1
            self._db_coll.replace_one(
                {'origin': '@_abbreviations'},
                {'origin': '@_abbreviations', 'map': pmap}
            )
        post_rid = '{' + prefix + '}' + tail
        return post_rid
        
    def _ensure_abbreviations(self):
        abbrev_obj = self._db_coll.find_one({'origin': '@_abbreviations'})
        if abbrev_obj is None:
            self._db_coll.insert_one({'origin': '@_abbreviations', 'map': {}})
        return
        
