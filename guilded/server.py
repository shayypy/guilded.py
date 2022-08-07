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

import datetime
import re
from typing import TYPE_CHECKING, Dict, Optional, List, Union

from .abc import ServerChannel, User

from .asset import Asset
from .channel import AnnouncementChannel, ChatChannel, DocsChannel, ForumChannel, ListChannel, MediaChannel, SchedulingChannel, Thread, VoiceChannel
from .errors import InvalidData
from .enums import ServerType, try_enum, ChannelType
from .group import Group
from .mixins import Hashable
from .role import Role
from .user import Member, MemberBan
from .utils import ISO8601, Object, get, find

if TYPE_CHECKING:
    from .emote import Emote
    from .flowbot import FlowBot
    from .webhook import Webhook

# ZoneInfo is in the stdlib in Python 3.9+
try:
    from zoneinfo import ZoneInfo  # type: ignore
except ImportError:
    # Fall back to pytz, if installed
    try:
        from pytz import timezone as ZoneInfo  # type: ignore
    except ImportError:
        ZoneInfo = None

__all__ = (
    'Guild',
    'Server',
)


class Server(Hashable):
    """Represents a server (or "guild") in Guilded.

    There is an alias for this class called ``Guild``\.

    .. container:: operations

        .. describe:: x == y

            Checks if two servers are equal.

        .. describe:: x != y

            Checks if two servers are not equal.

        .. describe:: hash(x)

            Returns the server's hash.

        .. describe:: str(x)

            Returns the server's name.

    Attributes
    -----------
    id: :class:`str`
        The server's id.
    name: :class:`str`
        The server's name.
    type: Optional[:class:`ServerType`]
        The type of server. This correlates to one of the options in the
        server settings page under "Server type".
    owner_id: :class:`str`
        The server's owner's id.
    created_at: :class:`datetime.datetime`
        When the server was created.
    about: :class:`str`
        The server's description.
    avatar: Optional[:class:`.Asset`]
        The server's set avatar, if any.
    banner: Optional[:class:`.Asset`]
        The server's banner, if any.
    slug: Optional[:class:`str`]
        The server's URL slug (or "vanity code").
        Referred to as a "Server URL" in the client.
        For a complete URL, see :attr:`.vanity_url`\.
    verified: :class:`bool`
        Whether the server is verified.
    timezone: Optional[:class:`datetime.tzinfo`]
        The server's timezone.
        If you are using Python 3.9 or greater, this is an instance of `ZoneInfo <https://docs.python.org/3/library/zoneinfo.html>`_.
        Otherwise, if `pytz <https://pypi.org/project/pytz>`_ is available in the working environment, an instance from pytz.
        If neither apply or the server does not have a timezone set, this will be ``None``.
    """

    def __init__(self, *, state, data):
        self._state = state

        self.id: str = data['id']
        self.type: Optional[ServerType]
        if data.get('type'):
            self.type = try_enum(ServerType, data['type'])
        else:
            self.type = None

        self._channels: Dict[str, ServerChannel] = {}
        self._threads: Dict[str, Thread] = {}
        self._groups: Dict[str, Group] = {}
        self._emotes: Dict[int, Emote] = {}
        self._members: Dict[str, Member] = {}
        self._roles: Dict[int, Role] = {}
        self._flowbots: Dict[str, FlowBot] = {}

        self._base_role: Optional[Role] = None
        self._bot_role: Optional[Role] = None

        self.owner_id: str = data.get('ownerId')
        self.name: str = data.get('name')
        self.slug: str = data.get('url')
        self.created_at: datetime.datetime = ISO8601(data.get('createdAt'))
        self.about: str = data.get('about') or ''
        self.default_channel_id: Optional[str] = data.get('defaultChannelId')
        self.verified: bool = data.get('isVerified') or False

        self.timezone: Optional[ZoneInfo]
        self.raw_timezone: Optional[str] = data.get('timezone')
        if self.raw_timezone and ZoneInfo:
            try:
                # 'America/Los Angeles (PST/PDT)' -> 'America/Los_Angeles'
                self.timezone = ZoneInfo(re.sub(r'( \(.+)', '', self.raw_timezone).replace(' ', '_'))
            except:
                # This might happen on outdated tzdata versions
                self.timezone = None
        else:
            self.timezone = None

        for member in data.get('members') or []:
            member['serverId'] = self.id
            self._members[member['id']] = self._state.create_member(data=member, server=self)

        for role_id, role in data.get('rolesById', {}).items():
            if role_id.isdigit():
                # "baseRole" is included in rolesById, resulting in a
                # duplicate entry for the base role.
                role: Role = Role(state=self._state, data=role, server=self)
                self._roles[role.id] = role
                if role.base:
                    self._base_role: Optional[Role] = role
                if role.is_bot():
                    self._bot_role: Optional[Role] = role

        avatar = None
        avatar_url = data.get('profilePicture') or data.get('avatar')
        if avatar_url:
            avatar = Asset._from_team_avatar(state, avatar_url)
        self.avatar: Optional[Asset] = avatar

        banner = None
        banner_url = data.get('teamDashImage') or data.get('banner')
        if banner_url:
            banner = Asset._from_team_banner(state, banner_url)
        self.banner: Optional[Asset] = banner

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f'<Server id={self.id!r} name={self.name!r}>'

    @property
    def description(self) -> str:
        """:class:`str`: |dpyattr|

        This is an alias of :attr:`.about`.

        The server's description.
        """
        return self.about

    @property
    def vanity_url(self) -> Optional[str]:
        """Optional[:class:`str`]: The server's vanity URL, if available."""
        return f'https://guilded.gg/{self.slug}' if self.slug is not None else None

    @property
    def member_count(self) -> int:
        """:class:`int`: |dpyattr|

        The server's member count.
        """
        return len(self.members)

    @property
    def owner(self) -> Optional[Member]:
        """Optional[:class:`.Member`]: The server's owner, if they are cached."""
        return self.get_member(self.owner_id)

    @property
    def me(self) -> Optional[Member]:
        """Optional[:class:`.Member`]: The client's member object in the server."""
        return self.get_member(self._state.my_id)

    @property
    def members(self) -> List[Member]:
        """List[:class:`.Member`]: The list of members in the server."""
        return list(self._members.values())

    @property
    def channels(self) -> List[ServerChannel]:
        """List[:class:`~.abc.ServerChannel`]: The list of channels in the server."""
        return list(self._channels.values())

    @property
    def threads(self) -> List[Thread]:
        """List[:class:`.Thread`]: The list of threads in the server."""
        return list(self._threads.values())

    @property
    def announcement_channels(self) -> List[AnnouncementChannel]:
        """List[:class:`.AnnouncementChannel`]: The list of announcement channels in the server."""
        channels = [ch for ch in self._channels.values() if isinstance(ch, AnnouncementChannel)]
        return channels

    @property
    def chat_channels(self) -> List[ChatChannel]:
        """List[:class:`.ChatChannel`]: The list of chat channels in the server."""
        channels = [ch for ch in self._channels.values() if isinstance(ch, ChatChannel)]
        return channels

    @property
    def docs_channels(self) -> List[DocsChannel]:
        """List[:class:`.DocsChannel`]: The list of docs channels in the server."""
        channels = [ch for ch in self._channels.values() if isinstance(ch, DocsChannel)]
        return channels

    @property
    def forum_channels(self) -> List[ForumChannel]:
        """List[:class:`.ForumChannel`]: The list of forum channels in the server."""
        channels = [ch for ch in self._channels.values() if isinstance(ch, ForumChannel)]
        return channels

    @property
    def forums(self) -> List[ForumChannel]:
        """List[:class:`.ForumChannel`]: |dpyattr|

        This is an alias of :attr:`.forum_channels`\.

        The list of forum channels in the server.
        """
        return self.forum_channels

    @property
    def media_channels(self) -> List[MediaChannel]:
        """List[:class:`.MediaChannel`]: The list of media channels in the server."""
        channels = [ch for ch in self._channels.values() if isinstance(ch, MediaChannel)]
        return channels

    @property
    def list_channels(self) -> List[ListChannel]:
        """List[:class:`.ListChannel`]: The list of list channels in the server."""
        channels = [ch for ch in self._channels.values() if isinstance(ch, ListChannel)]
        return channels

    @property
    def scheduling_channels(self) -> List[SchedulingChannel]:
        """List[:class:`.SchedulingChannel`]: The list of scheduling channels in the server."""
        channels = [ch for ch in self._channels.values() if isinstance(ch, SchedulingChannel)]
        return channels

    @property
    def text_channels(self) -> List[ChatChannel]:
        """List[:class:`.ChatChannel`]: |dpyattr|

        This is an alias of :attr:`.chat_channels`\.

        The list of chat channels in the server.
        """
        return self.chat_channels

    @property
    def voice_channels(self) -> List[VoiceChannel]:
        """List[:class:`.VoiceChannel`]: The list of voice channels in the server."""
        channels = [ch for ch in self._channels.values() if isinstance(ch, VoiceChannel)]
        return channels

    @property
    def groups(self) -> List[Group]:
        """List[:class:`.Group`]: The cached list of groups in the server."""
        return list(self._groups.values())

    @property
    def emotes(self) -> List[Emote]:
        """List[:class:`.Emote`]: The cached list of emotes in the server."""
        return list(self._emotes.values())

    @property
    def roles(self) -> List[Role]:
        """List[:class:`.Role`]: The cached list of roles in the server."""
        return list(self._roles.values())

    @property
    def base_role(self) -> Optional[Role]:
        """Optional[:class:`.Role`]: The base ``Member`` role for the server."""
        return self._base_role or get(self.roles, base=True)

    @property
    def bot_role(self) -> Optional[Role]:
        """Optional[:class:`.Role`]: The ``Bot`` role for the server."""
        return self._bot_role or find(lambda role: role.is_bot(), self.roles)

    @property
    def icon(self) -> Optional[Asset]:
        """Optional[:class:`.Asset`]: |dpyattr|

        This is an alias of :attr:`.avatar`.

        The server's set avatar, if any.
        """
        return self.avatar

    @property
    def default_channel(self) -> Optional[ServerChannel]:
        """Optional[:class:`~.abc.ServerChannel`]: The default channel of the server.

        It may be preferable to use :meth:`.fetch_default_channel` instead of
        this property, as it relies solely on cache which may not be present
        for newly joined servers.
        """
        return self.get_channel(self.default_channel_id)

    def get_member(self, member_id: str, /) -> Optional[Member]:
        """Optional[:class:`.Member`]: Get a member by their ID from the cache."""
        return self._members.get(member_id)

    def get_group(self, group_id: str, /) -> Optional[Group]:
        """Optional[:class:`~guilded.Group`]: Get a group by its ID from the cache."""
        return self._groups.get(group_id)

    def get_channel(self, channel_id: str, /) -> Optional[ServerChannel]:
        """Optional[:class:`~.abc.ServerChannel`]: Get a channel by its ID from the cache."""
        return self._channels.get(channel_id)

    def get_thread(self, thread_id: str, /) -> Optional[Thread]:
        """Optional[:class:`.Thread`]: Get a thread by its ID from the cache."""
        return self._threads.get(thread_id)

    def get_channel_or_thread(self, id: str) -> Optional[Union[ServerChannel, Thread]]:
        """Optional[Union[:class:`~.abc.ServerChannel`, :class:`.Thread`]]: Get
        a channel or thread by its ID from the cache."""
        return self.get_channel(id) or self.get_thread(id)

    def get_emote(self, emote_id: int, /) -> Optional[Emote]:
        """Optional[:class:`.Emote`]: Get an emote by its ID from the cache."""
        return self._emotes.get(emote_id)

    def get_role(self, role_id: int, /) -> Optional[Role]:
        """Optional[:class:`.Role`]: Get a role by its ID from the cache."""
        return self._roles.get(role_id)

    async def leave(self):
        """|coro|

        Leave the server.
        """
        await self.kick(Object(self._state.my_id))

    async def _create_channel(
        self,
        content_type: ChannelType,
        *,
        name: str,
        topic: str = None,
        public: bool = None,
        category: ServerChannel = None,
        group: Group = None,
    ) -> ServerChannel:

        data = await self._state.create_server_channel(
            self.id,
            content_type.value,
            name=name,
            topic=topic,
            public=public,
            category_id=category.id if category is not None else None,
            group_id=group.id if group is not None else None,
        )
        channel = self._state.create_channel(data=data['channel'], group=group, server=self)
        return channel

    async def create_announcement_channel(
        self,
        name: str,
        *,
        topic: str = None,
        public: bool = None,
        category: ServerChannel = None,
        group: Group = None,
    ) -> AnnouncementChannel:
        """|coro|

        Create a new announcement channel in the server.

        Parameters
        -----------
        name: :class:`str`
            The channel's name. Can include spaces.
        topic: :class:`str`
            The channel's topic.
        category: :class:`.CategoryChannel`
            The :class:`.CategoryChannel` to create this channel under. If not
            provided, it will be shown under the "Channels" header in the
            client (no category).
        public: :class:`bool`
            Whether this channel and its contents should be visible to people who aren't part of the server. Defaults to ``False``.
        group: :class:`.Group`
            The :class:`.Group` to create this channel in. If not provided, defaults to the base group.

        Returns
        --------
        :class:`.AnnouncementChannel`
            The created channel.
        """

        channel = await self._create_channel(
            ChannelType.announcements,
            name=name,
            topic=topic,
            public=public,
            category=category,
            group=group,
        )
        return channel

    async def create_chat_channel(
        self,
        name: str,
        *,
        topic: str = None,
        public: bool = None,
        category: ServerChannel = None,
        group: Group = None,
    ) -> ChatChannel:
        """|coro|

        Create a new chat channel in the server.

        Parameters
        -----------
        name: :class:`str`
            The channel's name. Can include spaces.
        topic: :class:`str`
            The channel's topic.
        category: :class:`.CategoryChannel`
            The :class:`.CategoryChannel` to create this channel under. If not
            provided, it will be shown under the "Channels" header in the
            client (no category).
        public: :class:`bool`
            Whether this channel and its contents should be visible to people who aren't part of the server. Defaults to ``False``.
        group: :class:`.Group`
            The :class:`.Group` to create this channel in. If not provided, defaults to the base group.

        Returns
        --------
        :class:`.ChatChannel`
            The created channel.
        """

        channel = await self._create_channel(
            ChannelType.chat,
            name=name,
            topic=topic,
            public=public,
            category=category,
            group=group,
        )
        return channel

    async def create_text_channel(
        self,
        name: str,
        *,
        topic: str = None,
        public: bool = None,
        category: ServerChannel = None,
        group: Group = None,
    ) -> ChatChannel:
        """|coro|

        |dpyattr|

        Create a new chat channel in the server.

        Parameters
        -----------
        name: :class:`str`
            The channel's name. Can include spaces.
        topic: :class:`str`
            The channel's topic.
        category: :class:`.CategoryChannel`
            The :class:`.CategoryChannel` to create this channel under. If not
            provided, it will be shown under the "Channels" header in the
            client (no category).
        public: :class:`bool`
            Whether this channel and its contents should be visible to people who aren't part of the server. Defaults to ``False``.
        group: :class:`.Group`
            The :class:`.Group` to create this channel in. If not provided, defaults to the base group.

        Returns
        --------
        :class:`.ChatChannel`
            The created channel.
        """

        return await self.create_chat_channel(
            name=name,
            topic=topic,
            public=public,
            category=category,
            group=group,
        )

    async def create_docs_channel(
        self,
        name: str,
        *,
        topic: str = None,
        public: bool = None,
        category: ServerChannel = None,
        group: Group = None,
    ) -> DocsChannel:
        """|coro|

        Create a new docs channel in the server.

        Parameters
        -----------
        name: :class:`str`
            The channel's name. Can include spaces.
        topic: :class:`str`
            The channel's topic.
        category: :class:`.CategoryChannel`
            The :class:`.CategoryChannel` to create this channel under. If not
            provided, it will be shown under the "Channels" header in the
            client (no category).
        public: :class:`bool`
            Whether this channel and its contents should be visible to people who aren't part of the server. Defaults to ``False``.
        group: :class:`.Group`
            The :class:`.Group` to create this channel in. If not provided, defaults to the base group.

        Returns
        --------
        :class:`.DocsChannel`
            The created channel.
        """

        channel = await self._create_channel(
            ChannelType.docs,
            name=name,
            topic=topic,
            public=public,
            category=category,
            group=group,
        )
        return channel

    async def create_forum_channel(
        self,
        name: str,
        *,
        topic: str = None,
        public: bool = None,
        category: ServerChannel = None,
        group: Group = None,
    ) -> ForumChannel:
        """|coro|

        Create a new forum channel in the server.

        Parameters
        -----------
        name: :class:`str`
            The channel's name. Can include spaces.
        topic: :class:`str`
            The channel's topic.
        category: :class:`.CategoryChannel`
            The :class:`.CategoryChannel` to create this channel under. If not
            provided, it will be shown under the "Channels" header in the
            client (no category).
        public: :class:`bool`
            Whether this channel and its contents should be visible to people who aren't part of the server. Defaults to ``False``.
        group: :class:`.Group`
            The :class:`.Group` to create this channel in. If not provided, defaults to the base group.

        Returns
        --------
        :class:`.ForumChannel`
            The created channel.
        """

        channel = await self._create_channel(
            ChannelType.forums,
            name=name,
            topic=topic,
            public=public,
            category=category,
            group=group,
        )
        return channel

    async def create_forum(
        self,
        name: str,
        *,
        topic: str = None,
        public: bool = None,
        category: ServerChannel = None,
        group: Group = None,
    ) -> ForumChannel:
        """|coro|

        |dpyattr|

        Create a new forum channel in the server.

        Parameters
        -----------
        name: :class:`str`
            The channel's name. Can include spaces.
        topic: :class:`str`
            The channel's topic.
        category: :class:`.CategoryChannel`
            The :class:`.CategoryChannel` to create this channel under. If not
            provided, it will be shown under the "Channels" header in the
            client (no category).
        public: :class:`bool`
            Whether this channel and its contents should be visible to people who aren't part of the server. Defaults to ``False``.
        group: :class:`.Group`
            The :class:`.Group` to create this channel in. If not provided, defaults to the base group.

        Returns
        --------
        :class:`.ForumChannel`
            The created channel.
        """

        return await self.create_forum_channel(
            name=name,
            topic=topic,
            public=public,
            category=category,
            group=group,
        )

    async def create_media_channel(
        self,
        name: str,
        *,
        topic: str = None,
        public: bool = None,
        category: ServerChannel = None,
        group: Group = None,
    ) -> MediaChannel:
        """|coro|

        Create a new media channel in the server.

        Parameters
        -----------
        name: :class:`str`
            The channel's name. Can include spaces.
        topic: :class:`str`
            The channel's topic.
        category: :class:`.CategoryChannel`
            The :class:`.CategoryChannel` to create this channel under. If not
            provided, it will be shown under the "Channels" header in the
            client (no category).
        public: :class:`bool`
            Whether this channel and its contents should be visible to people who aren't part of the server. Defaults to ``False``.
        group: :class:`.Group`
            The :class:`.Group` to create this channel in. If not provided, defaults to the base group.

        Returns
        --------
        :class:`.MediaChannel`
            The created channel.
        """

        channel = await self._create_channel(
            ChannelType.media,
            name=name,
            topic=topic,
            public=public,
            category=category,
            group=group,
        )
        return channel

    async def create_list_channel(
        self,
        name: str,
        *,
        topic: str = None,
        public: bool = None,
        category: ServerChannel = None,
        group: Group = None,
    ) -> ListChannel:
        """|coro|

        Create a new list channel in the server.

        Parameters
        -----------
        name: :class:`str`
            The channel's name. Can include spaces.
        topic: :class:`str`
            The channel's topic.
        category: :class:`.CategoryChannel`
            The :class:`.CategoryChannel` to create this channel under. If not
            provided, it will be shown under the "Channels" header in the
            client (no category).
        public: :class:`bool`
            Whether this channel and its contents should be visible to people who aren't part of the server. Defaults to ``False``.
        group: :class:`.Group`
            The :class:`.Group` to create this channel in. If not provided, defaults to the base group.

        Returns
        --------
        :class:`.ListChannel`
            The created channel.
        """

        channel = await self._create_channel(
            ChannelType.list,
            name=name,
            topic=topic,
            public=public,
            category=category,
            group=group,
        )
        return channel

    async def create_scheduling_channel(
        self,
        name: str,
        *,
        topic: str = None,
        public: bool = None,
        category: ServerChannel = None,
        group: Group = None,
    ) -> SchedulingChannel:
        """|coro|

        Create a new scheduling channel in the server.

        Parameters
        -----------
        name: :class:`str`
            The channel's name. Can include spaces.
        topic: :class:`str`
            The channel's topic.
        category: :class:`.CategoryChannel`
            The :class:`.CategoryChannel` to create this channel under. If not
            provided, it will be shown under the "Channels" header in the
            client (no category).
        public: :class:`bool`
            Whether this channel and its contents should be visible to people who aren't part of the server. Defaults to ``False``.
        group: :class:`.Group`
            The :class:`.Group` to create this channel in. If not provided, defaults to the base group.

        Returns
        --------
        :class:`.SchedulingChannel`
            The created channel.
        """

        channel = await self._create_channel(
            ChannelType.scheduling,
            name=name,
            topic=topic,
            public=public,
            category=category,
            group=group,
        )
        return channel

    async def create_voice_channel(
        self,
        name: str,
        *,
        topic: str = None,
        public: bool = None,
        category: ServerChannel = None,
        group: Group = None,
    ) -> VoiceChannel:
        """|coro|

        Create a new voice channel in the server.

        Parameters
        -----------
        name: :class:`str`
            The channel's name. Can include spaces.
        topic: :class:`str`
            The channel's topic.
        category: :class:`.CategoryChannel`
            The :class:`.CategoryChannel` to create this channel under. If not
            provided, it will be shown under the "Channels" header in the
            client (no category).
        public: :class:`bool`
            Whether this channel and its contents should be visible to people who aren't part of the server. Defaults to ``False``.
        group: :class:`.Group`
            The :class:`.Group` to create this channel in. If not provided, defaults to the base group.

        Returns
        --------
        :class:`.VoiceChannel`
            The created channel.
        """

        channel = await self._create_channel(
            ChannelType.voice,
            name=name,
            topic=topic,
            public=public,
            category=category,
            group=group,
        )
        return channel

    async def fetch_channel(self, channel_id: str, /) -> ServerChannel:
        """|coro|

        Fetch a channel.

        This method is an API call. For general usage, consider :meth:`.get_channel` instead.

        Returns
        --------
        :class:`~.abc.ServerChannel`
            The channel from the ID.

        Raises
        -------
        InvalidData
            The target channel does not belong to the current server.
        HTTPException
            Retrieving the channel failed.
        NotFound
            The channel to fetch does not exist.
        Forbidden
            You do not have permission to fetch this channel.
        """

        data = await self._state.get_channel(channel_id)
        if data['channel']['serverId'] != self.id:
            raise InvalidData('The target channel does not belong to the current server.')

        channel = self._state.create_channel(data=data['channel'], group=None, server=self)
        return channel

    async def getch_channel(self, channel_id: str, /) -> ServerChannel:
        return self.get_channel(channel_id) or await self.fetch_channel(channel_id)

    async def fetch_members(self) -> List[Member]:
        """|coro|

        Fetch the list of :class:`Member`\s in the server.

        Returns
        --------
        List[:class:`.Member`]
            The members in the server.
        """

        data = await self._state.get_members(self.id)
        data = data['members']

        member_list = []
        for member in data:
            try:
                member_obj = self._state.create_member(data=member, server=self)
            except:
                continue
            else:
                member_list.append(member_obj)

        return member_list

    async def fetch_member(self, user_id: str, /) -> Member:
        """|coro|

        Fetch a specific :class:`Member` in this server.

        Parameters
        -----------
        id: :class:`str`
            The member's ID to fetch.

        Returns
        --------
        :class:`Member`
            The member from their ID.

        Raises
        -------
        :class:`NotFound`
            A member with that ID does not exist in this server.
        """

        data = await self._state.get_member(self.id, user_id)
        member = self._state.create_member(data=data['member'], server=self)
        return member

    async def getch_member(self, user_id: str, /) -> Member:
        return self.get_member(user_id) or await self.fetch_member(user_id)

    async def fill_members(self) -> None:
        """Fill the member cache for this server.

        .. note::

            This is used internally and is generally not needed for most
            applications as member cache is created and discarded
            automatically throughout a connected client's lifetime.

        This method could be seen as analogous to `guild chunking <https://discord.com/developers/docs/topics/gateway#request-guild-members>`_, except that it uses HTTP and not the gateway.
        """

        data = await self._state.get_members(self.id)
        data = data['members']

        self._members.clear()
        for member_data in data:
            try:
                member = self._state.create_member(server=self, data=member_data)
            except:
                continue
            else:
                self._members[member.id] = member

    async def ban(
        self,
        user: User,
        *,
        reason: str = None,
    ) -> MemberBan:
        """|coro|

        Ban a user from the server.

        Parameters
        -----------
        user: :class:`abc.User`
            The user to ban.

        Returns
        --------
        :class:`.MemberBan`
            The ban that was created.
        """

        data = await self._state.ban_server_member(self.id, user.id, reason=reason)
        ban = MemberBan(state=self._state, data=data['serverMemberBan'], server=self)
        return ban

    async def unban(self, user: User):
        """|coro|

        Unban a user from the server.

        Parameters
        -----------
        user: :class:`abc.User`
            The user to unban.
        """
        await self._state.unban_server_member(self.id, user.id)

    async def bans(self) -> List[MemberBan]:
        """|coro|

        Get all bans that have been created in the server.

        Returns
        --------
        List[:class:`.MemberBan`]
            The list of bans in the server.
        """

        data = await self._state.get_server_bans(self.id)
        data = data['serverMemberBans']

        ban_list = []
        for ban_data in data:
            ban = MemberBan(state=self._state, data=ban_data, server=self)
            ban_list.append(ban)

        return ban_list

    async def kick(self, user: User):
        """|coro|

        Kick a user from the server.

        Parameters
        -----------
        user: :class:`abc.User`
            The user to kick.
        """
        await self._state.kick_member(self.id, user.id)

    async def create_webhook(
        self,
        name: str,
        *,
        channel: ServerChannel,
    ) -> Webhook:
        """|coro|

        Create a webhook in a channel.

        Parameters
        -----------
        name: :class:`str`
            The webhook's name.
        channel: Union[:class:`ChatChannel`, :class:`ListChannel`]
            The channel to create the webhook in.

        Raises
        -------
        HTTPException
            Creating the webhook failed.
        Forbidden
            You do not have permissions to create a webhook.

        Returns
        --------
        :class:`Webhook`
            The created webhook.
        """

        from .webhook import Webhook

        data = await self._state.create_webhook(
            self.id,
            name=name,
            channel_id=channel.id,
        )

        webhook = Webhook.from_state(data['webhook'], self._state)
        return webhook

    async def webhooks(self, *, channel: Optional[Union[ChatChannel, ListChannel]] = None) -> List[Webhook]:
        """|coro|

        Fetch the list of webhooks in this server.

        Parameters
        -----------
        channel: Optional[Union[:class:`.ChatChannel`, :class:`.ListChannel`]]
            The channel to fetch webhooks from.

            .. warning::

                If not specified, this method will make a request for every
                compatible channel in the server, which may be very slow.

        Returns
        --------
        List[:class:`.Webhook`]
            The webhooks in this server or, if specified, the channel.

        Raises
        -------
        Forbidden
            You do not have permission to get the webhooks.
        """

        if channel is not None:

            from .webhook import Webhook

            data = await self._state.get_server_webhooks(self.id, channel.id)
            webhooks = [
                Webhook.from_state(webhook_data, self._state)
                for webhook_data in data['webhooks']
            ]

        else:
            webhooks = []
            for channel in (self.chat_channels + self.list_channels):
                webhooks += await channel.webhooks()

        return webhooks

    async def fetch_default_channel(self) -> ServerChannel:
        """|coro|

        Fetch the default channel in this server.

        Returns
        --------
        :class:`~.abc.ServerChannel`
            The default channel.

        Raises
        -------
        ValueError
            This server has no default channel.
        """

        if not self.default_channel_id:
            raise ValueError('This server has no default channel.')

        return await self.fetch_channel(self.default_channel_id)

Guild = Server  # discord.py
