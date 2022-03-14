# test_pipeline.py (use pytest)
'''

Note: to see stdout, stderr & logging regardless of outcome:

pytest -s test/py/test_pipeline.py

'''

import os

# Requires pytest-mock
import pytest

from amara3 import iri
from versa import I, VTYPE_REL
from versa import util
from versa.driver.memory import newmodel
from versa.serial import literate
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

    ppl = generic_pipeline(FINGERPRINT_RULES, TRANSFORM_RULES, LABELIZE_RULES)

    modout = ppl.run(input_model=modin)
    # Use -s to see this
    print('='*10, 'test_basics_1', '='*10)
    literate.write(modout)

    assert len(modout) == 8
    assert len(list(util.all_origins(modout, only_types={BF_NS('Instance')}))) == 1
    assert len(list(util.all_origins(modout, only_types={BF_NS('Person')}))) == 1
    assert len(list(modout.match(None, BF_NS('birthDate'), '1919-01-01'))) == 1


# Similar to test_basics_2, but with redundant type information given in materialize(links=)
# With duplicate resources generation to make sure the same output resource ID & fingerprints result
def test_basics_2(testresourcepath, expected_modout1):
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

    ppl = generic_pipeline(FINGERPRINT_RULES, TRANSFORM_RULES, LABELIZE_RULES)

    literate.write(modin)
    modout = ppl.run(input_model=modin)
    # Use -s to see this
    print('='*10, 'test_basics_2, pt 1', '='*10)
    literate.write(modout)

    assert len(modout) == 8
    assert len(list(util.all_origins(modout, only_types={BF_NS('Instance')}))) == 1
    assert len(list(util.all_origins(modout, only_types={BF_NS('Person')}))) == 1
    assert len(list(modout.match(None, BF_NS('birthDate'), '1919-01-01'))) == 1

    # Run the pipeline again, now with the redundant type info
    TRANSFORM_RULES[SCH_NS('author')] = materialize(BF_NS('Person'),
                                    BF_NS('creator'),
                                    vars={
                                        'birthDate': follow(SCH_NS('authorBirthDate'),
                                            origin=var('input-resource'))
                                    },
                                    fprint=[
                                        (BF_NS('name'), target()),
                                        (BF_NS('birthDate'), var('birthDate')),
                                        # Here's the redundant type assertion
                                        (VTYPE_REL, BF_NS('Person')),
                                    ],
                                    links=[
                                        (BF_NS('name'), target()),
                                        (BF_NS('birthDate'), var('birthDate')),
                                    ]
        )
    ppl = generic_pipeline(FINGERPRINT_RULES, TRANSFORM_RULES, LABELIZE_RULES)

    modout.update(ppl.run(input_model=modin))
    # Use -s to see this
    print('='*10, 'test_basics_2, pt 2', '='*10)
    literate.write(modout, canonical=True)

    assert len(modout) == 8
    assert len(list(util.all_origins(modout, only_types={BF_NS('Instance')}))) == 1
    assert len(list(util.all_origins(modout, only_types={BF_NS('Person')}))) == 1
    assert len(list(modout.match(None, BF_NS('birthDate'), '1919-01-01'))) == 1


