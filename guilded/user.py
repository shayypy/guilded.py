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
from typing import Any, Callable, Coroutine, List, Optional, TYPE_CHECKING, Union

import guilded.abc

from .asset import Asset
from .colour import Colour
from .enums import MediaType
from .file import File
from .role import Role
from .utils import copy_doc, ISO8601

if TYPE_CHECKING:
    from .types.user import User as UserPayload


__all__ = (
    'BanEntry',
    'ClientUser',
    'Device',
    'Member',
    'MemberBan',
    'User',
)


class Device:
    """Represents a device that the :class:`ClientUser` is logged into.

    Attributes
    -----------
    type: :class:`str`
        The type of device. Could be ``desktop`` or ``mobile``.
    id: :class:`str`
        The ID of this device. This is a UUID for mobile devices but an even
        longer string for desktops.
    last_online: :class:`datetime.datetime`
        When this device was last active.
    active: :class:`bool`
        Whether this device is "active". This seems to always be ``True``.
    """
    def __init__(self, data):
        self.type: str = data.get('type')
        self.id: str = data.get('id')
        self.last_online: datetime.datetime = ISO8601(data.get('lastOnline'))
        self.active: bool = data.get('isActive', False)


class User(guilded.abc.User, guilded.abc.Messageable):
    """Represents a user in Guilded."""
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

    async def block(self):
        """|coro|

        |onlyuserbot|

        Block this user.
        """
        await self._state.block_user(self.id)

    async def unblock(self):
        """|coro|

        |onlyuserbot|

        Unblock this user.
        """
        await self._state.unblock_user(self.id)

    async def accept_friend_request(self):
        """|coro|

        |onlyuserbot|

        Accept this user's friend request, if it exists.
        """
        await self._state.accept_friend_request(self.id)

    async def decline_friend_request(self):
        """|coro|

        |onlyuserbot|

        Decline this user's friend request, if it exists.
        """
        await self._state.decline_friend_request(self.id)

    async def send_friend_request(self):
        """|coro|

        |onlyuserbot|

        Send a friend request to this user.
        """
        await self._state.create_friend_request([self.id])

    async def delete_friend_request(self):
        """|coro|

        |onlyuserbot|

        Delete your friend request to this user, if it exists.
        """
        await self._state.delete_friend_request(self.id)


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
    """Represents a member of a :class:`.Team`.

    .. container:: operations

        .. describe:: x == y

            Checks if two members are equal.
            Note that this works with :class:`User` instances too.

        .. describe:: x != y

            Checks if two members are not equal.
            Note that this works with :class:`User` instances too.

        .. describe:: str(x)

            Returns the member's name.

    Attributes
    -----------
    xp: :class:`int`
        The member's XP. Could be negative.
    joined_at: :class:`datetime.datetime`
        When the member joined their team.
    colour: Optional[:class:`.Colour`]
        The colour that the member's name displays with.
    nick: Optional[:class:`str`]
        The member's nickname, if any.
    """

    __slots__ = (
        '_state',
        '_role_ids',
        '_user'
        '_team',
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
        create_dm: Callable[[], Coroutine[Any, Any, guilded.abc.Messageable]]
        banner: Optional[Asset]

    def __init__(self, *, state, data, **extra):
        self._state = state
        self._user = User(state=state, data=data)
        state._users[self._user.id] = self._user

        self._team = extra.get('team') or extra.get('server')
        self.team_id: str = data.get('teamId') or data.get('serverId')

        self.bot_id: str = extra.get('bot_id')
        self._role_ids: List[int] = data.get('roleIds') or []
        self._owner: Optional[bool] = data.get('isOwner')
        self.nick: Optional[str] = data.get('nickname')
        self.xp: Optional[int] = data.get('teamXp')
        self.joined_at: datetime.datetime = ISO8601(data.get('joinedAt') or data.get('joinDate'))

        self.colour: Optional[Colour]
        colour = data.get('colour') or data.get('color')
        if colour is not None and not isinstance(colour, Colour):
            self.colour = Colour.from_str(colour)
        else:
            self.colour = colour

    def __repr__(self) -> str:
        return f'<Member id={self._user.id!r} name={self._user.name!r} type={self._user._user_type!r} team={self.team!r}>'

    def __str__(self) -> str:
        return str(self._user)

    def __eq__(self, other: guilded.abc.User) -> bool:
        return isinstance(other, guilded.abc.User) and other.id == self.id

    @property
    def team(self):
        """:class:`.Team`: The team that this member is from."""
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
    def color(self) -> Optional[Colour]:
        """Optional[:class:`.Colour`]: This is an alias of :attr:`.colour`."""
        return self.colour

    @property
    def roles(self) -> List[Role]:
        """List[:class:`.Role`]: The cached list of roles that this member has."""
        roles = [self.team.get_role(int(role_id)) for role_id in self._role_ids if self.team.get_role(int(role_id)) is not None]
        return roles

    @property
    def bot(self) -> bool:
        """:class:`bool`: Whether the member is a bot or webhook. For user/bot
        accounts, this attribute depends on :attr:`Team.bot_role`, so it may
        be unreliable as Guilded does not explicitly provide which role is the
        bot role."""
        return self._user.bot or (
            self.team is not None
            and self.team.bot_role is not None
            and self.team.bot_role.id in self._role_ids
        )

    @classmethod
    def _copy(cls, member):
        self = cls.__new__(cls)

        self._user = member._user
        self._role_ids = member._role_ids.copy()
        self._state = member._state
        self._team = member._team
        self.team_id = member.team_id

        self.nick = member.nick
        self.joined_at = member.joined_at
        self.xp = member.xp
        self.colour = member.colour

        return self

    def _update(self, data):
        try:
            self.nick = data.pop('nickname')
        except KeyError:
            pass

        super()._update(data)

    def _update_roles(self, role_ids: List[int]):
        self._role_ids = [int(role_id) for role_id in role_ids]

    def is_owner(self) -> bool:
        """:class:`bool`: Whether this member is the owner of their team.

        This may incorrectly be ``False`` when the member and team are both partial.
        """
        if self._owner is not None:
            return self._owner
        return self.team.owner_id == self.id

    async def edit(self, **kwargs):
        """|coro|

        Edit this member.

        All parameters are optional.

        Parameters
        -----------
        nick: :class:`str`
            A new nickname. Use ``None`` to reset.
        xp: :class:`int`
            A new XP value.
        """
        try:
            nick: str = kwargs.pop('nick')
        except KeyError:
            pass
        else:
            if self._state.userbot:
                if nick is None:
                    await self._state.reset_team_member_nickname(self.team.id, self.id)
                else:
                    await self._state.change_team_member_nickname(self.team.id, self.id, nick)
            else:
                if nick is None:
                    await self._state.delete_member_nickname(self.team.id, self.id)
                else:
                    data = await self._state.update_member_nickname(self.team.id, self.id, nick)
                    nick = data['nickname']
            self.nick = nick

        try:
            xp: int = kwargs.pop('xp')
        except KeyError:
            pass
        else:
            if self._state.userbot:
                await self._state.set_team_member_xp(self.team.id, self.id, xp)
            else:
                xp = await self.award_xp(xp - (self.xp or 0))
            self.xp = xp

    async def ban(self, **kwargs):
        """|coro|

        Ban this member. Equivalent to :meth:`Team.ban`.
        """
        return await self.team.ban(self, **kwargs)

    async def unban(self):
        """|coro|

        Unban this member. Equivalent to :meth:`Team.unban`.
        """
        return await self.team.unban(self)

    async def kick(self):
        """|coro|

        Kick this member. Equivalent to :meth:`Team.kick`.
        """
        return await self.team.kick(self)

    async def add_role(self, role: Role):
        """|coro|

        Add a role to this member.

        Parameters
        -----------
        role: :class:`.Role`
            The role to give this member.
        """
        await self._state.assign_role_to_member(self.team.id, self.id, role.id)

    async def add_roles(self, *roles: Role):
        """|coro|

        |dpyattr|

        .. note::

            Guilded does not support adding multiple roles in one request, so
            this method calls :meth:`.add_role` for each item passed to
            ``roles``.

        Parameters
        -----------
        roles: List[:class:`.Role`]
            The roles to add to the member.
        """
        for role in roles:
            await self.add_role(role)

    async def remove_role(self, role: Role):
        """|coro|

        Remove a role from this member.

        Parameters
        -----------
        role: :class:`.Role`
            The role to remove from member.
        """
        await self._state.remove_role_from_member(self.team.id, self.id, role.id)

    async def remove_roles(self, *roles: Role):
        """|coro|

        |dpyattr|

        .. note::

            Guilded does not support removing multiple roles in one request,
            so this method calls :meth:`.remove_role` for each item passed to
            ``roles``.

        Parameters
        -----------
        roles: List[:class:`.Role`]
            The roles to remove from the member.
        """
        for role in roles:
            await self.remove_role(role)

    async def fetch_role_ids(self):
        """|coro|

        |onlybot|

        Fetch the list of role IDs assigned to this member.

        Returns
        --------
        List[:class:`int`]
            The IDs of the roles that the member has.
        """
        data = await self._state.get_member_roles(self.team.id, self.id)
        return data['roleIds']

    async def award_xp(self, amount: int):
        """|coro|

        |onlybot|

        Award XP to this member. Could be a negative value to remove XP.

        .. note::

            This method *adds* XP to the current value. To set a member's XP
            total, use :meth:`.edit`.

        Parameters
        -----------
        amount: :class:`int`
            The amount of XP to award.

        Returns
        --------
        :class:`int`
            The total amount of XP this member now has.
        """
        data = await self._state.award_member_xp(self.team.id, self.id, amount)
        self.xp = data['total']
        return self.xp


class MemberBan:
    """Represents a ban created in a :class:`.Team`.

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
    team: :class:`.Team`
        The team that the ban is in.
    author_id: :class:`str`
        The user's ID who created the ban.
    """

    __slots__ = (
        '_state',
        'team',
        'user',
        'reason',
        'created_at',
        'author_id',
    )

    def __init__(self, *, state, data, team, user: Union[Member, User] = None):
        self._state = state
        self.team = team

        if 'user' in data:
            # Bot API
            _user = state.create_user(data=data['user'])
        elif 'userId' in data:
            # User API
            _user = state._get_user(data['userId']) or state.create_user(data={'id': data['userId']})
        else:
            # This shouldn't happen
            _user = None

        self.user: Union[Member, User] = user or _user
        self.reason: Optional[str] = data.get('reason')
        self.created_at: datetime.datetime = ISO8601(data.get('createdAt'))
        self.author_id: str = data.get('bannedBy', data.get('createdBy'))

    def __repr__(self) -> str:
        return f'<MemberBan user={self.user!r} team={self.team!r}>'

    def __eq__(self, other) -> bool:
        return isinstance(other, MemberBan) and other.team == self.team and other.user == self.user

    @property
    def author(self) -> Optional[Member]:
        """Optional[:class:`.Member`]: The user who created the ban."""
        return self.team.get_member(self.author_id)

    @property
    def guild(self):
        """|dpyattr|

        This is an alias of :attr:`.team`.
        """
        return self.team

    @property
    def server(self):
        """Optional[:class:`.Team`]: This is an alias of :attr:`.team`."""
        return self.team

    async def revoke(self):
        """|coro|

        Revoke this ban; unban the user it was created for.

        This is equivalent to :meth:`.Team.unban`.
        """
        await self.team.unban(self.user)

BanEntry = MemberBan  # discord.py


class ClientUser(guilded.abc.User):
    """Represents the current logged-in user.

    Attributes
    -----------
    devices: List[:class:`Device`]
        The devices this account is logged in on.
    """

    def __init__(self, *, state, data):
        super().__init__(state=state, data=data)
        user = data.get('user', data)

        self._bot: bool = not state.userbot
        self.devices: List[Device] = [Device(device_data) for device_data in user.get('devices', [])]
        self._accepted_friends = {}
        self._pending_friends = {}
        self._requested_friends = {}

        for partial_friend in data.get('friends', []):
            friend_user = self._state._get_user(partial_friend['friendUserId'])
            if not friend_user:
                friend_user = self._state.create_user(
                    data={'id': partial_friend['friendUserId']},
                    friend_status=partial_friend['friendStatus'],
                    friend_created_at=partial_friend['createdAt']
                )
            else:
                friend_user.friend_status = partial_friend['friendStatus']
                friend_user.friend_requested_at = ISO8601(partial_friend['createdAt'])

            if friend_user.friend_status == 'accepted':
                self._accepted_friends[friend_user.id] = friend_user
            elif friend_user.friend_status == 'pending':
                self._pending_friends[friend_user.id] = friend_user
            elif friend_user.friend_status == 'requested':
                self._requested_friends[friend_user.id] = friend_user

    def __repr__(self):
        return f'<ClientUser id={self.id!r} bot={self.bot} name={self.name!r}>'

    @property
    def friends(self):
        """List[:class:`User`]: This user's accepted, pending, and requested
        friends.

        All items in this list are expected to have ``id``, ``friend_status``,
        and ``friend_requested_at`` attributes at a bare minimum.
        """
        return self.accepted_friends + self.pending_friends + self.requested_friends

    @property
    def accepted_friends(self):
        """List[:class:`User`]: This account's accepted friends. Users in this
        list could be partial (only ``id``) if the user was not cached."""
        return list(self._accepted_friends.values())

    @property
    def pending_friends(self):
        """List[:class:`User`]: This account's pending friends (requested by
        this ``ClientUser``). Users in this list could be partial (only
        ``id``) if the user was not cached."""
        return list(self._pending_friends.values())

    @property
    def requested_friends(self):
        """List[:class:`User`]: This account's requested friends. Users in
        this list could be partial (only ``id``) if the user was not cached."""
        return list(self._requested_friends.values())

    @property
    def bot(self) -> bool:
        """class:`bool`: Whether this client is a bot account as opposed to a
        userbot."""
        return self._bot

    async def fetch_friends(self) -> List[User]:
        """|coro|

        Fetch a list of this account's accepted, pending, and requested friends.

        Returns
        --------
        List[:class:`User`]
            This user's accepted, pending, and requested friends.
        """
        friends = await self._state.get_friends()

        self._accepted_friends.clear()
        self._pending_friends.clear()
        self._requested_friends.clear()

        for friend_data in friends.get('friends', []):
            friend = self._state.create_user(data=friend_data, friend_status='accepted')
            self._accepted_friends[friend.id] = friend

        for friend_data in friends.get('friendRequests', {}).get('pending', []):
            friend = self._state.create_user(data=friend_data, friend_status='pending')
            self._pending_friends[friend.id] = friend

        for friend_data in friends.get('friendRequests', {}).get('requested', []):
            friend = self._state.create_user(data=friend_data, friend_status='requested')
            self._requested_friends[friend.id] = friend

        return self.friends

    async def edit_settings(self, **kwargs):
        """|coro|

        Change client settings.
        """
        payload = {}
        try:
            payload['useLegacyNav'] = kwargs.pop('legacy_navigation')
        except KeyError:
            pass

    async def edit(self, **kwargs):
        """|coro|

        Edit your account.
        """
        try:
            avatar = kwargs.pop('avatar')
        except KeyError:
            pass
        else:
            if avatar is None:
                image_url = None
            else:
                file = File(avatar)
                file.set_media_type(MediaType.user_avatar)
                await file._upload(self._state)
                image_url = file.url

            await self._state.set_profile_images(image_url)

        try:
            banner = kwargs.pop('banner')
        except KeyError:
            pass
        else:
            if banner is None:
                image_url = None
            else:
                file = File(banner)
                file.set_media_type(MediaType.user_banner)
                await file._upload(self._state)
                image_url = file.url

            await self._state.set_profile_banner(image_url)
