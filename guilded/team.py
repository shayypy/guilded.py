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

import asyncio
import datetime
from typing import Any, Dict, Optional, List, Union

from .abc import TeamChannel, User

from .asset import Asset
from .channel import ChannelType, ChatChannel, DocsChannel, ForumChannel, SchedulingChannel, Thread
from .errors import NotFound, InvalidArgument
from .emoji import Emoji
from .enums import try_enum, TeamFlairType
from .flowbot import FlowBot
from .gateway import UserbotGuildedWebSocket
from .group import Group
from .role import Role
from .user import Member
from .utils import ISO8601, get

__all__ = (
    'Guild',
    'Server',
    'SocialInfo',
    'Team',
    'TeamFlair',
)


class SocialInfo:
    """Represents the set social media connections for a :class:`Team`\.

    .. note::
        An instance of this class may have more attributes than listed below
        due to them being added dynamically using whatever the library
        receives from Guilded.

    Attributes
    -----------
    twitter: Optional[:class:`str`]
        The team's Twitter handle, including an ``@``\.
    facebook: Optional[:class:`str`]
        The team's Facebook page's name.
    youtube: Optional[:class:`str`]
        The full URL of the team's YouTube channel.
    twitch: Optional[:class:`str`]
        The full URL of the team's Twitch channel.
    """
    def __init__(self, **fields):
        self.twitter: Optional[str] = None
        self.facebook: Optional[str] = None
        self.youtube: Optional[str] = None
        self.twitch: Optional[str] = None

        for social, name in fields.items():
            # set dynamically so as to futureproof new social 
            # media connections being available
            setattr(self, social, name)


class TeamFlair:
    """Represents a flair on a :class:`.Team`\.

    Attributes
    -----------
    type: :class:`.TeamFlairType`
        The type of flair.
    amount: Optional[:class:`int`]
        For :attr:`.TeamFlairType.hot`, the number of members who joined the
        team in the last month.
    """

    def __init__(self, *, data: Dict[str, int]):
        self.type: TeamFlairType = try_enum(TeamFlairType, data['id'])
        self.amount: Optional[int] = data.get('amount')

    def __repr__(self) -> str:
        return f'<TeamFlair type={self.type!r} amount={self.amount!r}>'


