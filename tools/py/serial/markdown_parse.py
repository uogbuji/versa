'''
Parse the Versa Literate (Markdown) serialization of Versa

Proper entry point of use is versa.serial.literate

see: doc/literate_format.md

'''

import re
import itertools

import markdown

from amara3 import iri # for absolutize & matches_uri_syntax
from amara3.uxml import html5
from amara3.uxml.tree import treebuilder, element, text
from amara3.uxml.treeutil import *

from versa.contrib import mkdcomments
from versa import I, VERSA_BASEIRI
from versa.contrib.datachefids import idgen

# Temp until amara3-xml fix to add comment.xmnl_name
# from amara3.uxml.tree import comment


TEXT_VAL, RES_VAL, UNKNOWN_VAL = 1, 2, 3

TYPE_REL = VERSA_BASEIRI('type')

# IRI ref candidate
IRIREF_CAND_PAT = re.compile('<(.+)?>')

# Does not support the empty URL <> as a property name
# REL_PAT = re.compile('((<(.+)>)|([@\\-_\\w#/]+)):\s*((<(.+)>)|("(.*?)")|(\'(.*?)\')|(.*))', re.DOTALL)
REL_PAT = re.compile('((<(.+)>)|([@\\-_\\w#/]+)):\s*((<(.+)>)|("(.*)")|(\'(.*)\')|(.*))', re.DOTALL)

#
URI_ABBR_PAT = re.compile('@([\\-_\\w]+)([#/@])(.+)', re.DOTALL)
URI_EXPLICIT_PAT = re.compile('<(.+)>', re.DOTALL)

# Does not support the empty URL <> as a property name
RESOURCE_STR = '([^\s\\[\\]]+)?\s?(\\[([^\s\\[\\]]*?)\\])?'
RESOURCE_PAT = re.compile(RESOURCE_STR)
AB_RESOURCE_PAT = re.compile('<\s*' + RESOURCE_STR + '\s*>')

HEADER_PAT = re.compile('h\\d')

'''
>>> import re
>>> RESOURCE_PAT = re.compile('([^\s\\[\\]]+)?\s?(\\[([^\s\\[\\]]*?)\\])?')
>>> m = RESOURCE_PAT.match("ResourceID")
>>> m.groups()
('ResourceID', None, None)
>>> m = RESOURCE_PAT.match("[ResourceType]")
>>> m.groups()
(None, '[ResourceType]', 'ResourceType')
>>> m = RESOURCE_PAT.match("ResourceID [ResourceType]")
>>> m.groups()
('ResourceID', '[ResourceType]', 'ResourceType')
>>> m = RESOURCE_PAT.match("[]")
>>> m.groups()
(None, '[]', '')
'''

def handle_resourcelist(ltext, **kwargs):
    '''
    A helper that converts lists of resources from a textual format such as Markdown, including absolutizing relative IRIs
    '''
    base = kwargs.get('base', VERSA_BASEIRI)
    model = kwargs.get('model')
    iris = ltext.strip().split()
    newlist = model.generate_resource()
    for i in iris:
        model.add(newlist, VERSA_BASEIRI + 'item', I(iri.absolutize(i, base)))
    return newlist


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
    VERSA_BASEIRI + 'resource': lambda x, base=VERSA_BASEIRI, **kwargs: I(iri.absolutize(x, base)),
    VERSA_BASEIRI + 'resourceset': handle_resourceset,
}


