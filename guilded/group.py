"""
MIT License

Copyright (c) 2020-present shay (shayypy)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

------------------------------------------------------------------------------

This project includes code from https://github.com/Rapptz/discord.py, which is
available under the MIT license:

The MIT License (MIT)

Copyright (c) 2015-present Rapptz

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Optional, Tuple

from .asset import Asset
from .mixins import Hashable
from .utils import ISO8601, MISSING

if TYPE_CHECKING:
    from .emote import Emote
    from .server import Server
    from .user import Member

    from .types.group import Group as GroupPayload


__all__ = (
    'Group',
)


class Group(Hashable):
    """Represents a server group in Guilded.

    .. container:: operations

        .. describe:: x == y

            Checks if two groups are equal.

        .. describe:: x != y

            Checks if two groups are not equal.

        .. describe:: hash(x)

            Returns the group's hash.

        .. describe:: str(x)

            Returns the name of the group.

    Attributes
    -----------
    server: :class:`.Server`
        The server that the group is in.
    id: :class:`str`
        The group's id.
    name: :class:`str`
        The group's name.
    description: Optional[:class:`str`]
        The group's description.
    home: :class:`bool`
        Whether the group is the home group of its server.
    public: :class:`bool`
        Whether the group is able to be joined by anyone.
    emote_id: Optional[:class:`int`]
        The ID of the emote associated with the group, if any.
    created_at: :class:`datetime.datetime`
        When the group was created.
    updated_at: Optional[:class:`datetime.datetime`]
        When the group was last updated.
    archived_at: Optional[:class:`datetime.datetime`]
        When the group was archived, if applicable.
    """

    __slots__: Tuple[str, ...] = (
        '_state',
        'server',
        'server_id',
        'id',
        'name',
        'description',
        'home',
        'public',
        'emote_id',
        'author_id',
        'updated_by_id',
        'archived_by_id',
        'created_at',
        'updated_at',
        'archived_at',
        '_avatar',
    )

    def __init__(self, *, state, data: GroupPayload, server: Server):
        self._state = state
        self.server = server
        self.server_id: str = data.get('serverId')

        self.id: str = data['id']
        self.name: str = data.get('name')
        self.description: str = data.get('description') or ''

        self.home: bool = data.get('isHome') or False
        self.public: bool = data.get('isPublic') or False

        self.emote_id: Optional[int] = data.get('emoteId')
        self.author_id: Optional[str] = data.get('createdBy')
        self.updated_by_id: Optional[str] = data.get('updatedBy')
        self.archived_by_id: Optional[str] =  data.get('archivedBy')

        self.created_at: datetime.datetime = ISO8601(data.get('createdAt'))
        self.updated_at: Optional[datetime.datetime] = ISO8601(data.get('updatedAt'))
        self.archived_at: Optional[datetime.datetime] = ISO8601(data.get('archivedAt'))

        avatar = None
        if data.get('avatar'):
            avatar = Asset._from_group_avatar(state, data.get('avatar'))
        self._avatar: Optional[Asset] = avatar

    def __str__(self):
        return self.name

    def __repr__(self):
        return f'<Group id={self.id!r} name={self.name!r} server_id={self.server_id!r}>'

    @property
    def archived(self) -> bool:
        """:class:`bool`: Whether this group is archived."""
        return self.archived_at is not None

    @property
    def display_avatar(self) -> Optional[Asset]:
        """Optional[:class:`.Asset`]: The group's displayed avatar.
        If :attr:`.home` is ``True``, this will be the :attr:`.server`\'s avatar instead."""

        if self.home:
            return self._avatar or self.server.avatar

        return self._avatar

    @property
    def author(self) -> Optional[Member]:
        """Optional[:class:`.Member`]: The member who created the group."""
        return self.server.get_member(self.author_id)

    @property
    def updated_by(self) -> Optional[Member]:
        """Optional[:class:`.Member`]: The member who last updated the group, if any."""
        return self.server.get_member(self.updated_by_id)

    @property
    def archived_by(self) -> Optional[Member]:
        """Optional[:class:`.Member`]: The member who archived the group, if any."""
        return self.server.get_member(self.archived_by_id)

    async def edit(
        self,
        *,
        name: Optional[str] = MISSING,
        description: Optional[str] = MISSING,
        emote: Optional[Emote] = MISSING,
        public: bool = MISSING,
    ) -> Group:
        """|coro|

        Edit the group.

        All parameters are optional.

        .. versionadded:: 1.9

        Parameters
        -----------
        name: :class:`str`
            The name of the group.
        description: :class:`str`
            The description of the group.
        emote: :class:`.Emote`
            The emote associated with the group.
        public: :class:`bool`
            Whether the group is public.

        Raises
        -------
        HTTPException
            Editing the group failed.
        Forbidden
            You do not have permissions to edit the group.

        Returns
        --------
        :class:`Group`
            The newly edited group.
        """

        payload = {}

        if name is not MISSING:
            payload['name'] = name

        if description is not MISSING:
            payload['description'] = description

        if emote is not MISSING:
            emote_id: int = getattr(emote, 'id', emote)
            payload['emoteId'] = emote_id

        if public is not MISSING:
            payload['isPublic'] = public

        data = await self._state.update_group(
            self.server_id,
            self.id,
            payload=payload
        )

        group = Group(state=self._state, data=data['group'], server=self.server)
        return group

    async def delete(self) -> None:
        """|coro|

        Delete the group.

        .. versionadded:: 1.9

        Raises
        -------
        HTTPException
            Deleting the group failed.
        Forbidden
            You do not have permissions to delete the group.
        """
        await self._state.delete_group(self.server_id, self.id)

    async def add_member(self, member: Member, /) -> None:
        """|coro|

        Add a member to this group.

        Raises
        -------
        NotFound
            This group has been deleted or the member does not exist.
        Forbidden
            You do not have permission to add the member to this group.
        HTTPException
            Failed to add the member to this group.
        """
        await self._state.add_group_member(self.id, member.id)

    async def remove_member(self, member: Member, /) -> None:
        """|coro|

        Remove a member from this group.

        Raises
        -------
        NotFound
            This group has been deleted or the member does not exist.
        Forbidden
            You do not have permission to remove the member from this group.
        HTTPException
            Failed to remove the member from this group.
        """
        await self._state.remove_group_member(self.id, member.id)
