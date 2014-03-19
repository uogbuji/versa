'''

Requires http://pypi.python.org/pypi/nose-testconfig/ e.g.:

pip install nose-testconfig

----

Before running this, run:

createdb -U vuser versa_test "A temp DB for Versa test suite"

(replacing "vuser" with your user name, or omitting it for the default)


Use the nosetests command line to pass in your PG password, e.g.:

VUSER=vuser; VPASS=VUPassword; nosetests test/py/test_postgres.py --tc=pguser:$VUSER --tc=pgpasswd:$VPASS

or to debug:

VUSER=vuser; VPASS=VUPassword; nosetests test/py/test_postgres.py --tc=pguser:$VUSER --tc=pgpasswd:$VPASS --tc=debug:y


----

If something breaks and the temp DB isn't cleaned up, you can do:

VUSER=vuser; VPASS=VUPassword; python -c "import psycopg2; from versa.driver import postgres; c = postgres.connection('host=localhost dbname=versa_test user=$VUSER password=$VPASS'); c.drop_space()"

Replace host and password as needed

If you want to set up the temp DB for playing around, do:

createdb -U vuser versa_test "Test DB for Versa."
psql -U vuser versa_test < test/py/test1.sql

Then you can fiddle around:

psql -U vuser versa_test

SELECT relationship.rawid, relationship.subj, relationship.pred, relationship.obj FROM relationship, attribute WHERE relationship.subj = 'http://copia.ogbuji.net';
SELECT relationship.rawid, relationship.subj, relationship.pred, relationship.obj FROM relationship, attribute WHERE relationship.subj = 'http://copia.ogbuji.net' AND relationship.rawid = attribute.rawid AND attribute.name = '@context' AND attribute.value = 'http://copia.ogbuji.net#metadata';
SELECT relationship.rawid, relationship.subj, relationship.pred, relationship.obj, attribute.name, attribute.value FROM relationship, attribute WHERE relationship.subj = 'http://copia.ogbuji.net' AND relationship.rawid = attribute.rawid AND attribute.name = '@context' AND attribute.value = 'http://copia.ogbuji.net#metadata';


versa_test=# SELECT relationship.rawid, attribute.rawid, relationship.subj, relationship.pred, relationship.obj, attribute.name, attribute.value FROM relationship FULL JOIN attribute ON relationship.rawid = attribute.rawid WHERE relationship.subj = 'http://copia.ogbuji.net' AND EXISTS (SELECT 1 from attribute AS subattr WHERE subattr.rawid = relationship.rawid AND subattr.name = '@context' AND subattr.value = 'http://copia.ogbuji.net#_metadata');
 rawid | rawid |          subj           |                  pred                   |     obj     |   name   |               value               
-------+-------+-------------------------+-----------------------------------------+-------------+----------+-----------------------------------
     1 |     1 | http://copia.ogbuji.net | http://purl.org/dc/elements/1.1/creator | Uche Ogbuji | @context | http://copia.ogbuji.net#_metadata
     2 |     2 | http://copia.ogbuji.net | http://purl.org/dc/elements/1.1/title   | Copia       | @context | http://copia.ogbuji.net#_metadata
     2 |     2 | http://copia.ogbuji.net | http://purl.org/dc/elements/1.1/title   | Copia       | @lang    | en
(3 rows)

versa_test=# SELECT relationship.rawid, attribute.rawid, relationship.subj, relationship.pred, relationship.obj, attribute.name, attribute.value FROM relationship FULL JOIN attribute ON relationship.rawid = attribute.rawid WHERE relationship.subj = 'http://uche.ogbuji.net' AND EXISTS (SELECT 1 from attribute AS subattr WHERE subattr.rawid = relationship.rawid AND subattr.name = '@context' AND subattr.value = 'http://uche.ogbuji.net#_metadata') ORDER BY relationship.rawid;
 rawid | rawid |          subj          |                  pred                   |     obj     |   name   |              value               
-------+-------+------------------------+-----------------------------------------+-------------+----------+----------------------------------
     3 |     3 | http://uche.ogbuji.net | http://purl.org/dc/elements/1.1/creator | Uche Ogbuji | @context | http://uche.ogbuji.net#_metadata
     4 |     4 | http://uche.ogbuji.net | http://purl.org/dc/elements/1.1/title   | Uche's home | @context | http://uche.ogbuji.net#_metadata
     4 |     4 | http://uche.ogbuji.net | http://purl.org/dc/elements/1.1/title   | Uche's home | @lang    | en
     5 |     5 | http://uche.ogbuji.net | http://purl.org/dc/elements/1.1/title   | Ulo Uche    | @context | http://uche.ogbuji.net#_metadata
     5 |     5 | http://uche.ogbuji.net | http://purl.org/dc/elements/1.1/title   | Ulo Uche    | @lang    | ig
(5 rows)

versa_test=# SELECT relationship.rawid, attribute.rawid, relationship.subj, relationship.pred, relationship.obj, attribute.name, attribute.value FROM relationship FULL JOIN attribute ON relationship.rawid = attribute.rawid WHERE relationship.subj = 'http://uche.ogbuji.net' AND EXISTS (SELECT 1 from attribute AS subattr WHERE subattr.rawid = relationship.rawid AND subattr.name = '@context' AND subattr.value = 'http://uche.ogbuji.net#_metadata') AND EXISTS (SELECT 1 from attribute AS subattr WHERE subattr.rawid = relationship.rawid AND subattr.name = '@lang' AND subattr.value = 'ig') ORDER BY relationship.rawid;
 rawid | rawid |          subj          |                 pred                  |   obj    |   name   |              value               
-------+-------+------------------------+---------------------------------------+----------+----------+----------------------------------
     5 |     5 | http://uche.ogbuji.net | http://purl.org/dc/elements/1.1/title | Ulo Uche | @context | http://uche.ogbuji.net#_metadata
     5 |     5 | http://uche.ogbuji.net | http://purl.org/dc/elements/1.1/title | Ulo Uche | @lang    | ig
(2 rows)


See also:

 * http://www.postgresql.org/docs/9.1/static/app-pgdump.html
 * http://www.postgresql.org/docs/9.1/static/app-psql.html

'''

