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


WT = BF_NS('Work')
IT = BF_NS('Instance')

LABELIZE_RULES = {
    BF_NS('Work'): follow(BF_NS('name')),
    BF_NS('Instance'): follow(BF_NS('name')),
    BF_NS('Person'): follow(BF_NS('name'))
}


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

    ppl = generic_pipeline(FINGERPRINT_RULES, TRANSFORM_RULES, LABELIZE_RULES)

    modout = ppl.run(input_model=modin)
    # Use -s to see this
    literate.write(modout)

    assert len(modout) == 8
    assert len(list(util.all_origins(modout, only_types={BF_NS('Instance')}))) == 1
    assert len(list(util.all_origins(modout, only_types={BF_NS('Person')}))) == 1
    assert len(list(modout.match(None, BF_NS('birthDate'), '1919-01-01'))) == 1


def test_basics_2(testresourcepath):
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
                                (BF_NS('language'), var('lang')),
                            ],
                            links=[('http://instantiated-by', var('@stem'))],
                            attach=False # Can remove when we have smart sessions to avoid duplicate instantiates links
                        ),
                    )
                ],
                # Not really necessary; just testing vars in this scenario
                vars={'lang': follow(SCH_NS('inLanguage'))}
            )
        )
    }

    TRANSFORM_RULES = {
        # Rule for output resource type of Work or Instance
        (SCH_NS('name'), WT, IT): link(rel=BF_NS('name')),

        # Rule only for output resource type of Work
        (SCH_NS('author'), WT): materialize(BF_NS('Person'),
                                    BF_NS('creator'),
                                    vars={
                                        'birthDate': follow(SCH_NS('authorBirthDate'),
                                            origin=var('input-resource'))
                                    },
                                    fprint=[
                                        # Supplementary type
                                        (VTYPE_REL, SCH_NS('Novelist')),
                                        (BF_NS('name'), target()),
                                        (BF_NS('birthDate'), var('birthDate')),
                                    ],
                                    links=[
                                        # Supplementary type
                                        (VTYPE_REL, SCH_NS('Novelist')),
                                        (BF_NS('name'), target()),
                                        (BF_NS('birthDate'), var('birthDate')),
                                    ],
                                    preserve_fprint=True,
        ),
    }

    ppl = generic_pipeline(FINGERPRINT_RULES, TRANSFORM_RULES, LABELIZE_RULES)

    modout = ppl.run(input_model=modin)
    # Use -s to see this
    literate.write(modout)
    #import pprint; pprint.pprint(list(iter(modout)))

    assert len(modout) == 15
    assert len(list(util.all_origins(modout, only_types={BF_NS('Instance')}))) == 1
    assert len(list(util.all_origins(modout, only_types={BF_NS('Work')}))) == 1
    assert len(list(util.all_origins(modout, only_types={BF_NS('Person')}))) == 1
    assert len(list(modout.match(None, BF_NS('birthDate'), '1919-01-01'))) == 1

#SCH_NS('Novelist')

def test_basics_3(testresourcepath):
    modin = newmodel()
    modin_fpath = 'schemaorg/catcherintherye.md'
    literate.parse(open(os.path.join(testresourcepath, modin_fpath)).read(), modin)

    new_work = action_template(
        materialize(BF_NS('Work'),
            fprint=[
                (BF_NS('name'), var('title')),
                (BF_NS('creator'), var('author')),
                (BF_NS('language'), var('lang')),
            ],
            links=[('http://instantiated-by', var('stem'))],
            attach=False # Can remove when we have smart sessions to avoid duplicate instantiates links
        )
    )

    FINGERPRINT_RULES = {
        SCH_NS('Book'): ( 
            materialize(BF_NS('Instance'),
                fprint=[
                    (BF_NS('isbn'), follow(SCH_NS('isbn'))),
                ],
                links=[
                    (BF_NS('instantiates'),
                    new_work(
                        title=follow(SCH_NS('title')),
                        creator=follow(SCH_NS('author')),
                        lang=var('lang'),
                        # At this point both origin and target are the resource
                        # created by the materialize in scope i.e. the new Instance.
                        stem=origin(),
                    ))
                ],
                # Not really necessary; just testing vars in this scenario
                vars={'lang': follow(SCH_NS('inLanguage'))}
            )
        )
    }

    TRANSFORM_RULES = {
        # Rule for output resource type of Work or Instance
        (SCH_NS('name'), WT, IT): link(rel=BF_NS('name')),

        # Rule only for output resource type of Work
        (SCH_NS('author'), WT): materialize(BF_NS('Person'),
                                    BF_NS('creator'),
                                    vars={
                                        'birthDate': follow(SCH_NS('authorBirthDate'),
                                            origin=var('input-resource'))
                                    },
                                    fprint=[
                                        # Supplementary type
                                        (VTYPE_REL, SCH_NS('Novelist')),
                                        (BF_NS('name'), target()),
                                        (BF_NS('birthDate'), var('birthDate')),
                                    ],
                                    links=[
                                        # Supplementary type
                                        (VTYPE_REL, SCH_NS('Novelist')),
                                        (BF_NS('name'), target()),
                                        (BF_NS('birthDate'), var('birthDate')),
                                    ],
                                    preserve_fprint=True
        ),
    }

    ppl = generic_pipeline(FINGERPRINT_RULES, TRANSFORM_RULES, LABELIZE_RULES)

    modout = ppl.run(input_model=modin)
    # Use -s to see this
    literate.write(modout)
    #import pprint; pprint.pprint(list(iter(modout)))

    assert len(modout) == 15
    assert len(list(util.all_origins(modout, only_types={BF_NS('Instance')}))) == 1
    assert len(list(util.all_origins(modout, only_types={BF_NS('Work')}))) == 1
    assert len(list(util.all_origins(modout, only_types={BF_NS('Person')}))) == 1
    assert len(list(modout.match(None, BF_NS('birthDate'), '1919-01-01'))) == 1

#SCH_NS('Novelist')

if __name__ == '__main__':
    raise SystemExit("use py.test")
