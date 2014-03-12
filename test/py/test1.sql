--
-- PostgreSQL database dump
--

COMMENT ON DATABASE versa_test IS 'A temp DB for Versa test suite';


CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;


COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';


SET search_path = public, pg_catalog;

SET default_tablespace = '';

SET default_with_oids = false;

CREATE TABLE attribute (
    rawid integer,
    name text,
    value text
);

CREATE TABLE relationship (
    rawid integer NOT NULL,
    id text,
    subj text NOT NULL,
    pred text NOT NULL,
    obj text NOT NULL
);


CREATE SEQUENCE relationship_rawid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE relationship_rawid_seq OWNED BY relationship.rawid;

ALTER TABLE ONLY relationship ALTER COLUMN rawid SET DEFAULT nextval('relationship_rawid_seq'::regclass);

COPY attribute (rawid, name, value) FROM stdin;
1	@context	http://copia.ogbuji.net#_metadata
2	@context	http://copia.ogbuji.net#_metadata
2	@lang	en
3	@context	http://uche.ogbuji.net#_metadata
4	@context	http://uche.ogbuji.net#_metadata
4	@lang	en
5	@context	http://uche.ogbuji.net#_metadata
5	@lang	ig
\.


COPY relationship (rawid, id, subj, pred, obj) FROM stdin;
1	\N	http://copia.ogbuji.net	http://purl.org/dc/elements/1.1/creator	Uche Ogbuji
2	\N	http://copia.ogbuji.net	http://purl.org/dc/elements/1.1/title	Copia
3	\N	http://uche.ogbuji.net	http://purl.org/dc/elements/1.1/creator	Uche Ogbuji
4	\N	http://uche.ogbuji.net	http://purl.org/dc/elements/1.1/title	Uche's home
5	\N	http://uche.ogbuji.net	http://purl.org/dc/elements/1.1/title	Ulo Uche
\.


SELECT pg_catalog.setval('relationship_rawid_seq', 5, true);

ALTER TABLE ONLY relationship
    ADD CONSTRAINT relationship_id_key UNIQUE (id);

ALTER TABLE ONLY relationship
    ADD CONSTRAINT relationship_pkey PRIMARY KEY (rawid);

CREATE INDEX main_attribute_index ON attribute USING btree (name, value);

CREATE INDEX main_relationship_index ON relationship USING btree (subj, pred);

ALTER TABLE ONLY attribute
    ADD CONSTRAINT attribute_rawid_fkey FOREIGN KEY (rawid) REFERENCES relationship(rawid);


--
-- PostgreSQL database dump complete
--