def test_basics_3(testresourcepath):
    modin = newmodel()
    modin_fpath = 'schemaorg/catcherintherye-ugly.md'
    literate.parse(open(os.path.join(testresourcepath, modin_fpath)).read(), modin)

    FINGERPRINT_RULES = {
        SCH_NS('Book'): ( 
            materialize(var('itype'),
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
                vars={
                    'lang': follow(SCH_NS('inLanguage')),
                    'itype': BF_NS('Instance')
                    }
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
    print('='*10, 'test_basics_3', '='*10)
    literate.write(modout)
    #import pprint; pprint.pprint(list(iter(modout)))

    assert len(modout) == 15
    assert len(list(util.all_origins(modout, only_types={BF_NS('Instance')}))) == 1
    assert len(list(util.all_origins(modout, only_types={BF_NS('Work')}))) == 1
    assert len(list(util.all_origins(modout, only_types={BF_NS('Person')}))) == 1
    assert len(list(modout.match(None, BF_NS('birthDate'), '1919-01-01'))) == 1

#SCH_NS('Novelist')

def test_basics_4(testresourcepath):
    modin = newmodel()
    modin_fpath = 'schemaorg/catcherintherye-ugly.md'
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
    print('='*10, 'test_basics_4', '='*10)
    literate.write(modout)
    #import pprint; pprint.pprint(list(iter(modout)))

    assert len(modout) == 15
    assert len(list(util.all_origins(modout, only_types={BF_NS('Instance')}))) == 1
    assert len(list(util.all_origins(modout, only_types={BF_NS('Work')}))) == 1
    assert len(list(util.all_origins(modout, only_types={BF_NS('Person')}))) == 1
    assert len(list(modout.match(None, BF_NS('birthDate'), '1919-01-01'))) == 1

def test_basics_5(testresourcepath):
    '''
    Convert from schema.org to [MusicBrainz scheme](https://musicbrainz.org/doc/MusicBrainz_Database/Schema)
    '''
    import sys # Uncomment to debug
    MB_NS = I('https://musicbrainz.org/doc/MusicBrainz_Database/Schema/')
    R_TYP = MB_NS('Release')
    RG_TYP = MB_NS('ReleaseGroup')
    A_TYP = MB_NS('Artist')
    DOC_NS = I('http://example.org/records/')

    modin = newmodel()
    modin_fpath = 'schemaorg/blackstar.md'
    literate.parse(open(os.path.join(testresourcepath, modin_fpath)).read(), modin)
    # Hand-add a comment property to the Mos Def resource to test that this value doesn't bleed e.g. to Kweli's output
    modin.add(DOC_NS('md'), SCH_NS('comment'), 'test')

    FINGERPRINT_RULES = {
        SCH_NS('MusicAlbum'): ( 
            materialize(MB_NS('ReleaseGroup'),
                fprint=[
                    (MB_NS('title'), follow(SCH_NS('name'))),
                    (MB_NS('artist'), follow(SCH_NS('byArtist'), SCH_NS('name'))),
                ],
                links=[
                    (MB_NS('contains'), materialize(MB_NS('Release'),
                        fprint=[
                            (MB_NS('catalogue-number'), var('catnum')),
                        ],
                        links=[
                            (MB_NS('catalogue-number'), var('catnum')),
                        ]
                    ))
                ],
                vars={'catnum': follow(SCH_NS('catalogNumber'))},
                # debug=sys.stderr, # Uncomment to debug
            )
        ),

        SCH_NS('Person'): ( 
            materialize(MB_NS('Artist'),
                fprint=[
                    (MB_NS('name'), var('aname')),
                ],
                links=[
                    (MB_NS('name'), var('aname')),
                    (MB_NS('remark'), var('comment')),
                ],
                vars={'aname': follow(SCH_NS('name')), 'comment': follow(SCH_NS('comment'))},
            )
        )
    }

    TRANSFORM_RULES = {
        (SCH_NS('name'), R_TYP, RG_TYP): link(rel=MB_NS('title')),

        (SCH_NS('byArtist'), R_TYP): link(rel=MB_NS('by'), target=lookup('@resource')),
    }

    # Intentionally shadows the global LABELIZE_RULES
    LABELIZE_RULES = {
        MB_NS('ReleaseGroup'): follow(MB_NS('title')),
        MB_NS('Release'): follow(MB_NS('title')),
        MB_NS('Artist'): follow(MB_NS('name'))
    }

    ppl = generic_pipeline(FINGERPRINT_RULES, TRANSFORM_RULES, LABELIZE_RULES)

    modout = ppl.run(input_model=modin)
    # Use -s to see this
    print('='*10, 'test_basics_5', '='*10)
    literate.write(modout)
    # import pprint; pprint.pprint(list(iter(modout)))

    assert len(modout) == 16
    assert len(list(util.all_origins(modout, only_types={MB_NS('ReleaseGroup')}))) == 1
    assert len(list(util.all_origins(modout, only_types={MB_NS('ReleaseGroup')}))) == 1
    assert len(list(util.all_origins(modout, only_types={MB_NS('Artist')}))) == 2
    # assert len(list(modout.match(None, BF_NS('birthDate'), '1919-01-01'))) == 1
    # DOC_NS('md') -> I('i5GvPVm7ClA') in the transform
    assert [ l[0] for l in modout.match(None, MB_NS('remark'), 'test')] == [I('i5GvPVm7ClA')]


if __name__ == '__main__':
    raise SystemExit("use py.test")
