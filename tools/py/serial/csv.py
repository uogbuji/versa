# versa.serial.csv

"""
Serialize and deserialize between a Versa model and CSV

Import as:

from versa.serial.csv import parse as csv_parse

"""

import re
import csv
import logging
import operator
import inspect
from operator import truth
from itertools import chain, islice, repeat, starmap, takewhile

from amara3 import iri

from versa import I, VERSA_BASEIRI, ORIGIN, RELATIONSHIP, TARGET
from versa.terms import VERSA_BASEIRI, RDF_NS, RDFS_NS, VERSA_TYPE_REL, RDF_TYPE_REL
from versa.util import all_origins, lookup, resourcetypes
from versa import I, VERSA_BASEIRI
# from versa.contrib.datachefids import idgen, FROM_EMPTY_64BIT_HASH
from versa.driver.memory import newmodel

from .literate import parse as markdown_parse


SLUGCHARS = r'a-zA-Z0-9\-\_'
OMIT_FROM_SLUG_PAT = re.compile('[^%s]'%SLUGCHARS)


__all__ = ['parse', 'parse_iter', 'write',
    # Non-standard
]

def fromlist(l):
    return '|'.join(l)


def parse_iter(csvfp, template_obj, model_fact=newmodel,
                csv_fact=None, prerow=None, header_loc=None, nosy=None):
    '''
    Parse CSV file into Versa model based on template for interpreting the data
    Yield a new model representing each row

    csvfp - file-like object with CSV content
    template_obj - string format template that serves as Versa literal template
            for each row, or callable that takes the dict of each row's data and
            returns a versa literate string. e.g. of the latter might be a
            function that uses Jinja or Mako for more sophisticated templating
    model_fact - callable that provides a Versa model to receive the model
            intepreted from the Versa literate of each row
    csv_fact - callable that convers data from csvfp into Python csv
            module-compatible objects
    prerow - callable to preprocess row mapping from CSV
    header_loc - how many rows down in the CSV file header data can be found
    nosy - optional function which is called with the result of each row's
            Versa literal output, useful for debugging
    '''
    def process_rows(rows):
        '''
        Handle a list of rows (a list of 1 unless prerow is a generator)
        '''
        for row in rows:
            if isinstance(template_obj, str):
                vliterate_text = template_obj.format(**row)
            else:
                vliterate_text = template_obj(row)
            if nosy:
                nosy(vliterate_text)
            model = model_fact()
            markdown_parse(vliterate_text, model)
            yield model

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
        if inspect.isgeneratorfunction(prerow):
            yield from process_rows(prerow(row))
        elif prerow:
            yield from process_rows([prerow(row)])
        else:
            yield from process_rows([row])


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



def omap(m):
    '''
    Create a nested mapping from origin to property to values/attributes covering an entire Versa model
    '''
    om = {}
    for s, p, o, a in m.match():
        om.setdefault(s, {})
        om[s].setdefault(p, []).append((o, a))
    return om
        

def write(model, csvout, rulelist, write_header, base=None, logger=logging):
    '''
    models - input Versa model from which output is generated.
    '''
    properties = [ k for (k, v) in rulelist ]
    numprops = len(properties)
    headers = [ v for (k, v) in rulelist ]
    if write_header:
        csvout.writerow(['id', 'type'] + headers)

    rules = { k: v for (k, v) in rulelist }

    mapped = omap(model)
    for o, props in mapped.items():
        rtypes = list(map(operator.itemgetter(0), props.get(RDF_TYPE_REL, [])))
        if not rtypes: continue
        #print('RES TYPES:', rtypes)
        row = [o, fromlist(rtypes)] + [None] * numprops
        for ix, p in enumerate(properties):
            v = list(map(operator.itemgetter(0), props.get(p, [])))
            if v:
                row[ix + 2] = fromlist(v)
                csvout.writerow(row)

    return


def IGNORE():
    if False:
        for rid in all_origins(model):
            #print(rid, list(model.match(rid, RDF_TYPE_REL)))
            rtypes = list(lookup(model, rid, RDF_TYPE_REL))
            #if not rtypes: rtypes = list(lookup(model, rid, VERSA_TYPE_REL))
            #Ignore if no type
            if not rtypes: continue
            row = [rid, fromlist(rtypes)] + [None] * numprops
            for ix, p in enumerate(properties):
                #v = next(lookup(model, rid, RDF_TYPE_REL), None)
                v = list(lookup(model, rid, p))
                if v:
                    row[ix + 2] = fromlist(v)
                    csvout.writerow(row)
            
    return

