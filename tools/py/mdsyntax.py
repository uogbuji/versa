'''
Base tools for parsing the Markdown syntax of Versa

https://daringfireball.net/projects/markdown/basics

For example:




'''

import re

import markdown
from amara.lib.iri import absolutize, matches_uri_syntax
from amara.lib import U, inputsource
from amara.bindery import html

#Does not support the empty URL <> as a property name
REL_PAT = re.compile('(<[.+]>|\\w+):(.*)')

#FIXME: Isn't this just itertools.islice?
def results_until(items, end_criteria):
    for node in items:
        if node.xml_select(end_criteria):
            break
        else:
            yield node


def from_markdown(md, output, encoding='utf-8'):
    """
    Translate the Versa Markdown syntax into Versa model relationships

    md -- markdown source text
    output -- Versa model to take the output relationship
    encoding -- character encoding (defaults to UTF-8)

    No return value
    """
    h = markdown.markdown(md.decode(encoding))

    doc = html.markup_fragment(inputsource.text(h.encode('utf-8')))
    #Each section contains one resource description, but the special one named @docheader contains info to help interpret the rest
    top_section_fields = results_until(doc.xml_select(u'//h1[1]/following-sibling::h2'), u'self::h1')

    docheader = doc.xml_select(u'//h1[.="@docheader"]')[0]
    sections = doc.xml_select(u'//h1[not(.="@docheader")]')

    def fields(sect):
        import logging; logging.debug(repr(sect))
        sect_body_items = results_until(sect.xml_select(u'ul/li'), u'self::h1|self::h2|self::h3')
        #field_list = [ U(li) for ul in sect.xml_select(u'following-sibling::ul') for li in ul.xml_select(u'./li') ]
        field_list = [ U(li) for li in sect_body_items ]
        for field in field_list:
            if field.strip():
                m = REL_PAT.match(field)
                prop = m.group(1)
                val = m.group(2)
                #prop, val = [ part.strip() for part in U(li.xml_select(u'string(.)')).split(u':', 1) ]
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

