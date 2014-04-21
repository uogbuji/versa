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
HEADER_PAT = re.compile('([^\s\\[\\]]+)?\s?(\\[([^\s\\[\\]]*?)\\])?')

'''
>>> import re
>>> HEADER_PAT = re.compile('([^\s\\[\\]]+)?\s?(\\[([^\s\\[\\]]*?)\\])?')
>>> m = HEADER_PAT.match("ResourceID")
>>> m.groups()
('ResourceID', None, None)
>>> m = HEADER_PAT.match("[ResourceType]")
>>> m.groups()
(None, '[ResourceType]', 'ResourceType')
>>> m = HEADER_PAT.match("ResourceID [ResourceType]")
>>> m.groups()
('ResourceID', '[ResourceType]', 'ResourceType')
>>> m = HEADER_PAT.match("[]")
>>> m.groups()
(None, '[]', '')
'''

def handleirilist(ltext, **kwargs):
    base=kwargs.get('base', VERSA_BASEIRI)
    model=kwargs.get('model')
    iris = ltext.strip().split()
    newlist = model.generate_resource()
    for i in iris:
        model.add(newlist, VERSA_BASEIRI + 'item', I(iri.absolutize(i, base)))
    return newlist

def handleiriset(ltext, **kwargs):
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
    VERSA_BASEIRI + 'iri': lambda x, base=VERSA_BASEIRI, **kwargs: I(iri.absolutize(x, base)),
    VERSA_BASEIRI + 'iriset': handleiriset,
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
    syntaxtypemap = {}
    if config.get('autotype-h1'): syntaxtypemap[u'h1'] = config.get('autotype-h1')
    if config.get('autotype-h2'): syntaxtypemap[u'h2'] = config.get('autotype-h2')
    if config.get('autotype-h3'): syntaxtypemap[u'h3'] = config.get('autotype-h3')
    interp = config.get('interpretations', {})
    #Map the interpretation IRIs to functions to do the data prep
    for prop, interp_key in interp.iteritems():
        if interp_key in PREP_METHODS:
            interp[prop] = PREP_METHODS[interp_key]
        else:
            #just use the identity, i.e. no-op
            interp[prop] = lambda x, **kwargs: x

    #Parse the Markdown
    h = markdown.markdown(md.decode(encoding))

    doc = html.markup_fragment(inputsource.text(h.encode('utf-8')))
    #Each section contains one resource description, but the special one named @docheader contains info to help interpret the rest
    top_section_fields = results_until(doc.xml_select(u'//h1[1]/following-sibling::h2'), u'self::h1')

    docheader = doc.xml_select(u'//h1[.="@docheader"]')[0]
    sections = doc.xml_select(u'//h1|h2|h3[not(.="@docheader")]')

    def fields(sect):
        #import logging; logging.debug(repr(sect))
        sect_body_items = results_until(sect.xml_select(u'following-sibling::*'), u'self::h1|self::h2|self::h3')
        #field_list = [ U(li) for ul in sect.xml_select(u'following-sibling::ul') for li in ul.xml_select(u'./li') ]
        field_list = [ U(li) for elem in sect_body_items for li in elem.xml_select(u'li') ]
        for field in field_list:
            if field.strip():
                matched = REL_PAT.match(field)
                if not matched:
                    raise ValueError(_(u'Syntax error in relationship expression: {0}'.format(field)))
                prop = matched.group(1).strip()
                val = matched.group(2).strip()
                print val
                #prop, val = [ part.strip() for part in U(li.xml_select(u'string(.)')).split(u':', 1) ]
                #import logging; logging.debug(repr((prop, val)))
                yield (prop, val)

    #Gather the document-level metadata
    base = propbase = rbase = None
    for prop, val in fields(docheader):
        if prop == '@base':
            base = val
        if prop == '@property-base':
            propbase = val
        if prop == '@resource-base':
            rbase = val
    if not propbase: propbase = base
    if not rbase: rbase = base

    #Go through the resources expressed in remaining sections
    for sect in sections:
        #The header can take one of 4 forms: "ResourceID" "ResourceID [ResourceType]" "[ResourceType]" or "[]"
        #The 3rd form is for an anonymous resource with specified type and the 4th an anonymous resource with unspecified type
        matched = HEADER_PAT.match(U(sect))
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
        for prop, val in fields(sect):
            fullprop = I(iri.absolutize(prop, propbase))
            if fullprop in interp:
                val = interp[fullprop](val, rid=rid, fullprop=fullprop, base=base, model=output)
                if val is not None: output.add(rid, fullprop, val)
            else:
                output.add(rid, fullprop, val)

    return base

