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

from guilded.abc import TeamChannel

from .asset import Asset
from .channel import ChatChannel, Thread
from .errors import NotFound
from .gateway import GuildedWebSocket
from .user import Member
from .utils import ISO8601


class SocialInfo:
    '''Represents the set social media connections for a :class:`Team`.'''
    def __init__(self, **fields):
        self.twitter = None
        self.facebook = None
        self.youtube = None
        self.twitch = None

        for social, name in fields.items():
            # set dynamically so as to futureproof new social 
            # media connections being available
            setattr(self, social, name)

class TeamTimezone(datetime.tzinfo):
    # todo, lol
    pass

class Team:
    '''Represents a team (or "server") in Guilded.'''
    def __init__(self, *, state, data, ws=None):
        self._state = state
        self.ws = ws
        data = data.get('team', data)

        self.id = data.get('id')
        self.owner_id = data.get('ownerId')
        self.name = data.get('name')
        self.subdomain = data.get('subdomain')
        self.created_at = ISO8601(data.get('createdAt'))
        self.bio = data.get('bio') or ''
        self.description = data.get('description') or ''
        self.discord_guild_id = data.get('discordGuildId')
        self.discord_guild_name = data.get('discordServerName')
        self.socials = SocialInfo(**data.get('socialInfo', {}))
        self.timezone = data.get('timezone') # TeamTimezone(data.get('timezone'))

        for member in data.get('members', []):
            self._state.add_to_member_cache(
                self._state._get_team_member(self.id, member.get('id')) or Member(state=self._state, data=member)
            )
        #self.members = data.get('members', [])
        self.bots = data.get('bots', [])
        self.channels = data.get('channels', [])

        self.recruiting = data.get('isRecruiting', False)
        self.verified = data.get('isVerified', False)
        self.public = data.get('isPublic', False)
        self.pro = data.get('isPro', False)
        self.user_is_applicant = data.get('isUserApplicant', False)
        self.user_is_invited = data.get('isUserInvited', False)
        self.user_is_banned = data.get('isUserBannedFromTeam', False)
        self.user_is_following = data.get('userFollowsTeam', False)

        self.icon_url = Asset('profilePicture', state=self._state, data=data)
        self.banner_url = Asset('homeBannerImage', state=self._state, data=data)

        self._follower_count = data.get('followerCount') or 0
        self._member_count = data.get('memberCount') or data.get('measurements', {}).get('numMembers') or 0

    def __str__(self):
        return self.name

    def __repr__(self):
        return f'<Team id={self.id} name={self.name}>'

    @property
    def slug(self):
        # it's not a subdomain >:(
        return self.subdomain

    @property
    def vanity_url(self):
        return f'https://guilded.gg/{self.subdomain}' if self.subdomain is not None else None

    @property
    def member_count(self):
        # this attribute is only returned by the api sometimes.
        return int(self._member_count) or len(self.members)

    @property
    def follower_count(self):
        return int(self._follower_count)

    @property
    def owner(self):
        return self.get_member(self.owner_id) or self._state._get_user(self.owner_id)

    @property
    def me(self):
        return self.get_member(self._state.my_id)

    @property
    def members(self):
        return list(self._state._team_members.get(self.id, {}).values())

    def get_member(self, id):
        return self._state._get_team_member(self.id, id)

    async def ws_connect(self, client):
        '''Connect to the team's websocket.'''
        if self.ws is None:
            team_ws_build = GuildedWebSocket.build(client, loop=client.loop, teamId=self.id)
            self.ws = await asyncio.wait_for(team_ws_build, timeout=60)

    async def delete(self):
        '''Delete the team. You must be the team owner to do this.'''
        return await self._state.delete_team(self.id)

    async def leave(self):
        '''Leave the team.'''
        return await self._state.leave_team(self.id)

    async def create_chat_channel(self, *, name: str, category=None, public=False, group=None):
        '''Create a new chat (text) channel in the team.

        Parameters
        ==========
        name
            the channel's name. can include spaces.
        category
            the :class:`TeamCategory` to create this channel under. if not provided, it will be created under the "Channels" header in the interface (no category).
        public
            whether or not this channel and its contents should be visible to people who aren't part of the server. defaults to false.
        group
            the :class:`Group` to create this channel in. if not provided, defaults to the base group.

        Returns
        =======
        :class:`ChatChannel`
        '''

        return await self._state.create_team_channel(
            type='chat',
            team_id=self.id, 
            group_id=group.id if group is not None else self.base_group.id,
            category_id=category.id if category is not None else None,
            name=name,
            public=public
        )

    async def fetch_channels(self):
        '''Fetch the list of :class:`TeamChannel`s in this team.'''
        channels = await self._state.get_team_channels(self.id)
        channel_list = []
        data = {'state': self._state, 'group': None, 'team': self}
        for channel in channels.get('channels', []):
            data = {**data, 'data': channel}
            try:
                if channel.get('contentType') == 'chat':
                    channel_obj = ChatChannel(**data)
                else:
                    channel_obj = TeamChannel(**data)
            except:
                continue
            else:
                channel_list.append(channel_obj)

        for channel in channels.get('temporalChannels', []):
            data = {**data, 'data': channel}
            try:
                channel_obj = Thread(**data)
            except:
                continue
            else:
                channel_list.append(channel_obj)

        #for channel in channels.get('categories', []):
        #    data = {**data, 'data': channel}
        #    try:
        #        channel_obj = ChannelCategory(**data)
        #    except:
        #        continue
        #    else:
        #        channel_list.append(channel_obj)

        return channel_list

    async def fetch_channel(self, id):
        channels = await self.fetch_channels()
        channel = next((channel for channel in channels if channel.id == id), None)
        if channel:
            return channel

        raise NotFound(f'Channel with the ID "{id}" not found.')

    async def fetch_members(self):
        '''Fetch the list of :class:Member s in this team.'''
        members = await self._state.get_team_members(self.id)
        member_list = []
        for member in members.get('members', members):
            try:
                member_obj = Member(state=self._state, data=member, team=self)
            except:
                continue
            else:
                member_list.append(member_obj)

        return member_list

    async def fetch_member(self, id: str):
        '''Fetch a specific :class:Member in this team. Guilded does not actually have an endpoint \
        for this, so it is no more efficient than performing :class:Team.fetch_members and filtering \
        the list yourself, and exists solely for convenience.'''
        members = await self._state.get_team_members(self.id)
        for member in members.get('members', members):
            if member['id'] == id:
                return Member(state=self._state, data=member)

        raise NotFound(f'Member with the ID "{id}" not found.')

    async def getch_member(self, id: str):
        return self.get_member(id) or await self.fetch_member(id)

    async def create_invite(self):
        '''Create an invite to this team.

        Returns
            :class:`str` - the invite code that was created
        '''
        invite = await self._state.create_team_invite(self.id)
        return invite.get('invite', invite).get('id')
