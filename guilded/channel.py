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
from typing import Optional, Union, List

import guilded.abc

from .embed import Embed
from .emoji import Emoji
from .file import Attachment
#from .gateway import GuildedVoiceWebSocket
from .message import HasContentMixin, Message, Link
from .user import Member, User
from .utils import ISO8601, parse_hex_number
from .status import Game

__all__ = (
    'ChannelType',
    'ChatChannel',
    'DMChannel',
    'Doc',
    'DocsChannel',
    'DocReply',
    'ForumChannel',
    'ForumReply',
    'ForumTopic',
    'Thread',
    'VoiceChannel'
)


class ChannelType(Enum):
    chat = 'chat'
    text = chat
    voice = 'voice'
    forum = 'forum'
    docs = 'doc'
    doc = docs
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


class Doc(HasContentMixin):
    """Represents a doc in a :class:`DocsChannel`."""
    def __init__(self, *, state, data, channel, game=None):
        super().__init__()
        self._state = state
        self.channel = channel
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
        await self._state.add_doc_reaction(self.id, emoji.id)

    async def remove_self_reaction(self, emoji):
        """|coro|

        Remove your reaction from this doc.

        Parameters
        -----------
        emoji: :class:`.Emoji`
            The emoji to remove.
        """
        await self._state.remove_self_doc_reaction(self.id, emoji.id)

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
        data = await self._state.create_doc_reply(self.team.id, self.id, content=content, reply_to=kwargs.get('reply_to'))
        reply = DocReply(data=data['reply'], doc=self, state=self._state)
        return reply

    def get_reply(self, id: int):
        """Optional[:class:`.DocReply`]: Get a cached reply to this doc."""
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
        data = await self._state.get_doc_reply(self.id, id)
        reply = DocReply(data=data['reply'], doc=self, state=self._state)
        return reply

    async def move(self, id: int):
        """|coro|

        Move this doc to another :class:`.DocsChannel`.

        Parameters
        -----------
        to: :class:`.DocsChannel`
            The docs channel to move this topic to.
        """
        await self._state.move_doc(self.channel.id, self.id, to.id)


class DocReply(HasContentMixin):
    """Represents a reply to a :class:`Doc`."""
    def __init__(self, *, state, data, doc):
        super().__init__()
        self._state = state
        self.doc = doc
        self.channel = doc.channel
        self.team = doc.team

        self.author_id: str = data.get('createdBy')
        self.created_at: datetime.datetime = ISO8601(data.get('createdAt'))
        self.edited_at: Optional[datetime.datetime] = ISO8601(data.get('editedAt'))

        self.id: int = int(data['id'])
        self.content: str = self._get_full_content(data['message'])

    def __repr__(self):
        return f'<DocReply id={self.id!r} author={self.author!r} doc={self.doc!r}>'

    @property
    def author(self) -> Optional[Member]:
        """Optional[:class:`.Member`]: The :class:`.Member` that created the
        reply, if they are cached.
        """
        return self.team.get_member(self.author_id)

    async def add_reaction(self, emoji):
        """|coro|

        Add a reaction to this reply.

        Parameters
        -----------
        emoji: :class:`.Emoji`
            The emoji to add.
        """
        await self._state.add_doc_reply_reaction(self.id, emoji.id)

    async def remove_self_reaction(self, emoji):
        """|coro|

        Remove your reaction from this reply.

        Parameters
        -----------
        emoji: :class:`.Emoji`
            The emoji to remove.
        """
        await self._state.remove_self_doc_reply_reaction(self.id, emoji.id)

    async def delete(self):
        """|coro|

        Delete this reply.
        """
        await self._state.delete_doc_reply(self.team.id, self.doc.id, self.id)

    async def reply(self, *content, **kwargs):
        """|coro|

        Reply to this reply.

        This method is identical to :meth:`.Doc.reply`.
        """
        return await self.doc.reply(*content, **kwargs)


