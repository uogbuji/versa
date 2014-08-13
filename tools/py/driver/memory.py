#Simple in-memory driver for Versa, a Web semi-structured metadata tool
'''

[
    (subj, pred, obj, {attrname1: attrval1, attrname2: attrval2}),
]

The optional attributes are metadata bound to the statement itself

'''

#Note: for PyPy support port to pg8000 <http://pybrary.net/pg8000/>
#Reportedly PyPy/pg8000 is faster than CPython/psycopg2

import logging
#from itertools import groupby
#from operator import itemgetter
from amara3 import iri #for absolutize & matches_uri_syntax

from versa.driver import connection_base
from versa import ORIGIN, RELATIONSHIP, TARGET, ATTRIBUTES

class connection(connection_base):
    def __init__(self, baseuri=None, logger=None):
        '''
        '''
        self.create_space()
        self._baseuri = baseuri
        self._id_counter = 1
        self._logger = logger or logging
        return

    def create_space(self):
        '''Set up a new table space for the first time'''
        self._relationships = {}
        self._id_counter = 1
        return

    def drop_space(self):
        '''Dismantle an existing table space'''
        create_space(self)
        return

    def generate_resource(self):
        if self._baseuri:
            return iri.absolutize(str(self._id_counter), self._baseuri)
        else:
            return str(self._id_counter)

    def query(self, expr):
        '''Execute a Versa query'''
        raise NotImplementedError

    def __iter__(self):
        for rid, rel in self._relationships.items(): yield rid, (rel[0], rel[1], rel[2], rel[3].copy())

    #FIXME: For performance make each link an iterator, so that slice/copy isn't necessary?

    def match(self, subj=None, pred=None, obj=None, attrs=None, include_ids=False):
        '''
        Retrieve an iterator of relationship IDs that match a pattern of components

        subj - optional subject or origin of the relationship, an IRI coded as a unicode object. If omitted any subject will be matched.
        pred - optional predicate or type of the relationship, an IRI coded as a unicode object. If omitted any predicate will be matched.
        obj - optional object of the relationship, a boolean, floating point or unicode object. If omitted any object will be matched.
        attrs - optional attribute mapping of relationship metadata, i.e. {attrname1: attrval1, attrname2: attrval2}. If any attribute is specified, an exact match is made (i.e. the attribute name and value must match).

        '''
        for rid, rel in self._relationships.items(): #Can't use items or we risk RuntimeError: dictionary changed size during iteration

            matches = True
            if subj and subj != rel[ORIGIN]:
                matches = False
            if pred and pred != rel[RELATIONSHIP]:
                matches = False
            if obj and obj != rel[TARGET]:
                matches = False
            if attrs:
                for k, v in attrs.items():
                    if k not in rel[ATTRIBUTES] or rel[ATTRIBUTES].get(k) != v:
                        matches = False
            if matches:
                if include_ids:
                    yield rid, (rel[0], rel[1], rel[2], rel[3].copy())
                else:
                    yield (rel[0], rel[1], rel[2], rel[3].copy())
        return

    def add(self, subj, pred, obj, attrs=None, rid=None):
        '''
        Add one relationship to the extent

        subj - subject or origin of the relationship, an IRI coded as a unicode object
        pred - predicate or type of the relationship, an IRI coded as a unicode object
        obj - object of the relationship, a boolean, floating point or unicode object
        attrs - optional attribute mapping of relationship metadata, i.e. {attrname1: attrval1, attrname2: attrval2}
        rid - optional ID for the relationship in IRI form. If not specified one will be generated.
        '''
        #FIXME: return an ID (IRI) for the resulting relationship?
        attrs = attrs or {}
        if rid is None:
            rid = self.generate_resource()
            self._id_counter += 1
        self._relationships[rid] = (subj, pred, obj, attrs)
        return

    def add_many(self, rels):
        '''
        Add a list of relationships to the extent

        rels - a list of 0 or more relationship tuples, e.g.:
        [
            (subj, pred, obj, {attrname1: attrval1, attrname2: attrval2}, rid),
        ]

        subj - subject or origin of the relationship, an an IRI coded as a unicode object
        pred - predicate or type of the relationship, an an IRI coded as a unicode object
        obj - object of the relationship, a boolean, floating point or unicode object
        attrs - optional attribute mapping of relationship metadata, i.e. {attrname1: attrval1, attrname2: attrval2}
        rid - optional ID for the relationship in IRI form.  If not specified for any relationship, one will be generated.

        you can omit the dictionary of attributes if there are none, as long as you are not specifying a statement ID

        returns a list of IDs (IRI), one for each resulting relationship, in order
        '''
        for rel in rels:
            attrs = {}
            rid = None
            if len(rel) == 3:
                subj, pred, obj = rel
            elif len(rel) == 4:
                subj, pred, obj, attrs = rel
            elif len(rel) == 5:
                subj, pred, obj, attrs, rid = rel
            else:
                raise ValueError
            self.add(subj, pred, obj, attrs, ridNone)
        return

    def delete(rids):
        '''
        Delete one or more relationship, by ID, from the extent

        rids - either a single ID or an sequence or iterator of IDs
        '''
        if isinstance(rids, basestring):
            del self._relationships[rids]
        else:
            for rid in rids:
                del self._relationships[rid]

    def add_iri_prefix(prefix):
        '''
        Add an IRI prefix, for efficiency of table scan searches

        XXX We might or might not need such a method, based on perf testing
        '''
        raise NotImplementedError

    def close(self):
        '''Set up a new table space for the first time'''
        self._relationships = {}
        return

