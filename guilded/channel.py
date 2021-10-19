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

import datetime
from enum import Enum
import re
from typing import Optional, Union, List

import guilded.abc

from .asset import Asset
from .embed import Embed
from .emoji import Emoji
from .file import Attachment, File, FileType, MediaType
#from .gateway import GuildedVoiceWebSocket
from .message import HasContentMixin, Message, Link
from .user import Member, User
from .utils import ISO8601, parse_hex_number
from .status import Game

__all__ = (
    'Announcement',
    'AnnouncementChannel',
    'AnnouncementReply',
    'ChannelType',
    'ChatChannel',
    'DMChannel',
    'Doc',
    'DocsChannel',
    'DocReply',
    'ForumChannel',
    'ForumReply',
    'ForumTopic',
    'Media',
    'MediaChannel',
    'MediaReply',
    'ListChannel',
    'ListItem',
    'ListItemNote',
    'Thread',
    'VoiceChannel'
)


class ChannelType(Enum):
    announcement = 'announcement'
    announcements = announcement
    chat = 'chat'
    doc = 'doc'
    docs = doc
    dm = 'DM'
    forum = 'forum'
    media = 'media'
    news = announcement
    list = 'list'
    scheduling = 'scheduling'
    streaming = 'streaming'
    text = chat
    thread = 'temporal'
    voice = 'voice'

    @classmethod
    def from_str(self, string):
        return getattr(self, string, None)


class ChatChannel(guilded.abc.TeamChannel, guilded.abc.Messageable):
    """Represents a chat channel in a team."""
    def __init__(self, **fields):
        super().__init__(**fields)
        self.type = ChannelType.chat
        self._channel_id = self.id


class Doc(HasContentMixin):
    """Represents a doc in a :class:`DocsChannel`.

    .. container:: operations

        .. describe:: x == y

            Checks if two docs are equal.

        .. describe:: x != y

            Checks if two docs are not equal.

        .. describe:: str(x)

            Returns the title of the doc.

    Attributes
    -----------
    id: :class:`int`
        The doc's ID.
    title: :class:`str`
        The doc's title.
    content: :class:`str`
        The doc's text content.
    channel: :class:`.DocsChannel`
        The channel that the doc is in.
    group: :class:`.Group`
        The group that the doc is in.
    team: :class:`.Team`
        The team that the doc is in.
    public: :class:`bool`
        Whether the doc is public.
    draft: :class:`bool`
        Whether the doc is a draft.
    created_at: :class:`datetime.datetime`
        When the doc was created.
    edited_at: Optional[:class:`datetime.datetime`]
        When the doc was last modified.
    game: Optional[:class:`.Game`]
        The game associated with the doc.
    """
    def __init__(self, *, state, data, channel, game=None):
        super().__init__()
        self._state = state
        self.channel = channel
        self.group = channel.group
        self.team = channel.team
        self.game: Optional[Game] = game or (Game(game_id=data.get('gameId')) if data.get('gameId') else None)
        self.tags: str = data.get('tags')
        self._replies = {}

        self.public: bool = data.get('isPublic', False)
        self.credentialed: bool = data.get('isCredentialed', False)
        self.draft: bool = data.get('isDraft', False)

        self.author_id: str = data.get('createdBy')
        self.edited_by_id: Optional[str] = data.get('modifiedBy')

        self.created_at: datetime.datetime = ISO8601(data.get('createdAt'))
        self.edited_at: Optional[datetime.datetime] = ISO8601(data.get('modifiedAt'))

        self.id: int = int(data['id'])
        self.title: str = data['title']
        self.content: str = self._get_full_content(data['content'])

    def __repr__(self):
        return f'<Doc id={self.id!r} title={self.title!r} author={self.author!r} channel={self.channel!r}>'

    def __eq__(self, other):
        return isinstance(other, Doc) and other.id == self.id

    def __str__(self):
        return self.title

    @property
    def replies(self):
        """List[:class:`.DocReply`]: The list of cached replies to this doc."""
        return list(self._replies.values())

    @property
    def author(self) -> Optional[Member]:
        """Optional[:class:`.Member`]: The :class:`.Member` that created the
        doc, if they are cached.
        """
        return self.team.get_member(self.author_id)

    @property
    def edited_by(self) -> Optional[Member]:
        """Optional[:class:`.Member`]: The :class:`.Member` that last edited the
        doc, if they are cached.
        """
        return self.team.get_member(self.author_id)

    async def add_reaction(self, emoji):
        """|coro|

        Add a reaction to this doc.

        Parameters
        -----------
        emoji: :class:`.Emoji`
            The emoji to add.
        """
        await self._state.add_content_reaction('doc', self.id, emoji.id)

    async def remove_self_reaction(self, emoji):
        """|coro|

        Remove your reaction from this doc.

        Parameters
        -----------
        emoji: :class:`.Emoji`
            The emoji to remove.
        """
        await self._state.remove_self_content_reaction('doc', self.id, emoji.id)

    async def delete(self):
        """|coro|

        Delete this doc.
        """
        await self._state.delete_doc(self.channel.id, self.id)

    async def reply(self, *content, **kwargs):
        """|coro|

        Reply to this doc.

        Parameters
        ------------
        content: Any
            The content to create the reply with.
        reply_to: Optional[:class:`.DocReply`]
            An existing reply to reply to.

        Returns
        --------
        :class:`.DocReply`
            The created reply.
        """
        data = await self._state.create_content_reply('doc', self.team.id, self.id, content=content, reply_to=kwargs.get('reply_to'))
        reply = DocReply(data=data['reply'], parent=self, state=self._state)
        return reply

    def get_reply(self, id: int):
        """Optional[:class:`.DocReply`]: Get a reply by its ID."""
        return self._replies.get(id)

    async def fetch_reply(self, id: int):
        """|coro|

        Fetch a reply to this doc.

        Parameters
        -----------
        id: :class:`int`
            The ID of the reply.

        Returns
        --------
        :class:`.DocReply`
        """
        data = await self._state.get_content_reply('docs', self.channel.id, self.id, id)
        reply = DocReply(data=data['metadata']['reply'], parent=self, state=self._state)
        return reply

    async def move(self, to):
        """|coro|

        Move this doc to another :class:`.DocsChannel`.

        Parameters
        -----------
        to: :class:`.DocsChannel`
            The channel to move this doc to.
        """
        await self._state.move_doc(self.channel.id, self.id, to.id)