class DocsChannel(guilded.abc.TeamChannel):
    """Represents a docs channel in a team."""
    def __init__(self, **fields):
        super().__init__(**fields)
        self.type = ChannelType.docs
        self._docs = {}

    @property
    def docs(self):
        return list(self._docs.values())

    def get_doc(self, id: int):
        return self._docs.get(id)

    async def create_doc(self, *content, **kwargs):
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
    forum: :class:`.ForumChannel`
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
    def __init__(self, *, state, data, forum, group=None, team=None):
        super().__init__()
        self._state = state
        self.forum = forum
        self.forum_id = data.get('channelId')
        self.team = team or state._get_team(data.get('teamId'))
        self.team_id = data.get('teamId') or (self.team.id if self.team else None)
        self._group = group
        self.group_id = data.get('groupId')
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
    def group(self):
        """Optional[:class:`.Group`]: The group that the topic is in."""
        return self._group or self.team.get_group(self.group_id)

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
        data = await self._state.get_forum_topic_replies(self.forum_id, self.id, limit=limit)
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
        data = await self._state.get_forum_topic_reply(self.forum_id, self.id, id)
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
        data = await self._state.create_forum_topic_reply(self.forum_id or self.forum.id, self.id, content=content, reply_to=kwargs.get('reply_to'))
        return data['replyId']

    async def delete(self):
        """|coro|

        Delete this topic.
        """
        await self._state.delete_forum_topic(self.forum_id, self.id)

    async def move(self, to):
        """|coro|

        Move this topic to another :class:`.ForumChannel`.

        Parameters
        -----------
        to: :class:`.ForumChannel`
            The forum to move this topic to.
        """
        await self._state.move_forum_topic(self.forum_id, self.id, to.id)

    async def lock(self):
        """|coro|

        Lock this topic.
        """
        await self._state.lock_forum_topic(self.forum_id, self.id)

    async def unlock(self):
        """|coro|

        Unlock this topic.
        """
        await self._state.unlock_forum_topic(self.forum_id, self.id)

    async def sticky(self):
        """|coro|

        Sticky (pin) this topic.
        """
        await self._state.sticky_forum_topic(self.forum_id, self.id)

    async def unsticky(self):
        """|coro|

        Unsticky (unpin) this topic.
        """
        await self._state.unsticky_forum_topic(self.forum_id, self.id)


class ForumChannel(guilded.abc.TeamChannel):
    """Represents a forum channel in a team."""
    def __init__(self, **fields):
        super().__init__(**fields)
        self.type = ChannelType.forum
        self._topics = {}

    @property
    def topics(self):
        return list(self._topics.values())

    def get_topic(self, id):
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
        topic = ForumTopic(data=data, state=self._state, group=self.group, team=self.team, forum=self)
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
        topic = ForumTopic(data=data.get('thread', data), state=self._state, group=self.group, team=self.team, forum=self)
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
            topic = ForumTopic(data=topic_data, state=self._state, group=self.group, team=self.team, forum=self)

        return topics


class ForumReply(HasContentMixin):
    """Represents a forum reply.

    Attributes
    -----------
    id: :class:`int`
        The reply's ID.
    content: :class:`str`
        The reply's content.
    topic: :class:`.ForumTopic`
        The topic that the reply is in.
    forum: :class:`.ForumChannel`
        The forum channel that the reply is in.
    created_at: :class:`datetime.datetime`
        When the reply was created.
    edited_at: Optional[:class:`datetime.datetime`]
        When the reply was last edited.
    deleted_by: Optional[:class:`.Member`]
        Who deleted this reply. This will only be present through
        :meth:`on_forum_reply_delete`.
    """
    def __init__(self, *, state, data, forum):
        super().__init__()
        self._state = state
        self.forum = forum
        self.topic_id = data.get('repliesTo')
        self.id: int = int(data['id'])
        self.content: str = self._get_full_content(data['message'])

        self.author_id: str = data.get('createdBy')
        self.created_by_bot_id: Optional[int] = data.get('createdByBotId')
        self.created_at: datetime.datetime = ISO8601(data.get('createdAt'))
        self.edited_at: Optional[datetime.datetime] = ISO8601(data.get('editedAt'))
        self.deleted_by: Optional[Member] = None

        self.replied_to_id: Optional[int] = None
        self.replied_to_author_id: Optional[str] = None

    def __str__(self):
        return self.title

    def __repr__(self):
        return f'<ForumReply id={self.id!r} topic={self.topic!r}>'

    @property
    def team_id(self):
        return self.forum.team_id

    @property
    def team(self):
        return self.forum.team

    @property
    def author(self) -> Optional[Union[Member, User]]:
        """Optional[Union[:class:`.Member`, :class:`.User`]]:
        The :class:`.Member` that created the reply. If the member is no
        longer in the server (and they are cached), this will be a
        :class:`.User`.
        """
        return self.team.get_member(self.author_id) or self._state.get_user(self.author_id)

    @property
    def topic(self) -> Optional[ForumTopic]:
        """Optional[:class:`.ForumTopic`]: The :class:`.ForumTopic` that this
        reply is to. Will be ``None`` if the topic is not cached.
        """
        return self.forum.get_topic(self.topic_id)

    @property
    def replied_to(self):
        if self.replied_to_id:
            return self.topic.get_reply(self.replied_to_id)
        return None

    async def delete(self):
        """|coro|

        Delete this reply.
        """
        await self._state.delete_forum_topic_reply(self.forum.id, self.topic_id, self.id)

    async def reply(self, *content) -> int:
        """|coro|

        Reply to this reply.

        This method is identical to :meth:`.ForumTopic.reply`.
        """
        data = await self._state.create_forum_topic_reply(self.forum.id, self.topic_id, content=content, reply_to=self)
        return data['replyId']


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

    async def hide(self):
        """|coro|

        Visually hide this DM channel in the client.

        The channel's content will still exist, and the channel can be
        re-fetched with :meth:`User.create_dm` on whichever :class:`User` this
        channel is associated with.
        """
        await self._state.hide_dm_channel(self.id)
