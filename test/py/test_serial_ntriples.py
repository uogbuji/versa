'''
Test 
'''

import logging
import functools

# Requires pytest-mock
import pytest
from amara3 import iri

from versa import I
from versa.driver.memory import newmodel
from versa.serial.ntriples import *
# from versa.util import jsondump, jsonload

NT_SPEC = I('http://www.w3.org/2001/sw/RDFCore/ntriples/')
DC_CREATOR = I('http://purl.org/dc/elements/1.1/creator')
DC_PUBLISHER = I('http://purl.org/dc/elements/1.1/publisher')
W3C = I('http://www.w3.org/')

@pytest.fixture
def ntrips_1():
    return '''\
<http://www.w3.org/2001/sw/RDFCore/ntriples/> <http://purl.org/dc/elements/1.1/creator> "Dave Beckett" .
<http://www.w3.org/2001/sw/RDFCore/ntriples/> <http://purl.org/dc/elements/1.1/creator> "Art Barstow" .
<http://www.w3.org/2001/sw/RDFCore/ntriples/> <http://purl.org/dc/elements/1.1/publisher> <http://www.w3.org/> .
'''

def test_parse1(ntrips_1):
    m = newmodel()
    parse(ntrips_1, m)
    assert len(m) == 3, repr(m)
    assert 'Dave Beckett' in [ t for (o, r, t, a) in m.match(NT_SPEC, DC_CREATOR)]
    assert 'Art Barstow' in [ t for (o, r, t, a) in m.match(NT_SPEC, DC_CREATOR)]
    assert W3C in [ t for (o, r, t, a) in m.match(NT_SPEC, DC_PUBLISHER)]