class DocsChannel(guilded.abc.TeamChannel):
    """Represents a docs channel in a team."""
    def __init__(self, **fields):
        super().__init__(**fields)
        self.type = ChannelType.docs
        self._docs = {}

    @property
    def docs(self):
        """List[:class:`.Doc`]: The list of cached docs in this channel."""
        return list(self._docs.values())

    def get_doc(self, id: int):
        """Optional[:class:`.Doc`]: Get a cached doc in this channel."""
        return self._docs.get(id)

    async def getch_doc(self, id: int):
        return self.get_doc(id) or await self.fetch_doc(id)

    async def create_doc(self, *content, **kwargs):
        """|coro|

        Create a new doc in this channel.

        Parameters
        -----------
        content: Any
            The content to create the doc with.
        title: :class:`str`
            The doc's title.
        game: Optional[:class:`.Game`]
            The game associated with the doc.
        draft: Optional[:class:`bool`]
            Whether the doc should be a draft.

        Returns
        --------
        :class:`.Doc`
            The created doc.
        """
        title = kwargs.pop('title')
        game = kwargs.pop('game', None)
        draft = kwargs.pop('draft', False)

        data = await self._state.create_doc(
            self.id,
            title=title,
            content=content,
            game_id=(game.id if game else None),
            draft=draft
        )
        doc = Doc(data=data, channel=self, game=game, state=self._state)
        return doc

    async def fetch_doc(self, id: int) -> Doc:
        """|coro|

        Fetch an doc in this channel.

        Parameters
        -----------
        id: :class:`int`
            The doc's ID.

        Returns
        --------
        :class:`.Doc`
        """
        data = await self._state.get_doc(self.id, id)
        doc = Doc(data=data, channel=self, state=self._state)
        return doc

    async def fetch_docs(self, *, limit: int = 50, before: datetime.datetime = None) -> List[Doc]:
        """|coro|

        Fetch multiple docs in this channel.

        All parameters are optional.

        Parameters
        -----------
        limit: :class:`int`
            The maximum number of docs to return. Defaults to 50.
        before: :class:`datetime.datetime`
            The latest date that an doc can be from. Defaults to the
            current time.

        Returns
        --------
        List[:class:`.Doc`]
        """
        before = before or datetime.datetime.now(datetime.timezone.utc)
        data = await self._state.get_docs(self.id, limit=limit, before=before)
        docs = []
        for doc_data in data:
            docs.append(Doc(data=doc_data, channel=self, state=self._state))

        return docs


