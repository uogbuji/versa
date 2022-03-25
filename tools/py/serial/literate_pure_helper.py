# -*- coding: utf-8 -*-
# # versa.serial.literate_pure_helper.py

"""
Versa Literate in pure form (not by interpreting as Markdown)

see: doc/literate_format.md

"""

import re
from dataclasses import dataclass
from collections import namedtuple

from amara3 import iri # for absolutize & matches_uri_syntax

from versa import I, VERSA_BASEIRI
from versa.contrib.datachefids import idgen

from pyparsing import * # pip install pyparsing==3.0.0.rc1
# from amara3 import iri # for absolutize & matches_uri_syntax
ParserElement.setDefaultWhitespaceChars(' \t')

from versa import I, VERSA_BASEIRI, VERSA_NULL

URI_ABBR_PAT = re.compile('@([\\-_\\w]+)([#/@])(.+)', re.DOTALL)
URI_EXPLICIT_PAT = re.compile('<(.+)>', re.DOTALL)

TEXT_VAL, RES_VAL, UNKNOWN_VAL = 1, 2, 3

TYPE_REL = VERSA_BASEIRI('type')


# Really just for explicitness & annotation FIXME: Move to Versa's __init__
class LITERAL:
    def __init__(self, s):
        self._s = s

    def __str__(self):
        return self._s

    def __repr__(self):
        return f'LITERAL({repr(self._s)})'


# For parse trees
@dataclass
class prop_info:
    indent: int = None      # 
    key: str = None         # 
    value: list = None      # 
    children: list = None   # 


@dataclass
class doc_info:
    iri: str = None         # iri of the doc being parsed, itself
    resbase: str = None     # used to resolve relative resource IRIs
    schemabase: str = None  # used to resolve relative schema IRIs
    rtbase: str = None      # used to resolve relative resource type IRIs. 
    lang: str = None        # other IRI abbreviations
    iris: dict = None       # iterpretations of untyped values (e.g. string vs list of strs vs IRI)
    interp: dict = None     # default natural language of values


@dataclass
class value_info:
    verbatim: int = None    # 
    typeindic: int = None   # 


def make_tree(string, location, tokens):
    return prop_info(indent=len(tokens[0]), key=tokens[1], value=tokens[2], children=None)


def make_value(string, location, tokens):
    val = tokens[0].strip()
    if isinstance(val, I):
        typeindic = RES_VAL
    elif val[0] == val[-1] and val[0] in '"\'':
        typeindic = TEXT_VAL
        val = val[1:-1]
    #elif val[0] == '<' and val[-1] == '>':
    else:
        typeindic = UNKNOWN_VAL

    return value_info(verbatim=val, typeindic=typeindic)


def literal_parse_action(toks):
    return LITERAL(toks[0])

def iriref_parse_action(toks):
    return I(toks[0])

COMMENT         = cpp_style_comment | htmlComment
OPCOMMENT       = Optional(COMMENT)
IDENT           = Word(alphas, alphanums + '_' + '-')
IDENT_KEY       = Combine(Optional('@') + IDENT).leaveWhitespace()
# EXPLICIT_IRI    = QuotedString('<', end_quote_char='>')
QUOTED_STRING   = MatchFirst((QuotedString('"', escChar='\\'), QuotedString("'", escChar='\\'))) \
                    .setParseAction(literal_parse_action)
# See: https://rdflib.readthedocs.io/en/stable/_modules/rdflib/plugins/sparql/parser.html
IRIREF          = Regex(r'[^<>"{}|^`\\\[\]%s]*' % "".join(
                        "\\x%02X" % i for i in range(33)
                    )) \
                    .setParseAction(iriref_parse_action)
#REST_OF_LINE = rest_of_line.leave_whitespace()

blank_line      = ZeroOrMore(COMMENT) + White('\n')
explicit_iriref = Combine(Suppress("<") + IRIREF + Suppress(">")) \
                    .setParseAction(iriref_parse_action)

