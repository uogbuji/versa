# versa.serial.rdfalite
'''
'''

import sys
import logging
import warnings
from itertools import *

#from versa.writer.rdfs import prep as statement_prep
from versa import I, VERSA_BASEIRI, ORIGIN, RELATIONSHIP, TARGET, ATTRIBUTES

from .util import statement_prep, dumb_triples, rdfize, versalinks
from versa.writer.rdf import mock_bnode, prep, RDF_TYPE, RDF_NS

from amara3 import iri
# from amara3.uxml import tree
from amara3.uxml.treeutil import *
from amara3.uxml import html5

__all__ = ['parse', 'parse_iter', 'write',
    # Non-standard
]


#SCHEMAORG_NS is proper name. Deprecate the other
SCHEMAORG_NS = SCHEMA_NS = 'http://schema.org/'
FOAF_NS = 'http://xmlns.com/foaf/0.1/'
DC_NS = 'http://purl.org/dc/terms/'
BFL_NS = 'http://bibfra.me/vocab/lite/'

DEFAULT_PREFIXES = {
    'rdf': RDF_NS,
    'schema': SCHEMA_NS,
    'foaf': FOAF_NS,
    'dc': DC_NS,
    'bf': BFL_NS,
}

logger = logging.getLogger('rdfalite')
verbose = True
if verbose:
    logger.setLevel(logging.DEBUG)

def toversa(htmlsource, model, source_uri):
    '''
    >>> import urllib
    >>> from versa.reader import rdfalite
    >>> from versa.driver import memory
    >>> m = memory.connection()
    >>> burl = 'http://link.delawarelibrary.org/'
    >>> with urllib.request.urlopen(burl) as resourcefp: rdfalite.toversa(resourcefp.read(), m, burl)

    '''
    sink = versalinks(model)
    next(sink) #Prime the coroutine
    return parse(htmlsource, sink, source_uri)


def tordf(htmlsource, rdfgr, source_uri):
    '''

    '''
    sink = rdfize(rdfgr)
    next(sink) #Prime the coroutine
    return parse(htmlsource, sink, source_uri)


def totriples(htmlsource, triples, source_uri):
    '''

    '''
    sink = dumb_triples(triples)
    next(sink) #Prime the coroutine
    return parse(htmlsource, sink, source_uri)


def parse(htmlsource, statement_sink, source_uri):
    '''

    '''
    root = html5.parse(htmlsource)

    def do_parse(elem, resource, vocab=None, prop=None, prefixes=None):
        prefixes = prefixes or DEFAULT_PREFIXES.copy()
        vocab = elem.xml_attributes.get('vocab', vocab)
        #element_satisfied = False
        if vocab:
            prefix = elem.xml_attributes.get('prefix')
            if prefix:
                #logging.debug('{}'.format(prefix))
                prefix_bits = prefix.split()
                # a, b = tee(prefix.split())
                # next(b, None)
                # for p, ns in zip(a, b):
                #     p = p.strip().strip(':')
                #     ns = ns.strip()
                #     print((p, ns))
                #     #print(p, ns)
                #     prefixes[p] = ns
                for i, j in zip(range(0, len(prefix_bits), 2), range(1, len(prefix_bits), 2)):
                    p = prefix_bits[i].strip().strip(':')
                    ns = prefix_bits[j].strip()
                    #print(p, ns)
                    prefixes[p] = ns
            new_resource = elem.xml_attributes.get('resource')
            if new_resource:
                try:
                    resource = new_resource = I(iri.absolutize(new_resource, source_uri))
                except ValueError:
                    warnings.warn('Invalid URL or anchor {} found in {}. Ignored.'.format(new_resource, source_uri))
                    new_resource = None

            typeof_list = elem.xml_attributes.get('typeof')
            if typeof_list:
                if not new_resource: new_resource = mock_bnode('')
                for typeof in typeof_list.split():
                    try:
                        typeof = I(iri.absolutize(typeof, vocab))
                    except ValueError:
                        warnings.warn('Invalid URL or anchor {} found in {}. Ignored'.format(typeof, source_uri))
                    statement_sink.send((new_resource or resource, RDF_NS + 'type', typeof))

            new_prop_list = elem.xml_attributes.get('property')
            new_value = None
            if new_prop_list:
                if new_resource:
                    new_value = new_resource
                for new_prop in new_prop_list.split():
                    if new_prop == 'about':
                        continue
                    elif ':' in new_prop:
                        p, local = new_prop.split(':', 1)
                        if not p in prefixes:
                            #FIXME: Silent error for now
                            continue
                        try:
                            prop = I(iri.absolutize(local, prefixes[p]))
                        except ValueError:
                            warnings.warn('Invalid URL or anchor {} found in {}. Ignored'.format(local, source_uri))
                            continue
                    else:
                        try:
                            prop = I(iri.absolutize(new_prop, vocab))
                        except ValueError:
                            warnings.warn('Invalid URL or anchor {} found in {}. Ignored'.format(new_prop, source_uri))
                            continue
                    href_res = elem.xml_attributes.get('href')
                    if href_res:
                        try:
                            href_res = I(href_res)
                        except ValueError:
                            warnings.warn('Invalid URL or anchor {} found in {}. Ignored'.format(href_res, source_uri))
                            continue
                    href_src = elem.xml_attributes.get('src')
                    if href_src:
                        try:
                            href_src = I(href_src)
                        except ValueError:
                            warnings.warn('Invalid URL or anchor {} found in {}. Ignored'.format(href_src, source_uri))
                            continue
                    value = new_value or elem.xml_attributes.get('content') or href_res or href_src or elem.xml_value
                    statement_sink.send((resource, prop, value))
                    #logging.debug('{}'.format((resource, prop, value)))
                    #element_satisfied = True
            if new_value: resource = new_value
        for child in elem.xml_children:
            if isinstance(child, element):
                do_parse(child, resource, vocab=vocab, prop=prop, prefixes=prefixes)

    do_parse(root, source_uri)
    return


def parse_iter():
    raise NotImplementedError


def write():
    raise NotImplementedError
