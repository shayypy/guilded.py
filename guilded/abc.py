import abc

import guilded.user
from guilded.channel import Thread

from .activity import Activity
from .asset import Asset
from .embed import _EmptyEmbed, Embed
from .file import MediaType, FileType, File
from .message import Message
from .presence import Presence
from .utils import ISO8601


class Messageable(metaclass=abc.ABCMeta):
    def __init__(self, *, state, data):
        self._state = state
        self.id = data.get('id')
        self._channel_id = data.get('id')
        self.type = None

    async def send(self, *content, **kwargs):
        '''Send to a Guilded channel.'''
        content = list(content)
        if kwargs.get('file'):
            file = kwargs.get('file')
            file.set_media_type(MediaType.attachment)
            if file.url is None:
                await file._upload(self._state)
            content.append(file)
        for file in kwargs.get('files') or []:
            file.set_media_type(MediaType.attachment)
            if file.url is None:
                await file._upload(self._state)
            content.append(file)

        def embed_attachment_uri(embed):
            # pseudo-support attachment:// URI for use in embeds
            for slot in [('image', 'url'), ('thumbnail', 'url'), ('author', 'icon_url'), ('footer', 'icon_url')]:
                url = getattr(getattr(embed, slot[0]), slot[1])
                if isinstance(url, _EmptyEmbed):
                    continue
                if url.startswith('attachment://'):
                    filename = url.strip('attachment://')
                    for node in content:
                        if isinstance(node, File) and node.filename == filename:
                            getattr(embed, f'_{slot[0]}')[slot[1]] = node.url
                            content.remove(node)
                            break

            return embed

        # upload Files passed positionally
        for node in content:
            if isinstance(node, File) and node.url is None:
                node.set_media_type(MediaType.attachment)
                await node._upload(self._state)

        # handle attachment URIs for Embeds passed positionally
        # this is a separate loop to ensure that all files are uploaded first
        for node in content:
            if isinstance(node, Embed):
                content[content.index(node)] = embed_attachment_uri(node)

        if kwargs.get('embed'):
            content.append(embed_attachment_uri(kwargs.get('embed')))

        for embed in kwargs.get('embeds') or []:
            content.append(embed_attachment_uri(embed))

        response_coro, payload = self._state.send_message(self._channel_id, content)
        response = await response_coro
        payload['createdAt'] = response.pop('message', response or {}).pop('createdAt', None)
        payload['id'] = payload.pop('messageId')
        payload['channelId'] = self.id
        payload['teamId'] = self.team.id if self.team else None
        payload['createdBy'] = self._state.my_id

        if payload['teamId'] is not None:
            args = (payload['teamId'], payload['createdBy'])
            try:
                author = self._state._get_team_member(*args) or guilded.user.Member(state=self._state, data=await self._state.get_team_member(*args), team=self.team)
            except:
                author = None

        if author is None or payload['teamId'] is None:
            try:
                author = self._state._get_user(payload['createdBy']) or guilded.user.User(state=self._state, data=await self._state.get_user(payload['createdBy']))
            except:
                author = None

        return Message(state=self._state, channel=self, data=payload, author=author)

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
    def __init__(self, *, state, data, **extra):
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
        self.presence = Presence.from_value(data.get('userPresenceStatus', 5))
        status = data.get('userStatus', {})
        if status.get('content'):
            self.status = Activity.build(status['content'])
        else:
            self.status = None

        self.blocked_at = ISO8601(data.get('blockedDate'))
        self.online_at = ISO8601(data.get('lastOnline'))
        self.created_at = ISO8601(data.get('createdAt') or data.get('joinDate'))
        # in profilev3, createdAt is returned instead of joinDate

        self.avatar_url = Asset('profilePicture', state=self._state, data=data)
        self.banner_url = Asset('profileBanner', state=self._state, data=data)

        self.moderation_status = data.get('moderationStatus')
        self.badges = data.get('badges', [])

        self.bot = extra.get('bot', False)

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

    async def create_dm(self):
        dm = await self._state.create_dm(self.id)
        self._channel_id = dm._channel_id
        return Messageable(state=self._state, data=dm)

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

    #async def create_thread(self, name, *, message=None, initial_message: Message = None)
    #    return Thread(state=self._state, data=data)
