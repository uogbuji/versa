#Simple in-memory driver for Versa, a Web semi-structured metadata tool
'''

[
    (origin, rel, target, {attrname1: attrval1, attrname2: attrval2}),
]

The optional attributes are metadata bound to the statement itself

'''

#Note: for PyPy support port to pg8000 <http://pybrary.net/pg8000/>
#Reportedly PyPy/pg8000 is faster than CPython/psycopg2

import logging
import functools
#from itertools import groupby
#from operator import itemgetter
from amara3 import iri #for absolutize & matches_uri_syntax

from versa.driver import connection_base
from versa import I, ORIGIN, RELATIONSHIP, TARGET, ATTRIBUTES

class connection(connection_base):
    def __init__(self, baseiri=None, attr_cls=dict, logger=None):
        '''
        '''
        self._attr_cls = attr_cls # class used to hold attributes within a relationship
        self.create_space()
        self._baseiri = baseiri
        self._id_counter = 1
        self._logger = logger or logging
        return

    def create_space(self):
        '''Set up a new table space for the first time'''
        self._relationships = []
        self._id_counter = 1
        return

    def drop_space(self):
        '''Dismantle an existing table space'''
        create_space(self)
        return

    def query(self, expr):
        '''Execute a Versa query'''
        raise NotImplementedError

    def size(self):
        '''Return the number of links in the model'''
        return len(self._relationships)

    def __iter__(self):
        for index, rel in enumerate(self._relationships): yield index, (rel[0], rel[1], rel[2], rel[3].copy())

    #FIXME: For performance make each link an iterator, so that slice/copy isn't necessary?

    def match(self, origin=None, rel=None, target=None, attrs=None, include_ids=False):
        '''
        Retrieve an iterator of relationship IDs that match a pattern of components

        origin - (optional) origin of the relationship (similar to an RDF subject). If omitted any origin will be matched.
        rel - (optional) type IRI of the relationship (similar to an RDF predicate). If omitted any relationship will be matched.
        target - (optional) target of the relationship (similar to an RDF object), a boolean, floating point or unicode object. If omitted any target will be matched.
        attrs - (optional) attribute mapping of relationship metadata, i.e. {attrname1: attrval1, attrname2: attrval2}. If any attribute is specified, an exact match is made (i.e. the attribute name and value must match).
        include_ids - If true include statement IDs with yield values
        '''
        #Can't use items or we risk client side RuntimeError: dictionary changed size during iteration
        for index, curr_rel in enumerate(self._relationships):
            matches = True
            if origin and origin != curr_rel[ORIGIN]:
                matches = False
            if rel and rel != curr_rel[RELATIONSHIP]:
                matches = False
            if target and target != curr_rel[TARGET]:
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

    def add(self, origin, rel, target, attrs=None, index=None):
        '''
        Add one relationship to the extent

        origin - origin of the relationship (similar to an RDF subject)
        rel - type IRI of the relationship (similar to an RDF predicate)
        target - target of the relationship (similar to an RDF object), a boolean, floating point or unicode object
        attrs - optional attribute mapping of relationship metadata, i.e. {attrname1: attrval1, attrname2: attrval2}
        index - optional position for the relationship to be inserted
        '''
        #FIXME: return an ID (IRI) for the resulting relationship?
        assert rel

        # convert attribute class to the expected type
        if type(attrs) != type(self._attr_cls):
            attrs = self._attr_cls(attrs or {})

        item = (origin, rel, target, attrs)
        if index is not None:
            self._relationships.insert(index, item)
        else:
            self._relationships.append(item)

        return

    def add_many(self, rels):
        '''
        Add a list of relationships to the extent

        rels - a list of 0 or more relationship tuples, e.g.:
        [
            (origin, rel, target, {attrname1: attrval1, attrname2: attrval2}, rid),
        ]

        origin - origin of the relationship (similar to an RDF subject)
        rel - type IRI of the relationship (similar to an RDF predicate)
        target - target of the relationship (similar to an RDF object), a boolean, floating point or unicode object
        attrs - optional attribute mapping of relationship metadata, i.e. {attrname1: attrval1, attrname2: attrval2}
        rid - optional ID for the relationship in IRI form.  If not specified for any relationship, one will be generated.

        you can omit the dictionary of attributes if there are none, as long as you are not specifying a statement ID

        returns a list of IDs (IRI), one for each resulting relationship, in order
        '''
        for curr_rel in rels:
            attrs = self._attr_cls()
            rid = None
            if len(curr_rel) == 3:
                origin, rel, target = curr_rel
            elif len(curr_rel) == 4:
                origin, rel, target, attrs = curr_rel
            else:
                raise ValueError
            assert rel
            self.add(origin, rel, target, attrs)
        return

    def remove(self, index):
        '''
        Delete one or more relationship, by index, from the extent

        index - either a single index or a list of indices
        '''
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
        '''Set up a new table space for the first time'''
        self._relationships = []
        return

    def __repr__(self):
        '''
        Canonical representation used for equivalence testing in test cases
        '''
        import json
        from versa.util import OrderedJsonEncoder

        # Simple canonicalization of attributes for model sorting purposes
        # when model constructed with OrderedDict instances for attributes
        # (via attr_cls). Not canonical if only dict is used.
        # FIXME this doesn'yet handle the case of irirefs as keys or values
        # in the attributes
        rel_repr = functools.partial(json.dumps, cls=OrderedJsonEncoder)

        # rebuilding _relationships with sorted attributes
        rels = []
        for v in sorted(self._relationships, key=rel_repr):

            # Mark type of target as a pseudo attribute. Doesn't mutate
            # original Versa statement
            if isinstance(v[2], I):
                v[3]['@target-type'] = '@iri-ref'
            
            rels.append(v)

        return json.dumps(rels, indent=4, cls=OrderedJsonEncoder)

    def __eq__(self, other):
        return repr(other) == repr(self)
