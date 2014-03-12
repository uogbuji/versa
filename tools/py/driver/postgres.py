#A PostgreSQL driver for Akara Dendrite, a Web semi-structured metadata tool
'''

[
    (subj, pred, obj, {attrname1: attrval1, attrname2: attrval2}),
]

The optional attributes are metadata bound to the statement itself

'''

#Note: for PyPy support port to pg8000 <http://pybrary.net/pg8000/>
#Reportedly PyPy/pg8000 is faster than CPython/psycopg2

import logging
from itertools import groupby
from operator import itemgetter

import psycopg2 #http://initd.org/psycopg/

from versa.driver import connection_base

class connection(connection_base):
    def __init__(self, connstr, logger=None):
        '''
        connstr - the Postgres connection string
        '''
        self._conn = psycopg2.connect(connstr)
        self._logger = logger or logging
        return

    def create_space(self):
        '''Set up a new table space for the first time'''
        cur = self._conn.cursor()
        cur.execute(SQL_MODEL)
        self._conn.commit()
        cur.close()
        return

    def drop_space(self):
        '''Dismantle an existing table space'''
        cur = self._conn.cursor()
        cur.execute(DROP_SQL_MODEL)
        self._conn.commit()
        cur.close()
        return

    def query(self, expr):
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
        cur = self._conn.cursor()
        conditions = u""
        and_placeholder = u""
        tables = u"relationship"
        params = []
        if subj:
            conditions += u"relationship.subj = %s"
            params.append(subj)
            and_placeholder = u" AND "
        if obj:
            conditions += and_placeholder + u"relationship.obj = %s"
            params.append(obj)
            and_placeholder = u" AND "
        if pred:
            conditions += and_placeholder + u"relationship.pred = %s"
            params.append(pred)
            and_placeholder = u" AND "
        if attrs:
            tables = u"relationship, attribute"
            for a_name, a_val in attrs.iteritems():
                conditions += and_placeholder + u"EXISTS (SELECT 1 from attribute AS subattr WHERE subattr.rawid = relationship.rawid AND subattr.name = %s AND subattr.value = %s)"
                params.extend((a_name, a_val))
                and_placeholder = u" AND "
        #querystr = u"SELECT relationship.rawid, relationship.subj, relationship.pred, relationship.obj, attribute.name, attribute.value FROM {0} WHERE {1} ORDER BY relationship.rawid;".format(tables, conditions)
        #SELECT relationship.rawid, attribute.rawid, relationship.subj, relationship.pred, relationship.obj, attribute.name, attribute.value FROM relationship FULL JOIN attribute ON relationship.rawid = attribute.rawid WHERE relationship.subj = 'http://uche.ogbuji.net' AND EXISTS (SELECT 1 from attribute AS subattr WHERE subattr.rawid = relationship.rawid AND subattr.name = '@context' AND subattr.value = 'http://uche.ogbuji.net#_metadata') AND EXISTS (SELECT 1 from attribute AS subattr WHERE subattr.rawid = relationship.rawid AND subattr.name = '@lang' AND subattr.value = 'ig') ORDER BY relationship.rawid;
        querystr = u"SELECT relationship.rawid, relationship.subj, relationship.pred, relationship.obj, attribute.name, attribute.value FROM relationship FULL JOIN attribute ON relationship.rawid = attribute.rawid WHERE {1} ORDER BY relationship.rawid;".format(tables, conditions)
        #self._logger.debug(x.format(url))
        self._logger.debug(cur.mogrify(querystr, params))
        cur.execute(querystr, params)
        #Use groupby to batch up the returning statements acording to rawid then rol up the attributes
        #return ( (s, p, o, dict([(n,v) for n,v in xxx])) for s, p, o in yyy)
        #cur.fetchone()
        #cur.close()
        return self._process_db_rows_iter(cur)

    def _process_db_rows_iter(self, cursor):
        '''
        Turn the low-level rows from the result of a standard query join
        into higher-level statements, yielded iteratively. Note this might lead to
        idle transaction errors?

        '''
        #Be aware of: http://packages.python.org/psycopg2/faq.html#problems-with-transactions-handling
        #The results will come back grouped by the raw relationship IDs, in order
        for relid, relgroup in groupby(cursor, itemgetter(0)):
            rel = None
            attrs = None
            #Each relgroup are the DB rows corresponding to a single relationship,
            #With redundant subject/predicate/object but the sequence of attributes
            for row in relgroup:
                (rawid, subj, pred, obj, a_name, a_val) = row
                #self._logger.debug('Row: {0}'.format(repr(row)))
                if not rel: rel = (subj, pred, obj)
                if a_name:
                    if not attrs:
                        attrs = {}
                        rel = (subj, pred, obj, attrs)
                    attrs[a_name] = a_val
            yield rel
        cursor.close()
        self._conn.rollback() #Finish with the transaction
        return

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
        cur = self._conn.cursor()
        #relationship.
        if rid:
            querystr = u"INSERT INTO relationship (subj, pred, obj, rid) VALUES (%s, %s, %s, %s) RETURNING rawid;"
            cur.execute(querystr, (subj, pred, obj, rid))
        else:
            querystr = u"INSERT INTO relationship (subj, pred, obj) VALUES (%s, %s, %s) RETURNING rawid;"
            cur.execute(querystr, (subj, pred, obj))
        rawid = cur.fetchone()[0]
        for a_name, a_val in attrs.iteritems():
            querystr = u"INSERT INTO attribute (rawid, name, value) VALUES (%s, %s, %s);"
            cur.execute(querystr, (rawid, a_name, a_val))
        self._conn.commit()
        cur.close()
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
        raise NotImplementedError

    def delete(rids):
        '''
        Delete one or more relationship, by ID, from the extent

        rids - either a single ID or an sequence or iterator of IDs
        '''
        raise NotImplementedError

    def add_iri_prefix(prefix):
        '''
        Add an IRI prefix, for efficiency of table scan searches

        XXX We might or might not need such a method, based on perf testing
        '''
        raise NotImplementedError

    def close(self):
        '''Set up a new table space for the first time'''
        self._conn.close()
        return


SQL_MODEL = '''
CREATE TABLE relationship (
    rawid    SERIAL PRIMARY KEY,  -- a low level, internal ID purely for effieicnt referential integrity
    id       TEXT UNIQUE,         --The higher level relationship ID
    subj     TEXT NOT NULL,
    pred     TEXT NOT NULL,
    obj      TEXT NOT NULL
);

CREATE TABLE attribute (
    rawid    INT REFERENCES relationship (rawid),
    name     TEXT,
    value    TEXT
);

CREATE INDEX main_relationship_index ON relationship (subj, pred);

CREATE INDEX main_attribute_index ON attribute (name, value);
'''

DROP_SQL_MODEL = '''
DROP INDEX main_relationship_index;

DROP INDEX main_attribute_index;

DROP TABLE attribute;

DROP TABLE relationship;
'''

#Some notes on arrays:
# * http://fossplanet.com/f15/%5Bgeneral%5D-general-postgres-performance-tips-when-using-array-169307/

"""
>>> import psycopg2
>>> conn = psycopg2.connect("dbname=test user=postgres password=PeeeGeee")
"""

#cur.execute("CREATE TABLE test (id serial PRIMARY KEY, num integer, data varchar);")

