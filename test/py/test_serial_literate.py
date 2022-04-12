# -*- coding: utf-8 -*-
# test_serial_literate.py
'''
Test Literate parser

pytest -s test/py/test_serial_literate.py

Note: for now writing is tested only in test_serial_canonical_literate.py

'''

# import io

import pytest
from amara3 import iri

from versa import I
from versa.driver.memory import newmodel
from versa.serial.literate import parse, write

@pytest.fixture
def input_1_template():
    return '''\
{header}

# http://eg.org/abc [http://vocab.org/TYPE1]

* <http://vocab.org/uvw>: "1"    // CPP Comment
* <http://vocab.org/uvw>: 3
* <http://vocab.org/xyz>: <def>

<!-- Extra spaces -->


# http://eg.org/def [http://vocab.org/TYPE2]

* <http://vocab.org/badlabel>: 1 <!-- "\"1\"" -->

'''

@pytest.fixture
def input_2_template():
    return '''\
{header}

# http://eg.org/abc [http://vocab.org/TYPE1]

* <http://vocab.org/uvw>: "1"    // CPP Comment
    * http://vocab.org/nop: "7"
    * http://vocab.org/qrs: "6"
* <http://vocab.org/uvw>: "3"
* <http://vocab.org/xyz>: <def>

# http://eg.org/def [http://vocab.org/TYPE2]

* <http://vocab.org/badlabel>: 1 <!-- "\"1\"" -->
    * <http://vocab.org/corrected>: "1"

'''

# @pytest.fixture
# def parsed_input1():
#     modin = newmodel()
#      literate.parse('''
#      ''', modin)
#      return modin


def test_parse1(input_1_template):
    m = newmodel()
    parse(input_1_template.format(header=''), m)
    # Use -s to see this
    print('='*10, 'test_basics_1', '='*10)
    write(m)
    assert len(m) == 6
    # assert 'Dave Beckett' in [ t for (o, r, t, a) in m.match(NT_SPEC, DC_CREATOR)]
    # assert 'Art Barstow' in [ t for (o, r, t, a) in m.match(NT_SPEC, DC_CREATOR)]
    # assert W3C in [ t for (o, r, t, a) in m.match(NT_SPEC, DC_PUBLISHER)]



