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

RDFTYPE = namespaces.RDF_NAMESPACE + 'type'

#Does not support the empty URL <> as a property name
REL_PAT = re.compile('(<[.+]>|[@\\-_\\w]+):(.*)')

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
    config = config or {}
    typemap = {}
    if config.get('autotype-h1'): typemap[u'h1'] = config.get('autotype-h1')
    if config.get('autotype-h2'): typemap[u'h2'] = config.get('autotype-h2')
    if config.get('autotype-h3'): typemap[u'h3'] = config.get('autotype-h3')
    h = markdown.markdown(md.decode(encoding))

    doc = html.markup_fragment(inputsource.text(h.encode('utf-8')))
    #Each section contains one resource description, but the special one named @docheader contains info to help interpret the rest
    top_section_fields = results_until(doc.xml_select(u'//h1[1]/following-sibling::h2'), u'self::h1')

    docheader = doc.xml_select(u'//h1[.="@docheader"]')[0]
    sections = doc.xml_select(u'//h1[not(.="@docheader")]')

    def fields(sect):
        #import logging; logging.debug(repr(sect))
        sect_body_items = results_until(sect.xml_select(u'following-sibling::*'), u'self::h1|self::h2|self::h3')
        #field_list = [ U(li) for ul in sect.xml_select(u'following-sibling::ul') for li in ul.xml_select(u'./li') ]
        field_list = [ U(li) for elem in sect_body_items for li in elem.xml_select(u'li') ]
        for field in field_list:
            if field.strip():
                m = REL_PAT.match(field)
                if not m:
                    raise ValueError(_(u'Syntax error in relationship expression: {0}'.format(field)))
                prop = m.group(1).strip()
                val = m.group(2).strip()
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
        #The resource ID is the header itself
        rid = U(sect)
        rtype = typemap.get(sect.xml_local)
        if rtype:
            output.add(rid, RDFTYPE, rtype)
        for prop, val in fields(sect):
            output.add(rid, iri.absolutize(prop, propbase), val)

        continue
        to_remove = []
        for k, v in fields:
            if k == u'id':
                rid = absolutize(v, TEST_ID_BASE)
                to_remove.append((k, v))
        for pair in to_remove:
            fields.remove(pair)

    return

