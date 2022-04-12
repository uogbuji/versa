# -*- coding: utf-8 -*-
# test_serial_literate.py
'''
Test Literate writer in canonical mode

pytest -s test/py/test_serial_canonical_literate.py

'''

import io

# Requires pytest-mock
import pytest
from amara3 import iri

from versa import I
from versa.driver.memory import newmodel
from versa.serial.literate import write


def test_canonicallit_1(expected_1):
    outbuffer = io.StringIO()
    m = newmodel()
    vbase = 'http://vocab.org/'
    rbase = 'http://eg.org/'
    m.add(I(f'{rbase}def'), I(f'{vbase}xyz'), '2')
    m.add(I(f'{rbase}def'), I(f'{vbase}uvw'), '1')
    m.add(I(f'{rbase}def'), I(f'{vbase}uvw'), '3')
    m.add(I(f'{rbase}abc'), I(f'{vbase}xyz'), '2')
    m.add(I(f'{rbase}abc'), I(f'{vbase}uvw'), '1')
    m.add(I(f'{rbase}abc'), I(f'{vbase}uvw'), '3')
    write(m, outbuffer, canonical=True)

    result = outbuffer.getvalue()

    assert result == expected_1
    

def test_canonicallit_2(expected_2):
    outbuffer = io.StringIO()
    m = newmodel()
    vbase = 'http://vocab.org/'
    rbase = 'http://eg.org/'
    m.add(I(f'{rbase}def'), I(f'{vbase}xyz'), '2')
    m.add(I(f'{rbase}def'), I(f'{vbase}xyz'), '2', {I(f'{vbase}qrs'): '5', I(f'{vbase}nop'): '4'})
    m.add(I(f'{rbase}def'), I(f'{vbase}uvw'), '1')
    m.add(I(f'{rbase}def'), I(f'{vbase}uvw'), '3')
    m.add(I(f'{rbase}abc'), I(f'{vbase}xyz'), '2')
    m.add(I(f'{rbase}abc'), I(f'{vbase}uvw'), '1', {I(f'{vbase}nop'): '7', I(f'{vbase}qrs'): '6'})
    m.add(I(f'{rbase}abc'), I(f'{vbase}uvw'), '3')
    write(m, outbuffer, canonical=True)

    result = outbuffer.getvalue()

    assert result == expected_2
    

@pytest.fixture
def expected_1():
    return '''\


# http://eg.org/abc

* <http://vocab.org/uvw>: "1"
* <http://vocab.org/uvw>: "3"
* <http://vocab.org/xyz>: "2"

# http://eg.org/def

* <http://vocab.org/uvw>: "1"
* <http://vocab.org/uvw>: "3"
* <http://vocab.org/xyz>: "2"

'''

@pytest.fixture
def expected_2():
    return '''\


# http://eg.org/abc

* <http://vocab.org/uvw>: "1"
    * http://vocab.org/nop: "7"
    * http://vocab.org/qrs: "6"
* <http://vocab.org/uvw>: "3"
* <http://vocab.org/xyz>: "2"

# http://eg.org/def

* <http://vocab.org/uvw>: "1"
* <http://vocab.org/uvw>: "3"
* <http://vocab.org/xyz>: "2"
* <http://vocab.org/xyz>: "2"
    * http://vocab.org/nop: "4"
    * http://vocab.org/qrs: "5"

'''