import logging

from nose import with_setup
from testconfig import config

from versa.driver import postgres

#If you do this you also need --nologcapture
#Handle  --tc=debug:y option
if config.get('debug', 'n').startswith('y'):
    logging.basicConfig(level=logging.DEBUG)

def pg_setup():
    "set up test fixtures"
    global conn
    pgpasswd = config['pgpasswd']
    pguser = config.get('pguser', 'postgres')
    conn = postgres.connection("host=localhost dbname=versa_test user={0} password={1}".format(pguser, pgpasswd))
    conn.create_space()
    return
    

def pg_teardown():
    "tear down test fixtures"
    #conn.drop_space()
    conn.close()
    return


@with_setup(pg_setup, pg_teardown)
def test_basics():
    "test ..."
    for (subj, pred, obj, attrs) in RELS_1:
        conn.add(subj, pred, obj, attrs)
    results = conn.match(subj='http://copia.ogbuji.net')
    logging.debug('BASICS PART 1')
    for result in results:
        logging.debug('Result: {0}'.format(repr(result)))
        #assert result == ()
    #assert results == None, "Boo! "

    results = conn.match(subj='http://uche.ogbuji.net', attrs={u'@lang': u'ig'})
    logging.debug('BASICS PART 2')
    results = list(results)
    for result in results:
        logging.debug('Result: {0}'.format(repr(result)))
        #assert result == ()
    expected = ('http://uche.ogbuji.net', 'http://purl.org/dc/elements/1.1/title', 'Ulo Uche', {'@context': 'http://uche.ogbuji.net#_metadata', '@lang': 'ig'})
    assert results[0] == expected, (results[0], expected)


RELS_1 = [
    ("http://copia.ogbuji.net", "http://purl.org/dc/elements/1.1/creator", "Uche Ogbuji", {"@context": "http://copia.ogbuji.net#_metadata"}),
    ("http://copia.ogbuji.net", "http://purl.org/dc/elements/1.1/title", "Copia", {"@context": "http://copia.ogbuji.net#_metadata", '@lang': 'en'}),
    ("http://uche.ogbuji.net", "http://purl.org/dc/elements/1.1/creator", "Uche Ogbuji", {"@context": "http://uche.ogbuji.net#_metadata"}),
    ("http://uche.ogbuji.net", "http://purl.org/dc/elements/1.1/title", "Uche's home", {"@context": "http://uche.ogbuji.net#_metadata", '@lang': 'en'}),
    ("http://uche.ogbuji.net", "http://purl.org/dc/elements/1.1/title", "Ulo Uche", {"@context": "http://uche.ogbuji.net#_metadata", '@lang': 'ig'}),
]

if __name__ == '__main__':
    raise SystemExit("use nosetests")
