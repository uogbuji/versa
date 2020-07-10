# test_pipeline.py (use py.test)
'''

Note: to see stdout, stderr, ets:

py.test -s test/py/test_pipeline.py

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


def test_basics_1(testresourcepath, expected_modout1):
    modin = newmodel()
    modin_fpath = 'schemaorg/catcherintherye.md'
    literate.parse(open(os.path.join(testresourcepath, modin_fpath)).read(), modin)

    FINGERPRINT_RULES = {
        SCH_NS('Book'): ( 
            materialize(BF_NS('Instance'),
                fprint=[
                    (BF_NS('isbn'), follow(SCH_NS('isbn'))),
                ],
                links=[
                    (BF_NS('instantiates'),
                        materialize(BF_NS('Work'),
                            fprint=[
                                (BF_NS('name'), follow(SCH_NS('title'))),
                                (BF_NS('creator'), follow(SCH_NS('author'))),
                            ], attach=False # Can remove when we have smart sssions to avoid duplicate instantiates links
                        ),
                    )
                ]
            )
        )
    }

    WT = BF_NS('Work')
    IT = BF_NS('Instance')
    TRANSFORM_RULES = {
        # Rule for output resource type of Work or Instance
        SCH_NS('name'): link(rel=BF_NS('name')),

        # Rule only for output resource type of Work
        (SCH_NS('author'), WT): materialize(BF_NS('Person'),
                                    BF_NS('creator'),
                                    vars=[
                                        ('name', target()),
                                        ('birthDate', follow(SCH_NS('authorBirthDate'),
                                            origin=var('input-resource')
                                            )
                                        ),
                                    ],
                                    fprint=[
                                        (BF_NS('name'), var('name')),
                                        (BF_NS('birthDate'), var('birthDate')),
                                    ],
                                    links=[
                                        (BF_NS('name'), var('name')),
                                        (BF_NS('birthDate'), var('birthDate')),
                                    ]
        ),
    }

    LABELIZE_RULES = {
        BF_NS('Work'): follow(BF_NS('name')),
        BF_NS('Person'): follow(BF_NS('name'))
    }

    ppl = generic_pipeline(FINGERPRINT_RULES, TRANSFORM_RULES, LABELIZE_RULES)

    modout = ppl.run(input_model=modin)
    # Use -s to see this
    literate.write(modout)

    assert len(modout) == 11
    assert len(list(util.all_origins(modout, only_types={BF_NS('Instance')}))) == 1
    assert len(list(util.all_origins(modout, only_types={BF_NS('Work')}))) == 1
    assert len(list(util.all_origins(modout, only_types={BF_NS('Person')}))) == 1



if __name__ == '__main__':
    raise SystemExit("use py.test")
