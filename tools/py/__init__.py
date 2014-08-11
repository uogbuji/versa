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


from versa.iriref import iriref as I

VERSA_BASEIRI = I('http://bibfra.me/purl/versa/')

class context(object):
    def __init__(self, origin, linkset, linkspace, base=None):
        self.origin = origin
        self.linkset = linkset
        self.linkspace = linkspace
        self.base = base

