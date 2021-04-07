import abc

from .asset import Asset
from .file import MediaType
from .message import Message
from .activity import Activity
from .utils import ISO8601, GUILDED_EPOCH_ISO8601

class Messageable(metaclass=abc.ABCMeta):
    def __init__(self, *, state, data):
        self._state = state
        self.id = data.get('id')
        self._channel_id = data.get('id')
        self.type = None

    async def send(self, content: str = None, *, embed = None, embeds: list = None, file = None, files: list = None):
        '''Send to a Guilded channel.'''
        payload = {}
        if content:
            payload['content'] = content
        if embed:
            embeds = [embed, *(embeds or [])]
        if embeds is not None:
            payload['embeds'] = [embed.to_dict() for embed in embeds]
        if file:
            files = [file, *(files or [])]
        if files is not None:
            pl_files = []
            for file in files:
                file.type = MediaType.attachment
                if file.url is None:
                    await file._upload(self._state)
                pl_files.append(file)

            payload['files'] = pl_files

        response_coro, payload = self._state.send_message(self._channel_id, **payload)
        response = await response_coro
        payload['createdAt'] = response.pop('message', response or {}).pop('createdAt', None)
        payload['id'] = payload.pop('messageId')

        return Message(state=self._state, channel=self, data=payload)

    async def trigger_typing(self):
        '''Begin your typing indicator in this channel.'''
        return await self._state.trigger_typing(self._channel_id)

    async def history(self, *, limit: int = 51):
        history = await self._state.get_channel_messages(self._channel_id, limit=limit)
        messages = []
        for message in history.get('messages', []):
            try:
                messages.append(Message(state=self._state, channel=self, data=message))
            except:
                pass

        return messages

    async def fetch_message(self, id: str):
        message_data = await self._state.get_channel_message(self._channel_id, id)
        return Message(state=self._state, channel=self, data=message_data)

class User(metaclass=abc.ABCMeta):
    def __init__(self, state, data):
        self._state = state
        data = data.get('user', data)

        self.type = None
        self.id = data.get('id')
        self.name = data.get('name')
        self.subdomain = data.get('subdomain')
        self.email = data.get('email')
        self.service_email = data.get('serviceEmail')
        self.games = data.get('aliases', [])
        self.bio = (data.get('aboutInfo') or {}).get('bio') or ''
        self.tagline = (data.get('aboutInfo') or {}).get('tagLine') or ''
        activity = data.get('userStatus', {})
        if activity.get('content'):
            self.activity = Activity.build(activity['content'])
        else:
            self.activity = None

        self.online_at = ISO8601(data.get('lastOnline', GUILDED_EPOCH_ISO8601))
        self.created_at = ISO8601(data.get('joinDate', GUILDED_EPOCH_ISO8601))
        # ^ this will end up being the team join date for a member,
        # not much I can do without re-fetching the user

        self.avatar_url = Asset('profilePicture', state=self._state, data=data)
        self.banner_url = Asset('profileBanner', state=self._state, data=data)

        self.moderation_status = data.get('moderationStatus')
        self.badges = data.get('badges', [])

    def __str__(self):
        return f'{self.name}#{self.id}'

    def __eq__(self, other):
        try:
            return self.id == other.id
        except:
            return False

    @property
    def slug(self):
        return self.subdomain

    @property
    def url(self):
        return self.subdomain

    @property
    def profile_url(self):
        return f'https://guilded.gg/profile/{self.id}'

    @property
    def vanity_url(self):
        if self.subdomain:
            return f'https://guilded.gg/{self.subdomain}'
        else:
            return None

    @property
    def mention(self):
        return f'<@{self.id}>'

class TeamChannel(Messageable):
    def __init__(self, *, state, group, data, **extra):
        super().__init__(state=state, data=data)
        #self._state = state
        self.group = group
        self.team = extra.get('team') or getattr(group, 'team', None)
        data = data.get('channel', data)

        #self.id = data.get('id')
        #self._channel_id = self.id
        self.name = data.get('name')
        self.position = data.get('priority')
        self.description = data.get('description')
        self.roles_synced = data.get('isRoleSynced')
        self.public = data.get('isPublic')
        self.settings = data.get('settings') # no clue

        self.created_at = ISO8601(data.get('createdAt'))
        self.updated_at = ISO8601(data.get('updatedAt'))
        self.added_at = ISO8601(data.get('addedAt')) # i have no idea what this means
        self.archived_at = ISO8601(data.get('archivedAt'))
        self.auto_archive_at = ISO8601(data.get('autoArchiveAt'))
        self.created_by = extra.get('created_by')
        self.archived_by = extra.get('archived_by')
        self.created_by = extra.get('created_by')
        self.created_by_webhook_id = data.get('createdByWebhookId')
        self.archived_by_webhook_id = data.get('archivedByWebhookId')

    @property
    def topic(self):
        return self.description

    def __str__(self):
        return self.name

    def __repr__(self):
        return f'<TeamChannel id={self.id} name={self.name} team={repr(self.team)}>'

    def __eq__(self, other):
        try:
            return self.id == other.id
        except:
            return False

    async def delete(self):
        return await self._state.delete_team_channel(self.team.id, self.group.id, self.id)
