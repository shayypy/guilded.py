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

from typing import TYPE_CHECKING, List, Optional, Tuple, Union

from .asset import Asset
from .colour import Colour
from .mixins import Hashable
from .utils import ISO8601
from .permissions import Permissions

if TYPE_CHECKING:
    from .types.role import Role as RolePayload
    from .user import Member
    from .server import Server


__all__ = (
    'Role',
)


class Role(Hashable):
    """Represents a role in a :class:`.Server`.

    .. container:: operations

        .. describe:: x == y

            Checks if two roles are equal.

        .. describe:: x != y

            Checks if two roles are not equal.

        .. describe:: hash(x)

            Returns the role's hash.

        .. describe:: str(x)

            Returns the name of the role.

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
    position: :class:`int`
        The role's position in the role hierarchy.
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

    __slots__: Tuple[str, ...] = (
        '_state',
        'server_id',
        'id',
        'name',
        '_colours',
        'created_at',
        'updated_at',
        '_icon',
        '_permissions',
        'position',
        'mentionable',
        'self_assignable',
        'displayed_separately',
        'base',
    )

    def __init__(self, *, state, data: RolePayload):
        self._state = state
        self.server_id: str = data.get('serverId')

        self.id: int = data['id']
        self.name: str = data.get('name') or ''
        self._colours: List[int] = data.get('colors') or []
        self._permissions = data.get('permissions') or []

        self.created_at = ISO8601(data.get('createdAt'))
        self.updated_at = ISO8601(data.get('updatedAt'))

        self._icon = data.get('icon')

        self.position: int = data.get('position', 0)
        self.mentionable: bool = data.get('isMentionable', False)
        self.self_assignable: bool = data.get('isSelfAssignable', False)
        self.displayed_separately: bool = data.get('isDisplayedSeparately', False)
        self.base: bool = data.get('isBase', False)

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f'<Role id={self.id!r} name={self.name!r}>'

    @property
    def mention(self) -> str:
        """:class:`str`: The mention string for this role.

        When sent in an :class:`.Embed`, this will render a role mention, but
        it will not notify anybody.
        """
        return f'<@{self.id}>'

    @property
    def server(self) -> Server:
        """:class:`.Server`: The server that this role is from."""
        return self._state._get_server(self.server_id)

    @property
    def guild(self) -> Server:
        """:class:`.Server`: |dpyattr|

        This is an alias of :attr:`.server`.

        The server that this role is from.
        """
        return self.server

    @property
    def colours(self) -> List[Colour]:
        """List[:class:`.Colour`]: The colour(s) of the role. If there are two
        values, the second indicates the end of the gradient.

        .. versionadded:: 1.9
        """
        return [Colour(value) for value in self._colours]

    colors = colours

    @property
    def colour(self) -> Colour:
        """:class:`.Colour`: The primary colour of the role."""
        return Colour(self._colours[0] if self._colours else 0)

    color = colour

    @property
    def members(self) -> List[Member]:
        """List[:class:`.Member`]: The list of members that have this role."""
        all_members = list(self.server._members.values())
        if self.base:
            return all_members

        role_id = self.id
        return [member for member in all_members if role_id in member._role_ids]

    @property
    def icon(self) -> Optional[Asset]:
        """Optional[:class:`.Asset`]: The role's icon asset, if any.

        .. versionadded:: 1.9
        """
        if self._icon is None:
            return None

        # All role icons are really just emojis so
        # we're borrowing some `Emote` code here
        stock = '/asset/Emojis' in self._icon
        stock_guilded = stock and '/asset/Emojis/Custom' in self._icon
        stock_unicode = stock and '/asset/Emojis/Custom' not in self._icon

        if stock_guilded:
            return Asset._from_guilded_stock_reaction(self._state, self._icon.replace('/asset/Emojis/Custom/', '').replace('.webp', ''))
        elif stock_unicode:
            return Asset._from_unicode_stock_reaction(self._state, self._icon.replace('/asset/Emojis/', '').replace('.webp', ''))
        else:
            return Asset._from_custom_reaction(self._state, self._icon, animated='ia=1' in self._icon)

    @property
    def display_icon(self) -> Optional[Union[Asset, str]]:
        """Optional[:class:`.Asset`]: |dpyattr|

        This is an alias of :attr:`.icon`.

        The role's icon asset, if any.
        """
        return self.icon

    @property
    def hoist(self) -> bool:
        """|dpyattr|

        This is an alias of :attr:`.displayed_separately`.
        """
        return self.displayed_separately

    @property
    def permissions(self) -> Permissions:
        """:class:`.Permissions`: The permissions that the role has."""
        return Permissions(*self._permissions)

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