class ForumTopic(HasContentMixin):
    """Represents a forum topic.

    Attributes
    -----------
    id: :class:`int`
        The topic's ID.
    title: :class:`str`
        The topic's title.
    content: :class:`str`
        The topic's content.
    team: :class:`.Team`
        The team that the topic is in.
    channel: :class:`.ForumChannel`
        The forum channel that the topic is in.
    created_at: :class:`datetime.datetime`
        When the topic was created.
    bumped_at: :class:`datetime.datetime`
        When the topic was last bumped. This may be the same as
        :attr:`.created_at`.
    edited_at: Optional[:class:`datetime.datetime`]
        When the topic was last edited.
    stickied: :class:`bool`
        Whether the topic is stickied (pinned) in its channel.
    locked: :class:`bool`
        Whether the topic is locked.
    deleted: :class:`bool`
        Whether the topic is deleted.
    deleted_by: Optional[:class:`.Member`]
        Who deleted this topic. This will only be present through
        :meth:`on_forum_topic_delete`.
    reply_count: :class:`int`
        How many replies the topic has.
    """
    def __init__(self, *, state, data, channel):
        super().__init__()
        self._state = state
        self.channel = channel
        self.group = channel.group
        self.team = channel.team

        self.channel_id = data.get('channelId') or self.channel.id
        self.team_id = data.get('teamId') or (self.team.id if self.team else None)
        self.group_id = data.get('groupId') or (self.group.id if self.group else None)

        self.id: int = data['id']
        self.title: str = data['title']
        self.content: str = self._get_full_content(data['message'])

        self.author_id: str = data.get('createdBy')
        self.game_id: Optional[int] = data.get('gameId')
        self.created_by_bot_id: Optional[int] = data.get('createdByBotId')
        self.created_at: datetime.datetime = ISO8601(data.get('createdAt'))
        self.edited_at: Optional[datetime.datetime] = ISO8601(data.get('editedAt'))
        self.bumped_at: Optional[datetime.datetime] = ISO8601(data.get('bumpedAt'))
        self.visibility: str = data.get('visibility')
        self.stickied: bool = data.get('isSticky')
        self.locked: bool = data.get('isLocked')
        self.shared: bool = data.get('isShare')
        self.deleted: bool = data.get('isDeleted')
        self.deleted_by: Optional[Member] = None
        self.reply_count: int = int(data.get('replyCount', 0))
        self._replies = {}

    def __str__(self):
        return self.title

    def __repr__(self):
        return f'<ForumTopic id={self.id!r} title={self.title!r} forum={self.forum!r}>'

    @property
    def game(self) -> Game:
        """Optional[:class:`.Game`]: The game that the topic is for."""
        return Game(game_id=self.game_id)

    @property
    def author(self) -> Optional[Member]:
        """Optional[:class:`.Member`]: The :class:`.Member` that created the
        topic, if they are cached.
        """
        return self.team.get_member(self.author_id)

    @property
    def replies(self):
        return list(self._replies.values())

    def get_reply(self, id):
        """Optional[:class:`.ForumReply`]: Get a reply by its ID."""
        return self._replies.get(id)

    async def fetch_replies(self, *, limit=50):
        """|coro|

        Fetch the replies to this topic.

        Returns
        --------
        List[:class:`.ForumReply`]
        """
        replies = []
        data = await self._state.get_forum_topic_replies(self.channel.id, self.id, limit=limit)
        for reply_data in data.get('threadReplies', data) or []:
            reply = ForumReply(data=reply_data, forum=self.forum, state=self._state)
            replies.append(reply)

        return replies

    async def fetch_reply(self, id: int):
        """|coro|

        Fetch a reply to this topic.

        Returns
        --------
        :class:`.ForumReply`
        """
        data = await self._state.get_content_reply('forums', self.channel.id, self.id, id)
        reply = ForumReply(data=data['metadata']['reply'], forum=self.forum, state=self._state)
        return reply

    async def reply(self, *content, **kwargs) -> int:
        """|coro|

        Create a new reply to this topic.

        Parameters
        ------------
        content: Any
            The content to create the reply with.
        reply_to: Optional[:class:`.ForumReply`]
            An existing reply to reply to.

        Returns
        --------
        :class:`int`
            The ID of the created reply.

            .. note::
                Guilded does not return the full object in response to this.
                Nevertheless, if you are connected to the gateway, it should
                end up getting cached and accessible via :meth:`.get_reply`.
        """
        data = await self._state.create_forum_topic_reply(self.channel.id, self.id, content=content, reply_to=kwargs.get('reply_to'))
        return data['replyId']

    async def delete(self):
        """|coro|

        Delete this topic.
        """
        await self._state.delete_forum_topic(self.channel.id, self.id)

    async def move(self, to):
        """|coro|

        Move this topic to another :class:`.ForumChannel`.

        Parameters
        -----------
        to: :class:`.ForumChannel`
            The forum to move this topic to.
        """
        await self._state.move_forum_topic(self.channel.id, self.id, to.id)

    async def lock(self):
        """|coro|

        Lock this topic.
        """
        await self._state.lock_forum_topic(self.channel.id, self.id)

    async def unlock(self):
        """|coro|

        Unlock this topic.
        """
        await self._state.unlock_forum_topic(self.channel.id, self.id)

    async def sticky(self):
        """|coro|

        Sticky (pin) this topic.
        """
        await self._state.sticky_forum_topic(self.channel.id, self.id)

    async def unsticky(self):
        """|coro|

        Unsticky (unpin) this topic.
        """
        await self._state.unsticky_forum_topic(self.channel.id, self.id)

    async def pin(self):
        """|coro|

        Pin (sticky) this topic. This is an alias of :meth:`.sticky`.
        """
        return await self.sticky()

    async def unpin(self):
        """|coro|

        Unpin (unsticky) this topic. This is an alias of :meth:`.sticky`.
        """
        return await self.unsticky()


class ForumChannel(guilded.abc.TeamChannel):
    """Represents a forum channel in a team."""
    def __init__(self, **fields):
        super().__init__(**fields)
        self.type = ChannelType.forum
        self._topics = {}

    @property
    def topics(self):
        return list(self._topics.values())

    def get_topic(self, id) -> Optional[ForumTopic]:
        """Optional[:class:`.ForumTopic`]: Get a topic by its ID."""
        return self._topics.get(id)

    async def create_topic(self, *content, **kwargs) -> ForumTopic:
        """|coro|

        Create a new topic in this forum.

        Parameters
        ------------
        content: Any
            The content to create the topic with.
        title: :class:`str`
            The title to create the topic with.

        Returns
        --------
        :class:`.ForumTopic`
            The topic that was created.
        """
        title = kwargs['title']
        data = await self._state.create_forum_topic(self.id, title=title, content=content)
        topic = ForumTopic(data=data, channel=self, state=self._state)
        return topic

    async def fetch_topic(self, id: int) -> ForumTopic:
        """|coro|

        Fetch a topic from this forum.

        Parameters
        -----------
        id: :class:`int`
            The topic's ID.

        Returns
        --------
        :class:`.ForumTopic`
            The topic by its ID.
        """
        data = await self._state.get_forum_topic(self.id, id)
        topic = ForumTopic(data=data.get('thread', data), channel=self, state=self._state)
        return topic

    async def getch_topic(self, id: int) -> ForumTopic:
        return self.get_topic(id) or await self.fetch_topic(id)

    async def fetch_topics(self, *, limit: int = 50, page: int = 1, before: datetime.datetime = None) -> List[ForumTopic]:
        """|coro|

        Fetch the topics in this forum.

        All parameters are optional.

        Parameters
        -----------
        limit: :class:`int`
            The maximum number of topics to return. Defaults to 50.
        before: :class:`datetime.datetime`
            The latest date that a topic can be from. Defaults to the current
            time.

        Returns
        --------
        List[:class:`.ForumTopic`]
            The topics in this forum.
        """
        before = before or datetime.datetime.now(datetime.timezone.utc)
        data = await self._state.get_forum_topics(self.id, limit=limit, page=page, before=before)
        topics = []
        for topic_data in data.get('threads', data):
            topic = ForumTopic(data=topic_data, channel=self, state=self._state)

        return topics


class VoiceChannel(guilded.abc.TeamChannel, guilded.abc.Messageable):
    """Represents a voice channel in a team."""
    def __init__(self, **fields):
        super().__init__(**fields)
        self.type = ChannelType.voice
        self._channel_id = self.id
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

    async def hide(self):
        """|coro|

        Visually hide this DM channel in the client.

        The channel's content will still exist, and the channel can be
        re-fetched with :meth:`User.create_dm` on whichever :class:`User` this
        channel is associated with.
        """
        await self._state.hide_dm_channel(self.id)


