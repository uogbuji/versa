# versa.serial.csv

"""
Serialize and deserialize between a Versa model and CSV

Import as:

from versa.serial.csv import parse as csv_parse

"""

import re
import json
import logging
import operator
from operator import truth
from itertools import chain, islice, repeat, starmap, takewhile

from versa import I, VERSA_BASEIRI, ORIGIN, RELATIONSHIP, TARGET
from versa.driver.memory import newmodel

from .literate import parse as vlit_parse

__all__ = ['parse', 'parse_iter', 'write',
    # Non-standard
]


def parse(objlist, vl_template, model, encoding='utf-8', nosy=None):
    for obj in objlist:
        vl_text = vl_template.render(_=obj, **obj)
        if nosy: nosy(vl_text)
        vlit_parse(vl_text, model)


# FIXME: Seems to be massive cut & paste error
def parse_iter(csvfp, template_obj, model_fact=newmodel,
                csv_fact=None, header_loc=None, nosy=None):
    '''
    Parse simple Python object (e.g. loaded from JSON) into Versa model based
    on template for interpreting the data. Yield a new model representing each row

    csvfp - file-like object with CSV content
    template_obj - string format template that serves as Versa literal template
            for each object, or callable that takes the dict of each and
            returns a versa literate string. e.g. of the latter might be a
            function that uses Jinja or Mako for more sophisticated templating
    model_fact - callable that provides a Versa model to receive the model
            intepreted from the Versa literate of each row
    csv_fact - callable that convers data from csvfp into Python csv
            module-compatible objects
    header_loc - how many rows down in the CSV file header data can be found
    nosy - optional function which is called with the result of each row's
            Versa literal output, useful for debugging
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
                # URI escape, but treat spaces as special case, for convenience
                adapted = iri.percent_encode(k.replace(' ', '_'))
                #adapted = OMIT_FROM_SLUG_PAT.sub('_', k)
                # Ensure there are no clashes after escaping
                while adapted in adapted_keys:
                    adapted_keys += '_'
                adapted_keys[k] = adapted
            first_proper_row = False

        for k, ad_k in adapted_keys.items():
            row[ad_k] = row[k]
        if isinstance(template_obj, str):
            vliterate_text = template_obj.format(**row)
        else:
            vliterate_text = template_obj(row)
        model = model_fact()
        vlit_parse(vliterate_text, model)
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
        vlit_parse(vliterate_text, model)
    return at_least_one_row


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


def write():
    raise NotImplementedError
