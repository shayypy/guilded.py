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
    'Thread',
    'VoiceChannel'
)


class ChannelType(Enum):
    chat = 'chat'
    text = chat
    voice = 'voice'
    forum = 'forum'
    doc = 'doc'
    docs = doc
    announcement = 'announcement'
    announcements = announcement
    news = announcement
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
            The message to create the thread from. Passing either this or
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
        data = await self._state.get_forum_topic_reply(self.channel.id, self.id, id)
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


class AnnouncementChannel(guilded.abc.TeamChannel):
    """Represents an announcements channel in a team"""
    def __init__(self, **fields):
        super().__init__(**fields)
        self.type = ChannelType.announcements
        self._announcements = {}

    @property
    def announcements(self):
        """List[:class:`.Announcement`]: The list of cached announcements in this channel."""
        return list(self._announcements.values())

    def get_announcement(self, id):
        """Optional[:class:`.Announcement`]: Get a cached announcement in this channel."""
        return self._announcements.get(id)

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


class AnnouncementReply(guilded.abc.Reply):
    """Represents a reply to an :class:`Announcement`."""
    pass


class DocReply(guilded.abc.Reply):
    """Represents a reply to a :class:`Doc`."""
    pass


class ForumReply(guilded.abc.Reply):
    """Represents a reply to a :class:`ForumTopic`."""
    pass