class Announcement(HasContentMixin):
    """Represents an announcement in an :class:`AnnouncementChannel`.

    Attributes
    -----------
    id: :class:`str`
        The announcement's ID.
    title: :class:`str`
        The announcement's title.
    content: :class:`str`
        The announcement's text content.
    channel: :class:`.AnnouncementChannel`
        The channel that the announcement is in.
    group: :class:`.Group`
        The group that the announcement is in.
    team: :class:`.Team`
        The team that the announcement is in.
    public: :class:`bool`
        Whether the announcement is public.
    pinned: :class:`bool`
        Whether the announcement is pinned.
    created_at: :class:`datetime.datetime`
        When the announcement was created.
    edited_at: Optional[:class:`datetime.datetime`]
        When the announcement was last edited.
    slug: Optional[:class:`str`]
        The announcement's URL slug.
    game: Optional[:class:`.Game`]
        The game associated with the announcement.
    """
    def __init__(self, *, state, data, channel, game=None):
        super().__init__()
        self._state = state
        self.channel = channel
        self.group = channel.group
        self.team = channel.team
        self.game: Optional[Game] = game or (Game(game_id=data.get('gameId')) if data.get('gameId') else None)
        self.tags: str = data.get('tags')
        self._replies = {}

        for reply_data in data.get('replies', []):
            reply = AnnouncementReply(data=reply_data, parent=self, state=self._state)
            self._replies[reply.id] = reply

        self.public: bool = data.get('isPublic', False)
        self.pinned: bool = data.get('isPinned', False)
        self.slug: Optional[str] = data.get('slug')

        self.author_id: str = data.get('createdBy')
        self.created_at: datetime.datetime = ISO8601(data.get('createdAt'))
        self.edited_at: Optional[datetime.datetime] = ISO8601(data.get('editedAt'))

        self.id: str = data['id']
        self.title: str = data['title']
        self.content: str = self._get_full_content(data['content'])

    def __repr__(self):
        return f'<Announcement id={self.id!r} title={self.title!r} author={self.author!r}>'

    @property
    def author(self) -> Optional[Member]:
        """Optional[:class:`.Member`]: The :class:`.Member` that created the
        topic, if they are cached.
        """
        return self.team.get_member(self.author_id)

    @property
    def blog_url(self) -> Optional[str]:
        if self.channel.vanity_url and self.slug:
            return f'{self.channel.vanity_url}/{self.slug}'
        return None

    @property
    def share_url(self) -> str:
        if self.channel:
            return f'{self.channel.share_url}/{self.id}'
        return None

    @property
    def replies(self):
        return list(self._replies.values())

    def get_reply(self, id):
        """Optional[:class:`.AnnouncementReply`]: Get a reply by its ID."""
        return self._replies.get(id)

    async def sticky(self):
        """|coro|

        Sticky (pin) this announcement.
        """
        await self._state.toggle_announcement_pin(self.channel.id, self.id, pinned=True)
        self.pinned = True

    async def unsticky(self):
        """|coro|

        Unsticky (unpin) this announcement.
        """
        await self._state.toggle_announcement_pin(self.channel.id, self.id, pinned=False)
        self.pinned = False

    async def pin(self):
        """|coro|

        Pin (sticky) this announcement. This is an alias of :meth:`.sticky`.
        """
        return await self.sticky()

    async def unpin(self):
        """|coro|

        Unpin (unsticky) this announcement. This is an alias of :meth:`.sticky`.
        """
        return await self.unsticky()

    async def delete(self):
        """|coro|

        Delete this announcement.
        """
        await self._state.delete_announcement(self.channel.id, self.id)

    async def add_reaction(self, emoji):
        """|coro|

        Add a reaction to this announcement.

        Parameters
        -----------
        emoji: :class:`.Emoji`
            The emoji to add.
        """
        await self._state.add_content_reaction(self.channel.type.value, self.id, emoji.id)

    async def remove_self_reaction(self, emoji):
        """|coro|

        Remove your reaction from this announcement.

        Parameters
        -----------
        emoji: :class:`.Emoji`
            The emoji to remove.
        """
        await self._state.remove_self_content_reaction(self.channel.type.value, self.id, emoji.id)

    async def fetch_reply(self, id: int):
        """|coro|

        Fetch a reply to this announcement.

        Parameters
        -----------
        id: :class:`int`
            The ID of the reply.

        Returns
        --------
        :class:`.AnnouncementReply`
        """
        data = await self._state.get_content_reply('announcements', self.channel.id, self.id, id)
        reply = AnnouncementReply(data=data['metadata']['reply'], parent=self, state=self._state)
        return reply

    async def reply(self, *content, **kwargs):
        """|coro|

        Reply to this announcement.

        Parameters
        ------------
        content: Any
            The content to create the reply with.
        reply_to: Optional[:class:`.AnnouncementReply`]
            An existing reply to reply to.

        Returns
        --------
        :class:`.AnnouncementReply`
            The created reply.
        """
        data = await self._state.create_content_reply(self.channel.type.value, self.team.id, self.id, content=content, reply_to=kwargs.get('reply_to'))
        reply = AnnouncementReply(data=data['reply'], parent=self, state=self._state)
        return reply


