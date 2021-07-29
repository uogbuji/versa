# versa.serial.mermaid

"""
Render a Versa model as [Mermaid](https://mermaid-js.github.io/)

Note: you'll probably want something like mermaid-cli

"""

# Need npm to install mermaid-cli, so see: https://nodejs.org/en/

import sys

from slugify import slugify # pip install python-slugify

from amara3 import iri

from versa import I, VERSA_BASEIRI, ORIGIN, RELATIONSHIP, TARGET, VLABEL_REL, VTYPE_REL
from versa.util import all_origins, labels

__all__ = ['parse', 'parse_iter', 'write',
    # Non-standard
]


TAG_MAX_STEM_LENGTH = 12

def lookup_tag(obj, tag_map, label, is_node=True):
    '''
    '''
    stem = tag_map.get(obj)
    disambig = ''
    if stem is None:
        # FIXME: A bit wasteful here. We could just maintain the set after one-time creation
        existing_tags = set(tag_map.values())
        stem = str(obj).split('/')[-1]
        if len(stem) >= TAG_MAX_STEM_LENGTH:
            split_point = TAG_MAX_STEM_LENGTH // 2
            # Tried using '\u2026' but leads to Mermaid syntax error
            stem = stem[:split_point] + '...' + stem[-split_point:]

        disambig = 0
        while f'{stem}-{disambig}' in existing_tags:
            disambig += 1

        disambig = '' if not disambig else str(disambig)
        tag_map[obj] = f'{stem}{"-" if disambig else ""}{disambig}'

    asc_stem = slugify(stem)
    # Raw node ID
    node_id = f'{asc_stem}{disambig}'
    # Node label
    if label:
        # Implies its a resource
        if len(label) >= TAG_MAX_STEM_LENGTH:
            split_point = TAG_MAX_STEM_LENGTH // 2
            # Tried using '\u2026' but leads to Mermaid syntax error
            label = label[:split_point] + '...' + label[-split_point:]
        return f'{node_id}(fa:fa-tag {label})'

    label = f'{stem}{"-" if disambig else ""}{disambig}'
    if is_node:
        if isinstance(obj, I):
            return f'{node_id}({label})'
        else:
            return f'{node_id}[{label}]'
    else:
        return label


# TODO: Use stereotype to indicate @type
def write(model, out=sys.stdout):
    '''
    models - input Versa model from which output is generated.
    '''
    resource_tags = {}
    property_tags = {}
    value_tags = {}

    out.write('graph TD\n')

    for o in all_origins(model):
        o_label = next(labels(model, o), None)
        o_tag = lookup_tag(o, resource_tags, o_label)
        for _, r, t, a in model.match(o):
            r_tag = lookup_tag(r, property_tags, None, is_node=False)
            if isinstance(t, I):
                t_label = next(labels(model, t), None)
                t_tag = lookup_tag(t, resource_tags, t_label)
            else:
                t_tag = lookup_tag(t, value_tags, None)

            out.write(f'    {o_tag} -->|{r_tag}| {t_tag}\n')

        out.write('\n')
    return


# Intentionally not supporting parse
def parse():
    raise NotImplementedError


def parse_iter():
    raise NotImplementedError
