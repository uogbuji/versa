#versa conftest.py

import pytest

def pytest_addoption(parser):
    parser.addoption("--user", action="store", default="versa", help="Postgres user")
    parser.addoption("--pass", action="store", help="Postgres password")
    parser.addoption("--host", action="store", default="localhost", help="Postgres host")


@pytest.fixture
def user(request):
    return request.config.getoption("--user")


@pytest.fixture
def passwd(request):
    return request.config.getoption("--pass")


@pytest.fixture
def host(request):
    return request.config.getoption("--host")


@pytest.fixture()
def pgdb(request):
    "set up test fixtures"
    from versa.driver import postgres
    user = request.config.getoption("--user")
    passwd = request.config.getoption("--pass")
    host = request.config.getoption("--host")
    conn = postgres.connection("host={0} dbname=versa_test user={1} password={2}".format(host, user, passwd))
    conn.create_space()
    def teardown():
        "tear down test fixture"
        #conn.drop_space()
        conn.close()
        return
    request.addfinalizer(teardown)
    return conn

