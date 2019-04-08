#A PostgreSQL driver for Akara Dendrite, a Web semi-structured metadata tool
'''

[
    (origin, rel, target, {attrname1: attrval1, attrname2: attrval2}),
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

    def size(self):
        '''Return the number of links in the model'''
        cur = self._conn.cursor()
        querystr = "SELECT COUNT(*) FROM relationship;"
        cur.execute(querystr)
        result = cur.fetchone()
        return result[0]

    def __iter__(self):
        cur = self._conn.cursor()
        tables = "relationship"
        querystr = "SELECT relationship.rawid, relationship.origin, relationship.rel, relationship.target, attribute.name, attribute.value FROM relationship FULL JOIN attribute ON relationship.rawid = attribute.rawid;".format(tables)
        cur.execute(querystr)
        return self._process_db_rows_iter(cur)

    def match(self, origin=None, rel=None, target=None, attrs=None, include_ids=False):
        '''
        Retrieve an iterator of relationship IDs that match a pattern of components

        origin - (optional) origin of the relationship (similar to an RDF subject). If omitted any origin will be matched.
        rel - (optional) type IRI of the relationship (similar to an RDF predicate). If omitted any relationship will be matched.
        target - (optional) target of the relationship (similar to an RDF object), a boolean, floating point or unicode object. If omitted any target will be matched.
        attrs - (optional) attribute mapping of relationship metadata, i.e. {attrname1: attrval1, attrname2: attrval2}. If any attribute is specified, an exact match is made (i.e. the attribute name and value must match).
        include_ids - If true include statement IDs with yield values
        '''
        #FIXME: Implement include_ids
        cur = self._conn.cursor()
        conditions = ""
        and_placeholder = ""
        tables = "relationship"
        params = []
        if origin:
            conditions += "relationship.origin = %s"
            params.append(origin)
            and_placeholder = " AND "
        if target:
            conditions += and_placeholder + "relationship.target = %s"
            params.append(target)
            and_placeholder = " AND "
        if rel:
            conditions += and_placeholder + "relationship.rel = %s"
            params.append(rel)
            and_placeholder = " AND "
        if attrs:
            tables = "relationship, attribute"
            for a_name, a_val in attrs.items():
                conditions += and_placeholder + "EXISTS (SELECT 1 from attribute AS subattr WHERE subattr.rawid = relationship.rawid AND subattr.name = %s AND subattr.value = %s)"
                params.extend((a_name, a_val))
                and_placeholder = " AND "
        #querystr = "SELECT relationship.rawid, relationship.origin, relationship.rel, relationship.target, attribute.name, attribute.value FROM {0} WHERE {1} ORDER BY relationship.rawid;".format(tables, conditions)
        #SELECT relationship.rawid, attribute.rawid, relationship.origin, relationship.rel, relationship.target, attribute.name, attribute.value FROM relationship FULL JOIN attribute ON relationship.rawid = attribute.rawid WHERE relationship.origin = 'http://uche.ogbuji.net' AND EXISTS (SELECT 1 from attribute AS subattr WHERE subattr.rawid = relationship.rawid AND subattr.name = '@context' AND subattr.value = 'http://uche.ogbuji.net#_metadata') AND EXISTS (SELECT 1 from attribute AS subattr WHERE subattr.rawid = relationship.rawid AND subattr.name = '@lang' AND subattr.value = 'ig') ORDER BY relationship.rawid;
        querystr = "SELECT relationship.rawid, relationship.origin, relationship.rel, relationship.target, attribute.name, attribute.value FROM relationship FULL JOIN attribute ON relationship.rawid = attribute.rawid WHERE {1} ORDER BY relationship.rawid;".format(tables, conditions)
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
            curr_rel = None
            attrs = None
            #Each relgroup are the DB rows corresponding to a single relationship,
            #With redundant origin/rel/target but the sequence of attributes
            for row in relgroup:
                (rawid, origin, rel, target, a_name, a_val) = row
                #self._logger.debug('Row: {0}'.format(repr(row)))
                if not curr_rel: curr_rel = (origin, rel, target)
                if a_name:
                    if not attrs:
                        attrs = {}
                        curr_rel = (origin, rel, target, attrs)
                    attrs[a_name] = a_val
            yield curr_rel
        cursor.close()
        self._conn.rollback() #Finish with the transaction
        return

    def add(self, origin, rel, target, attrs=None, rid=None):
        '''
        Add one relationship to the extent

        origin - origin of the relationship (similar to an RDF subject)
        rel - type IRI of the relationship (similar to an RDF predicate)
        target - target of the relationship (similar to an RDF object), a boolean, floating point or unicode object
        attrs - optional attribute mapping of relationship metadata, i.e. {attrname1: attrval1, attrname2: attrval2}
        rid - optional ID for the relationship in IRI form. If not specified one will be generated.

        '''
        #FIXME no it doesn't re:
        #returns an ID (IRI) for the resulting relationship
        cur = self._conn.cursor()
        #relationship.
        if rid:
            querystr = "INSERT INTO relationship (origin, rel, target, rid) VALUES (%s, %s, %s, %s) RETURNING rawid;"
            cur.execute(querystr, (origin, rel, target, rid))
        else:
            querystr = "INSERT INTO relationship (origin, rel, target) VALUES (%s, %s, %s) RETURNING rawid;"
            cur.execute(querystr, (origin, rel, target))
        rawid = cur.fetchone()[0]
        for a_name, a_val in attrs.items():
            querystr = "INSERT INTO attribute (rawid, name, value) VALUES (%s, %s, %s);"
            cur.execute(querystr, (rawid, a_name, a_val))
        self._conn.commit()
        cur.close()
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

    def close(self):
        '''Set up a new table space for the first time'''
        self._conn.close()
        return


SQL_MODEL = '''
CREATE TABLE relationship (
    rawid    SERIAL PRIMARY KEY,  -- a low level, internal ID purely for effieicnt referential integrity
    id       TEXT UNIQUE,         --The higher level relationship ID
    origin   TEXT NOT NULL,
    rel      TEXT NOT NULL,
    target   TEXT NOT NULL
);

CREATE TABLE attribute (
    rawid    INT REFERENCES relationship (rawid),
    name     TEXT,
    value    TEXT
);

CREATE INDEX main_relationship_index ON relationship (origin, rel);

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

