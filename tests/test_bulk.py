import pytest

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


async def test_update_docs_on_empty(database):
    async with database.update_docs([]) as bulk:
        pass

    assert bulk._docs == []
    keys = [key async for key in database.akeys()]
    assert len(keys) == 0


async def test_update_docs_creating(database):
    async with database.update_docs(["foobar"], create=True):
        pass

    keys = [key async for key in database.akeys()]

    assert len(keys) == 1
    assert sorted(keys) == ["foobar"]


async def test_update_docs_creating_not_ok(database):
    with pytest.raises(KeyError):
        async with database.update_docs(["foobar"]):
            pass


async def test_update_docs(database):
    async with database.update_docs(["foo", "baz"], create=True) as docs:
        async for doc in docs:
            doc["llama"] = "awesome"

    keys = [key async for key in database.akeys()]

    assert len(keys) == 2
    assert sorted(keys) == ["baz", "foo"]

    async for doc in database.values():
        assert "llama" in doc
        assert doc["llama"] == "awesome"


async def test_update_docs_no_change(filled_database):
    async with filled_database.update_docs(["foo", "baz"]) as docs:
        pass

    assert docs.status == []


async def test_update_docs_for_deleted(filled_database):
    doc = await filled_database["foo"]
    await doc.delete()

    async with filled_database.update_docs(["foo"], create=True) as docs:
        async for doc in docs:
            doc["llama"] = "awesome"

    doc = await filled_database["foo"]

    assert "_deleted" not in doc
    assert "_rev" in doc
    assert doc["_rev"].startswith("3-")
    assert doc["llama"] == "awesome"


async def test_update_docs_for_errored(filled_database):
    doc = await filled_database["foo"]
    doc["something"] = 42
    async with filled_database.update_docs(["foo", "baz"]) as docs:
        # provoke a conflict for document foo
        await doc.save()

        async for doc in docs:
            doc["thing"] = 42

    assert docs.status is not None
    assert len(docs.status) == 2

    assert len(docs.ok) == 1
    doc_ok = docs.ok[0]
    assert doc_ok.id == "baz"
    assert doc_ok["thing"] == 42
    assert doc_ok["_rev"].startswith("2-")

    assert len(docs.error) == 1
    doc_err = docs.error[0]
    assert doc_err.id == "foo"
    assert doc_err["_rev"].startswith("1-")
    assert "something" not in doc_err


async def test_create_docs_with_ids(database):
    async with database.create_docs(["foo", "baz"]) as docs:
        pass

    assert len(docs.status) == 2

    keys = [key async for key in database.akeys()]

    assert len(keys) == 2
    assert sorted(keys) == ["baz", "foo"]


async def test_create_docs_with_create(database):
    async with database.create_docs() as docs:
        docs.create("foo", data={"counter": 42})
        docs.create("baz")

    assert len(docs.status) == 2

    keys = [key async for key in database.akeys()]

    assert len(keys) == 2
    assert sorted(keys) == ["baz", "foo"]

    foo = await database["foo"]
    assert "counter" in foo
    assert foo["counter"] == 42


async def test_create_docs_with_create_duplicate(database):
    async with database.create_docs() as docs:
        docs.create("foo")
        docs.create("foo")

    assert len(docs.status) == 2

    assert "ok" in docs.status[0]
    assert "error" in docs.status[1]
    assert docs.status[1]["error"] == "conflict"

    keys = [key async for key in database.akeys()]

    assert len(keys) == 1
    assert sorted(keys) == ["foo"]


async def test_create_docs_mixed(database):
    async with database.create_docs(["foo"]) as docs:
        docs.create("baz")

    assert len(docs.status) == 2

    keys = [key async for key in database.akeys()]

    assert len(keys) == 2
    assert sorted(keys) == ["baz", "foo"]
