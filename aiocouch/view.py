from .remote import RemoteView
from .document import Document


class View(RemoteView):
    def __init__(self, database, design_doc, id):
        super().__init__(database, design_doc, id)

    async def get(self, **params):
        result_chunk = await self._get(**params)

        for res in result_chunk["rows"]:
            yield res

    async def post(self, ids, create=False, **params):
        result_chunk = await self._post(ids, **params)

        for res in result_chunk["rows"]:
            yield res

    async def akeys(self, keys=None, prefix=None, **params):
        if prefix is not None:
            params["startkey"] = f'"{prefix}"'
            params["endkey"] = f'"{prefix}香"'

        if keys is None:
            async for res in self.get(**params):
                if "error" not in res:
                    yield res["id"]
        else:
            async for res in self.post(keys, **params):
                if "error" not in res:
                    yield res["id"]

    async def values(self, **params):
        async for res in self.get(**params):
            yield res["key"], res["value"]

    @staticmethod
    def _is_deleted(res):
        try:
            return "deleted" in res["value"]
        except KeyError:
            return False

    async def docs(self, ids=None, create=False, prefix=None, **params):
        params["include_docs"] = True
        if prefix is None:
            if ids is None:
                iter = self.get(**params)
            else:
                iter = self.post(ids, **params)
        else:
            if ids is not None or create:
                raise ValueError(
                    "prefix cannot be used together with ids or create parameter"
                )

            params["startkey"] = f'"{prefix}"'
            params["endkey"] = f'"{prefix}香"'

            iter = self.get(**params)

        async for res in iter:
            if "error" not in res and not self._is_deleted(res):
                doc = Document(self._database, res["id"])
                doc._update_cache(res["doc"])
                yield doc
            elif create:
                doc = Document(self._database, res["key"])
                yield doc
            else:
                raise KeyError(
                    f"The document '{res['key']}' does not exist in the database {self._database.id}."
                )


class AllDocsView(View):
    def __init__(self, database):
        super().__init__(database, None, "_all_docs")

    @property
    def endpoint(self):
        return f"/{self._database.id}/_all_docs"
