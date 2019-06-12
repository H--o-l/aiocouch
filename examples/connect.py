import asyncio

from aiocouch import CouchDB


async def main_with():
    async with CouchDB(
        "http://localhost:5984", user="admin", password="admin"
    ) as couchdb:

        database = await couchdb["config"]

        async for doc in database.docs(["db-hta"]):
            print(doc)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main_with())
