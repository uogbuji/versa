#versa.query

from versa.driver import memory
from .parser import parser
from .miniparser import parser as miniparser

def execute(model, q, variables=None, extras=None):
    '''
    >>> from versa.query import execute as vquery
    >>> from versa.reader import rdfalite
    >>> from versa.driver import memory
    >>> m = memory.connection()
    >>> HTML5 = 'http://www.w3.org/TR/html5/'; U = 'http://uche.ogbuji.net#'
    >>> LINKS = [
    >>> ["http://uche.ogbuji.net/ndewo/", "http://www.w3.org/TR/html5/title", "Ndewo, Colorado", {"@lang": "en"}],
    >>> ["http://uche.ogbuji.net/ndewo/", "http://www.w3.org/TR/html5/link-type/author", "http://uche.ogbuji.net/", {"link/description": "Uche Ogbuji"}],
    >>> ["http://uche.ogbuji.net/ndewo/", "http://www.w3.org/TR/html5/link-type/see-also", "", {"@label": "Goodreads"}],
    >>> ["http://uche.ogbuji.net/", "http://www.w3.org/TR/html5/link-type/see-also", "http://uche.ogbuji.net/ndewo/", {}]
    >>> ]
    >>> [ m.add(*l) for l in LINKS ]
    >>> vquery(m, "?($a, DC 'title', *)", variables={'DC': 'http://purl.org/dc/elements/1.1/'})
    >>> 
    '''
    ctxlink = next(iter(model), None)
    if not ctxlink:
        raise RuntimeError('Empty model.')
    ctx = context(ctxlink, model, variables=variables, extras=extras)
    q_ast = parser.parse(q)
    result = q_ast.evaluate(ctx)
    return result


def parse(q):
    '''

    '''
    q_ast = parser.parse(q)
    return q_ast


def miniparse(q):
    '''

    '''
    q_ast = miniparser.parse(q)
    return q_ast


class context(object):
    #Default way to create a model for the transform output, if one is not provided
    transform_factory = memory.connection

    def __init__(self, current_link, model, origin=None, base=None, extras=None, variables=None, matchvars=None):
        '''
        origin - resource used as the starting point for following links
        current_link - one of the links in input_model, a key reference for the transform
        input_model - Versa model treated as overall input to the transform
        base - reference base IRI, e.g. used to resolve created resources
        '''
        self.current_link = current_link
        self.model = model
        self.origin = origin or (self.current_link[0] if self.current_link else None)
        self.base = base
        self.extras = extras or {}
        self.variables = variables or {}
        self.matchvars = matchvars or {}

    def copy(self, current_link=None, model=None, origin=None, base=None, extras=None, variables=None, matchvars=None):
        current_link = current_link if current_link else self.current_link
        model = model if model else self.model
        origin = origin if origin else self.origin
        base = base if base else self.base
        extras = extras if extras else self.extras
        variables = variables if variables else self.variables
        matchvars = matchvars if matchvars else self.matchvars
        return context(current_link=current_link, model=model, origin=origin, base=base, extras=extras, variables=variables, matchvars=matchvars)
