# test_pipeline_context_extras.py (use py.test)
'''

Note: to see stdout, stderr, ets:

py.test -s test/py/test_pipeline_context_extras.py

'''

import os

# Requires pytest-mock
import pytest

from versa import I, VERSA_BASEIRI, VTYPE_REL, VLABEL_REL, ORIGIN, RELATIONSHIP, TARGET
from versa import util
from versa.driver.memory import newmodel
from versa.serial import csv, literate, mermaid
from versa.pipeline import *

SCH_NS = I('https://schema.org/')
BF_NS = I('http://bibfra.me/')


@pytest.fixture
def expected_modout1():
    modout = newmodel()
    #literate.parse('''

    #''', modout)
    return modout


WT = BF_NS('Work')
IT = BF_NS('Instance')

LABELIZE_RULES = {
    BF_NS('Work'): follow(BF_NS('name')),
    BF_NS('Instance'): follow(BF_NS('name')),
    BF_NS('Person'): follow(BF_NS('name'))
}


def test_basics_1(testresourcepath, expected_modout1):
    modin = newmodel()
    modin_fpath = 'schemaorg/catcherintherye-ugly.md'
    literate.parse(open(os.path.join(testresourcepath, modin_fpath)).read(), modin)

    FINGERPRINT_RULES = {
        SCH_NS('Book'): ( 
            materialize(BF_NS('Instance'),
                fprint=[
                    (BF_NS('isbn'), follow(SCH_NS('isbn'))),
                ],
            )
        )
    }

    TRANSFORM_RULES = {
        SCH_NS('name'): link(rel=BF_NS('name')),

        SCH_NS('author'): materialize(BF_NS('Person'),
                                    BF_NS('creator'),
                                    vars={
                                        'birthDate': follow(SCH_NS('authorBirthDate'),
                                            origin=var('input-resource'))
                                    },
                                    fprint=[
                                        (BF_NS('name'), target()),
                                        (BF_NS('birthDate'), var('birthDate')),
                                    ],
                                    links=[
                                        (BF_NS('name'), target()),
                                        (BF_NS('birthDate'), var('birthDate')),
                                    ]
        ),
    }

    modout = newmodel()
    def new_entity_hook(eid):
        # Add a triple to each materialized resource
        modout.add(eid, 'http://example.org/materializedBy', 'py.test')
        return

    ctxextras = {'@new-entity-hook': new_entity_hook}
    root_ctx = DUMMY_CONTEXT.copy(output_model=modout, extras=ctxextras)

    ppl = generic_pipeline(FINGERPRINT_RULES, TRANSFORM_RULES, LABELIZE_RULES, root_ctx=root_ctx)

    ppl.run(input_model=modin, output_model=modout)
    # Use -s to see this
    print('='*10, 'test_basics_1', '='*10)
    literate.write(modout)

    assert len(list(modout.match(None, 'http://example.org/materializedBy', None))) == 2


if __name__ == '__main__':
    raise SystemExit("use py.test")
