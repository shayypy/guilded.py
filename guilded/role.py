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

import datetime
from typing import Optional

from .colour import Colour
from .utils import ISO8601, parse_hex_number
from .permissions import Permissions


__all__ = (
    'Role',
)


class Role:
    """Represents a role in a :class:`.Team`.

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

    def __init__(self, *, state, data, **extra):
        self._state = state

        self._team = extra.get('team') or extra.get('server')
        self.team_id: str = data.get('teamId') or data.get('serverId')

        self._members = {}

        self.id: int = int(data['id'])
        self.name: str = data.get('name') or ''
        colour = data.get('colour') or data.get('color')
        if colour == 'transparent':
            self.colour = None
        elif colour is not None and not isinstance(colour, Colour):
            self.colour = parse_hex_number(colour.strip('#'))
        else:
            self.colour = colour

        self.created_at: Optional[datetime.datetime] = ISO8601(data.get('createdAt'))
        self.updated_at: Optional[datetime.datetime] = ISO8601(data.get('updatedAt'))

        self.permissions = Permissions(**data.get('permissions', {}))
        self.priority: int = data.get('priority', 0)
        self.base: bool = data.get('isBase', False)
        self._bot: bool = data.get('botScope') is not None
        self.mentionable: bool = data.get('isMentionable', False)
        self.self_assignable: bool = data.get('isSelfAssignable', False)
        self.displayed_separately: bool = data.get('isDisplayedSeparately', False)

        self.discord_synced_at: Optional[datetime.datetime] = ISO8601(data.get('discordSyncedAt'))
        discord_role_id: Optional[int] = data.get('discordRoleId')
        if discord_role_id is not None:
            self.discord_role_id: Optional[int] = int(discord_role_id)
        else:
            self.discord_role_id: Optional[int] = None

    def __str__(self):
        return self.name

    def __repr__(self):
        return f'<Role id={self.id!r} name={self.name!r}>'

    @property
    def mention(self) -> str:
        """:class:`str`: The mention string of this role. This will not notify
        members when sent as is. To notify members, send the :class:`.Role`
        instance positionally in content instead, e.g.,
        ``await messageable.send('Here\'s a role mention: ', role)``
        """
        return f'<@{self.id}>'

    @property
    def team(self):
        """:class:`.Team`: The team that this role is from."""
        return self._team or self._state._get_team(self.team_id)

    @property
    def server(self):
        """:class:`.Team`: This is an alias of :attr:`.team`."""
        return self.team

    @property
    def guild(self):
        """|dpyattr|

        This is an alias of :attr:`.team`.
        """
        return self.team

    @property
    def members(self):
        """List[:class:`.Member`]: The cached list of members that have this
        role."""
        return list(self._members.values())

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
    def bot(self) -> bool:
        """:class:`bool`: Whether the role is the internal ``Bot`` role, which
        every bot in the team has."""
        return self._bot

    def is_default(self) -> bool:
        """|dpyattr|

        This is an alias of :attr:`.base`.
        """
        return self.base

    async def award_xp(self, amount: int):
        """|coro|

        |onlybot|

        Award XP to all members with this role. Could be a negative value to
        remove XP.

        Parameters
        -----------
        amount: :class:`int`
            The amount of XP to award.
        """
        await self._state.award_role_xp(self.team.id, self.id, amount)
