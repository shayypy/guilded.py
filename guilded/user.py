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

from .utils import ISO8601
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
    pass

class Member(guilded.abc.User, guilded.abc.Messageable):
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
        self.team = extra.get('team') or data.get('team')
        self.team_id = data.get('teamId') or (self.team.id if self.team else None)
        self.nick = data.get('nickname')
        self.xp = data.get('teamXp')
        self.joined_at = ISO8601(data.get('joinDate'))
        self.colour = data.get('colour') or data.get('color')

    def __repr__(self):
        return f'<Member id={self.id} name={self.name} team={repr(self.team)}>'

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
    """
    def __init__(self, *, state, data):
        super().__init__(state=state, data=data)
        user = data.get('user', data)

        self.devices = [Device(device_data) for device_data in user.get('devices', [])]

    def __repr__(self):
        return f'<ClientUser id={self.id} name={self.name}>'

    async def edit_settings(self, **kwargs):
        """|coro|
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
