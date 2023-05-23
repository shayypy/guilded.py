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

from __future__ import annotations

import abc
import datetime
import re
from typing import TYPE_CHECKING, List, Optional, Sequence
from typing_extensions import Self

from .asset import Asset
from .colour import Colour
from .enums import ChannelType, try_enum, UserType
from .message import HasContentMixin, ChatMessage
from .mixins import Hashable
from .presence import Presence
from .status import Status
from .utils import ISO8601, MISSING

if TYPE_CHECKING:
    from .types.user import User as UserPayload
    from .types.channel import ServerChannel as ServerChannelPayload
    from .types.comment import ContentComment

    from .embed import Embed
    from .group import Group
    from .server import Server
    from .user import Member


__all__ = (
    'GuildChannel',
    'Messageable',
    'Reply',
    'ServerChannel',
    'User',
)


class Messageable(metaclass=abc.ABCMeta):
    """An ABC for models that messages can be sent to.

    The following implement this ABC:

        * :class:`.ChatChannel`
        * :class:`.VoiceChannel`
        * :class:`.Thread`
        * :class:`.DMChannel`
        * :class:`.User`
        * :class:`.Member`
        * :class:`.ext.commands.Context`
    """
    def __init__(self, *, state, data):
        self._state = state
        self.id: str = data.get('id')
        self._channel_id: str = data.get('id')

    @property
    def _channel(self) -> Messageable:
        if isinstance(self, User):
            return self.dm_channel
        elif hasattr(self, 'channel'):
            return self.channel
        else:
            return self

    async def send(
        self,
        content: Optional[str] = MISSING,
        *,
        embed: Optional[Embed] = MISSING,
        embeds: Optional[Sequence[Embed]] = MISSING,
        reference: Optional[ChatMessage] = MISSING,
        reply_to: Optional[Sequence[ChatMessage]] = MISSING,
        mention_author: Optional[bool] = None,
        silent: Optional[bool] = None,
        private: bool = False,
        delete_after: Optional[float] = None,
    ) -> ChatMessage:
        """|coro|

        Send a message to a Guilded channel.

        .. warning::

            Replying with both ``silent`` and ``private`` set to ``True`` (a
            private reply with no mention) will not send the reply to the
            author of the message(s) until they refresh the channel. This is a
            Guilded bug.

        Parameters
        -----------
        content: :class:`str`
            The text content to send with the message.
        embed: :class:`.Embed`
            An embed to send with the message.
            This parameter cannot be meaningfully combined with ``embeds``.
        embeds: List[:class:`.Embed`]
            A list of embeds to send with the message.
            This can contain at most 1 value.
            This parameter cannot be meaningfully combined with ``embed``.
        reply_to: List[:class:`.ChatMessage`]
            A list of up to 5 messages to reply to.
        silent: :class:`bool`
            Whether this message should not mention the members mentioned in
            it, including the authors of messages it is in reply to, if any.
            Defaults to ``False``.
        private: :class:`bool`
            Whether this message should only be visible to its author (the
            bot) and the authors of the messages it is replying to. Defaults
            to ``False``. You should not include sensitive data in these
            because private replies can still be visible to server moderators.
        delete_after: :class:`float`
            If provided, the number of seconds to wait in the background before deleting the sent message.
            If the deletion fails, then it is silently ignored.
        """

        from .http import handle_message_parameters

        if reference is not MISSING:
            reply_to = [reference]

        params = handle_message_parameters(
            content=content,
            embed=embed,
            embeds=embeds,
            reply_to=[message.id for message in reply_to] if reply_to is not MISSING else MISSING,
            private=private,
            silent=silent if silent is not None else not mention_author if mention_author is not None else None,
        )

        data = await self._state.create_channel_message(
            self._channel_id,
            payload=params.payload,
        )
        message = self._state.create_message(
            data=data['message'],
            channel=self._channel,
        )

        if delete_after is not None:
            await message.delete(delay=delete_after)

        return message

    async def trigger_typing(self) -> None:
        """|coro|

        Begin your typing indicator in this channel.
        """
        await self._state.trigger_typing(self._channel_id)

    async def history(self,
        *,
        before: datetime.datetime = None,
        after: datetime.datetime = None,
        limit: int = 50,
        include_private: bool = False,
    ) -> List[ChatMessage]:
        """|coro|

        Fetch the message history of this channel.

        All parameters are optional.

        Parameters
        -----------
        before: :class:`datetime.datetime`
            Fetch messages sent before this timestamp.
        after: :class:`datetime.datetime`
            Fetch messages sent after this timestamp.
        limit: :class:`int`
            The maximum number of messages to fetch. Defaults to 50.
        include_private: :class:`bool`
            Whether to include private messages in the response. Defaults to ``False``.
            If the client is a user account, this has no effect and is always ``True``.

        Returns
        --------
        List[:class:`.ChatMessage`]
        """
        # TODO: Paginate automatically if limit > 100
        # TODO: Return an async iterator
        history = await self._state.get_channel_messages(
            self._channel_id,
            before=before,
            after=after,
            limit=limit,
            include_private=include_private,
        )

        messages = []
        for message in history.get('messages', []):
            try:
                messages.append(self._state.create_message(channel=self._channel, data=message))
            except:
                pass

        return messages

    async def fetch_message(self, message_id: str, /) -> ChatMessage:
        """|coro|

        Fetch a message.

        Returns
        --------
        :class:`.ChatMessage`
            The message from the ID.
        """
        data = await self._state.get_channel_message(self._channel_id, message_id)
        message = self._state.create_message(data=data['message'], channel=self._channel)
        return message

    #async def create_thread(self, *content, **kwargs) -> Thread:
    #    """|coro|

    #    Create a new thread in this channel.

    #    Parameters
    #    -----------
    #    \*content: Any
    #        The content of the message that should be created as the initial
    #        message of the newly-created thread. Passing either this or
    #        ``message`` is required.
    #    name: :class:`str`
    #        The name to create the thread with.
    #    message: Optional[:class:`.ChatMessage`]
    #        The message to create the thread from. Passing either this or
    #        values for ``content`` is required.

    #    Returns
    #    --------
    #    :class:`.Thread`
    #        The thread that was created.
    #    """
    #    name = kwargs.get('name')
    #    message = kwargs.get('message')
    #    if not name:
    #        raise TypeError('name is a required argument that is missing.')
    #    if not message and not content:
    #        raise TypeError('Must include message, an argument list of content, or both.')

    #    data = await self._state.create_thread(self._channel_id, content, name=name, initial_message=message)
    #    thread = self._state.create_channel(data=data.get('thread', data), group=self.group, server=self.server)
    #    return thread

    #async def pins(self) -> List[ChatMessage]:
    #    """|coro|

    #    Fetch the list of pinned messages in this channel.

    #    Returns
    #    --------
    #    List[:class:`.ChatMessage`]
    #        The pinned messages in this channel.
    #    """
    #    messages = []
    #    data = await self._state.get_pinned_messages(self._channel_id)
    #    for message_data in data['messages']:
    #        message = self._state.create_message(data=message_data, channel=self._channel)
    #        messages.append(message)

    #    return messages


