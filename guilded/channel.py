from enum import Enum

import guilded.abc
from .utils import ISO8601

class ChannelType(Enum):
    chat = 'chat'
    voice = 'voice'
    forum = 'forum'
    docs = 'doc'
    thread = 'temporal'
    dm = 'DM'

class ChatChannel(guilded.abc.TeamChannel):
    def __init__(self, **fields):
        super().__init__(**fields)
        self.type = ChannelType.chat

class Thread(guilded.abc.TeamChannel):
    def __init__(self, **fields):
        super().__init__(**fields)
        data = fields.get('data', fields.get('channel', {}))  # i mean, just in case
        self.type = ChannelType.thread
        self.participants = []
        if data.get('type').lower() == 'team':
            self.team = fields.get('team') or self._state._get_team(data.get('teamId'))
            team_id = getattr(self.team, 'id', None) or data.get('teamId')
            self.parent = fields.get('parent') or self._state._get_team_channel(data.get('parentChannelId'))
            self.created_by = fields.get('created_by') or self._state._get_team_member(team_id, data.get('createdBy'))
            for user in data.get('participants'):
                _id = user.get('id')
                user = self._state._get_team_member(team_id, data.get('createdBy'))
                if user is not None: self.participants.append(user)

        else:  # realistically this should only ever be DM, but process for any non-team context instead anyway
            self.team = None
            self.parent = fields.get('parent') or self._state._get_dm_channel(data.get('parentChannelId'))
            self.created_by = fields.get('created_by') or self._state._get_user(data.get('createdBy'))
            for user in data.get('participants'):
                _id = user.get('id')
                user = self._state._get_user(data.get('createdBy'))
                if user is not None: self.participants.append(user)

class DMChannel(guilded.abc.Messageable):
    def __init__(self, *, state, data):
        self.type = ChannelType.dm
        self.id = data.get('id')
        self._channel_id = self.id
        self.users = []
        self.recipient = None
        self.team = None
        for user_data in data.get('users', []):
            user = self._state._get_user(user_data.get('id'))
            if user:
                self.users.append(user)
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
            author = self._state._get_user(message_data.get('createdBy'))
            message = self._state._get_message(message_data.get('id')) or Message(state=self._state, channel=self, data=message_data, author=author)
            self.last_message = message