value_expr      = Combine(explicit_iriref | QUOTED_STRING | rest_of_line).leaveWhitespace()
prop            = Optional(White(' \t').leaveWhitespace(), '') + Suppress('*' + White()) + ( explicit_iriref | IDENT_KEY | IRIREF  ) + Suppress(':') + Optional(value_expr, None)
propset         = Group(delimited_list(prop | COMMENT, delim='\n'))
resource_header = Word('#') + Optional(IRIREF, None) + Optional(QuotedString('[', end_quote_char=']'), None)
resource_block  = Forward()
resource_block  << Group(resource_header + White('\n').suppress() + Suppress(ZeroOrMore(blank_line)) + propset)

# Start symbol
resource_seq    = OneOrMore(Suppress(ZeroOrMore(blank_line)) + resource_block + White('\n').suppress() + Suppress(ZeroOrMore(blank_line)))

prop.setParseAction(make_tree)
value_expr.setParseAction(make_value)
# subprop.setParseAction(make_tree)


def parse(vlit, model, encoding='utf-8', config=None):
    """
    Translate Versa Literate text into Versa model relationships

    vlit -- Versa Literate source text
    model -- Versa model to take the output relationship
    encoding -- character encoding (defaults to UTF-8)

    Returns: The overall base URI (`@base`) specified in the Markdown file, or None

    >>> from versa.driver.memory import newmodel
    >>> from versa.serial.literate import parse # Delegates to literate_pure_helper.parse
    >>> m = newmodel()
    >>> parse(open('test/resource/poetry.md').read(), m)
    'http://uche.ogbuji.net/poems/'
    >>> m.size()
    40
    >>> next(m.match(None, 'http://uche.ogbuji.net/poems/updated', '2013-10-15'))
    (I(http://uche.ogbuji.net/poems/1), I(http://uche.ogbuji.net/poems/updated), '2013-10-15', {})
    """
    #Set up configuration to interpret the conventions for the Markdown
    config = config or {}
    #This mapping takes syntactical elements such as the various header levels in Markdown and associates a resource type with the specified resources
    syntaxtypemap = {}
    if config.get('autotype-h1'): syntaxtypemap['h1'] = config.get('autotype-h1')
    if config.get('autotype-h2'): syntaxtypemap['h2'] = config.get('autotype-h2')
    if config.get('autotype-h3'): syntaxtypemap['h3'] = config.get('autotype-h3')
    interp_stanza = config.get('interpretations', {})

    interp = setup_interpretations(interp_stanza)

    # Prep ID generator, in case needed
    idg = idgen(None)

    # Set up doc info
    doc = doc_info(iri=None, resbase=None, schemabase=None, rtbase=None, iris=None, interp=interp, lang={})

    parsed = resource_seq.parseString(vlit)

    for resblock in parsed:
        process_resblock(resblock, model, doc)

    return doc.iri


def setup_interpretations(interp):
    #Map the interpretation IRIs to functions to do the data prep
    interpretations = {}
    for prop, interp_key in interp.items():
        if interp_key.startswith('@'):
            interp_key = iri.absolutize(interp_key[1:], VERSA_BASEIRI)
        if interp_key in PREP_METHODS:
            interpretations[prop] = PREP_METHODS[interp_key]
        else:
            #just use the identity, i.e. no-op
            interpretations[prop] = lambda x, **kwargs: x
    return interpretations


def expand_iri(iri_in, base, relcontext=None):
    if iri_in is None:
        return VERSA_NULL
    if iri_in.startswith('@'):
        return I(iri.absolutize(iri_in[1:], VERSA_BASEIRI))
    iri_match = URI_EXPLICIT_PAT.match(iri_in)
    if iri_match:
        return iri_match.group(1) if base is None else I(iri.absolutize(iri_match.group(1), base))
    iri_match = URI_ABBR_PAT.match(iri_in)
    if iri_match:
        uri = iris[iri_match.group(1)]
        fulliri = URI_ABBR_PAT.sub(uri + '\\2\\3', iri_in)
    else:
        # Replace upstream ValueError with our own
        if relcontext and not(iri.matches_uri_ref_syntax(iri_in)):
            # FIXME: Replace with a Versa-specific error
            raise ValueError(f'Invalid IRI reference provided for relation {relcontext}: "{iri_in}"')
        fulliri = iri_in if base is None else I(iri.absolutize(iri_in, base))
    return I(fulliri)


