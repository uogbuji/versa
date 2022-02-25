#versa
import gettext
import locale
import logging
from enum import Enum #https://docs.python.org/3.4/library/enum.html

from amara3 import iri

#XXX Try to use enums for this?
ORIGIN = RESOURCE = SUBJECT = 0
RELATIONSHIP = 1
TARGET = VALUE = 2
ATTRIBUTES = 3

from amara3.util import coroutine

class link(Enum):
    origin = 0
    relationship = 1
    target = 2
    attributes = 3

#LINKROLES = {0: link.origin, 1: link.relationship, 2: link.target, 3: link.attributes}


def init_localization():
    '''prepare l10n'''
    locale.setlocale(locale.LC_ALL, '') # User's preferred locale, according to environment

    # Use first two characters of country code, defaulting to 'en' in the absence of a preference
    loc = locale.getlocale()
    lang = loc[0][0:2] if loc[0] else 'en'
    filename = "res/messages_%s.mo" % lang

    try:
        logging.debug( "Opening message file %s for locale %s", filename, loc[0] )
        trans = gettext.GNUTranslations(open( filename, "rb" ) )
    except IOError:
        logging.debug( "Locale not found. Using default messages" )
        trans = gettext.NullTranslations()

    trans.install()


#Intentionally after the localization setup
from versa.iriref import iriref as I
VERSA_BASEIRI = I('http://bibfra.me/purl/versa/')

#Very common Versa:specific types. Analogous to rdf:type & rdfs:label
VTYPE_REL = I(iri.absolutize('type', VERSA_BASEIRI))
VLABEL_REL = I(iri.absolutize('label', VERSA_BASEIRI))

VERSA_NULL = VERSA_BASEIRI('NULL')
