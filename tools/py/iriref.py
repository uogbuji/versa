#versa.iriref
'''
Versa distinguishes declared IRI references from strings which coincidentally look like IRI references
'''

from amara3 import iri
import logging

from versa import init_localization

init_localization()

#VERSA_BASEIRI = 'http://bibfra.me/purl/versa/'

class iriref(str):
    '''
    IRI references object, just a slightly decorated unicode

    >>> from versa.iriref import iriref
    >>> iriref('spam')
    'spam'
    >>> iriref('spam eggs')
    [raises ValueError]
    '''
    def __new__(cls, value):
        if not iri.matches_uri_ref_syntax(value):
            raise ValueError(_('Invalid IRI reference: "{0}"'.format(value)))
        self = super(iriref, cls).__new__(cls, value)
        #self = unicode, cls).__new__(cls, value)
        # optionally do stuff to self here
        return self

    def __repr__(self):
        return u'I(' + str(self) + ')'
