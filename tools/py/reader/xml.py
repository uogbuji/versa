#dendrite.importr

#FIXME: OBSOLETE. Use Markdown, JSON or other format

import re

from amara.bindery import parse
from amara.lib import U

ABBR_PAT = re.compile(r'\$(\w+)')


def import_resources(source, model):
    doc = parse(source)
    abbrs = {}

    curr_context = None

    def interpret(text):
        '''
        Expand any inline abbreviations
        '''
        def replace(match):
            eid = match.group(1)
            return abbrs[eid]

        return ABBR_PAT.sub(replace, text)

    #Process only global abbreviations, for now
    for abbr in doc.resources.abbr:
        repl = interpret(U(abbr.repl))
        abbrs[U(abbr.tag)] = repl

    def interpret(text):
        '''
        Expand any inline abbreviations
        '''
        def replace(match):
            eid = match.group(1)
            return abbrs[eid]

        return ABBR_PAT.sub(replace, text)

    def process(resource, context):
        subj = interpret(resource.id)
        for rel in resource.xml_select('*'):
            if rel.xml_name == 'rel':
                #Rel id is in an attribute
                pass
            else:
                #Look up rel id from abbrs
                relid = abbrs[rel.xml_local]
            val = U(rel)
            attrs = {}
            if context:
                attrs['@context'] = context
            for ans, aname in rel.xml_attributes:
                aval = rel.xml_attributes[ans, aname]
                if aname == 'value':
                    val = interpret(rel.value)
                else:
                    attrs[abbrs.get(U(aname), U(aname))] = interpret(U(aval))
            print (subj, relid, val, attrs)
            #model.add(subj, relid, val, attrs)
        return


    #Process resources sans context
    for resource in doc.xml_select('/resources/resource'):
        process(resource)
    #Now with context
    for c in doc.xml_select('/resources/context'):
        curr_context = interpret(c.id)
        for resource in c.resource:
            process(resource, curr_context)
    return

if __name__ == "__main__":
    #python -m akara.dendrite.importr test/resource/test2.xml
    import sys
    model = None
    import_resources(sys.argv[1], model)