class AnnouncementChannel(guilded.abc.TeamChannel):
    """Represents an announcements channel in a team"""
    def __init__(self, **fields):
        super().__init__(**fields)
        self.type = ChannelType.announcements
        self._announcements = {}

    @property
    def announcements(self) -> List[Announcement]:
        """List[:class:`.Announcement`]: The list of cached announcements in this channel."""
        return list(self._announcements.values())

    def get_announcement(self, id) -> Optional[Announcement]:
        """Optional[:class:`.Announcement`]: Get a cached announcement in this channel."""
        return self._announcements.get(id)

    async def getch_announcement(self, id: str) -> Announcement:
        return self.get_announcement(id) or await self.fetch_announcement(id)

    async def fetch_announcement(self, id: str) -> Announcement:
        """|coro|

        Fetch an announcement in this channel.

        Parameters
        -----------
        id: :class:`str`
            The announcement's ID.

        Returns
        --------
        :class:`.Announcement`
        """
        data = await self._state.get_announcement(self.id, id)
        announcement = Announcement(data=data['announcement'], channel=self, state=self._state)
        return announcement

    async def fetch_announcements(self, *, limit: int = 50, before: datetime.datetime = None) -> List[Announcement]:
        """|coro|

        Fetch multiple announcements in this channel.

        All parameters are optional.

        Parameters
        -----------
        limit: :class:`int`
            The maximum number of announcements to return. Defaults to 50.
        before: :class:`datetime.datetime`
            The latest date that an announcement can be from. Defaults to the
            current time.

        Returns
        --------
        List[:class:`.Announcement`]
        """
        before = before or datetime.datetime.now(datetime.timezone.utc)
        data = await self._state.get_announcements(self.id, limit=limit, before=before)
        announcements = []
        for announcement_data in data['announcements']:
            announcements.append(Announcement(data=announcement_data, channel=self, state=self._state))

        return announcements

    async def fetch_pinned_announcements(self) -> List[Announcement]:
        """|coro|

        Fetch all pinned announcements in this channel.

        Returns
        --------
        List[:class:`.Announcement`]
        """
        data = await self._state.get_pinned_announcements(self.id)
        announcements = []
        for announcement_data in data['announcements']:
            announcements.append(Announcement(data=announcement_data, channel=self, state=self._state))

        return announcements

    async def create_announcement(self, *content, **kwargs) -> Announcement:
        """|coro|

        Create an announcement in this channel.

        Parameters
        -----------
        content: Any
            The content of the announcement.
        title: :class:`str`
            The title of the announcement.
        game: Optional[:class:`.Game`]
            The game to be associated with this announcement.
        send_notifications: Optional[:class:`bool`]
            Whether to send notifications to all members ("Notify all
            members" in the client). Defaults to ``True`` if not specified.

        Returns
        --------
        :class:`.Announcement`
            The created announcement.
        """
        title = kwargs.pop('title')
        game = kwargs.pop('game', None)
        dont_send_notifications = not kwargs.pop('send_notifications', True)

        data = await self._state.create_announcement(
            self.id,
            title=title,
            content=content,
            game_id=(game.id if game else None),
            dont_send_notifications=dont_send_notifications
        )
        announcement = Announcement(data=data['announcement'], channel=self, game=game, state=self._state)
        return announcement


class Media(HasContentMixin):
    """Represents a media post in a :class:`.MediaChannel`.

    .. container:: operations

        .. describe:: x == y

            Checks if two medias are equal.

        .. describe:: x != y

            Checks if two medias are not equal.

        .. describe:: str(x)

            Returns the URL of the media.

        .. describe:: len(x)

            Returns the length of the media's URL.

    Attributes
    -----------
    id: :class:`int`
        The media's ID.
    title: :class:`str`
        The media's title.
    description: :class:`str`
        The media's description.
    url: :class:`str`
        The media's URL on Guilded's CDN.
    thumbnail: Optional[:class:`.Asset`]
        An asset for the media's thumbnail.
    channel: :class:`.MediaChannel`
        The channel that the media is in.
    group: :class:`.Group`
        The group that the media is in.
    team: :class:`.Team`
        The team that the media is in.
    public: :class:`bool`
        Whether the media is public.
    created_at: :class:`datetime.datetime`
        When the media was created.
    reply_count: :class:`int`
        How many replies the media has.
    game: Optional[:class:`.Game`]
        The game associated with the media.
    """
    def __init__(self, *, state, data, channel, game=None):
        super().__init__()
        self._state = state
        self.type = getattr(FileType, (data.get('type', 'image')), None)
        self.channel = channel
        self.group = channel.group
        self.team = channel.team
        self.game: Optional[Game] = game or (Game(game_id=data.get('gameId')) if data.get('gameId') else None)
        self.tags: List[str] = list(data.get('tags') or [])  # sometimes an empty string is present instead of a list
        self._replies = {}

        self.public: bool = data.get('isPublic', False)
        self.url: str = data.get('src')
        if data.get('srcThumbnail'):
            self.thumbnail: Optional[Asset] = Asset('mediaThumbnail', state=self._state, data={'mediaThumbnail': data['srcThumbnail']})
        else:
            self.thumbnail: Optional[Asset] = None

        self.author_id: str = data.get('createdBy')
        self.created_at: datetime.datetime = ISO8601(data.get('createdAt'))

        self.id: int = int(data['id'])
        self.title: str = data['title']
        self.description: str = data.get('description', '')

        self.reply_count: int = int(data.get('replyCount', 0))

        if data.get('additionalInfo', {}).get('externalVideoSrc'):
            self.youtube_embed_url = data['additionalInfo']['externalVideoSrc']
            self.youtube_video_id = re.sub(r'^https?:\/\/(www\.)youtube\.com\/embed\/', '', self.youtube_embed_url)

    def __repr__(self):
        return f'<Media id={self.id!r} title={self.title!r} author={self.author!r}>'

    def __str__(self):
        return self.url

    def __len__(self):
        return len(str(self))

    def __eq__(self, other):
        return isinstance(other, Media) and self.id == other.id and self.url == other.url

    async def add_reaction(self, emoji):
        """|coro|

        Add a reaction to this media post.

        Parameters
        -----------
        emoji: :class:`.Emoji`
            The emoji to add.
        """
        await self._state.add_content_reaction(self.channel.content_type, self.id, emoji.id)

    async def remove_self_reaction(self, emoji):
        """|coro|

        Remove your reaction from this media post.

        Parameters
        -----------
        emoji: :class:`.Emoji`
            The emoji to remove.
        """
        await self._state.remove_self_content_reaction(self.channel.content_type, self.id, emoji.id)

    async def reply(self, *content, **kwargs):
        """|coro|

        Reply to this media.

        Parameters
        ------------
        content: Any
            The content to create the reply with.
        reply_to: Optional[:class:`.MediaReply`]
            An existing reply to reply to.

        Returns
        --------
        :class:`.MediaReply`
            The created reply.
        """
        data = await self._state.create_content_reply(self.channel.content_type, self.team.id, self.id, content=content, reply_to=kwargs.get('reply_to'))
        reply = MediaReply(data=data['reply'], parent=self, state=self._state)
        return reply

    def get_reply(self, id: int):
        """Optional[:class:`.MediaReply`]: Get a reply by its ID."""
        return self._replies.get(id)

    async def fetch_reply(self, id: int):
        """|coro|

        Fetch a reply to this media.

        Parameters
        -----------
        id: :class:`int`
            The ID of the reply.

        Returns
        --------
        :class:`.MediaReply`
        """
        data = await self._state.get_content_reply(self.channel.type.value, self.channel.id, self.id, id)
        # metadata uses 'media' and not 'team_media'
        reply = MediaReply(data=data['metadata']['reply'], parent=self, state=self._state)
        return reply

    async def move(self, id: int):
        """|coro|

        Move this media post to another :class:`.DocsChannel`.

        Parameters
        -----------
        to: :class:`.DocsChannel`
            The media channel to move this topic to.
        """
        await self._state.move_media(self.channel.id, self.id, to.id)

    async def delete(self):
        """|coro|

        Delete this media post.
        """
        return await self._state.delete_media(self.id)

    async def read(self):
        """|coro|

        Fetches the raw data of this media as a :class:`bytes`.

        Returns
        --------
        :class:`bytes`
            The raw data of this media.
        """
        return await self._state.read_filelike_data(self)


