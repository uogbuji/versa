# versa.serial.literate

"""
Serialize and deserialize between a Versa model and Versa Literate (Markdown)

see: doc/literate_format.md

"""

import sys

from amara3 import iri

from versa import I, VERSA_BASEIRI, ORIGIN, RELATIONSHIP, TARGET
from versa.util import all_origins

from .markdown_parse import parse

TYPE_REL = I(iri.absolutize('type', VERSA_BASEIRI))

__all__ = ['parse', 'parse_iter', 'write',
    # Non-standard
    'longtext',
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


def write(model, out=sys.stdout, base=None, propertybase=None, shorteners=None):
    '''
    models - input Versa model from which output is generated
    '''
    shorteners = shorteners or {}

    all_propertybase = [propertybase] if propertybase else []
    all_propertybase.append(VERSA_BASEIRI)

    if any((base, propertybase, shorteners)):
        out.write('# @docheader\n\n* @iri:\n')
    if base:
        out.write('    * @base: {0}'.format(base))
    #for k, v in shorteners:
    #    out.write('    * @base: {0}'.format(base))

    out.write('\n\n')

    origin_space = set(all_origins(model))

    for o in origin_space:
        out.write('# {0}\n\n'.format(o))
        for o_, r, t, a in model.match(o):
            rendered_r = abbreviate(r, all_propertybase)
            if isinstance(rendered_r, I):
                rendered_r = f'<{rendered_r}>'
            value_format(t)
            out.write(f'* {rendered_r}: {value_format(t)}\n')
            for k, v in a.items():
                rendered_k = abbreviate(k, all_propertybase)
                if isinstance(rendered_k, I):
                    rendered_r = f'<{rendered_k}>'
                out.write(f'    * {rendered_k}: {value_format(t)}\n')

        out.write('\n')
    return
