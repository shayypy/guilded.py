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
from typing import TYPE_CHECKING, List, Optional

from .colour import Colour
from .utils import ISO8601
from .permissions import Permissions

if TYPE_CHECKING:
    from .types.role import Role as RolePayload
    from .user import Member
    from .server import Server


__all__ = (
    'Role',
)


class Role:
    """Represents a role in a :class:`.Server`.

    Attributes
    -----------
    id: :class:`int`
        The role's ID.
    name: :class:`str`
        The role's name.
    created_at: Optional[:class:`datetime.datetime`]
        When the role was created.
    updated_at: Optional[:class:`datetime.datetime`]
        When the role was last updated.
    priority: :class:`int`
        The role's priority. The base role has a priority of 1, but you should
        rely on :attr:`.base` instead.
    mentionable: :class:`bool`
        Whether members may mention this role.
    self_assignable: :class:`bool`
        Whether members may add themselves to this role without requiring
        permissions to manage roles.
    displayed_separately: :class:`bool`
        Whether the role is displayed seperately (or "hoisted") in the member
        list.
    base: :class:`bool`
        Whether the role is the base ``Member`` role.
    """

    def __init__(self, *, state, data: RolePayload, **extra):
        self._state = state
        self._member_ids = set()

        self.server_id: str = data.get('serverId') or data.get('teamId')

        self.id: int = int(data['id'])
        self.name: str = data.get('name') or ''

        self.colour: Optional[Colour]
        colour = data.get('colour') or data.get('color')
        if colour == 'transparent':
            self.colour = None
        elif colour is not None and not isinstance(colour, Colour):
            self.colour = Colour.from_str(colour)
        else:
            self.colour = colour

        self.created_at: Optional[datetime.datetime] = ISO8601(data.get('createdAt'))
        self.updated_at: Optional[datetime.datetime] = ISO8601(data.get('updatedAt'))

        self._permissions = data.get('permissions', {})
        self.priority: int = data.get('priority', 0)
        self.base: bool = data.get('isBase', False)
        self._is_bot_role: bool = data.get('botScope') is not None
        self.bot_user_id: Optional[str] = (data.get('botScope') or {}).get('userId')
        self.mentionable: bool = data.get('isMentionable', False)
        self.self_assignable: bool = data.get('isSelfAssignable', False)
        self.displayed_separately: bool = data.get('isDisplayedSeparately', False)

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f'<Role id={self.id!r} name={self.name!r}>'

    @property
    def mention(self) -> str:
        """:class:`str`: The mention string for this role.

        This will not notify members when sent as-is. If the client is a user
        account, send the :class:`.Role` instance positionally instead,
        e.g., ``await messageable.send('Here\'s a role mention: ', role)``.

        This will render a role mention when sent in an :class:`.Embed`, but it will not notify anybody.
        """
        return f'<@{self.id}>'

    @property
    def server(self) -> Server:
        """:class:`.Server`: The server that this role is from."""
        return self._state._get_server(self.server_id)

    @property
    def guild(self) -> Server:
        """|dpyattr|

        This is an alias of :attr:`.server`.

        The server that this role is from.
        """
        return self.server

    @property
    def members(self) -> List[Member]:
        """List[:class:`.Member`]: The list of members that have this role."""
        return [
            self.server.get_member(member_id)
            for member_id in self._member_ids
            if self.server.get_member(member_id) is not None
        ]

    @property
    def hoist(self) -> bool:
        """|dpyattr|

        This is an alias of :attr:`.displayed_separately`.
        """
        return self.displayed_separately

    @property
    def position(self) -> int:
        return self.priority

    @property
    def permissions(self) -> Permissions:
        """:class:`.Permissions`: The permissions that the role has."""
        return Permissions(**self._permissions)

    @property
    def bot_member(self) -> Optional[Member]:
        """Optional[:class:`.Member`]: The bot member that this managed role is assigned to."""
        return self.server.get_member(self.bot_user_id)

    def is_bot(self) -> bool:
        """:class:`bool`: Whether the role is the internal ``Bot`` role, which every bot in the server has."""
        return self._is_bot_role and self.bot_user_id is None

    def is_bot_managed(self) -> bool:
        """:class:`bool`: Whether the role is associated with a specific bot in the server."""
        return self._is_bot_role and self.bot_user_id is not None

    def is_default(self) -> bool:
        """|dpyattr|

        This is an alias of :attr:`.base`.
        """
        return self.base

    def is_assignable(self) -> bool:
        """:class:`bool`: Whether the bot can give the role to users.

        Does not account for your permissions.
        """
        # TODO: Account for role hierarchy
        return (
            not self.is_default()
            and not self._is_bot_role
        )

    async def award_xp(self, amount: int) -> None:
        """|coro|

        Award XP to all members with this role. Could be a negative value to
        remove XP.

        Parameters
        -----------
        amount: :class:`int`
            The amount of XP to award.
        """
        await self._state.award_role_xp(self.server.id, self.id, amount)
