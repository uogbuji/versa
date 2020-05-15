#

# 

import re
import csv
import itertools

from amara3 import iri #for absolutize & matches_uri_syntax
from amara3.uxml.parser import parse, event
from amara3.uxml.tree import treebuilder, element, text
from amara3.uxml.treeutil import *
#from amara import namespaces

from versa.reader.md import parse as markdown_parse
from versa import I, VERSA_BASEIRI
from versa.contrib.datachefids import idgen, FROM_EMPTY_64BIT_HASH

SLUGCHARS = r'a-zA-Z0-9\-\_'
OMIT_FROM_SLUG_PAT = re.compile('[^%s]'%SLUGCHARS)


#New, consistent API
def parse(csvfp, vliterate_template, model, csv_cls=None, encoding='utf-8', header_loc=None):
    if csv_cls is None:
        rows = csv.DictReader(csvfp, delimiter=',',
                                quotechar='"', quoting=csv.QUOTE_MINIMAL)
    else:
        rows = csv_cls(csvfp)

    row = next(rows, None)
    if row:
        adapted_keys = {}
        for k in row.keys():
            # FIXME: Needs uniqueness post-check
            adapted = OMIT_FROM_SLUG_PAT.sub('_', k)
            adapted_keys[k] = adapted

        for row in itertools.chain(iter([row]), rows):
            for k, ad_k in adapted_keys.items():
                row[ad_k] = row[k]
            vliterate_text = vliterate_template.format(**row)
            markdown_parse(vliterate_text, model)

