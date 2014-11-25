'''
Base tools for parsing the Markdown syntax of Versa

https://daringfireball.net/projects/markdown/basics

For example:




'''

import re
import itertools

import markdown
from versa.contrib import mkdcomments

from amara3 import iri #for absolutize & matches_uri_syntax
from amara3.uxml.parser import parse, event
from amara3.uxml.tree import treebuilder, element, text
from amara3.uxml.treeutil import *
#from amara import namespaces

from versa import I, VERSA_BASEIRI

TEXT_VAL, RES_VAL, UNKNOWN_VAL = 1, 2, 3

TYPE_REL = I(iri.absolutize('type', VERSA_BASEIRI))

#Does not support the empty URL <> as a property name
REL_PAT = re.compile('((<(.+)>)|([@\\-_\\w#/]+)):\s*((<(.+)>)|("(.*?)")|(\'(.*?)\')|(.*))', re.DOTALL)

#
URI_ABBR_PAT = re.compile('@([\\-_\\w]+)([#/@])(.+)', re.DOTALL)

#Does not support the empty URL <> as a property name
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
    base=kwargs.get('base', VERSA_BASEIRI)
    model=kwargs.get('model')
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


def from_markdown(md, output, encoding='utf-8', config=None):
    """
    Translate the Versa Markdown syntax into Versa model relationships

    md -- markdown source text
    output -- Versa model to take the output relationship
    encoding -- character encoding (defaults to UTF-8)

    Returns: The overall base URI (`@base`) specified in the Markdown file, or None
    
    >>> from versa.driver import memory
    >>> from versa.reader.md import from_markdown
    >>> m = memory.connection()
    >>> from_markdown(open('test/resource/poetry.md').read(), m)
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
    
    #Parse the Markdown
    #Alternately:
    #from xml.sax.saxutils import escape, unescape
    #h = markdown.markdown(escape(md.decode(encoding)), output_format='html5')
    #Note: even using safe_mode this should not be presumed safe from tainted input
    #h = markdown.markdown(md.decode(encoding), safe_mode='escape', output_format='html5')
    comments = mkdcomments.CommentsExtension()
    h = markdown.markdown(md, safe_mode='escape', output_format='html5', extensions=[comments])

    #doc = html.markup_fragment(inputsource.text(h.encode('utf-8')))
    tb = treebuilder()
    h = '<html>' + h + '</html>'
    root = tb.parse(h)
    #Each section contains one resource description, but the special one named @docheader contains info to help interpret the rest
    first_h1 = next(select_name(descendants(root), 'h1'))
    #top_section_fields = itertools.takewhile(lambda x: x.xml_name != 'h1', select_name(following_siblings(first_h1), 'h2'))

    docheader = next(select_value(select_name(descendants(root), 'h1'), '@docheader')) # //h1[.="@docheader"]
    sections = filter(lambda x: x.xml_value != '@docheader', select_name_pattern(descendants(root), HEADER_PAT)) # //h1[not(.="@docheader")]|h2[not(.="@docheader")]|h3[not(.="@docheader")]

    def fields(sect):
        '''
        Each section represents a resource and contains a list with its properties
        This generator parses the list and yields the key value pairs representing the properties
        Some properties have attributes, expressed in markdown as a nested list. If present these attributes
        Are yielded as well, else None is yielded
        '''
        #import logging; logging.debug(repr(sect))
        #Pull all the list elements until the next header. This accommodates multiple lists in a section
        sect_body_items = itertools.takewhile(lambda x: HEADER_PAT.match(x.xml_name) is None, select_elements(following_siblings(sect)))
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
                #print matched.groups()
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

        #Go through each list item
        for li in field_list:
            #Is there a nested list, which expresses attributes on a property
            if list(select_name(li, 'ul')):
                #main = ''.join([ node.xml_value
                #        for node in itertools.takewhile(
                #            lambda x: x.xml_name != 'ul', select_elements(li)
                #            )
                #    ])
                main = ''.join(itertools.takewhile(
                            lambda x: isinstance(x, text), li.xml_children
                            ))
                #main = li.xml_select('string(ul/preceding-sibling::node())')
                prop, val, typeindic = parse_li(main)
                subfield_list = [ parse_li(sli.xml_value) for e in select_name(li, 'ul') for sli in (
                                select_name(e, 'li')
                                ) ]
                subfield_list = [ (p, v, t) for (p, v, t) in subfield_list if p is not None ]
                #Support a special case for syntax such as in the @iri and @interpretations: stanza of @docheader
                if val is None: val = ''
                yield prop, val, typeindic, subfield_list
            #Just a regular, unadorned property
            else:
                prop, val, typeindic = parse_li(li.xml_value)
                if prop: yield prop, val, typeindic, None

    iris = {}

    #Gather the document-level metadata from the @docheader section
    base = propbase = rtbase = document_iri = None
    for prop, val, typeindic, subfield_list in fields(docheader):
        #The @iri section is where key IRI prefixes can be set
        if prop == '@iri':
            for (k, uri, typeindic) in subfield_list:
                if k == '@base':
                    base = propbase = rtbase = uri
                elif k == '@property':
                    propbase = uri
                elif k == '@resource-type':
                    rtbase = uri
                else:
                    iris[k] = uri
        #The @interpretations section is where defaults can be set as to the primitive types of values from the Markdown, based on the relevant property/relationship
        elif prop == '@interpretations':
            #Iterate over items from the @docheader/@interpretations section to set up for further parsing
            interp = {}
            for k, v, x in subfield_list:
                interp[I(iri.absolutize(k, propbase))] = v
            setup_interpretations(interp)
        #Setting an IRI for this very document being parsed
        elif prop == '@document':
            document_iri = val
        #If we have a resource to which to attach them, just attach all other properties
        elif document_iri or base:
            rid = document_iri or base
            fullprop = I(iri.absolutize(prop, propbase or base))
            if fullprop in interpretations:
                val = interpretations[fullprop](val, rid=rid, fullprop=fullprop, base=base, model=output)
                if val is not None: output.add(rid, fullprop, val)
            else:
                output.add(rid, fullprop, val)


    #Default IRI prefixes if @iri/@base is set
    if not propbase: propbase = base
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
        if rid:
            rid = I(iri.absolutize(rid, base))
        if not rid:
            rid = I(iri.absolutize(output.generate_resource(), base))
        if rtype:
            rtype = I(iri.absolutize(rtype, base))
        #Resource type might be set by syntax config
        if not rtype:
            rtype = syntaxtypemap.get(sect.xml_name)
        if rtype:
            output.add(rid, TYPE_REL, rtype)
        #Add the property
        for prop, val, typeindic, subfield_list in fields(sect):
            attrs = {}
            for (aprop, aval, atype) in subfield_list or ():
                if atype == RES_VAL:
                    valmatch = URI_ABBR_PAT.match(aval)
                    if valmatch:
                        uri = iris[valmatch.group(1)]
                        attrs[aprop] = URI_ABBR_PAT.sub(uri + '\\2\\3', aval)
                    else:
                        attrs[aprop] = I(iri.absolutize(aval, rtbase))
                elif atype == TEXT_VAL:
                    attrs[aprop] = aval
                elif atype == UNKNOWN_VAL:
                    attrs[aprop] = aval
                    if aprop in interpretations:
                        aval = interpretations[aprop](aval, rid=rid, fullprop=aprop, base=base, model=output)
                        if aval is not None: attrs[aprop] = aval
                    else:
                        attrs[aprop] = aval
            propmatch = URI_ABBR_PAT.match(prop)
            if propmatch:
                uri = iris[propmatch.group(1)]
                fullprop = URI_ABBR_PAT.sub(uri + '\\2\\3', prop)
            else:
                fullprop = I(iri.absolutize(prop, propbase))
            if typeindic == RES_VAL:
                valmatch = URI_ABBR_PAT.match(aval)
                if valmatch:
                    uri = iris[valmatch.group(1)]
                    val = URI_ABBR_PAT.sub(uri + '\\2\\3', val)
                else:
                    val = I(iri.absolutize(val, rtbase))
                output.add(rid, fullprop, val, attrs)
            elif typeindic == TEXT_VAL:
                output.add(rid, fullprop, val, attrs)
            elif typeindic == UNKNOWN_VAL:
                if fullprop in interpretations:
                    val = interpretations[fullprop](val, rid=rid, fullprop=fullprop, base=base, model=output)
                    if val is not None: output.add(rid, fullprop, val)
                else:
                    output.add(rid, fullprop, val, attrs)
            #resinfo = AB_RESOURCE_PAT.match(val)
            #if resinfo:
            #    val = resinfo.group(1)
            #    valtype = resinfo.group(3)
            #    if not val: val = output.generate_resource()
            #    if valtype: attrs[TYPE_REL] = valtype

    return document_iri

