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
import inspect
import itertools
from operator import attrgetter
from typing import Any, List, Optional, TYPE_CHECKING, Set, Union

import guilded.abc

from .asset import Asset
from .role import Role
from .utils import MISSING, Object, copy_doc, ISO8601

if TYPE_CHECKING:
    from .types.user import (
        User as UserPayload,
        ServerMember as ServerMemberPayload,
        ServerMemberBan as ServerMemberBanPayload,
    )

    from .server import Server


__all__ = (
    'BanEntry',
    'ClientUser',
    'Member',
    'MemberBan',
    'User',
)


class User(guilded.abc.User, guilded.abc.Messageable):
    """Represents a user in Guilded.

    .. container:: operations

        .. describe:: x == y

            Checks if two users are equal.

        .. describe:: x != y

            Checks if two users are not equal.

        .. describe:: hash(x)

            Returns the user's hash.

        .. describe:: str(x)

            Returns the user's name.
    """
    def _update(self, data: UserPayload):
        try:
            self.stonks: int = data.pop('stonks')
        except KeyError:
            pass

        try:
            self.badges: List[str] = data.pop('badges')
        except KeyError:
            pass

        try:
            self.tagline: str = data.pop('tagline')
        except KeyError:
            pass

        try:
            self.bio: str = data.pop('bio')
        except KeyError:
            pass

        try:
            self.subdomain: str = data.pop('subdomain')
        except KeyError:
            pass

        if 'profilePicture' in data and data['profilePicture'] is not None:
            self.avatar: Optional[Asset] = Asset._from_user_avatar(self._state, data.pop('profilePicture'))
        elif 'avatar' in data and data['avatar'] is not None:
            self.avatar: Optional[Asset] = Asset._from_user_avatar(self._state, data.pop('avatar'))
        elif 'profilePicture' in data or 'avatar' in data:
            self.avatar: Optional[Asset] = None

        if 'profileBannerBlur' in data and data['profileBannerBlur'] is not None:
            self.banner: Optional[Asset] = Asset._from_user_banner(self._state, data.pop('profileBannerBlur'))
        elif 'banner' in data and data['banner'] is not None:
            self.banner: Optional[Asset] = Asset._from_user_banner(self._state, data.pop('banner'))
        elif 'profilePicture' in data or 'banner' in data:
            self.banner: Optional[Asset] = None


def flatten_user(cls: Any):
    for attr, value in itertools.chain(guilded.abc.User.__dict__.items(), User.__dict__.items()):
        # ignore private/special methods
        if attr.startswith('_'):
            continue

        # don't override what we already have
        if attr in cls.__dict__:
            continue

        # if it's a slotted attribute or a property, redirect it
        # slotted members are implemented as member_descriptors in Type.__dict__
        if not hasattr(value, '__annotations__'):
            getter = attrgetter('_user.' + attr)
            setattr(cls, attr, property(getter, doc=f'Equivalent to :attr:`User.{attr}`'))
        else:
            # Technically, this can also use attrgetter
            # However I'm not sure how I feel about "functions" returning properties
            # It probably breaks something in Sphinx.
            # probably a member function by now
            def generate_function(x):
                # We want sphinx to properly show coroutine functions as coroutines
                if inspect.iscoroutinefunction(value):

                    async def general(self, *args, **kwargs):  # type: ignore
                        return await getattr(self._user, x)(*args, **kwargs)

                else:

                    def general(self, *args, **kwargs):
                        return getattr(self._user, x)(*args, **kwargs)

                general.__name__ = x
                return general

            func = generate_function(attr)
            func = copy_doc(value)(func)
            setattr(cls, attr, func)

    return cls