class ListItemNote(HasContentMixin):
    """Represents the note on a :class:`.ListItem`.

    .. note::
        Item notes are not their own resource in the API, thus they have no ID
        or dedicated endpoints. Methods on an instance of this class are
        shortcuts to the parent rather than being unique to a "List Item Note"
        model.

    Attributes
    -----------
    parent: :class:`.ListItem`
        The note's parent item.
    content: :class:`str`
        The note's content.
    """
    def __init__(self, *, data, parent):
        super().__init__()
        self.parent = parent
        self.content = self._get_full_content(data)

    def __repr__(self):
        return f'<ListItemNote parent={self.parent!r} author={self.author!r}>'

    @property
    def author(self) -> Optional[Member]:
        """Optional[:class:`.Member`]: The :class:`.Member` that created the
        note, if they are cached.
        """
        return self.parent.team.get_member(self.parent.note_author_id)

    @property
    def edited_by(self) -> Optional[Member]:
        """Optional[:class:`.Member`]: The :class:`.Member` that last edited
        the note, if they are cached.
        """
        return self.parent.team.get_member(self.parent.note_edited_by_id)

    async def delete(self):
        """|coro|

        Delete this note.
        """
        return await self.parent.edit(note=None)

    async def edit(self, *content):
        """|coro|

        Edit this note.

        Parameters
        -----------
        content: Any
            The new content of the note.
        """
        return await self.parent.edit(note=content)