def process_resblock(resblock, model, doc):
    headermarks, rid, rtype, props = resblock
    headdepth = len(headermarks)
    #print(resblock)

    if rid == '@docheader':
        process_docheader(props, model, doc)
        return

    rid = expand_iri(rid, doc.resbase)
    # typeindic = RES_VAL | TEXT_VAL | UNKNOWN_VAL
    # FIXME: Use syntaxtypemap
    if rtype:
        model.add(rid, TYPE_REL, expand_iri(rtype, doc.schemabase))

    outer_indent = -1
    current_outer_prop = None
    for prop in props:
        if isinstance(prop, str):
            #Just a comment. Skip.
            continue

        # @iri section is where key IRI prefixes can be set
        # First property encountered determines outer indent
        if outer_indent == -1:
            outer_indent = prop.indent

        if prop.indent == outer_indent:
            if current_outer_prop:
                model.add(rid, current_outer_prop.key, current_outer_prop.value, attrs)

            current_outer_prop = prop
            attrs = {}

            pname = prop.key
            prop.key = expand_iri(pname, doc.schemabase)
            if prop.value:
                prop.value, typeindic = prop.value.verbatim, prop.value.typeindic
                if typeindic == RES_VAL:
                    prop.value = expand_iri(prop.value, doc.rtbase, relcontext=prop.key)
                elif typeindic == TEXT_VAL:
                    if '@lang' not in attrs and doc.lang:
                        attrs['@lang'] = doc.lang
                elif typeindic == UNKNOWN_VAL:
                    if prop.key in doc.interp:
                        prop.value = doc.interp[prop.key](prop.value, rid=rid, fullprop=current_outer_prop.key, base=doc.iri, model=model)

        else:
            aprop, aval, atype = prop.key, prop.value, UNKNOWN_VAL
            aval, typeindic = aval.verbatim, aval.typeindic
            fullaprop = expand_iri(aprop, doc.schemabase)
            if atype == RES_VAL:
                aval = expand_iri(aval, doc.rtbase)
                valmatch = URI_ABBR_PAT.match(aval)
                if valmatch:
                    uri = doc.iris[I(valmatch.group(1))]
                    attrs[fullaprop] = I(URI_ABBR_PAT.sub(uri + '\\2\\3', aval))
                else:
                    attrs[fullaprop] = I(iri.absolutize(aval, doc.rtbase))
            elif atype == TEXT_VAL:
                attrs[fullaprop] = aval
            elif atype == UNKNOWN_VAL:
                val_iri_match = URI_EXPLICIT_PAT.match(aval)
                if val_iri_match:
                    aval = expand_iri(aval, doc.rtbase)
                elif fullaprop in doc.interp:
                    aval = doc.interp[fullaprop](aval, rid=rid, fullprop=fullaprop, base=base, model=model)
                if aval is not None:
                    attrs[fullaprop] = aval

    # Don't forget the final fencepost property
    if current_outer_prop:
        model.add(rid, current_outer_prop.key, current_outer_prop.value, attrs)


def process_docheader(props, model, doc):
    outer_indent = -1
    current_outer_prop = None
    for prop in props:
        # @iri section is where key IRI prefixes can be set
        # First property encountered determines outer indent
        if outer_indent == -1:
            outer_indent = prop.indent
        if prop.indent == outer_indent:
            current_outer_prop = prop
            #Setting an IRI for this very document being parsed
            if prop.key == '@document':
                doc.iri = prop.value.verbatim
            elif prop.key == '@language':
                doc.lang = prop.value.verbatim
            #If we have a resource to which to attach them, just attach all other properties
            elif doc.iri:
                fullprop = I(iri.absolutize(prop.key, doc.schemabase))
                if fullprop in doc.interp:
                    val = doc.interp[fullprop](prop.value.verbatim, rid=doc.iri, fullprop=fullprop, base=doc.resbase, model=model)
                    if val is not None: model.add(doc.iri, fullprop, val)
                else:
                    model.add(doc.iri, fullprop, prop.value.verbatim)
        elif current_outer_prop.key == '@iri':
            k, uri = prop.key, prop.value.verbatim
            if k == '@base':
                doc.resbase = doc.rtbase = uri
            elif k == '@schema':
                doc.schemabase = uri
            elif k == '@resource-type':
                doc.rtbase = uri
            else:
                doc.iris[k] = uri
        # @interpretations section is where defaults can be set as to the primitive types of values from the Markdown, based on the relevant property/relationship
        # Note: @iri section must come before @interpretations
        elif current_outer_prop.key == '@interpretations':
            k, uri = prop.key, prop.value.verbatim
            interp_basis = {I(iri.absolutize(k, doc.schemabase)): uri}
            doc.interp.update(setup_interpretations(interp_basis))
    return


