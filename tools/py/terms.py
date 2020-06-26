from amara3 import iri

from . import iriref
from . import I, VERSA_BASEIRI

RDF_NS = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'
RDFS_NS = 'http://www.w3.org/2000/01/rdf-schema#'

VERSA_TYPE = VERSA_TYPE_REL = I(VERSA_BASEIRI + 'type')
RDF_TYPE = RDF_TYPE_REL = I(RDF_NS + 'type')

VFPRINT_REL = I(VFPRINT_REL + 'fingerprint')

