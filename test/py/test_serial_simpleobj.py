# -*- coding: utf-8 -*-
# test_serial_simpleobj.py
'''
Test CSV serializer

pytest -s test/py/test_serial_simpleobj.py
'''

import logging
import functools
from jinja2 import Template

# Requires pytest-mock
import pytest
from amara3 import iri

from versa import I
from versa.driver.memory import newmodel
from versa.serial.simpleobj import *
# from versa.util import jsondump, jsonload

# Sample use pattern
def objmock():
    obj = {'Wikidata': 'Q15761337', '©': '2016', 'WD link': 'link -->', 'Journal title': 'Časopis pro Moderní Filologii'}
    return [obj]


def test_simpleobj_usecase1():
    m = newmodel()
    # FiXME: Fails unless there are 2 \n's at the end
    tmpl = Template('# http://example.org#{{ Wikidata }}\n\n  * <http://example.org/voc/copyright>: {{ _["©"] }}\n\n')
    # use -s option to see the nosy print
    m = newmodel()
    parse(objmock(), tmpl, m, nosy=print)
    
    assert len(m) == 1, repr(m)
    assert ('http://example.org#Q15761337', 'http://example.org/voc/copyright', '2016', {}) == next(m.match())

