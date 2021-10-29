from amara3 import iri

from . import iriref
from . import I, VERSA_BASEIRI

RDF_NS = I('http://www.w3.org/1999/02/22-rdf-syntax-ns#')
RDFS_NS = I('http://www.w3.org/2000/01/rdf-schema#')

VERSA_TYPE = VERSA_TYPE_REL = VTYPE_REL = VERSA_BASEIRI('type')
RDF_TYPE = RDF_TYPE_REL = RDF_NS('type')

VFPRINT_REL = VERSA_BASEIRI('fingerprint')

VFPRINT_REL = I(VERSA_BASEIRI + 'fingerprint')