def handle_resourceset(ltext, **kwargs):
    '''
    A helper that converts sets of resources from a textual format such as Markdown, including absolutizing relative IRIs
    '''
    fullprop=kwargs.get('fullprop')
    rid=kwargs.get('rid')
    base=kwargs.get('base', VERSA_BASEIRI)
    model=kwargs.get('model')
    iris = ltext.strip().split()
    for i in iris:
        model.add(rid, fullprop, I(iri.absolutize(i, base)))
    return None


PREP_METHODS = {
    VERSA_BASEIRI + 'text': lambda x, **kwargs: x,
    # '@text': lambda x, **kwargs: x,
    VERSA_BASEIRI + 'resource': lambda x, base=VERSA_BASEIRI, **kwargs: I(iri.absolutize(x, base)),
    VERSA_BASEIRI + 'resourceset': handle_resourceset,
}

'''
    from versa.driver.memory import newmodel
    m = newmodel()
    parse(open('/tmp/poetry.md').read(), m)
    print(m.size())
    import pprint; pprint.pprint(list(m.match()))
    # next(m.match(None, 'http://uche.ogbuji.net/poems/updated', '2013-10-15'))
'''


'''

for s in [  '# resX\n<!-- COMMENT -->\n\n  * a-b-c: <quick-brown-fox>',
            ]:
    print(s, end='')
    parsed = resource_block.parseString(s)
    print('→', parsed)

for s in [  '  * a-b-c: <quick-brown-fox>',
            '  * a-b-c:  quick brown fox',
            '  * a-b-c: " quick brown fox"',
            ]:
    parsed = prop.parseString(s)
    print(s, '→', parsed)

for s in [  '# resX\n  * a-b-c: <quick-brown-fox>',
            '# resX [Person]\n  * a-b-c: <quick-brown-fox>',
            '# resX [Person]\n  * a-b-c: <quick-brown-fox>\n  * d-e-f: "lazy dog"',
            ]:
    parsed = resource_block.parseString(s)
    print(s, '→', parsed)

for s in [  '# resX\n  a-b-c: <quick-brown-fox>\n    lang: en',
            ]:
    parsed = resource_block.parseString(s)
    print(s, '→', parsed)


  a-b-c: <quick-brown-fox> → [prop_info(key='a-b-c', value=ParseResults([I(quick-brown-fox)], {}), children=[ParseResults([], {})])]
  a-b-c:  quick brown fox → [prop_info(key='a-b-c', value=ParseResults(['quick brown fox'], {}), children=[ParseResults([], {})])]
  a-b-c: " quick brown fox" → [prop_info(key='a-b-c', value=ParseResults([LITERAL(' quick brown fox')], {}), children=[ParseResults([], {})])]
# resX
  a-b-c: <quick-brown-fox> → [I(resX), None, prop_info(key='a-b-c', value=ParseResults([I(quick-brown-fox)], {}), children=[ParseResults([], {})])]
# resX [Person]
  a-b-c: <quick-brown-fox> → [I(resX), 'Person', prop_info(key='a-b-c', value=ParseResults([I(quick-brown-fox)], {}), children=[ParseResults([], {})])]
# resX [Person]
  a-b-c: <quick-brown-fox>
  d-e-f: "lazy dog" → [I(resX), 'Person', prop_info(key='a-b-c', value=ParseResults([I(quick-brown-fox)], {}), children=[ParseResults([prop_info(key='d-e-f', value=LITERAL('lazy dog'), children=[])], {})])]
# resX
  a-b-c: <quick-brown-fox>
    lang: en → [I(resX), None, prop_info(key='a-b-c', value=ParseResults([I(quick-brown-fox)], {}), children=[ParseResults([prop_info(key='lang', value='en', children=[])], {})])]

'''
