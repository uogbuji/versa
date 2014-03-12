from akara.dendrite import importr


def test_importr1():
    expected_statements = [(u'http://uche.ogbuji.net/data#uche.ogbuji', u'http://purl.org/xml3k/dendrite/test1/name', u'Uche Ogbuji', {u'@context': u'http://purl.org/xml3k/dendrite/test1/', u'http://purl.org/xml3k/dendrite/test1/form': u'familiar'}),
        (u'http://uche.ogbuji.net/data#uche.ogbuji', u'http://purl.org/xml3k/dendrite/test1/works-at', u'http://uche.ogbuji.net/data#zepheira', {u'http://purl.org/xml3k/dendrite/test1/temporal-assertion': u'2007-', u'@context': u'http://purl.org/xml3k/dendrite/test1/'}),
        (u'http://uche.ogbuji.net/data#zepheira', u'http://purl.org/xml3k/dendrite/test1/name', u'Zepheira', {u'@context': u'http://purl.org/xml3k/dendrite/test1/', u'http://purl.org/xml3k/dendrite/test1/form': u'familiar'}),
        (u'http://uche.ogbuji.net/data#zepheira', u'http://purl.org/xml3k/dendrite/test1/name', u'Zepheira LLC', {u'@context': u'http://purl.org/xml3k/dendrite/test1/', u'http://purl.org/xml3k/dendrite/test1/form': u'legal'}),
        (u'http://uche.ogbuji.net/data#zepheira', u'http://purl.org/xml3k/dendrite/test1/webaddress', u'http://zepheira.com', {u'@context': u'http://purl.org/xml3k/dendrite/test1/'})]
    model = dummy_model()
    result = importr.import_resources(open('test/resource/test2.xml'), model)
    assert expected_statements == result, result