class User(Hashable, metaclass=abc.ABCMeta):
    """An ABC for user-type models.

    The following implement this ABC:

        * :class:`~guilded.User`
        * :class:`.Member`
        * :class:`.ClientUser`

    Attributes
    -----------
    id: :class:`str`
        The user's id.
    name: :class:`str`
        The user's name.
    bot_id: Optional[:class:`str`]
        The user's corresponding bot ID, if any.
        This will likely only be available for the connected :class:`.ClientUser`.
    avatar: Optional[:class:`.Asset`]
        The user's set avatar, if any.
    banner: Optional[:class:`.Asset`]
        The user's profile banner, if any.
    created_at: :class:`datetime.datetime`
        When the user's account was created.
    status: Optional[:class:`.Status`]
        The custom status set by the user.
    """

    __slots__ = (
        'type',
        '_user_type',
        'id',
        'bot_id',
        'dm_channel',
        'name',
        'nick',
        'colour',
        'subdomain',
        'games',
        'bio',
        'tagline',
        'presence',
        'status',
        'blocked_at',
        'online_at',
        'created_at',
        'default_avatar',
        'avatar',
        'banner',
        'moderation_status',
        'badges',
        'stonks',
    )

    def __init__(self, *, state, data: UserPayload, **extra):
        self._state = state
        data = data.get('user', data)

        self.type = None
        self._user_type = try_enum(UserType, data.get('type', 'user'))
        self.id: str = data.get('id')
        self.bot_id: str = data.get('botId')
        self.dm_channel = None
        self.name: str = data.get('name') or ''
        self.nick: Optional[str] = None
        self.colour: Colour = Colour(0)
        self.slug: Optional[str] = data.get('subdomain')
        self.games: List = data.get('aliases', [])
        self.bio: str = (data.get('aboutInfo') or {}).get('bio') or ''
        self.tagline: str = (data.get('aboutInfo') or {}).get('tagLine') or ''
        self.presence: Presence = Presence.from_value(data.get('userPresenceStatus')) or None
        self.status = Status(data=data.get('status')) if data.get('status') else None

        self.blocked_at: Optional[datetime.datetime] = ISO8601(data.get('blockedDate'))
        self.online_at: Optional[datetime.datetime] = ISO8601(data.get('lastOnline'))
        self.created_at: datetime.datetime = ISO8601(data.get('createdAt') or data.get('joinDate'))
        # in profilev3, createdAt is returned instead of joinDate

        self.default_avatar: Asset = Asset._from_default_user_avatar(self._state, 1)

        avatar = None
        _avatar_url = data.get('avatar') or data.get('profilePicture') or data.get('profilePictureLg') or data.get('profilePictureSm') or data.get('profilePictureBlur')
        if _avatar_url:
            if 'WebhookThumbnail' in _avatar_url:
                # Custom webhook avatars. Default webhook avatars use UserAvatar.
                avatar = Asset._from_webhook_thumbnail(self._state, _avatar_url)
            else:
                avatar = Asset._from_user_avatar(self._state, _avatar_url)
        self.avatar: Optional[Asset] = avatar

        banner = None
        _banner_url = data.get('banner') or data.get('profileBannerLg') or data.get('profileBannerSm') or data.get('profileBannerBlur')
        if _banner_url:
            banner = Asset._from_user_banner(self._state, _banner_url)
        self.banner: Optional[Asset] = banner

        self.moderation_status: Optional[str] = data.get('moderationStatus')
        self.badges: List = data.get('badges') or []
        self.stonks: Optional[int] = data.get('stonks')

    def __str__(self) -> str:
        return self.display_name or ''

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} id={self.id!r} name={self.name!r} type={self._user_type!r}>'

    @property
    def profile_url(self) -> str:
        return f'https://guilded.gg/profile/{self.id}'

    @property
    def vanity_url(self) -> Optional[str]:
        if self.slug:
            return f'https://guilded.gg/{self.slug}'
        return None

    @property
    def mention(self) -> str:
        """:class:`str`: The mention string for this user.

        This will render and deliver a mention when sent in an :class:`.Embed`.
        """
        return f'<@{self.id}>'

    @property
    def display_name(self) -> str:
        return self.nick if self.nick is not None else self.name

    @property
    def color(self) -> Colour:
        return self.colour

    @property
    def _channel_id(self) -> Optional[str]:
        return self.dm_channel.id if self.dm_channel else None

    @property
    def bot(self) -> bool:
        """:class:`bool`: |dpyattr|

        Whether the user is a bot account or webhook.
        """
        return self._user_type is UserType.bot

    @property
    def display_avatar(self) -> Asset:
        """:class:`.Asset`: The "top-most" avatar for this user, or, the avatar
        that the client will display in the member list and in chat."""
        return self.avatar or self.default_avatar


