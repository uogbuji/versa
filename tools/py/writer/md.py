#versa.writer.md
"""
Render a Versa model as Versa Literate (Markdown)

see: doc/literate_format.md

"""

import re
import sys
import os
import glob
import time
from itertools import islice
import logging

from amara3 import iri

from versa import I, VERSA_BASEIRI, ORIGIN, RELATIONSHIP, TARGET
from versa.driver import memory
from versa import VERSA_BASEIRI
from versa.reader.md import from_markdown
from versa.util import all_origins

TYPE_REL = I(iri.absolutize('type', VERSA_BASEIRI))


def abbreviate(rel, bases):
    for base in bases:
        abbr = iri.relativize(rel, base, subPathOnly=True)
        if abbr:
            if base is VERSA_BASEIRI:
                abbr = '@' + abbr
            return abbr
    return rel


def value_format(val):
    if isinstance(val, I):
        return str(val)
    else:
        return repr(val)


def write(model, out=None, base=None, propertybase=None, shorteners=None, logger=logging):
    '''
    models - input Versa model from which output is generated
    '''
    assert out is not None #Output stream required
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
            abbr_r = abbreviate(r, all_propertybase)
            value_format(t)
            out.write('* {0}: {1}\n'.format(abbr_r, value_format(t)))
            for k, v in a.items():
                abbr_k = abbreviate(k, all_propertybase)
                out.write('    * {0}: {1}\n'.format(k, value_format(v)))

        out.write('\n')
    return