@flatten_user
class Member(User):
    """Represents a member of a :class:`.Server`.

    .. container:: operations

        .. describe:: x == y

            Checks if two members are equal.
            Note that this works with :class:`~guilded.User` instances too.

        .. describe:: x != y

            Checks if two members are not equal.
            Note that this works with :class:`~guilded.User` instances too.

        .. describe:: hash(x)

            Returns the member's hash.

        .. describe:: str(x)

            Returns the member's name.

    Attributes
    -----------
    joined_at: :class:`datetime.datetime`
        When the member joined their server.
    nick: Optional[:class:`str`]
        The member's nickname, if any.
    """

    __slots__ = (
        '_state',
        '_role_ids',
        '_user'
        '_server',
        'bot_id',
        'nick',
        'xp',
        'joined_at',
        'colour',
    )

    if TYPE_CHECKING:
        id: str
        name: str
        created_at: datetime.datetime
        default_avatar: Asset
        avatar: Optional[Asset]
        dm_channel: Optional[guilded.abc.Messageable]
        banner: Optional[Asset]

    def __init__(self, *, state, data: ServerMemberPayload, **extra):
        self._state = state
        self._user = User(state=state, data=data)
        state._users[self._user.id] = self._user

        self._server = extra.get('server')
        self.server_id: str = data.get('teamId') or data.get('serverId')

        self._role_ids: Set[int] = set(data.get('roleIds') or [])
        self._owner: Optional[bool] = data.get('isOwner')
        self.nick: Optional[str] = data.get('nickname')
        self.joined_at: datetime.datetime = ISO8601(data.get('joinedAt'))

    def __repr__(self) -> str:
        return f'<Member id={self._user.id!r} name={self._user.name!r} type={self._user._user_type!r} server={self.server!r}>'

    def __str__(self) -> str:
        return str(self._user)

    @property
    def server(self) -> Server:
        """:class:`.Server`: The server that this member is from."""
        return self._server or self._state._get_server(self.server_id)

    @property
    def guild(self) -> Server:
        """|dpyattr|

        This is an alias of :attr:`.server`.
        """
        return self.server

    @property
    def roles(self) -> List[Role]:
        """List[:class:`.Role`]: The cached list of roles that this member has."""
        roles = [
            self.server.get_role(int(role_id))
            for role_id in self._role_ids
            if self.server.get_role(int(role_id)) is not None
        ]
        return roles

    @property
    def bot(self) -> bool:
        """:class:`bool`: Whether the member is a bot or webhook. For user/bot
        accounts, this attribute depends on :attr:`Server.bot_role`, so it may
        be unreliable as Guilded does not explicitly provide which role is the
        bot role."""
        return self._user.bot or (
            self.server is not None
            and self.server.bot_role is not None
            and self.server.bot_role.id in self._role_ids
        )

    @classmethod
    def _copy(cls, member: Member):
        self = cls.__new__(cls)

        self._user = member._user
        self._role_ids = member._role_ids.copy()
        self._state = member._state
        self._server = member._server
        self.server_id = member.server_id

        self.nick = member.nick
        self.joined_at = member.joined_at
        self._owner = member._owner

        return self

    def _update(self, data: ServerMemberPayload):
        try:
            self.nick = data.pop('nickname')
        except KeyError:
            pass

        super()._update(data)

    def _update_roles(self, role_ids: List[int]):
        self._role_ids = {int(role_id) for role_id in role_ids}

    def is_owner(self) -> bool:
        """:class:`bool`: Whether this member is the owner of their server.

        This may incorrectly be ``False`` when the member and server are both partial.
        """
        if self._owner is not None:
            return self._owner
        return self.server.owner_id == self.id

    async def set_nickname(self, nickname: Optional[str], /) -> Optional[str]:
        """|coro|

        Set this member's nickname. Use ``None`` to remove their nickname.

        Returns
        --------
        Optional[:class:`str`]
            The member's nickname after the operation.

        Raises
        -------
        NotFound
            This member does not exist.
        Forbidden
            You are not allowed to edit this member's nickname.
            You can never edit a member who is above you in the role hierarchy.
        HTTPException
            Failed to set this member's nickname.
        """
        if nickname is None:
            await self._state.delete_member_nickname(self.server.id, self.id)
        else:
            data = await self._state.update_member_nickname(self.server.id, self.id, nickname)
            return data['nickname']  # In case it was modified silently

    async def edit(
        self,
        *,
        nick: Optional[str] = MISSING,
        roles: List[Role] = MISSING,
        **kwargs,
    ) -> None:
        """|coro|

        Edit this member.

        Depending on the parameters provided, this method requires different permissions:

        +-----------------+--------------------------------------+
        |   Parameter     |              Permission              |
        +-----------------+--------------------------------------+
        | nick            | :attr:`Permissions.manage_nicknames` |
        +-----------------+--------------------------------------+
        | roles           | :attr:`Permissions.manage_roles`     |
        +-----------------+--------------------------------------+

        All parameters are optional.

        Parameters
        -----------
        nick: :class:`str`
            A new nickname. Use ``None`` to remove their nickname.
        roles: List[:class:`.Role`]
            The member's new list of roles. This *replaces* the roles.
            Providing this parameter causes your client to make multiple API requests.

        Raises
        -------
        NotFound
            This member does not exist.
        Forbidden
            You are not allowed to edit this member.
            You can never edit a member who is above you in the role hierarchy.
        HTTPException
            Failed to edit this member.
        """
        
        if nick is not MISSING:
            await self.set_nickname(nick)

        if roles is not MISSING:
            new_role_ids = [role.id for role in roles]
            current_role_ids = await self.fetch_role_ids()

            # Add new roles
            for role in roles:
                if role.id not in current_role_ids:
                    await self.add_role(role)

            # Remove roles not passed
            for role_id in current_role_ids:
                if role_id not in new_role_ids:
                    await self.remove_role(Object(role_id))

    async def ban(self, **kwargs) -> MemberBan:
        """|coro|

        Ban this member. Equivalent to :meth:`Server.ban`.
        """
        return await self.server.ban(self, **kwargs)

    async def unban(self) -> None:
        """|coro|

        Unban this member. Equivalent to :meth:`Server.unban`.
        """
        await self.server.unban(self)

    async def kick(self) -> None:
        """|coro|

        Kick this member. Equivalent to :meth:`Server.kick`.
        """
        return await self.server.kick(self)

    async def add_role(self, role: Role) -> None:
        """|coro|

        Add a role to this member.

        Parameters
        -----------
        role: :class:`.Role`
            The role to give this member.
        """

        await self._state.assign_role_to_member(self.server.id, self.id, role.id)
        self._role_ids.add(role.id)

    async def add_roles(self, *roles: Role) -> None:
        """|coro|

        |dpyattr|

        Add roles to this member.

        Parameters
        -----------
        roles: List[:class:`.Role`]
            The roles to add to the member.
        """

        for role in roles:
            await self.add_role(role)

    async def remove_role(self, role: Role) -> None:
        """|coro|

        Remove a role from this member.

        Parameters
        -----------
        role: :class:`.Role`
            The role to remove from member.
        """

        await self._state.remove_role_from_member(self.server.id, self.id, role.id)
        self._role_ids.discard(role.id)

    async def remove_roles(self, *roles: Role) -> None:
        """|coro|

        |dpyattr|

        Remove roles from this member.

        Parameters
        -----------
        roles: List[:class:`.Role`]
            The roles to remove from the member.
        """

        for role in roles:
            await self.remove_role(role)

    async def fetch_role_ids(self) -> List[int]:
        """|coro|

        Fetch the list of role IDs assigned to this member.

        Returns
        --------
        List[:class:`int`]
            The IDs of the roles that the member has.
        """

        data = await self._state.get_member_roles(self.server.id, self.id)
        return data['roleIds']

    async def award_xp(self, amount: int, /) -> int:
        """|coro|

        Award XP to this member. Could be a negative value to remove XP.

        .. note::

            This method *modifies* the current value, it does not replace it.

        Parameters
        -----------
        amount: :class:`int`
            The amount of XP to award.

        Returns
        --------
        :class:`int`
            The total amount of XP this member has after the operation.
        """

        data = await self._state.award_member_xp(self.server.id, self.id, amount)
        self.xp = data['total']
        return self.xp


