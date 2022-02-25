# versa.serial.markdown

"""
Serialize and deserialize between a Versa model and Versa Literate (Markdown)

Using the old PyMarkdown-based parser

see: doc/literate_format.md

"""

import sys
import re

from amara3 import iri

from versa import I, VERSA_BASEIRI, ORIGIN, RELATIONSHIP, TARGET, VTYPE_REL
from versa.util import all_origins, resourcetypes

from versa.serial.markdown_parse import parse

TYPE_REL = I(iri.absolutize('type', VERSA_BASEIRI))

__all__ = ['parse', 'parse_iter', 'write',
    # Extras
    'longtext', 'md_escape',
]


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


def write(model, out=sys.stdout, base=None, schema=None, shorteners=None):
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

    for o in origin_space:
        # First type found
        # XXX: Maybe there could be a standard primary-type attribute
        # to flag the property with the type to highlight
        first_type = next(resourcetypes(model, o), None)
        if first_type:
            first_type_str = abbreviate(first_type, all_schema)
            out.write(f'# {o} [{first_type_str}]\n\n')
        else:
            out.write(f'# {o}\n\n')
        for o_, r, t, a in model.match(o):
            if (r, t) == (VTYPE_REL, first_type): continue
            rendered_r = abbreviate(r, all_schema)
            if isinstance(rendered_r, I):
                rendered_r = f'<{rendered_r}>'
            value_format(t)
            out.write(f'* {rendered_r}: {value_format(t)}\n')
            for k, v in a.items():
                rendered_k = abbreviate(k, all_schema)
                if isinstance(rendered_k, I):
                    rendered_r = f'<{rendered_k}>'
                out.write(f'    * {rendered_k}: {value_format(t)}\n')

        out.write('\n')
    return


# ESCAPE_MD_PAT = re.compile(r'([\\\`\*_\{\}\[\]\(\)\#\+\-\.\!])')
# GENERAL_ESCAPE_PAT = re.compile(r'([\\]|)')

# FIXME: Make < pattern stricter, to avoid false positives
LINE_START_ESCAPE_PAT = re.compile(r'^(#|\*|-|=|<|_)')
LINE_START_AFTER_SPACE_ESCAPE_PAT = re.compile(r'^(\s+)(\*|-)')

def md_escape(t):
    '''
    Useful resources:
      * https://wilsonmar.github.io/markdown-text-for-github-from-html/

    >>> from versa.serial.literate import md_escape
    >>> md_escape('*_\\ abc')
    ... '\\*\\_\\\\ abc'
    >>> md_escape(' * spam\n * eggs')
    ... ' \\* spam  * eggs'
    '''
    # Super-simple wouldd be data = re.sub(r'([\\*_])', r'\\\1', data)
    # subbed_t = ESCAPE_MD_PAT.sub(r'\\\1', t)
    # Strip newlines, for now. Investigate escaping with more nuance
    oneline_t = ' '.join(t.splitlines())
    subbed_t = LINE_START_ESCAPE_PAT.sub(r'\\\1', oneline_t)
    subbed_t = LINE_START_AFTER_SPACE_ESCAPE_PAT.sub(r'\1\\\2', subbed_t)
    # subbed_t = ESCAPE_MD_PAT.sub(lambda m: '\\'+m.group(1))
    return subbed_t