def parse(md, model, encoding='utf-8', config=None):
    """
    Translate the Versa Markdown syntax into Versa model relationships

    md -- markdown source text
    model -- Versa model to take the output relationship
    encoding -- character encoding (defaults to UTF-8)

    Returns: The overall base URI (`@base`) specified in the Markdown file, or None

    >>> from versa.driver.memory import newmodel
    >>> from versa.serial.literate import parse
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
    interpretations = {}

    def setup_interpretations(interp):
        #Map the interpretation IRIs to functions to do the data prep
        for prop, interp_key in interp.items():
            if interp_key.startswith('@'):
                interp_key = iri.absolutize(interp_key[1:], VERSA_BASEIRI)
            if interp_key in PREP_METHODS:
                interpretations[prop] = PREP_METHODS[interp_key]
            else:
                #just use the identity, i.e. no-op
                interpretations[prop] = lambda x, **kwargs: x

    setup_interpretations(interp_stanza)

    #Prep ID generator, in case needed
    idg = idgen(None)

    #Preprocess the Markdown to deal with IRI-valued property values
    def iri_ref_tool(m):
        body = m.group(1)
        lchar = '&lt;' if iri.matches_uri_ref_syntax(body ) else '<'
        return lchar + m.group(1) + '>'
    md = IRIREF_CAND_PAT.sub(iri_ref_tool, md)

    # Parse the Markdown
    # Alternately:
    # from xml.sax.saxutils import escape, unescape
    # h = markdown.markdown(escape(md.decode(encoding)), output_format='html5')
    # Note: even using safe_mode this should not be presumed safe from tainted input
    # h = markdown.markdown(md.decode(encoding), safe_mode='escape', output_format='html5')
    comments = mkdcomments.CommentsExtension()
    h = markdown.markdown(md, safe_mode='escape', output_format='html5', extensions=[comments])

    #doc = html.markup_fragment(inputsource.text(h.encode('utf-8')))
    tb = treebuilder()
    h = '<html>' + h + '</html>'
    root = html5.parse(h)
    #root = tb.parse(h)
    #Each section contains one resource description, but the special one named @docheader contains info to help interpret the rest
    first_h1 = next(select_name(descendants(root), 'h1'))
    #top_section_fields = itertools.takewhile(lambda x: x.xml_name != 'h1', select_name(following_siblings(first_h1), 'h2'))

    # Extract header elements. Notice I use an empty element with an empty parent as the default result
    docheader = next(select_value(select_name(descendants(root), 'h1'), '@docheader'),
                    element('empty', parent=root)) # //h1[.="@docheader"]
    sections = filter(lambda x: x.xml_value != '@docheader',
                    select_name_pattern(descendants(root), HEADER_PAT)) # //h1[not(.="@docheader")]|h2[not(.="@docheader")]|h3[not(.="@docheader")]

    def fields(sect):
        '''
        Each section represents a resource and contains a list with its properties
        This generator parses the list and yields the key value pairs representing the properties
        Some properties have attributes, expressed in markdown as a nested list. If present these attributes
        Are yielded as well, else None is yielded
        '''
        #import logging; logging.debug(repr(sect))
        #Pull all the list elements until the next header. This accommodates multiple lists in a section
        try:
            sect_body_items = itertools.takewhile(lambda x: HEADER_PAT.match(x.xml_name) is None, select_elements(following_siblings(sect)))
        except StopIteration:
            return
        #results_until(sect.xml_select('following-sibling::*'), 'self::h1|self::h2|self::h3')
        #field_list = [ U(li) for ul in sect.xml_select('following-sibling::ul') for li in ul.xml_select('./li') ]
        field_list = [ li for elem in select_name(sect_body_items, 'ul') for li in select_name(elem, 'li') ]

        def parse_li(pair):
            '''
            Parse each list item into a property pair
            '''
            if pair.strip():
                matched = REL_PAT.match(pair)
                if not matched:
                    raise ValueError(_('Syntax error in relationship expression: {0}'.format(pair)))
                if matched.group(3): prop = matched.group(3).strip()
                if matched.group(4): prop = matched.group(4).strip()
                if matched.group(7):
                    val = matched.group(7).strip()
                    typeindic = RES_VAL
                elif matched.group(9):
                    val = matched.group(9).strip()
                    typeindic = TEXT_VAL
                elif matched.group(11):
                    val = matched.group(11).strip()
                    typeindic = TEXT_VAL
                elif matched.group(12):
                    val = matched.group(12).strip()
                    typeindic = UNKNOWN_VAL
                else:
                    val = ''
                    typeindic = UNKNOWN_VAL
                #prop, val = [ part.strip() for part in U(li.xml_select('string(.)')).split(':', 1) ]
                #import logging; logging.debug(repr((prop, val)))
                return prop, val, typeindic
            return None, None, None

        def prep_li(li):
            '''
            Take care of Markdown parsing minutiae. Also, Exclude child uls

            * a/href embedded in the li means it was specified as <link_text>.
            Restore the angle brackets as expected by the li parser
            * Similar for cases where e.g. prop: <abc> gets turned into prop: <abc></abc>
            '''
            prepped = ''
            for ch in itertools.takewhile(
                lambda x: not (isinstance(x, element) and x.xml_name == 'ul'), li.xml_children
            ):
                if isinstance(ch, text):
                    prepped += ch
                elif isinstance(ch, element):
                    if ch.xml_name == 'a':
                        prepped += '<' + ch.xml_value + '>'
                    else:
                        prepped += '<' + ch.xml_name + '>'
            return prepped

        #Go through each list item
        for li in field_list:
            #Is there a nested list, which expresses attributes on a property
            if list(select_name(li, 'ul')):
                #main = ''.join([ node.xml_value
                #        for node in itertools.takewhile(
                #            lambda x: x.xml_name != 'ul', select_elements(li)
                #            )
                #    ])
                main = prep_li(li)
                prop, val, typeindic = parse_li(main)
                subfield_list = [ parse_li(prep_li(sli)) for e in select_name(li, 'ul') for sli in (
                                select_name(e, 'li')
                                ) ]
                subfield_list = [ (p, v, t) for (p, v, t) in subfield_list if p is not None ]
                #Support a special case for syntax such as in the @iri and @interpretations: stanza of @docheader
                if val is None: val = ''
                yield prop, val, typeindic, subfield_list
            #Just a regular, unadorned property
            else:
                prop, val, typeindic = parse_li(prep_li(li))
                if prop: yield prop, val, typeindic, None

    iris = {}

    # Gather the document-level metadata from the @docheader section
    base = schemabase = rtbase = document_iri = default_lang = None
    for prop, val, typeindic, subfield_list in fields(docheader):
        #The @iri section is where key IRI prefixes can be set
        if prop == '@iri':
            for (k, uri, typeindic) in subfield_list:
                if k == '@base':
                    base = schemabase = rtbase = uri
                # @property is legacy
                elif k == '@schema' or k == '@property':
                    schemabase = uri
                elif k == '@resource-type':
                    rtbase = uri
                else:
                    iris[k] = uri
        #The @interpretations section is where defaults can be set as to the primitive types of values from the Markdown, based on the relevant property/relationship
        elif prop == '@interpretations':
            #Iterate over items from the @docheader/@interpretations section to set up for further parsing
            interp = {}
            for k, v, x in subfield_list:
                interp[I(iri.absolutize(k, schemabase))] = v
            setup_interpretations(interp)
        #Setting an IRI for this very document being parsed
        elif prop == '@document':
            document_iri = val
        elif prop == '@language':
            default_lang = val
        #If we have a resource to which to attach them, just attach all other properties
        elif document_iri or base:
            rid = document_iri or base
            fullprop = I(iri.absolutize(prop, schemabase or base))
            if fullprop in interpretations:
                val = interpretations[fullprop](val, rid=rid, fullprop=fullprop, base=base, model=model)
                if val is not None: model.add(rid, fullprop, val)
            else:
                model.add(rid, fullprop, val)


    #Default IRI prefixes if @iri/@base is set
    if not schemabase: schemabase = base
    if not rtbase: rtbase = base
    if not document_iri: document_iri = base

    #Go through the resources expressed in remaining sections
    for sect in sections:
        #if U(sect) == '@docheader': continue #Not needed because excluded by ss
        #The header can take one of 4 forms: "ResourceID" "ResourceID [ResourceType]" "[ResourceType]" or "[]"
        #The 3rd form is for an anonymous resource with specified type and the 4th an anonymous resource with unspecified type
        matched = RESOURCE_PAT.match(sect.xml_value)
        if not matched:
            raise ValueError(_('Syntax error in resource header: {0}'.format(sect.xml_value)))
        rid = matched.group(1)
        rtype = matched.group(3)
        if rtype:
            rtype = I(iri.absolutize(rtype, schemabase))

        if rid:
            rid = I(iri.absolutize(rid, base))
        if not rid:
            rid = next(idg)

        #Resource type might be set by syntax config
        if not rtype:
            rtype = syntaxtypemap.get(sect.xml_name)
        if rtype:
            model.add(rid, TYPE_REL, rtype)

        def expand_iri(iri_in, base):
            if iri_in.startswith('@'):
                return I(iri.absolutize(iri_in[1:], VERSA_BASEIRI))
            iri_match = URI_EXPLICIT_PAT.match(iri_in)
            if iri_match:
                return I(iri.absolutize(iri_match.group(1), base))
            iri_match = URI_ABBR_PAT.match(iri_in)
            if iri_match:
                uri = iris[iri_match.group(1)]
                fulliri = URI_ABBR_PAT.sub(uri + '\\2\\3', iri_in)
            else:
                fulliri = I(iri.absolutize(iri_in, base))
            return fulliri

        #Add the property
        for prop, val, typeindic, subfield_list in fields(sect):
            attrs = {}
            for (aprop, aval, atype) in subfield_list or ():
                fullaprop = expand_iri(aprop, schemabase)
                if atype == RES_VAL:
                    val = expand_iri(aval, rtbase)
                    valmatch = URI_ABBR_PAT.match(aval)
                    if valmatch:
                        uri = iris[valmatch.group(1)]
                        attrs[fullaprop] = URI_ABBR_PAT.sub(uri + '\\2\\3', aval)
                    else:
                        attrs[fullaprop] = I(iri.absolutize(aval, rtbase))
                elif atype == TEXT_VAL:
                    attrs[fullaprop] = aval
                elif atype == UNKNOWN_VAL:
                    val_iri_match = URI_EXPLICIT_PAT.match(aval)
                    if val_iri_match:
                        aval = expand_iri(aval, rtbase)
                    elif fullaprop in interpretations:
                        aval = interpretations[fullaprop](aval, rid=rid, fullprop=fullaprop, base=base, model=model)
                    if aval is not None:
                        attrs[fullaprop] = aval

            fullprop = expand_iri(prop, schemabase)
            if typeindic == RES_VAL:
                val = expand_iri(val, rtbase)
                model.add(rid, fullprop, val, attrs)
            elif typeindic == TEXT_VAL:
                if '@lang' not in attrs: attrs['@lang'] = default_lang
                model.add(rid, fullprop, val, attrs)
            elif typeindic == UNKNOWN_VAL:
                val_iri_match = URI_EXPLICIT_PAT.match(val)
                if val_iri_match:
                    val = expand_iri(val, rtbase)
                elif fullprop in interpretations:
                    val = interpretations[fullprop](val, rid=rid, fullprop=fullprop, base=base, model=model)
                if val is not None:
                    model.add(rid, fullprop, val, attrs)

            #resinfo = AB_RESOURCE_PAT.match(val)
            #if resinfo:
            #    val = resinfo.group(1)
            #    valtype = resinfo.group(3)
            #    if not val: val = model.generate_resource()
            #    if valtype: attrs[TYPE_REL] = valtype

    return document_iri


# XXX Add support for long Versa literate docs fed incrementally
def parse_iter():
    raise NotImplementedError