class MemberBan:
    """Represents a ban created in a :class:`.Server`.

    .. container:: operations

        .. describe:: x == y

            Checks if two bans are equal.

        .. describe:: x != y

            Checks if two bans are not equal.

    Attributes
    -----------
    user: Union[:class:`.Member`, :class:`.User`]
        The user that is banned.
    reason: Optional[:class:`str`]
        The reason for the ban.
    created_at: :class:`datetime.datetime`
        When the ban was created.
    server: :class:`.Server`
        The server that the ban is in.
    author_id: :class:`str`
        The user's ID who created the ban.
    """

    __slots__ = (
        '_state',
        'server',
        'user',
        'reason',
        'created_at',
        'author_id',
    )

    def __init__(self, *, state, data: ServerMemberBanPayload, server: Server):
        self._state = state
        self.server = server

        self.user: Union[Member, User] = state.create_user(data=data['user'])
        self.reason: Optional[str] = data.get('reason')
        self.created_at: datetime.datetime = ISO8601(data.get('createdAt'))
        self.author_id: str = data.get('bannedBy', data.get('createdBy'))

    def __repr__(self) -> str:
        return f'<MemberBan user={self.user!r} server={self.server!r}>'

    def __eq__(self, other) -> bool:
        return isinstance(other, MemberBan) and other.server == self.server and other.user == self.user

    @property
    def author(self) -> Optional[Member]:
        """Optional[:class:`.Member`]: The user who created the ban."""
        return self.server.get_member(self.author_id)

    @property
    def guild(self) -> Server:
        """|dpyattr|

        This is an alias of :attr:`.server`.
        """
        return self.server

    async def revoke(self) -> None:
        """|coro|

        Revoke this ban; unban the user it was created for.

        This is equivalent to :meth:`.Server.unban`.
        """
        await self.server.unban(self.user)

BanEntry = MemberBan  # discord.py


class ClientUser(guilded.abc.User):
    """Represents the current logged-in user."""

    def __init__(self, *, state, data: UserPayload):
        super().__init__(state=state, data=data)

    def __repr__(self):
        return f'<ClientUser id={self.id!r} bot_id={self.bot_id!r} name={self.name!r}>'
