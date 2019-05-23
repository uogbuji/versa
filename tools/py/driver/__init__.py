'''

[
    (origin, rel, target, {attrname1: attrval1, attrname2: attrval2}),
]

The optional attributes are metadata bound to the statement itself

'''

class connection_base(object):
    @classmethod
    def newmodel(cls, baseiri=None):
        '''
        Return a new, empty Versa model
        '''
        return cls(baseiri=baseiri)

    def query(self, expr):
        '''Execute a Versa query'''
        raise NotImplementedError

    def match(self, origin=None, rel=None, target=None, attrs=None, include_ids=False):
        '''
        Retrieve an iterator of relationship IDs that match a pattern of components

        origin - (optional) origin of the relationship (similar to an RDF subject). If omitted any origin will be matched.
        rel - (optional) type IRI of the relationship (similar to an RDF predicate). If omitted any relationship will be matched.
        target - (optional) target of the relationship (similar to an RDF object), a boolean, floating point or unicode object. If omitted any target will be matched.
        attrs - optional attribute mapping of relationship metadata, i.e. {attrname1: attrval1, attrname2: attrval2}. If any attribute is specified, an exact match is made (i.e. the attribute name and value must match).
        include_ids - If true include statement IDs with yield values
        '''
        raise NotImplementedError

    def add(self, origin, rel, target, attrs=None, rid=None):
        '''
        Add one relationship to the extent

        origin - origin of the relationship (similar to an RDF subject)
        rel - type IRI of the relationship (similar to an RDF predicate)
        target - target of the relationship (similar to an RDF object), a boolean, floating point or unicode object
        attrs - optional attribute mapping of relationship metadata, i.e. {attrname1: attrval1, attrname2: attrval2}
        rid - optional ID for the relationship in IRI form. If not specified one will be generated.

        returns an ID (IRI) for the resulting relationship
        '''
        raise NotImplementedError

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
        raise NotImplementedError

    def remove(self, rids):
        '''
        Delete one or more relationship, by ID, from the extent

        rids - either a single ID or an sequence or iterator of IDs
        '''
        raise NotImplementedError

    def add_iri_prefix(self, prefix):
        '''
        Add an IRI prefix, for efficiency of table scan searches

        XXX We might or might not need such a method, based on perf testing
        '''
        raise NotImplementedError

#import postgresql

#DRIVERS = {
#    'http://purl.org/xml3k/akara/dendrite/drivers/postgresql': postgresql.connection,
#}