class ListItem(HasContentMixin):
    """Represents an item in a :class:`ListChannel`.

    Attributes
    -----------
    id: :class:`str`
        The item's ID.
    channel: :class:`.ListChannel`
        The channel that the item is in.
    group: :class:`.Group`
        The group that the item is in.
    team: :class:`.Team`
        The team that the item is in.
    created_at: :class:`datetime.datetime`
        When the item was created.
    message: :class:`str`
        The main message of the item.
    position: :class:`int`
        Where the item is in its :attr:`.channel`. A value of ``0`` is
        at the bottom of the list visually.
    has_note: :class:`bool`
        Whether the item has a note.
    note: Optional[:class:`ListItemNote`]
        The note of an item. If this instance was not obtained via creation,
        then this attribute must first be fetched with :meth:`.fetch_note`.
    note_created_by_bot_id: Optional[:class:`int`]
        The ID of the bot that created the item's note, if any.
    note_created_at: Optional[:class:`datetime.datetime`]
        When the item's note was created.
    note_edited_at: Optional[:class:`datetime.datetime`]
        When the note was last edited.
    updated_at: Optional[:class:`datetime.datetime`]
        When the item was last updated.
    completed_at: Optional[:class:`datetime.datetime`]
        When the item was marked as completed.
    deleted_at: Optional[:class:`datetime.datetime`]
        When the item was deleted.
    """
    def __init__(self, *, state, data, channel):
        super().__init__()
        self._state = state
        self.channel = channel
        self.group = channel.group
        self.team = channel.team

        self.parent_id: Optional[str] = data.get('parentId')
        self.team_id: str = data.get('teamId')
        self.webhook_id: Optional[str] = data.get('webhookId')
        self.bot_id: Optional[int] = data.get('botId')

        self.author_id: str = data.get('createdBy')
        self.created_at: datetime.datetime = ISO8601(data.get('createdAt'))
        self.updated_by_id: Optional[str] = data.get('updatedBy')
        self.updated_at: Optional[datetime.datetime] = ISO8601(data.get('updatedAt'))
        self.completed_by_id: Optional[str] = data.get('completedBy')
        self.completed_at: Optional[datetime.datetime] = ISO8601(data.get('completedAt'))
        self.deleted_by_id: Optional[str] = data.get('deletedBy')
        self.deleted_at: Optional[datetime.datetime] = ISO8601(data.get('deletedAt'))
        self._assigned_to = data.get('assignedTo') or []

        self.id: str = data['id']
        self.position: int = data.get('priority')

        self._raw_message = data['message']
        self.message: str = self._get_full_content(self._raw_message)

        self.has_note: bool = data.get('hasNote', False)
        self.note_author_id: Optional[str] = data.get('noteCreatedBy')
        self.note_created_by_bot_id: Optional[int] = data.get('noteCreatedByBotId')
        self.note_created_at: Optional[datetime.datetime] = ISO8601(data.get('noteCreatedAt'))
        self.note_edited_by_id: Optional[str] = data.get('noteUpdatedBy')
        self.note_edited_at: Optional[datetime.datetime] = ISO8601(data.get('noteUpdatedAt'))
        self._raw_note = data.get('note')
        if self._raw_note:
            self.note: Optional[ListItemNote] = ListItemNote(data=self._raw_note, parent=self)
        else:
            self.note: Optional[ListItemNote] = None

    def __repr__(self):
        return f'<ListItem id={self.id!r} author={self.author!r} has_note={self.has_note!r}>'

    @property
    def author(self) -> Optional[Member]:
        """Optional[:class:`.Member`]: The :class:`.Member` that created the
        item, if they are cached.
        """
        return self.team.get_member(self.author_id)

    @property
    def share_url(self) -> str:
        if self.channel:
            return f'{self.channel.share_url}/{self.id}'
        return None

    @property
    def replies(self):
        return list(self._replies.values())

    def get_reply(self, id):
        """Optional[:class:`.MediaReply`]: Get a reply by its ID."""
        return self._replies.get(id)

    def deleted_by(self) -> Optional[Member]:
        """Optional[:class:`.Member`]: The :class:`.Member` that deleted the
        item, if that information is available and they are cached.
        """
        return self.team.get_member(self.deleted_by_id)

    @property
    def updated_by(self) -> Optional[Member]:
        """Optional[:class:`.Member`]: The :class:`.Member` that last updated
        the item, if they are cached.
        """
        return self.team.get_member(self.updated_by_id)

    @property
    def completed_by(self) -> Optional[Member]:
        """Optional[:class:`.Member`]: The :class:`.Member` that marked the
        the item as completed, if applicable and they are cached.
        """
        return self.team.get_member(self.completed_by_id)

    @property
    def share_url(self) -> Optional[str]:
        return f'{self.channel.share_url}?listItemId={self.id}'

    @property
    def assigned_to(self) -> List[Member]:
        """List[:class:`.Member`]: The members that the item is assigned to,
        designated by mentions in :attr:`message`.
        """
        members = []
        for assigned in self._assigned_to:
            id_ = assigned.get('mentionId')
            if assigned.get('mentionType') == 'person':
                members.append(self.team.get_member(id_))

            # TODO: get members of role if mentionType == role

        return members

    @property
    def parent(self):
        """Optional[:class:`.ListItem`]: The item that this item is a child of,
        if it exists and is cached.
        """
        return self.channel.get_item(self.parent_id)

    async def fetch_parent(self):
        """|coro|
        
        Fetch the item that this item is a child of, if it exists.

        Returns
        --------
        :class:`.ListItem`
        """
        return await self.channel.fetch_item(self.parent_id)

    async def fetch_note(self) -> ListItemNote:
        """|coro|

        Fetch this item's note. This should only be necessary if you obtained
        this object through :meth:`ListChannel.fetch_items`.

        Returns
        --------
        :class:`.ListItemNote`
        """
        item = await self.channel.fetch_item(self.id)
        self.note = item.note
        return self.note

    async def delete(self):
        """|coro|

        Delete this item.
        """
        await self._state.delete_list_item(self.channel.id, self.id)

    async def edit(self, **kwargs):
        """|coro|

        Edit this item.

        All parameters are optional.

        .. note::
            If ``position`` and ``message`` or ``note`` are specified, this
            method will make multiple API requests.

        Parameters
        -----------
        message: Any
            The new main content of the item.
        note: Any
            The new note of the item.
        position: :class:`int`
            The new position of the item. A value of ``0`` appears at the
            bottom visually.
        """
        message_payload = {}
        try:
            message = kwargs.pop('message')
        except KeyError:
            pass
        else:
            message_payload['message'] = self._state.compatible_content(message)
        try:
            note = kwargs.pop('note')
        except KeyError:
            pass
        else:
            message_payload['note'] = self._state.compatible_content(note)

        if message_payload:
            await self._state.edit_list_item_message(self.channel.id, self.id, message_payload)

        if kwargs.get('position') is not None:
            position = kwargs['position']
            if not isinstance(position, int):
                raise TypeError(f'position must be type int, not {position.__class__.__name__}')

            rich_positions = []
            all_items = await self.channel.fetch_items()
            for item in all_items:
                rich_positions.append(item)

            rich_positions.sort(key=lambda item: item.position)
            rich_positions.insert(position, self)

            positions = [item.id for item in rich_positions]
            await self._state.edit_list_item_priority(self.channel.id, positions)
            self.position = position

    async def create_item(self, *message, **kwargs):
        """|coro|

        Create an item with this item as its parent.

        This method is identical to :meth:`ListChannel.create_item`.
        """
        kwargs['parent'] = self
        return await self.channel.create_item(*message, **kwargs)

    async def move(self, to):
        """|coro|

        Move this item to another channel.

        .. bug::
            Guilded will raise a 500 upon calling this method.

        Parameters
        -----------
        to: :class:`.ListChannel`
            The list channel to move this item to.
        """
        await self._state.move_list_item(self.channel.id, self.id, to.id)

    async def complete(self):
        raise NotImplementedError

    async def uncomplete(self):
        raise NotImplementedError


