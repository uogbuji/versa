#versa
import gettext
import locale
import logging

ORIGIN = RESOURCE = SUBJECT = 0
RELATIONSHIP = 1
TARGET = VALUE = 2
ATTRIBUTES = 3


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

from versa.driver import memory
from versa.contrib.datachefids import idgen as default_idgen, FROM_EMPTY_HASH

VERSA_BASEIRI = I('http://bibfra.me/purl/versa/')


class context(object):
    #Default way to create a model for the transform output, if one is not provided
    transform_factory = memory.connection

    #Note: origin was eliminated; not really needed since the origin of current_link can be used
    def __init__(self, current_link, input_model, output_model=None, base=None, extras=None, idgen=None, existing_ids=None):
        '''
        current_link - one of the links in input_model, a key reference for the transform
        input_model - Versa model treated as overall input to the transform
        output_model - Versa model treated as overall output to the transform; if None an empty model is created
        base - reference base IRI, e.g. used to resolve created resources
        '''
        self.current_link = current_link
        self.input_model = input_model
        self.output_model = output_model or context.transform_factory()
        self.base = base
        self.extras = extras or {}
        #FIXME: idgen requires a base IRI. Think this over.
        self.idgen = idgen or default_idgen(base)
        self.existing_ids = existing_ids or set()

    def copy(self, current_link=None, input_model=None, output_model=None, base=None, extras=None, idgen=None, existing_ids=None):
        current_link = current_link if current_link else self.current_link
        input_model = input_model if input_model else self.input_model
        output_model = output_model if output_model else self.output_model
        base = base if base else self.base
        extras = extras if extras else self.extras
        idgen = idgen if idgen else self.idgen
        existing_ids = existing_ids if existing_ids else self.existing_ids
        return context(current_link=current_link, input_model=input_model, output_model=output_model, base=base, extras=extras, idgen=idgen, existing_ids=existing_ids)

