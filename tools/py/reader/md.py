'''
Base tools for parsing the Markdown syntax of Versa

https://daringfireball.net/projects/markdown/basics

For example:




'''

import re

import markdown
from amara.lib import iri #for absolutize & matches_uri_syntax
from amara.lib import U, inputsource
from amara.bindery import html
from amara import namespaces

from versa import I, VERSA_BASEIRI

RDFTYPE = namespaces.RDF_NAMESPACE + 'type'

#Does not support the empty URL <> as a property name
REL_PAT = re.compile('(<.+>|[@\\-_\\w]+):(.*)', re.DOTALL)

#Does not support the empty URL <> as a property name
RESOURCE_STR = '([^\s\\[\\]]+)?\s?(\\[([^\s\\[\\]]*?)\\])?'
RESOURCE_PAT = re.compile(RESOURCE_STR)
AB_RESOURCE_PAT = re.compile('<\s*' + RESOURCE_STR + '\s*>')

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

#FIXME: Isn't this just itertools.islice?
def results_until(items, end_criteria):
    for node in items:
        if node.xml_select(end_criteria):
            break
        else:
            yield node


def from_markdown(md, output, encoding='utf-8', config=None):
    """
    Translate the Versa Markdown syntax into Versa model relationships

    md -- markdown source text
    output -- Versa model to take the output relationship
    encoding -- character encoding (defaults to UTF-8)

    No return value
    """
    #Set up configuration to interpret the conventions for the Markdown
    config = config or {}
    #This mapping takes syntactical elements such as the various header levels in Markdown and associates a resource type with the specified resources
    syntaxtypemap = {}
    if config.get('autotype-h1'): syntaxtypemap[u'h1'] = config.get('autotype-h1')
    if config.get('autotype-h2'): syntaxtypemap[u'h2'] = config.get('autotype-h2')
    if config.get('autotype-h3'): syntaxtypemap[u'h3'] = config.get('autotype-h3')
    interp_stanza = config.get('interpretations', {})
    interpretations = {}

    def setup_interpretations(interp):
        #Map the interpretation IRIs to functions to do the data prep
        for prop, interp_key in interp.iteritems():
            if interp_key.startswith(u'@'):
                interp_key = iri.absolutize(interp_key[1:], VERSA_BASEIRI)
            if interp_key in PREP_METHODS:
                interpretations[prop] = PREP_METHODS[interp_key]
            else:
                #just use the identity, i.e. no-op
                interpretations[prop] = lambda x, **kwargs: x

    setup_interpretations(interp_stanza)

    #Parse the Markdown
    h = markdown.markdown(md.decode(encoding))

    doc = html.markup_fragment(inputsource.text(h.encode('utf-8')))
    #Each section contains one resource description, but the special one named @docheader contains info to help interpret the rest
    top_section_fields = results_until(doc.xml_select(u'//h1[1]/following-sibling::h2'), u'self::h1')

    docheader = doc.xml_select(u'//h1[.="@docheader"]')[0]
    sections = doc.xml_select(u'//h1[not(.="@docheader")]|h2[not(.="@docheader")]|h3[not(.="@docheader")]')
    #sections = doc.xml_select(u'//h1|h2|h3')

    def fields(sect):
        '''
        Each section represents a resource and contains a list with its properties
        This generator parses the list and yields the key value pairs representing the properties
        Some properties have attributes, expressed in markdown as a nested list. If present these attributes
        Are yielded as well, else None is yielded
        '''
        #import logging; logging.debug(repr(sect))
        #Pull all the list elements until the next header. This accommodates multiple lists in a section
        sect_body_items = results_until(sect.xml_select(u'following-sibling::*'), u'self::h1|self::h2|self::h3')
        #field_list = [ U(li) for ul in sect.xml_select(u'following-sibling::ul') for li in ul.xml_select(u'./li') ]
        field_list = [ li for elem in sect_body_items for li in elem.xml_select(u'li') ]

        def parse_pair(pair):
            '''
            Parse each list item into a property pair
            '''
            if pair.strip():
                matched = REL_PAT.match(pair)
                if not matched:
                    raise ValueError(_(u'Syntax error in relationship expression: {0}'.format(field)))
                prop = matched.group(1).strip()
                val = matched.group(2).strip()
                #prop, val = [ part.strip() for part in U(li.xml_select(u'string(.)')).split(u':', 1) ]
                #import logging; logging.debug(repr((prop, val)))
                return prop, val
            return None, None

        #Go through each list item
        for li in field_list:
            #Is there a nested list, which expresses attributes on a property
            if li.xml_select(u'ul'):
                main = ''.join([ U(node) for node in results_until(li.xml_select(u'node()'), u'self::ul') ])
                #main = li.xml_select(u'string(ul/preceding-sibling::node())')
                prop, val = parse_pair(main)
                subfield_list = [ sli for sli in li.xml_select(u'ul/li') ]
                subfield_dict = dict([ parse_pair(U(pair)) for pair in subfield_list ])
                if None in subfield_dict: del subfield_dict[None]
                yield prop, val, subfield_dict
            #Just a regular, unadorned property
            else:
                prop, val = parse_pair(U(li))
                if prop: yield prop, val, None

    #Gather the document-level metadata
    base = propbase = rbase = interp_from_instance = None
    for prop, val, subfield_dict in fields(docheader):
        if prop == '@base':
            base = propbase = rbase = val
        if prop == '@property-base':
            propbase = val
        if prop == '@resource-base':
            rbase = val
        if prop == '@interpretations':
            interp_from_instance = subfield_dict

    if interp_from_instance:
        interp = {}
        for k in interp_from_instance:
            interp[I(iri.absolutize(k, rbase))] = interp_from_instance[k]
        setup_interpretations(interp)

    if not propbase: propbase = base
    if not rbase: rbase = base

    #Go through the resources expressed in remaining sections
    for sect in sections:
        #if U(sect) == u'@docheader': continue #Not needed because excluded by ss
        #The header can take one of 4 forms: "ResourceID" "ResourceID [ResourceType]" "[ResourceType]" or "[]"
        #The 3rd form is for an anonymous resource with specified type and the 4th an anonymous resource with unspecified type
        matched = RESOURCE_PAT.match(U(sect))
        if not matched:
            raise ValueError(_(u'Syntax error in resource header: {0}'.format(U(sect))))
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
            rtype = syntaxtypemap.get(sect.xml_local)
        if rtype:
            output.add(rid, RDFTYPE, rtype)
        #Add the property
        for prop, val, subfield_dict in fields(sect):
            attrs = subfield_dict or {}
            fullprop = I(iri.absolutize(prop, propbase))
            resinfo = AB_RESOURCE_PAT.match(val)
            if resinfo:
                val = resinfo.group(1)
                valtype = resinfo.group(3)
                if not val: val = output.generate_resource()
                if valtype: attrs[RDFTYPE] = valtype
            if fullprop in interp:
                val = interpretations[fullprop](val, rid=rid, fullprop=fullprop, base=base, model=output)
                if val is not None: output.add(rid, fullprop, val)
            else:
                output.add(rid, fullprop, val, attrs)

    return base

