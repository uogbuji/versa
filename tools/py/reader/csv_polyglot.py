#

# 

import re
import csv
from itertools import chain, islice, repeat, starmap, takewhile
from operator import truth

from amara3 import iri #for absolutize & matches_uri_syntax
from amara3.uxml.parser import parse, event
from amara3.uxml.tree import treebuilder, element, text
from amara3.uxml.treeutil import *
#from amara import namespaces

from versa.reader.md import parse as markdown_parse
from versa import I, VERSA_BASEIRI
from versa.contrib.datachefids import idgen, FROM_EMPTY_64BIT_HASH
from versa.driver.memory import newmodel

SLUGCHARS = r'a-zA-Z0-9\-\_'
OMIT_FROM_SLUG_PAT = re.compile('[^%s]'%SLUGCHARS)


#New, consistent API: parse & parse_iter are the main entry points
def parse_iter(csvfp, template_obj, model_fact=newmodel,
                csv_fact=None, header_loc=None):
    '''
    Parse CSV file into Versa model based on template for interpreting the data
    Yield a new model representing each row
    '''
    if csv_fact is None:
        rows = csv.DictReader(csvfp, delimiter=',',
                                quotechar='"', quoting=csv.QUOTE_MINIMAL)
    else:
        rows = csv_fact(csvfp)

    first_proper_row = True
    for (row_ix, row) in enumerate(rows):
        if first_proper_row:
            adapted_keys = {}
            for k in row.keys():
                # FIXME: Needs uniqueness post-check
                adapted = OMIT_FROM_SLUG_PAT.sub('_', k)
                adapted_keys[k] = adapted
            first_proper_row = False

        for k, ad_k in adapted_keys.items():
            row[ad_k] = row[k]
        if isinstance(template_obj, str):
            vliterate_text = template_obj.format(**row)
        else:
            vliterate_text = template_obj(row)
        model = model_fact()
        markdown_parse(vliterate_text, model)
        yield model


# Optimized version courtesy https://stackoverflow.com/a/34935239
def chunker(n, iterable):  # n is size of each chunk; last chunk may be smaller
    # operator.truth is *significantly* faster than bool for the case of
    # exactly one positional argument
    return takewhile(truth, map(tuple, starmap(islice, repeat((iterable, n)))))


# New, consistent API
def do_parse(csvobj, adapted_keys, vliterate_template, model):
    at_least_one_row = False
    for row in csvobj:
        at_least_one_row = True
        for k, ad_k in adapted_keys.items():
            row[ad_k] = row[k]
        vliterate_text = vliterate_template.format(**row)
        markdown_parse(vliterate_text, model)
    return at_least_one_row


# New, consistent API
def parse(csvfp, vliterate_template, model, csv_cls=None, encoding='utf-8', header_loc=None):
    if csv_cls is None:
        rows = csv.DictReader(csvfp, delimiter=',',
                                quotechar='"', quoting=csv.QUOTE_MINIMAL)
    else:
        rows = csv_cls(csvfp)

    row = next(rows, None)
    # Handle column headers with non-ID characters
    if row:
        adapted_keys = {}
        for k in row.keys():
            # FIXME: Needs uniqueness post-check
            adapted = OMIT_FROM_SLUG_PAT.sub('_', k)
            adapted_keys[k] = adapted

        do_parse(chain(iter([row]), rows), adapted_keys, vliterate_template, model)


# Batch option
def parse_batched(csvfp, vliterate_template, model, batch_size, csv_cls=None, encoding='utf-8', header_loc=None):
    if csv_cls is None:
        rows = csv.DictReader(csvfp, delimiter=',',
                                quotechar='"', quoting=csv.QUOTE_MINIMAL)
    else:
        rows = csv_cls(csvfp)

    row = next(rows, None)
    # Handle column headers with non-ID characters
    if row:
        adapted_keys = {}
        for k in row.keys():
            # FIXME: Needs uniqueness post-check
            adapted = OMIT_FROM_SLUG_PAT.sub('_', k)
            adapted_keys[k] = adapted

        curr_model = model
        chunks = chunker(batch_size, chain(iter([row]), rows))
        while True:
            print((id(curr_model)))
            chunk = next(chunks, None)
            print(chunk)
            curr_model = yield
            do_parse(chunk, adapted_keys, vliterate_template, curr_model)
            if chunk is None: break

