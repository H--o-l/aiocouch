import pytest

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


async def test_null_view_keys(filled_database_with_view):
    values = [
        key
        async for key in filled_database_with_view.view(
            "test_ddoc", "null_view"
        ).akeys()
    ]

    assert len(values) == 4

    assert values[0] == "baz"
    assert values[1] == "baz2"
    assert values[2] == "foo"
    assert values[3] == "foo2"


async def test_null_view_ids(filled_database_with_view):
    values = [
        key
        async for key in filled_database_with_view.view("test_ddoc", "null_view").ids()
    ]

    assert len(values) == 4

    assert values[0] == "baz"
    assert values[1] == "baz2"
    assert values[2] == "foo"
    assert values[3] == "foo2"


async def test_null_view_docs(filled_database_with_view):
    values = [
        doc.id
        async for doc in filled_database_with_view.view("test_ddoc", "null_view").docs()
    ]

    assert len(values) == 4

    assert values[0] == "baz"
    assert values[1] == "baz2"
    assert values[2] == "foo"
    assert values[3] == "foo2"


async def test_null_view_docs_with_deleted(filled_database_with_view):
    doc = await filled_database_with_view["baz"]
    await doc.delete()

    docs = [
        doc
        async for doc in filled_database_with_view.view("test_ddoc", "null_view").docs(
            ids=["baz"]
        )
    ]

    assert len(docs) == 0


async def test_create_existing_view(filled_database_with_view):
    ddoc = await filled_database_with_view.design_doc("test_ddoc", exists_ok=True)

    with pytest.raises(KeyError):
        await ddoc.create_view("null_view", "function (doc) { emit(doc._id, null); }")


async def test_create_view_with_reduce(database):
    ddoc = await database.design_doc("my_test_ddoc")

    await ddoc.create_view(
        "my_test_view", "function (doc) { emit(doc._id, null); }", "_count"
    )


async def test_view_avalues(filled_database_with_view):
    docs = [
        doc
        async for doc in filled_database_with_view.view(
            "test_ddoc", "null_view"
        ).avalues()
    ]

    assert len(docs) == 4


async def test_holding_docs_wrong(filled_database_with_view):
    with pytest.raises(ValueError):
        async for doc in filled_database_with_view.view("test_ddoc", "null_view").docs(
            ids=["baz"], prefix="foo"
        ):
            pass


async def test_null_view_ids_with_prefix(filled_database_with_view):
    values = [
        key
        async for key in filled_database_with_view.view("test_ddoc", "null_view").ids(
            prefix="ba"
        )
    ]

    assert len(values) == 2

    assert values[0] == "baz"
    assert values[1] == "baz2"
