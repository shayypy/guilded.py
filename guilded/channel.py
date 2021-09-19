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

from enum import Enum

import guilded.abc

#from .gateway import GuildedVoiceWebSocket
from .message import Message
from .utils import ISO8601

__all__ = (
    'ChannelType',
    'ChatChannel',
    'VoiceChannel',
    'DMChannel',
    'Thread'
)

class ChannelType(Enum):
    chat = 'chat'
    text = chat
    voice = 'voice'
    forum = 'forum'
    docs = 'doc'
    announcements = 'announcements'
    news = announcements
    thread = 'temporal'
    dm = 'DM'

    @classmethod
    def from_str(self, string):
        return getattr(self, string, None)

class ChatChannel(guilded.abc.TeamChannel, guilded.abc.Messageable):
    """Represents a chat channel in a team."""
    def __init__(self, **fields):
        super().__init__(**fields)
        self.type = ChannelType.chat

    async def create_thread(self, *content, **kwargs):
        """|coro|

        Create a new thread in this channel.

        Parameters
        ------------
        content: Any
            The content of the message that should be created as the initial
            message of the newly-created thread. Passing either this or
            ``message`` is required.
        name: :class:`str`
            The name to create the thread with.
        message: Optional[:class:`ChatMessage`]
            The message to create this thread from. Passing either this or
            values for ``content`` is required.
        """
        name = kwargs.get('name')
        message = kwargs.get('message')
        if not name:
            raise TypeError('name is a required argument that is missing.')
        if not message and not content:
            raise TypeError('Must include message, an argument list of content, or both.')

        data = await self._state.create_thread(self.id, content, name=name, initial_message=message)
        thread = Thread(data=data.get('thread', data), state=self._state, group=self.group, team=self.team)
        return thread

class VoiceChannel(guilded.abc.TeamChannel, guilded.abc.Messageable):
    """Represents a voice channel in a team."""
    def __init__(self, **fields):
        super().__init__(**fields)
        self.type = ChannelType.voice
        self._ws = None

    #async def connect(self):
    #    state = self._state

    #    connection_info = await state.get_voice_connection_info(self.id)
    #    endpoint = connection_info['endpoint']
    #    token = connection_info['token']

    #    ws_build = GuildedVoiceWebSocket.build( loop=self.loop)
    #    gws = await asyncio.wait_for(ws_build, timeout=60)
    #    if type(gws) != GuildedVoiceWebSocket:
    #        self.dispatch('error', gws)
    #        return

    #    self._ws = gws
    #    self.dispatch('connect')

    #    lobby = await state.get_voice_lobby(endpoint, self.id)
    #    lobby_connection_data = await state.connect_to_voice_lobby(
    #        endpoint,
    #        self.id,
    #        rtp_capabilities=lobby['routerRtpCapabilities']
    #    )

    #    dtls_parameters = lobby_connection_data['sendTransportOptions']['dtlsParameters']
    #    # The client transforms the default "auto" to "server" and sends only
    #    # the fingerprint where algorithm is "sha-256"
    #    dtls_parameters['role'] = 'server'

    #    transport = await state.connect_to_voice_transport(
    #        endpoint,
    #        self.id,
    #        transport_id=lobby_connection_data['sendTransportOptions']['id'],
    #        dtls_parameters=dtls_parameters
    #    )

class Thread(guilded.abc.TeamChannel, guilded.abc.Messageable):
    """Represents a thread in a team."""
    def __init__(self, **fields):
        super().__init__(**fields)
        data = fields.get('data') or fields.get('channel', {})
        self.type = ChannelType.thread

        self._message_count = data.get('messageCount') or 0
        self.initial_message_id = data.get('threadMessageId')
        self._initial_message = self._state._get_message(self.initial_message_id)
        # this is unlikely to not be None given the temporal nature of message
        # cache but may as well try anyway

        self.participants = []
        participants = data.get('participants')
        if participants is None:
            participants = [{'id': user_id} for user_id in data.get('userIds', [])]
        for member_obj in (participants or []):
            member = self._state._get_team_member(self.team_id, member_obj.get('id'))
            if member is None:
                # it's just an empty member with only ID, better than nothing?
                member = self._state.create_member(member_obj)

            self.participants.append(member)

    @property
    def message_count(self):
        return int(self._message_count)

    @property
    def initial_message(self):
        return self._initial_message

    async def archive(self):
        """|coro|

        Archive this thread.
        """
        request = self._state.archive_team_thread(self.team_id, self.group_id, self.id)
        await request

    async def restore(self):
        """|coro|

        Restore this thread.
        """
        request = self._state.restore_team_thread(self.team_id, self.group_id, self.id)
        await request

    async def leave(self):
        """|coro|

        Leave this thread.
        """
        request = self._state.leave_thread(self.id)
        await request

    async def fetch_initial_message(self):
        """|coro|

        Fetch the initial message in this channel. Sometimes this may be
        available via :attr:`Thread.initial_message`, but it is unlikely
        when dealing with existing threads because it relies on message cache.

        Roughly equivilent to:

        .. code-block:: python3

            initial_message = await thread.fetch_message(thread.initial_message_id)
        """
        data = await self._state.get_message(self.id, self.initial_message_id)
        message = self._state.create_message(data)
        return message

class DMChannel(guilded.abc.Messageable):
    def __init__(self, *, state, data):
        data = data.get('channel', data)
        super().__init__(state=state, data=data)
        self.type = ChannelType.dm
        self.team = None
        self.group = None

        self._users = {}
        self.recipient = None
        for user_data in data.get('users', []):
            user = self._state.create_user(data=user_data)
            if user:
                self._users[user.id] = user
                if user.id != self._state.my_id:
                    self.recipient = user

        self.created_at = ISO8601(data.get('createdAt'))
        self.updated_at = ISO8601(data.get('updatedAt'))
        self.deleted_at = ISO8601(data.get('deletedAt'))
        self.archived_at = ISO8601(data.get('archivedAt'))
        self.auto_archive_at = ISO8601(data.get('autoArchiveAt'))
        self.voice_participants = data.get('voiceParticipants')
        self.last_message = None
        if data.get('lastMessage'):
            message_data = data.get('lastMessage')
            author = self._users.get(message_data.get('createdBy'))
            message = self._state.create_message(channel=self, data=message_data, author=author)
            self.last_message = message

    @property
    def users(self):
        return list(self._users.values())

    def __repr__(self):
        return f'<DMChannel id={self.id!r} recipient={self.recipient!r}>'