class ServerChannel(Hashable, metaclass=abc.ABCMeta):
    """An ABC for the various types of server channels.

    The following implement this ABC:

        * :class:`.AnnouncementChannel`
        * :class:`.ChatChannel`
        * :class:`.DocsChannel`
        * :class:`.ForumChannel`
        * :class:`.ListChannel`
        * :class:`.MediaChannel`
        * :class:`.Thread`
        * :class:`.SchedulingChannel`
        * :class:`.VoiceChannel`
    """

    def __init__(self, *, state, data: ServerChannelPayload, group: Group, **extra):
        self._state = state
        self._group = group

        self.group_id: str = data.get('groupId')
        self.server_id: str = data.get('serverId')
        self.category_id: Optional[int] = data.get('categoryId')

        self.id: str = data['id']
        self.type: ChannelType = try_enum(ChannelType, data.get('type'))
        self.name: str = data.get('name') or ''
        self.topic: str = data.get('topic') or ''
        self.public: bool = data.get('isPublic', False)

        self.created_by_id: Optional[str] = extra.get('createdBy')
        self.created_at: datetime.datetime = ISO8601(data.get('createdAt'))
        self.updated_at: Optional[datetime.datetime] = ISO8601(data.get('updatedAt'))

        self.archived_by_id: Optional[str] = data.get('archivedBy')
        self.archived_at: Optional[datetime.datetime] = ISO8601(data.get('archivedAt'))

    @property
    def share_url(self) -> str:
        """:class:`str`: The share URL of the channel."""
        # For channel links, any real type will work in the client, but
        # linking to individual content requires the proper type string
        if hasattr(self, '_shareable_content_type'):
            type_ = self._shareable_content_type
        elif self.type is not None:
            type_ = self.type.value
        else:
            type_ = 'chat'

        if self.server and self.server.slug:
            # We must have the proper string here, or else when the link is
            # visited, the client will either dead-end at the server overview
            # or end up on whichever user or server owns the slug
            server_portion = self.server.slug
        elif self.server:
            # Take our best guess - remove everything other than [\w-]:
            server_portion = re.sub(r'(?![\w-]).', '', self.server.name.replace(' ', '-'))
        else:
            server_portion = f'teams/{self.server_id}'

        return f'https://guilded.gg/{server_portion}/groups/{self.group_id}/channels/{self.id}/{type_}'

    jump_url = share_url

    @property
    def mention(self) -> str:
        return f'<#{self.id}>'

    @property
    def group(self) -> Group:
        """:class:`~guilded.Group`: The group that this channel is in."""
        group = self._group
        if not group and self.server:
            group = self.server.get_group(self.group_id)

        return group

    @property
    def server(self) -> Server:
        """:class:`.Server`: The server that this channel is in."""
        return self._state._get_server(self.server_id)

    @property
    def guild(self) -> Server:
        """:class:`.Server`: |dpyattr|

        This is an alias of :attr:`.server`.

        The server that this channel is in.
        """
        return self.server

    @property
    def parent(self) -> Optional[ServerChannel]:
        return self.server.get_channel_or_thread(self.parent_id)

    @property
    def created_by(self) -> Optional[Member]:
        return self.server.get_member(self.created_by_id)

    @property
    def archived_by(self) -> Optional[Member]:
        return self.server.get_member(self.archived_by_id)

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} id={self.id!r} name={self.name!r} server={self.server!r}>'

    async def edit(
        self,
        *,
        name: str = MISSING,
        topic: str = MISSING,
        public: bool = None,
    ) -> Self:
        """|coro|

        Edit this channel.

        All parameters are optional.

        Parameters
        -----------
        name: :class:`str`
            The channel's name.
        topic: :class:`str`
            The channel's topic. Not applicable to threads.
        public: :class:`bool`
            Whether the channel should be public, i.e., visible to users who
            are not a member of the server. Not applicable to threads.

        Returns
        --------
        :class:`.ServerChannel`
            The newly edited channel.
        """

        payload = {}
        if name is not MISSING:
            payload['name'] = name

        if topic is not MISSING:
            payload['topic'] = topic

        if public is not None:
            payload['isPublic'] = public

        data = await self._state.update_channel(
            self.id,
            payload=payload,
        )
        channel = self.__class__.__init__(
            data=data['channel'],
            state=self._state,
            group=self.group,
        )
        return channel

    async def delete(self) -> None:
        """|coro|

        Delete this channel.
        """
        await self._state.delete_channel(self.id)

