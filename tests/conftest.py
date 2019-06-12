import pytest


@pytest.fixture
async def couchdb():
    from aiocouch import CouchDB
    import os

    try:
        hostname = os.environ["COUCHDB_HOST"]
    except KeyError:
        hostname = "http://localhost:5984"

    try:
        user = os.environ["COUCHDB_USER"]
    except KeyError:
        user = "admin"

    try:
        password = os.environ["COUCHDB_PASS"]
    except KeyError:
        password = "admin"

    async with CouchDB(hostname, user=user, password=password) as couchdb:
        yield couchdb


@pytest.fixture
async def database(couchdb):
    database = await couchdb.create("aiocouch_test_fixture_database")

    yield database

    await database.delete()


@pytest.fixture
async def filled_database(database):
    doc = await database.create("foo")
    doc["bar"] = True
    await doc.save()

    doc = await database.create("foo2")
    doc["bar"] = True
    await doc.save()

    doc = await database.create("baz")
    doc["bar"] = False
    await doc.save()

    doc = await database.create("baz2")
    doc["bar"] = True
    await doc.save()

    yield database


@pytest.fixture
async def doc(database):
    doc = await database.create("foo")
    yield doc
