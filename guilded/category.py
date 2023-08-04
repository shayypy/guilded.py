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
"""

from __future__ import annotations
import datetime
from typing import TYPE_CHECKING, Optional, Tuple

from .mixins import Hashable
from .utils import ISO8601

if TYPE_CHECKING:
    from .types.category import Category as CategoryPayload

    from .group import Group
    from .server import Server

__all__ = (
    'Category',
    'CategoryChannel',
)


class Category(Hashable):
    """Represents a channel category.

    .. container:: operations

        .. describe:: x == y

            Checks if two categories are equal.

        .. describe:: x != y

            Checks if two categories are not equal.

        .. describe:: hash(x)

            Returns the category's hash.

        .. describe:: str(x)

            Returns the name of the category.

    .. versionadded:: 1.11

    Attributes
    -----------
    id: :class:`int`
        The category's ID.
    name: :class:`str`
        The category's name.
    created_at: :class:`datetime.datetime`
        When the category was created.
    updated_at Optional[:class:`datetime.datetime`]
        When the category was last updated.
    server_id: :class:`str`
        The ID of the server that the category is in.
    group_id: :class:`str`
        The ID of the group that the category is in.
    """

    __slots__: Tuple[str, ...] = (
        '_state',
        '_server',
        '_group',
        'id',
        'name',
        'server_id',
        'group_id',
        'created_at',
        'updated_at',
    )

    def __init__(self, *, state, data: CategoryPayload, **extra):
        self._state = state
        self._server: Optional[Server] = extra.get('server')
        self._group: Optional[Group] = extra.get('group')

        self.id: int = data['id']
        self.name: str = data.get('name') or ''
        self.server_id: str = data.get('serverId')
        self.group_id: str = data.get('groupId')
        self.created_at: datetime.datetime = ISO8601(data.get('createdAt'))
        self.updated_at: Optional[datetime.datetime] = ISO8601(data.get('updatedAt'))

    def __str__(self):
        return self.name

    def __repr__(self):
        return f'<Category id={self.id!r} name={self.name!r} group={self.group!r}>'

    @property
    def group(self) -> Optional[Group]:
        """Optional[:class:`~guilded.Group`]: The group that this category is in."""
        group = self._group
        if not group and self.server:
            group = self.server.get_group(self.group_id)

        return group

    @property
    def server(self) -> Server:
        """:class:`.Server`: The server that this category is in."""
        return self._group.server if self._group else self._server or self._state._get_server(self.server_id)

    @property
    def guild(self) -> Server:
        """:class:`.Server`: |dpyattr|

        This is an alias of :attr:`.server`.

        The server that this category is in.
        """
        return self.server

    def is_nsfw(self) -> bool:
        """:class:`bool`: |dpyattr|

        Always returns ``False``.
        """
        return False

    async def edit(self, *, name: str) -> Category:
        """|coro|

        Edit this category.

        Parameters
        -----------
        name: :class:`str`
            The category's name.

        Returns
        --------
        :class:`.Category`:
            The newly edited category.
        """

        payload = {
            'name': name,
        }
        data = await self._state.update_category(self.server_id, self.id, payload=payload)
        return Category(state=self._state, data=data['category'], group=self._group, server=self._server)

CategoryChannel = Category  # discord.py
