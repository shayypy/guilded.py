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


class Device:
    def __init__(self, data):
        self.type = data.get('type')
        self.id = data.get('id')
        self.last_online = ISO8601(data.get('lastOnline'))
        self.active = data.get('isActive', False)

class User(guilded.abc.User, guilded.abc.Messageable):
    pass

class Member(guilded.abc.User, guilded.abc.Messageable):
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
