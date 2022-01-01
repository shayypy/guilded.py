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

from .asset import Asset
from .enums import FlowTriggerType, FlowActionType, try_enum
from .utils import ISO8601


__all__ = (
    'Flow',
    'FlowBot'
)


class FlowBot:
    """Represents a flowbot in a :class:`.Team`.

    Attributes
    -----------
    id: :class:`str`
        The flowbot's ID.
    name: :class:`str`
        The flowbot's name.
    enabled: :class:`str`
        Whether the flowbot is enabled.
    created_at: Optional[:class:`str`]
        When the flowbot was created.
    deleted_at: Optional[:class:`str`]
        When the flowbot was deleted.
    """
    def __init__(self, *, state, data, **extra):
        self._state = state

        self._flows = {}
        for flow_data in data.get('flows') or []:
            flow = Flow(data=flow_data, bot=self)
            self._flows[flow.id] = flow

        self._team = extra.get('team')
        self.team_id: str = data.get('teamId')

        self.user_id: str = data.get('userId')
        if self.member:
            self.member._bot: bool = True

        self._author = extra.get('author')
        self.author_id: str = data.get('createdBy')

        self.id: str = data['id']
        self.name: str = data.get('name') or ''
        self.enabled: bool = data.get('enabled', False)
        self.icon_url: Asset = Asset('iconUrl', state=self._state, data=data)

        self.created_at: Optional[datetime.datetime] = ISO8601(data.get('createdAt'))
        self.deleted_at: Optional[datetime.datetime] = ISO8601(data.get('deletedAt'))

    def __str__(self):
        return self.name

    def __repr__(self):
        return f'<FlowBot id={self.id!r} name={self.name!r} enabled={self.enabled} flows={len(self.flows)} team={self.team!r}>'

    @property
    def team(self):
        """:class:`.Team`: The team that this flowbot is in."""
        return self._team or self._state._get_team(self.team_id)

    @property
    def guild(self):
        """:class:`.Team`: This is an alias of :attr:`.team`."""
        return self.team

    @property
    def author(self):
        """Optional[:class:`.Member`]: The user that
        created this flowbot, if they are cached.
        """
        return (
            self._author
            or self._state._get_team_member(self.team_id, self.author_id)
        )

    @property
    def member(self):
        """Optional[:class:`.Member`]: This bot's member object in this team,
        if it is cached."""
        return self._state._get_team_member(self.team_id, self.user_id)

    @property
    def flows(self):
        """List[:class:`.Flow`]: The cached list of flows for this flowbot."""
        return list(self._flows.values())

    @property
    def mention(self) -> str:
        """:class:`str`: The mention string of this flowbot's member object.
        This is roughly equivalent to ``flowbot.member.mention``."""
        return f'<@{self.user_id}>'


class Flow:
    def __init__(self, *, data, bot):
        self.bot = bot
        self.bot_id: str = data.get('botId')

        self.id: str = data['id']
        self.trigger_type: FlowTriggerType = try_enum(FlowTriggerType, data.get('triggerType'))
        self.action_type: FlowActionType = try_enum(FlowActionType, data.get('actionType'))

        self.enabled: bool = data.get('enabled', False)
        self.error: bool = data.get('error', False)
        self.team_id: str = data.get('teamId')
        self.author_id: str = data.get('userId', data.get('createdBy'))

        self.created_at: Optional[datetime.datetime] = ISO8601(data.get('createdAt'))
        self.deleted_at: Optional[datetime.datetime] = ISO8601(data.get('deletedAt'))

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return f'<Flow id={self.id!r} enabled={self.enabled} trigger_type={self.trigger_type!r} action_type={self.action_type!r} bot={self.bot!r}>'
