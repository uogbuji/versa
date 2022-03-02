# versa.serial.literate

"""
Serialize and deserialize between a Versa model and Versa Literate (Markdown)

see: doc/literate_format.md

"""

import sys
import re

from amara3 import iri

from versa import I, VERSA_BASEIRI, ORIGIN, RELATIONSHIP, TARGET, VTYPE_REL
from versa.util import all_origins, resourcetypes

# from versa.serial.markdown_parse import parse
from versa.serial.literate_pure_helper import parse

TYPE_REL = I(iri.absolutize('type', VERSA_BASEIRI))

__all__ = ['parse', 'parse_iter', 'write',
    # Extras
    'longtext', 'md_escape',
]

def md_escape(s):
    # import warnings
    # warnings.warn('md_escape is no longer needed, and will be removed soon', DeprecationWarning)
    # Actually, one relevant case: the string starts & ends with </> & user forgot to wrap with quotes
    stripped = s.strip()
    if stripped and stripped[0] == '<' and stripped[-1] == '>':
        s = '\"' + s.replace('"', '\\"') + '\"'
    return s


def longtext(t):
    '''
    Prepare long text to be e.g. included as a Versa literate property value,
    according to markdown rules

    Only use this function if you're Ok with possible whitespace-specific changes

    >>> from versa.serial.literate import longtext
    >>> longtext()
    '''
# >>> markdown.markdown('* abc\ndef\nghi')
# '<ul>\n<li>abc\ndef\nghi</li>\n</ul>'
# >>> markdown.markdown('* abc\n\ndef\n\nghi')
# '<ul>\n<li>abc</li>\n</ul>\n<p>def</p>\n<p>ghi</p>'
# >>> markdown.markdown('* abc\n\n    def\n\n    ghi')
# '<ul>\n<li>\n<p>abc</p>\n<p>def</p>\n<p>ghi</p>\n</li>\n</ul>'

    # Insert blank line after the list item and before the start of your secondary paragraph. Make sure to indent the line with at least one space to ensure that it is indented as part of the list.
    endswith_cr = t[-1] == '\n'
    new_t = t.replace('\n', '\n    ')
    if endswith_cr:
        new_t = new_t[:-5]
    return new_t


def abbreviate(rel, bases):
    for base in bases:
        abbr = iri.relativize(rel, base, subPathOnly=True)
        if abbr:
            if base is VERSA_BASEIRI:
                abbr = '@' + abbr
            return abbr
    return I(rel)


def value_format(val):
    if isinstance(val, I):
        return f'<{val}>'
    else:
        return f'"{val}"'


def write(model, out=sys.stdout, base=None, schema=None, shorteners=None, canonical=False):
    '''
    models - input Versa model from which output is generated
    '''
    shorteners = shorteners or {}

    all_schema = [schema] if schema else []
    all_schema.append(VERSA_BASEIRI)

    if any((base, schema, shorteners)):
        out.write('# @docheader\n\n* @iri:\n')
    if base:
        out.write('    * @base: {0}'.format(base))
    if schema:
        out.write('    * @schema: {0}'.format(schema))
    #for k, v in shorteners:
    #    out.write('    * @base: {0}'.format(base))

    out.write('\n\n')

    origin_space = set(all_origins(model))
    if canonical:
        origin_space = sorted(origin_space)

    for o in origin_space:
        # First type found
        # XXX: Maybe there could be a standard primary-type attribute
        # to flag the property with the type to highlight
        first_type = next(iter(sorted(resourcetypes(model, o))), None)
        if first_type:
            first_type_str = abbreviate(first_type, all_schema)
            out.write(f'# {o} [{first_type_str}]\n\n')
        else:
            out.write(f'# {o}\n\n')
        rels = model.match(o)
        rels = [ (o_, r, t, sorted(a.items())) for (o_, r, t, a) in rels ]
        if canonical:
            rels = sorted(rels)
        for o_, r, t, a in rels:
            if (r, t) == (VTYPE_REL, first_type): continue
            rendered_r = abbreviate(r, all_schema)
            if isinstance(rendered_r, I):
                rendered_r = f'<{rendered_r}>'
            value_format(t)
            out.write(f'* {rendered_r}: {value_format(t)}\n')
            for k, v in a:
                rendered_k = abbreviate(k, all_schema)
                if isinstance(rendered_k, I):
                    rendered_r = f'<{rendered_k}>'
                out.write(f'    * {rendered_k}: {value_format(v)}\n')

        out.write('\n')
    return
