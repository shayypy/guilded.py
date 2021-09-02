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

import guilded.abc

from .colour import Colour
from .utils import ISO8601, parse_hex_number
from .file import File, MediaType


class Device:
    """Represents a device that the :class:`ClientUser` is logged into.

    Attributes
    ------------
    type: :class:`str`
        The type of device. Could be ``desktop`` or ``mobile``.
    id: :class:`str`
        The ID of this device. This is a UUID for mobile devices but an even
        longer string on desktops.
    last_online: :class:`datetime.datetime`
        When this device was last active.
    active: :class:`bool`
        Whether this device is "active". This seems to always be ``True``.
    """
    def __init__(self, data):
        self.type = data.get('type')
        self.id = data.get('id')
        self.last_online = ISO8601(data.get('lastOnline'))
        self.active = data.get('isActive', False)

class User(guilded.abc.User, guilded.abc.Messageable):
    async def block(self):
        """|coro|

        Block this user.
        """
        await self._state.block_user(self.id)

    async def unblock(self):
        """|coro|

        Unblock this user.
        """
        await self._state.unblock_user(self.id)

    async def accept_friend_request(self):
        """|coro|

        Accept this user's friend request, if it exists.
        """
        await self._state.accept_friend_request(self.id)

    async def decline_friend_request(self):
        """|coro|

        Decline this user's friend request, if it exists.
        """
        await self._state.decline_friend_request(self.id)

    async def send_friend_request(self):
        """|coro|

        Send a friend request to this user.
        """
        await self._state.create_friend_request([self.id])

    async def delete_friend_request(self):
        """|coro|

        Delete your friend request to this user, if it exists.
        """
        await self._state.delete_friend_request(self.id)

class Member(User):
    """Represents a member of a team.

    Attributes
    ------------
    team: :class:`Team`
        The team this member is from.
    xp: :class:`int`
        This member's XP. Could be negative.
    joined_at: :class:`datetime.datetime`
        When this user joined their team.
    display_name: :class:`str`
        This member's display name (``nick`` if present, else ``name``)
    colour: Optional[:class:`int`]
        The color that this member's name displays with. There is an alias for 
        this called ``color``.
    nick: Optional[:class:`str`]
        This member's nickname, if any.
    """
    def __init__(self, *, state, data, **extra):
        super().__init__(state=state, data=data)
        self._team = extra.get('team') or data.get('team')
        self.team_id = data.get('teamId') or (self._team.id if self._team else None)

        self.nick = data.get('nickname')
        self.xp = data.get('teamXp')
        self.joined_at = ISO8601(data.get('joinDate'))
        colour = data.get('colour') or data.get('color')
        if colour is not None and not isinstance(colour, Colour):
            self.colour = parse_hex_number(colour)
        else:
            self.colour = colour

    def __repr__(self):
        return f'<Member id={self.id!r} name={self.name!r} team={self.team!r}>'

    @property
    def team(self):
        return self._team or self._state._get_team(self.team_id)

    @property
    def guild(self):
        return self.team

    @property
    def color(self):
        return self.colour

    @property
    def display_name(self):
        return self.nick or self.name

    async def edit(self, **kwargs):
        """|coro|

        Edit this member.

        Parameters
        ------------
        nick: Optional[:class:`str`]
            A new nickname. Use ``None`` to reset.
        xp: Optional[:class:`int`]
            A new XP value.
        """
        try:
            nick = kwargs.pop('nick')
        except KeyError:
            pass
        else:
            if nick is None:
                await self._state.reset_team_member_nickname(self.team.id, self.id)
            else:
                await self._state.change_team_member_nickname(self.team.id, self.id, nick)
            self.nick = nick

        try:
            xp = kwargs.pop('xp')
        except KeyError:
            pass
        else:
            await self._state.set_team_member_xp(self.team.id, self.id, xp)
            self.xp = xp

class ClientUser(guilded.abc.User):
    """Represents the current logged-in user.

    Attributes
    ------------
    devices: List[:class:`Device`]
        The devices this account is logged in on.
    accepted_friends: List[:class:`User`]
        This account's accepted friends. Could be partial (only ID) if the
        user was not cached.
    pending_friends: List[:class:`User`]
        This account's pending friends (requested by this ``ClientUser``).
        Could be partial (only ID) if the user was not cached.
    requested_friends: List[:class:`User`]
        This account's requested friends. Could be partial (only ID) if the
        user was not cached.
    """
    def __init__(self, *, state, data):
        super().__init__(state=state, data=data)
        user = data.get('user', data)

        self.devices = [Device(device_data) for device_data in user.get('devices', [])]
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

    @property
    def friends(self):
        """This user's accepted, pending, and requested friends.

        All items in this list are expected to have ``id``, ``friend_status``,
        and ``friend_requested_at`` attributes at a bare minimum.
        """
        return self.accepted_friends + self.pending_friends + self.requested_friends

    @property
    def accepted_friends(self):
        return list(self._accepted_friends.values())

    @property
    def pending_friends(self):
        return list(self._pending_friends.values())

    @property
    def requested_friends(self):
        return list(self._requested_friends.values())

    def __repr__(self):
        return f'<ClientUser id={repr(self.id)} name={repr(self.name)}>'

    async def fetch_friends(self):
        """|coro|

        Fetch a list of this account's accepted, pending, and requested friends.

        Returns
        ---------
        List[:class:`User`]
            This user's accepted, pending, and requested friends.
        """
        friends = await self._state.get_friends()

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

        #payload = {}
        #await self._state.edit_current_user()
