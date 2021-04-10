import guilded.abc
from .errors import *
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
        super().__init__(state, data)
        user = data.get('user', data)

        self.devices = [Device(device_data) for device_data in user.get('devices', [])]
