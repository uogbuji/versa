#Dendrite: a Web semi-structured metadata tool
'''

[
    (subj, pred, obj, {attrname1: attrval1, attrname2: attrval2}),
]

The optional attributes are metadata bound to the statement itself

'''

class connection_base(object):
    def query(expr):
        '''Execute a Versa query'''
        raise NotImplementedError

    def match(self, subj=None, pred=None, obj=None, attrs=None):
        '''
        Retrieve an iterator of relationship IDs that match a pattern of components

        subj - optional subject or origin of the relationship, an IRI coded as a unicode object. If omitted any subject will be matched.
        pred - optional predicate or type of the relationship, an IRI coded as a unicode object. If omitted any predicate will be matched.
        obj - optional object of the relationship, a boolean, floating point or unicode object. If omitted any object will be matched.
        attrs - optional attribute mapping of relationship metadata, i.e. {attrname1: attrval1, attrname2: attrval2}. If any attribute is specified, an exact match is made (i.e. the attribute name and value must match).

        '''
        raise NotImplementedError

    def add(self, subj, pred, obj, attrs=None, rid=None):
        '''
        Add one relationship to the extent

        subj - subject or origin of the relationship, an IRI coded as a unicode object
        pred - predicate or type of the relationship, an IRI coded as a unicode object
        obj - object of the relationship, a boolean, floating point or unicode object
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
        raise NotImplementedError

    def delete(self, rids):
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