class Team:
    """Represents a team (or "guild") in Guilded.

    This is usually referred to as a "server" in the client.

    There is an alias for this class called ``Guild``\.

    Attributes
    -----------
    id: :class:`str`
        The team's id.
    name: :class:`str`
        The team's name.
    owner_id: :class:`str`
        The team's owner's id.
    created_at: :class:`datetime.datetime`
        When the team was created.
    bio: :class:`str`
        The team's bio. Seems to be unused in favor of :attr:`.description`\.
    description: :class:`str`
        The team's "About" section.
    avatar: Optional[:class:`.Asset`]
        The team's set avatar, if any.
    banner: Optional[:class:`.Asset`]
        The team's banner, if any.
    social_info: :class:`SocialInfo`
        The team's linked social media pages.
    recruiting: :class:`bool`
        Whether the team's moderators are recruiting new members.
    verified: :class:`bool`
        Whether the team is verified.
    public: :class:`bool`
        Whether the team is public.
    pro: :class:`bool`
        Whether the team is "pro".
    user_is_applicant: :class:`bool`
        Whether the current user is an applicant to the team.
    user_is_invited: :class:`bool`
        Whether the current user has been invited to the team.
    user_is_banned: :class:`bool`
        Whether the current user is banned from the team.
    user_is_following: :class:`bool`
        Whether the current user is following the team.
    subdomain: Optional[:class:`str`]
        The team's "subdomain", or vanity code. Referred to as a "Server URL"
        in the client.
    discord_guild_id: Optional[:class:`str`]
        The id of the linked Discord guild.
    discord_guild_name: Optional[:class:`str`]
        The name of the linked Discord guild.
    base_group: Optional[:class:`Group`]
        The team's base or "home" group.
    """

    def __init__(self, *, state, data, ws=None):
        self._state = state
        data = data.get('team', data)

        if state.userbot:
            self.ws = ws

        self.id: str = data['id']

        self._channels = {}
        self._threads = {}
        self._groups = {}
        self._emojis = {}
        self._members = {}
        self._roles = {}
        self._flowbots = {}
        self._flairs = {}

        self._base_role: Optional[Role] = None
        self._bot_role: Optional[Role] = None

        self.owner_id: str = data.get('ownerId')
        self.name: str = data.get('name') or ''
        self.subdomain: str = data.get('subdomain')
        self.created_at: datetime.datetime = ISO8601(data.get('createdAt'))
        self.bio: str = data.get('bio') or ''
        self.description: str = data.get('description') or ''
        self.discord_guild_id: str = data.get('discordGuildId')
        self.discord_guild_name: str = data.get('discordServerName')

        for flair_data in data.get('flair') or []:
            flair = TeamFlair(data=flair_data)
            self._flairs[flair.type.value] = flair

        self.base_group: Optional[Group] = None
        for group_data in data.get('groups') or []:
            group = Group(state=self._state, team=self, data=group_data)
            self._groups[group_data['id']] = group
            if group.base:
                self.base_group: Group = group

        if self.base_group is None and data.get('baseGroup') is not None:
            self.base_group: Optional[Group] = Group(state=self._state, team=self, data=data['baseGroup'])
            self._groups[self.base_group.id] = self.base_group

        self.social_info: SocialInfo = SocialInfo(**data.get('socialInfo', {}))
        self.timezone = data.get('timezone')

        for member in data.get('members') or []:
            member['teamId'] = self.id
            self._members[member['id']] = self._state.create_member(data=member, team=self)

        for channel in data.get('channels') or []:
            channel = (
                self._state._get_team_channel(self.id, channel['id'])
                or self._state.create_channel(data=channel)
            )
            if channel and channel.type is ChannelType.thread:
                self._threads[channel.id] = channel
            elif channel:
                self._channels[channel.id] = channel

        for bot in data.get('bots', []) or data.get('webhooks', []):
            if bot.get('flows') is not None:
                # Update member to bot if found within flowbots
                member = self.get_member(bot.get('userId', ''))
                if member:
                    member._bot = True
                bot = FlowBot(state=self._state, data=bot, team=self)
                self._flowbots[bot.id] = bot

        for role_id, role in data.get('rolesById', {}).items():
            if role_id.isdigit():
                # "baseRole" is included in rolesById, resulting in a
                # duplicate entry for the base role.
                role: Role = Role(state=self._state, data=role, team=self)
                self._roles[role.id] = role
                if role.base:
                    self._base_role: Optional[Role] = role
                if role.bot:
                    self._bot_role: Optional[Role] = role

        self.recruiting: bool = data.get('isRecruiting', False)
        self.verified: bool = data.get('isVerified', False)
        self.public: bool = data.get('isPublic', False)
        self.pro: bool = data.get('isPro', False)
        self.user_is_applicant: bool = data.get('isUserApplicant', False)
        self.user_is_invited: bool = data.get('isUserInvited', False)
        self.user_is_banned: bool = data.get('isUserBannedFromTeam', False)
        self.user_is_following: bool = data.get('userFollowsTeam', False)

        avatar = None
        if data.get('profilePicture'):
            avatar = Asset._from_team_avatar(state, data.get('profilePicture'))
        self.avatar: Optional[Asset] = avatar

        banner = None
        if data.get('teamDashImage'):
            banner = Asset._from_team_banner(state, data.get('teamDashImage'))
        self.banner: Optional[Asset] = banner

        self._follower_count = data.get('followerCount') or 0
        self._member_count = data.get('memberCount') or data.get('measurements', {}).get('numMembers') or 0

    def __str__(self):
        return self.name

    def __repr__(self):
        return f'<Team id={self.id!r} name={self.name!r}>'

    @property
    def slug(self) -> Optional[str]:
        """Optional[:class:`str`]: This is an alias of :attr:`.subdomain`."""
        return self.subdomain

    @property
    def vanity_url(self) -> Optional[str]:
        """Optional[:class:`str`]: The team's vanity URL."""
        return f'https://guilded.gg/{self.subdomain}' if self.subdomain is not None else None

    @property
    def member_count(self) -> int:
        """:class:`int`: The team's member count.

        .. note::
            This may be inaccurate; it does not update during the bot's
            lifetime unless the team is re-fetched and the attribute is
            replaced.
        """
        # this attribute is only returned by the api sometimes.
        return int(self._member_count) or len(self.members)

    @property
    def follower_count(self) -> int:
        """:class:`int`: The team's follower count.

        .. note::
            This may be inaccurate; it does not update during the bot's
            lifetime unless the team is re-fetched and the attribute is
            replaced.
        """
        return int(self._follower_count)

    @property
    def owner(self) -> Member:
        """Optional[Union[:class:`.Member`, :class:`User`]]: This team's
        owner, if they are cached."""
        return self.get_member(self.owner_id) or self._state._get_user(self.owner_id)

    @property
    def me(self) -> Optional[Member]:
        """Optional[:class:`.Member`]: Your own member object in this team."""
        return self.get_member(self._state.my_id)

    @property
    def members(self) -> List[Member]:
        """List[:class:`.Member`]: The cached list of members in this team.

        .. note::
            Many objects may not have all the desired information due to
            partial data returned by Guilded for some endpoints.
        """
        return list(self._members.values())

    @property
    def channels(self) -> TeamChannel:
        """List[:class:`~.abc.TeamChannel`]: The cached list of channels
        in this team."""
        return list(self._channels.values())

    @property
    def groups(self) -> List[Group]:
        """List[:class:`.Group`]: The cached list of groups in this team."""
        return list(self._groups.values())

    @property
    def emojis(self) -> List[Emoji]:
        """List[:class:`.Emoji`]: The cached list of emojis in this team."""
        return list(self._emojis.values())

    @property
    def flowbots(self) -> List[FlowBot]:
        """List[:class:`.FlowBot`]: The cached list of flowbots in this team."""
        return list(self._flowbots.values())

    @property
    def roles(self) -> List[Role]:
        """List[:class:`.Role`]: The cached list of roles in this team."""
        return list(self._roles.values())

    @property
    def base_role(self) -> Optional[Role]:
        """Optional[:class:`.Role`]: The base ``Member`` role for this team."""
        return self._base_role or get(self.roles, base=True)

    @property
    def bot_role(self) -> Optional[Role]:
        """Optional[:class:`.Role`]: The ``Bot`` role for this team."""
        return self._bot_role or get(self.roles, bot=True)

    @property
    def flairs(self) -> List[TeamFlair]:
        """List[:class:`.TeamFlair`]: The cached list of flairs that this team has."""
        return list(self._flairs.values())

    @property
    def icon(self) -> Optional[Asset]:
        """|dpyattr|

        This is an alias of :attr:`.avatar`.

        Returns
        --------
        Optional[:class:`.Asset`]
        """
        return self.avatar

    def get_member(self, id: str) -> Optional[Member]:
        """Optional[:class:`.Member`]: Get a member by their ID from the
        internal cache."""
        return self._members.get(id)

    def get_channel(self, id: str) -> Optional[TeamChannel]:
        """Optional[:class:`~.abc.TeamChannel`]: Get a channel by its ID
        from the internal cache."""
        return self._channels.get(id)

    def get_thread(self, id: str) -> Optional[Thread]:
        """Optional[:class:`.Thread`]: Get a thread by its ID
        from the internal cache."""
        return self._threads.get(id)

    def get_channel_or_thread(self, id: str) -> Optional[Union[TeamChannel, Thread]]:
        """Optional[Union[:class:`~.abc.TeamChannel`, :class:`.Thread`]]: Get
        a channel or thread by its ID from the internal cache."""
        return self.get_channel(id) or self.get_thread(id)

    def get_emoji(self, id: int) -> Optional[Emoji]:
        """Optional[:class:`.Emoji`]: Get an emoji by its ID from the internal
        cache."""
        return self._emojis.get(id)

    def get_flowbot(self, id: str) -> Optional[FlowBot]:
        """Optional[:class:`.FlowBot`]: Get a flowbot by its ID from the
        internal cache."""
        return self._flowbots.get(id)

    @property
    def get_bot(self) -> Optional[FlowBot]:
        return self.get_flowbot

    def get_role(self, id: int) -> Optional[Role]:
        """Optional[:class:`.Role`]: Get a role by its ID from the internal
        cache."""
        return self._roles.get(id)

    async def ws_connect(self, client):
        """|coro|

        |onlyuserbot|

        Connect to the team's gateway.

        .. warning::
            This method does not start listening to the websocket, so you
            shouldn't call it yourself.
        """
        if self.ws is None:
            team_ws_build = UserbotGuildedWebSocket.build(client, loop=client.loop, teamId=self.id)
            self.ws = await asyncio.wait_for(team_ws_build, timeout=60)

    async def delete(self):
        """|coro|

        |onlyuserbot|

        Delete the team. You must be the team owner to do this.
        """
        return await self._state.delete_team(self.id)

    async def leave(self):
        """|coro|

        |onlyuserbot|

        Leave the team.
        """
        return await self._state.leave_team(self.id)

    async def create_chat_channel(self, *, name: str, category=None, public=False, group=None) -> ChatChannel:
        """|coro|

        |onlyuserbot|

        Create a new chat (text) channel in the team.

        Parameters
        -----------
        name: :class:`str`
            The channel's name. Can include spaces.
        category: :class:`TeamCategory`
            The :class:`TeamCategory` to create this channel under. If not
            provided, it will be shown under the "Channels" header in the
            client (no category).
        public: :class:`bool`
            Whether this channel and its contents should be visible to people who aren't part of the server. Defaults to ``False``.
        group: :class:`Group`
            The :class:`Group` to create this channel in. If not provided, defaults to the base group.

        Returns
        --------
        :class:`ChatChannel`
            The created channel.
        """
        group = group or self.base_group
        data = await self._state.create_team_channel(
            content_type=ChannelType.chat.value,
            name=name,
            public=public,
            team_id=self.id,
            group_id=group.id,
            category_id=category.id if category is not None else None,
        )
        channel = self._state.create_channel(data=data['channel'], group=group, team=self)
        self._state.add_to_team_channel_cache(channel)
        return channel

    async def create_forum_channel(self, *, name: str, category=None, public=False, group=None) -> ForumChannel:
        """|coro|

        |onlyuserbot|

        Create a new forum channel in the team.

        Parameters
        -----------
        name: :class:`str`
            The channel's name. Can include spaces.
        category: :class:`TeamCategory`
            The :class:`TeamCategory` to create this channel under. If not
            provided, it will be shown under the "Channels" header in the
            client (no category).
        public: :class:`bool`
            Whether this channel and its contents should be visible to people who aren't part of the server. Defaults to ``False``.
        group: :class:`Group`
            The :class:`Group` to create this channel in. If not provided, defaults to the base group.

        Returns
        --------
        :class:`ForumChannel`
            The created channel.
        """
        group = group or self.base_group
        data = await self._state.create_team_channel(
            content_type=ChannelType.forum.value,
            name=name,
            public=public,
            team_id=self.id,
            group_id=group.id,
            category_id=category.id if category is not None else None,
        )
        channel = self._state.create_channel(data=data['channel'], group=group, team=self)
        self._state.add_to_team_channel_cache(channel)
        return channel

    async def create_docs_channel(self, *, name: str, category=None, public=False, group=None) -> DocsChannel:
        """|coro|

        |onlyuserbot|

        Create a new docs channel in the team.

        Parameters
        -----------
        name: :class:`str`
            The channel's name. Can include spaces.
        category: :class:`TeamCategory`
            The :class:`TeamCategory` to create this channel under. If not
            provided, it will be shown under the "Channels" header in the
            client (no category).
        public: :class:`bool`
            Whether this channel and its contents should be visible to people who aren't part of the server. Defaults to ``False``.
        group: :class:`Group`
            The :class:`Group` to create this channel in. If not provided, defaults to the base group.

        Returns
        --------
        :class:`DocsChannel`
            The created channel.
        """
        group = group or self.base_group
        data = await self._state.create_team_channel(
            content_type=ChannelType.docs.value,
            name=name,
            public=public,
            team_id=self.id,
            group_id=group.id,
            category_id=category.id if category is not None else None,
        )
        channel = self._state.create_channel(data=data['channel'], group=group, team=self)
        self._state.add_to_team_channel_cache(channel)
        return channel

    async def create_scheduling_channel(self, *, name: str, category=None, public=False, group=None) -> SchedulingChannel:
        """|coro|

        |onlyuserbot|

        Create a new scheduling channel in the team.

        Parameters
        -----------
        name: :class:`str`
            The channel's name. Can include spaces.
        category: :class:`TeamCategory`
            The :class:`TeamCategory` to create this channel under. If not
            provided, it will be shown under the "Channels" header in the
            client (no category).
        public: :class:`bool`
            Whether this channel and its contents should be visible to people who aren't part of the server. Defaults to ``False``.
        group: :class:`Group`
            The :class:`Group` to create this channel in. If not provided, defaults to the base group.

        Returns
        --------
        :class:`.SchedulingChannel`
            The created channel.
        """
        group = group or self.base_group
        data = await self._state.create_team_channel(
            content_type=ChannelType.scheduling.value,
            name=name,
            public=public,
            team_id=self.id,
            group_id=group.id,
            category_id=category.id if category is not None else None,
        )
        channel = self._state.create_channel(data=data['channel'], group=group, team=self)
        self._state.add_to_team_channel_cache(channel)
        return channel

    async def fetch_channels(self) -> List[TeamChannel]:
        """|coro|

        |onlyuserbot|

        Fetch the list of :class:`TeamChannel`\s in this team.

        This method is an API call. For general usage, consider
        :attr:`channels` instead.
        """
        channels = await self._state.get_team_channels(self.id)
        channel_list = []
        for channel_data in channels.get('channels', []):
            channel_data = channel_data.get('channel', channel_data)
            channel_data['type'] = 'team'
            channel = self._state.create_channel(data=channel_data, group=None, team=self)
            channel_list.append(channel)

        #for thread_data in channels.get('temporalChannels', []):
        #    channel = self._state.create_channel(data=thread_data)
        #    channel_list.append(channel_obj)

        #for channel in channels.get('categories', []):
        #    data = {**data, 'data': channel}
        #    try:
        #        channel_obj = ChannelCategory(**data)
        #    except:
        #        continue
        #    else:
        #        channel_list.append(channel_obj)

        return channel_list

    async def fetch_channel(self, id) -> TeamChannel:
        """|coro|

        Fetch a channel.

        This method is an API call. For general usage, consider
        :meth:`get_channel` instead.

        .. warning::
            If this is an early access bot, this method will only work for
            public channels.

        .. note::
            The channel does not have to be part of the current team because
            there is no team-specific "get channel" endpoint. Therefore,
            guilded.py will not raise any explicit indication that you have
            fetched a channel not part of the current team.
        """
        request = self._state.get_channel(id)
        data = await request
        data = data.get('channel', data)
        data['type'] = 'team'
        channel = self._state.create_channel(data=data['metadata']['channel'], group=None, team=self)
        return channel

    async def getch_channel(self, id) -> TeamChannel:
        return self.get_channel(id) or await self.fetch_channel(id)

    async def fetch_members(self) -> List[Member]:
        """|coro|

        Fetch the list of :class:`Member`\s in this team.
        """
        data = await self._state.get_team(self.id)
        member_list = []
        for member in data['team']['members']:
            try:
                member_obj = self._state.create_member(team=self, data=member)
            except:
                continue
            else:
                member_list.append(member_obj)

        return member_list

    async def fetch_member(self, id: str, *, full=True) -> Member:
        """|coro|

        |onlyuserbot|

        Fetch a specific :class:`Member` in this team.

        Parameters
        -----------
        id: :class:`str`
            The member's id to fetch.
        full: Optional[:class:`bool`]
            Whether to fetch full user data for this member. If this is
            ``False``, only team-specific data about this member will be
            returned. Defaults to ``True``.

            .. note::
                When this is ``True``, this method will make two HTTP requests.
                If the extra information returned by doing this is not necessary
                for your use-case, it is recommended to set it to ``False``.

        Returns
        --------
        :class:`Member`
            The member from their ID.

        Raises
        -------
        :class:`NotFound`
            A member with that ID does not exist in this team.
        """
        data = (await self._state.get_team_member(self.id, id))[id]
        if full is True:
            user_data = await self._state.get_user(id)
            user_data['user']['createdAt'] = user_data['user'].get('createdAt', user_data['user'].get('joinDate'))
            data = {**user_data, **data}

        member = self._state.create_member(team=self, data=data)
        self._state.add_to_member_cache(member)
        return member

    async def getch_member(self, id: str) -> Member:
        return self.get_member(id) or await self.fetch_member(id)

    async def create_invite(self) -> str:
        """|coro|

        |onlyuserbot|

        Create an invite to this team.

        Returns
        --------
        :class:`str`
            The invite code that was created.
        """
        invite = await self._state.create_team_invite(self.id)
        return invite.get('invite', invite).get('id')
    
    async def ban(self, user: User, *,
        reason: str = None,
        delete_after: datetime.datetime = None,
        delete_message_days: int = None
    ):
        """|coro|

        |onlyuserbot|

        Ban a user from the team.

        Parameters
        -----------
        user: :class:`abc.User`
            The user to ban.
        reason: Optional[:class:`str`]
            The reason to ban this user with. Shows up in the "bans" menu,
            but not the audit log.
        delete_after: Optional[:class:`datetime.datetime`]
            The :class:`datetime.datetime` to start wiping the user's message
            history from. If not specified, deletes no message history.
        delete_message_days: Optional[:class:`int`]
            How many days of the user's message history to wipe. This
            parameter mainly exists for convenience; interally this is
            converted into a :class:`datetime.datetime` and that is used
            instead. If not specified, deletes no message history.

        Raises
        -------
        InvalidArgument
            You specified both ``delete_message_days`` and ``delete_after``
        """
        if delete_message_days is not None and delete_after is not None:
            raise InvalidArgument('Specify delete_message_days or delete_after, not both.')

        if delete_message_days is not None:
            now = datetime.datetime.now(datetime.timezone.utc)
            diff = now - datetime.timedelta(days=delete_message_days)
            delete_after = diff
        
        coro = self._state.create_team_ban(self.id, user.id, reason=reason, after=delete_after)
        await coro

    async def unban(self, user: User):
        """|coro|

        |onlyuserbot|

        Unban a user from the team.

        Parameters
        -----------
        user: :class:`abc.User`
            The user to unban.
        """
        coro = self._state.remove_team_ban(self.id, user.id)
        await coro

    async def kick(self, user: User):
        """|coro|

        |onlyuserbot|

        Kick a user from the team.

        Parameters
        -----------
        user: :class:`abc.User`
            The user to kick.
        """
        coro = self._state.remove_team_member(self.id, user.id)
        await coro

    def get_group(self, id: str) -> Optional[Group]:
        """|onlyuserbot|

        Get a group by its ID from the internal cache.

        Returns
        --------
        Optional[:class:`Group`]
        """
        return self._groups.get(id)

    async def fetch_group(self, id: str) -> Group:
        """|coro|

        |onlyuserbot|

        Fetch a :class:`Group` in this team by its ID.

        Parameters
        -----------
        id: :class:`str`
            The group's id to fetch.
        """
        data = await self._state.get_team_group(self.id, id)
        group = Group(state=self._state, team=self, data=data)
        return group

    async def fetch_groups(self) -> List[Group]:
        """|coro|

        |onlyuserbot|

        Fetch the list of :class:`Group`\s in this team.

        Some groups may not be returned due to inadequate permissions. There
        is no real way to know if this has happened.
        """
        data = await self._state.get_team_groups(self.id)
        groups = []
        for group_data in data.get('groups', data):
            group = Group(state=self._state, team=self, data=group_data)
            groups.append(group)

        return groups

    async def fetch_emojis(self, *,
        limit: int = None,
        search: str = None,
        created_by: User = None,
        when_upper: datetime.datetime = None,
        when_lower: datetime.datetime = None,
        created_before: Emoji = None
    ) -> List[Emoji]:
        """|coro|

        |onlyuserbot|

        Fetch the list of :class:`Emoji`\s in this team.

        All parameters are optional.

        Parameters
        -----------
        limit: :class:`int`
            The maximum number of emojis to return.
        search: :class:`str`
            Filter by a search term, matching emoji names.
        created_by: :class:`~.abc.User`
            Filter by a user, matching emoji authors.
        when_upper: :class:`datetime.datetime`
            Filter by an upper limit (later datetime), matching emoji creation
            date.
        when_lower: :class:`datetime.datetime`
            Filter by a lower limit (earlier datetime), matching emoji creation
            date.
        created_before: :class:`Emoji`
            Filter by a timeframe, matching emojis created before this emoji.
            This is likely intended to be used for pagination by the client.
        """
        data = await self._state.get_team_emojis(
            self.id,
            limit=limit,
            search=search,
            created_by=created_by,
            when_upper=when_upper,
            when_lower=when_lower,
            created_before=created_before
        )
        emojis = []
        for emoji_data in data:
            emoji = Emoji(team=self, data=emoji_data, state=self._state)
            emojis.append(emoji)

        return emojis

Guild = Team  # discord.py
Server = Team  # bot API