GuildChannel = ServerChannel  # discord.py


class Reply(Hashable, HasContentMixin, metaclass=abc.ABCMeta):
    """An ABC for replies to posts.

    The following implement this ABC:

        * :class:`.ForumTopicReply`

    .. container:: operations

        .. describe:: x == y

            Checks if two replies are equal.

        .. describe:: x != y

            Checks if two replies are not equal.

        .. describe:: hash(x)

            Returns the reply's hash.

    Attributes
    -----------
    id: :class:`int`
        The reply's ID.
    content: :class:`str`
        The reply's content.
    created_at: :class:`datetime.datetime`
        When the reply was created.
    updated_at: Optional[:class:`datetime.datetime`]
        When the reply was last updated.
    """

    __slots__ = (
        'id',
        'content',
        '_mentions',
        'author_id',
        'created_at',
        'updated_at',
        'channel_id',
        'replied_to_id',
        'replied_to_author_id',
        '_state',
    )

    def __init__(self, *, state, data: ContentComment):
        super().__init__()
        self._state = state
        self.channel_id: str = data.get('channelId')

        self.id: int = int(data['id'])
        self.content: str = data['content']
        self._mentions = self._create_mentions(data.get('mentions'))
        self._extract_attachments(self.content)

        self.author_id: str = data.get('createdBy')
        self.created_at: datetime.datetime = ISO8601(data.get('createdAt'))
        self.updated_at: Optional[datetime.datetime] = ISO8601(data.get('updatedAt'))

        self.replied_to_id: Optional[int] = None
        self.replied_to_author_id: Optional[str] = None

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} id={self.id!r} author={self.author!r}>'

    @property
    def _content_type(self) -> str:
        return getattr(self.channel, 'content_type', self.channel.type.value)

    @property
    def author(self) -> Optional[Member]:
        """Optional[:class:`.Member`]: The :class:`.Member` that created the
        reply, if they are cached."""
        return self.server.get_member(self.author_id)

    @property
    def channel(self) -> ServerChannel:
        """:class:`~.abc.ServerChannel`: The channel that the reply is in."""
        return self.parent.channel

    @property
    def group(self) -> Group:
        """:class:`~guilded.Group`: The group that the reply is in."""
        return self.parent.group

    @property
    def server(self) -> Server:
        """:class:`.Server`: The server that the reply is in."""
        return self.parent.server

    @classmethod
    def _copy(cls, reply):
        self = cls.__new__(cls)

        self.parent = reply.parent
        self.parent_id = reply.parent_id
        self.id = reply.id
        self.content = reply.content
        self.author_id = reply.author_id
        self.created_at = reply.created_at
        self.updated_at = reply.updated_at
        self.replied_to_id = reply.replied_to_id
        self.replied_to_author_id = reply.replied_to_author_id

        return self

    def _update(self, data: ContentComment) -> None:
        try:
            self.content = data['content']
        except KeyError:
            pass

        try:
            self.updated_at = ISO8601(data['updatedAt'])
        except KeyError:
            pass