class MediaChannel(guilded.abc.TeamChannel):
    """Represents a media channel in a team."""
    def __init__(self, **fields):
        super().__init__(**fields)
        self.type = ChannelType.media
        self.content_type = 'team_media'
        self._medias = {}

    @property
    def medias(self):
        """List[:class:`.Media`]: The list of cached medias in this channel."""
        return list(self._medias.values())

    def get_media(self, id):
        """Optional[:class:`.Media`]: Get a cached media post in this channel."""
        return self._medias.get(id)

    async def getch_media(self, id: int) -> Media:
        return self.get_media(id) or await self.fetch_media(id)

    async def fetch_media(self, id: int) -> Media:
        """|coro|

        Fetch a media post in this channel.

        Parameters
        -----------
        id: :class:`int`
            The media's ID.

        Returns
        --------
        :class:`.Media`
        """
        data = await self._state.get_media(self.id, id)
        media = Media(data=data, channel=self, state=self._state)
        return media

    async def fetch_medias(self, *, limit: int = 50) -> List[Media]:
        """|coro|

        Fetch multiple media posts in this channel.

        All parameters are optional.

        Parameters
        -----------
        limit: :class:`int`
            The maximum number of media posts to return. Defaults to 50.

        Returns
        --------
        List[:class:`.Media`]
        """
        data = await self._state.get_medias(self.id, limit=limit)
        medias = []
        for media_data in data:
            medias.append(Media(data=media_data, channel=self, state=self._state))

        return medias

    async def create_media(self, *,
        title: str,
        description: str = None,
        file: Optional[File] = None,
        youtube_url: Optional[str] = None,
        tags: List[str] = None,
        game: Optional[Game] = None
    ) -> Media:
        """|coro|

        Create a media post in this channel.

        Parameters
        -----------
        title: :class:`str`
            The title of the media.
        description: Optional[:class:`str`]
            The description of the media. Does not accept markdown or any
            inline content.
        file: :class:`.File`
            The file to upload. Either this or ``youtube_url`` is required.
        youtube_url: :class:`str`
            The YouTube embed URL to use (``https://www.youtube.com/embed/...``).
            Either this or ``file`` is required.
        game: Optional[:class:`.Game`]
            The game to be associated with this media.

        Returns
        --------
        :class:`.Media`
            The created media.
        """
        if file and youtube_url:
            raise ValueError('Must not specify both file and youtube_url')
        if not file and not youtube_url:
            raise ValueError('Must specify either file or youtube_url')

        src_data = {}
        file_type = FileType.image
        if file:
            file.set_media_type(MediaType.media_channel_upload)
            await file._upload(self._state)
            src_data = {'src': file.url}
            file_type = file.file_type
        elif youtube_url:
            data = await self._state.upload_third_party_media(youtube_url)
            src_data = {'src': data['url'], 'additionalInfo': {'externalVideoSrc': youtube_url}}
            file_type = FileType.video

        data = await self._state.create_media(
            self.id,
            file_type=file_type,
            title=title,
            src_data=src_data,
            description=description,
            tags=(tags or []),
            game_id=(game.id if game else None)
        )
        media = Media(data=data, channel=self, game=game, state=self._state)
        return media


class ListChannel(guilded.abc.TeamChannel):
    """Represents a list channel in a team"""
    def __init__(self, **fields):
        super().__init__(**fields)
        self.type = ChannelType.list
        self._items = {}

    @property
    def items(self) -> List[ListItem]:
        """List[:class:`.ListItem`]: The list of cached items in this channel."""
        return list(self._items.values())

    def get_item(self, id) -> Optional[ListItem]:
        """Optional[:class:`.ListItem`]: Get a cached item in this channel."""
        return self._items.get(id)

    async def getch_item(self, id: str) -> ListItem:
        return self.get_item(id) or await self.fetch_item(id)

    async def fetch_item(self, id: str) -> ListItem:
        """|coro|

        Fetch a item in this channel.

        Parameters
        -----------
        id: :class:`str`
            The item's ID.

        Returns
        --------
        :class:`.ListItem`
        """
        data = await self._state.get_list_item(self.id, id)
        listitem = ListItem(data=data, channel=self, state=self._state)
        return listitem

    async def fetch_items(self) -> List[ListItem]:
        """|coro|

        Fetch all items in this channel.

        Returns
        --------
        List[:class:`.ListItem`]
        """
        data = await self._state.get_list_items(self.id)
        items = []
        for item_data in data:
            items.append(ListItem(data=item_data, channel=self, state=self._state))

        return items

    async def create_item(self, *message, **kwargs) -> ListItem:
        """|coro|

        Create an item in this channel.

        Parameters
        -----------
        message: Any
            The main content of the item.
        note: Optional[Any]
            The item's note.
        parent: Optional[:class:`ListItem`]
            An existing item to create this item under.
        position: Optional[:class:`int`]
            The item's position. Defaults to ``0`` if not specified (appears
            at the bottom of the list).
        send_notifications: Optional[:class:`bool`]
            Whether to "notify all clients" by creating this item. Defaults to
            ``False`` if not specified.

        Returns
        --------
        :class:`.ListItem`
            The created item.
        """
        note = tuple(kwargs.get('note', ''))
        parent = kwargs.get('parent')
        position = kwargs.get('position', 0)
        send_notifications = kwargs.get('send_notifications', False)

        data = await self._state.create_list_item(
            self.id,
            message=message,
            note=note,
            parent_id=(parent.id if parent else None),
            position=position,
            send_notifications=send_notifications
        )
        listitem = ListItem(data=data, channel=self, state=self._state)
        return listitem


class AnnouncementReply(guilded.abc.Reply):
    """Represents a reply to an :class:`Announcement`."""
    pass


class DocReply(guilded.abc.Reply):
    """Represents a reply to a :class:`Doc`."""
    pass


class ForumReply(guilded.abc.Reply):
    """Represents a reply to a :class:`ForumTopic`."""
    pass


class MediaReply(guilded.abc.Reply):
    """Represents a reply to a :class:`Media`."""
    pass
