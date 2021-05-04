# -*- mode: python -*-
# -*- coding: utf-8 -*-
'''
filter_musicalbum.py - Versa pipeline rules specification to be used with versa transform command

The following example, run from the Versadistribution root directory, will generate a filtered down model file in /tmp/musicalbums-trimmed.vlit

versa transform demo/pipeline/filter_musicalbum.py demo/model/musicalbums.vlit /tmp/musicalbums-trimmed.vlit
'''


DOC_NS = I('http://example.org/records/')
SCH_NS = I('https://schema.org/')

FINGERPRINT_RULES = {
    SCH_NS('MusicAlbum'): ( 
        if_(contains(follow(SCH_NS('byArtist')), DOC_NS('md')),
            materialize(COPY())
        )
    ),

    SCH_NS('Person'): ( 
        materialize(COPY())
    ),
}

VERSA_PIPELINE_ENTRY = generic_pipeline(FINGERPRINT_RULES, {}, {})
