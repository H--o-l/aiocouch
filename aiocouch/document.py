# Copyright (c) 2019, ZIH,
# Technische Universitaet Dresden,
# Federal Republic of Germany
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#     * Redistributions of source code must retain the above copyright notice,
#       this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright notice,
#       this list of conditions and the following disclaimer in the documentation
#       and/or other materials provided with the distribution.
#     * Neither the name of metricq nor the names of its contributors
#       may be used to endorse or promote products derived from this software
#       without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from .remote import RemoteDocument
from .exception import ConflictError, ForbiddenError, raises

from contextlib import suppress
import json


class Document(RemoteDocument):
    def __init__(self, database, id):
        super().__init__(database, id)
        self._data = {"_id": id}
        self._data_hash = None

    def _update_hash(self):
        self._data_hash = hash(json.dumps(self._data, sort_keys=True))

    @property
    def _dirty_cache(self):
        return self._data_hash is None or self._data_hash != hash(
            json.dumps(self._data, sort_keys=True)
        )

    async def fetch(self, discard_changes=False):
        if self._dirty_cache and not discard_changes:
            raise ConflictError(
                f"Cannot fetch document '{self.id}' from server, as the local cache has unsaved changes."
            )
        self._update_cache(await self._get())

    async def save(self):
        if self._dirty_cache:
            data = await self._put(self._data)
            self._update_rev_after_save(data)

    async def delete(self, discard_changes=False):
        if self._dirty_cache and not discard_changes:
            raise ConflictError(
                f"Cannot delete document '{self.id}' from server, as the local cache has unsaved changes."
            )
        self._update_cache(await self._delete(rev=self["_rev"]))

    async def copy(self, new_id):
        await self._copy(new_id)

        return await self._database[new_id]

    @property
    def data(self):
        return self._data if self.exists else None

    @property
    def exists(self):
        return "_rev" in self and "_deleted" not in self

    def _update_rev_after_save(self, data):
        with suppress(KeyError):
            self._data["_rev"] = data["rev"]
        self._update_hash()

    def _update_cache(self, new_cache):
        self._data = new_cache
        self._update_hash()

    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, value):
        self._data[key] = value

    def __delitem__(self, key):
        del self._data[key]

    def __contains__(self, key):
        return key in self._data

    def update(self, data):
        self._data.update(data)

    def items(self):
        return self._data.items()

    def keys(self):
        return self._data.keys()

    def values(self):
        return self._data.values()

    def get(self, key, default=None):
        return self._data.get(key, default)

    def setdefault(self, key, default=None):
        return self._data.setdefault(key, default)

    def __repr__(self):
        return json.dumps(self._data, indent=2)


class SecurityDocument(Document):
    def __init__(self, database):
        super().__init__(database, "_security")
        del self._data["_id"]

    async def fetch(self, discard_changes=False):
        await super().fetch(discard_changes)
        self.setdefault("members", {"names": [], "roles": []})
        self.setdefault("admins", {"names": [], "roles": []})

    @property
    def members(self):
        return self["members"]["names"]

    @property
    def member_roles(self):
        return self["members"]["roles"]

    @property
    def admins(self):
        return self["admins"]["names"]

    @property
    def admin_roles(self):
        return self["admins"]["roles"]

    def add_member(self, member):
        if member not in self["members"]["names"]:
            self["members"]["names"].append(member)

    def remove_member(self, member):
        if member in self["members"]["names"]:
            self["members"]["names"].remove(member)
        else:
            raise KeyError(
                f"The user '{member}' isn't a member of the database '{self._database.id}'"
            )

    def add_admin(self, admin):
        if admin not in self["admins"]["names"]:
            self["admins"]["names"].append(admin)

    def remove_admin(self, admin):
        if admin in self["admins"]["names"]:
            self["admins"]["names"].remove(admin)
        else:
            raise KeyError(
                f"The user '{admin}' isn't an admin of the database '{self._database.id}'"
            )

    @raises(500, "You are not a database or server admin", ForbiddenError)
    async def save(self):
        await super().save()
