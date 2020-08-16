__title__ = 'guilded'
__author__ = 'shay'
__copyright__ = 'Copyright 2020 shay'
__version__ = '0.0.1'

import re
import json
import aiohttp
import asyncio
import datetime
import websockets
BASE   = 'https://api.guilded.gg/'
WS_URL = 'wss://api.guilded.gg/socket.io/?jwt=undefined&EIO=3&transport=websocket'

session = None
async def make_session():
    global session
    session = aiohttp.ClientSession()

def make_datetime(initial):
    # for dates formatted like 2020-07-28T22:28:01.151Z
    j1        = initial.split('T')
    j1_date   = j1[0].split('-')
    j1_time   = j1[1].split(':')
    j1_year   = int(j1_date[0])
    j1_month  = int(j1_date[1])
    j1_day    = int(j1_date[2])
    j1_hour   = int(j1_time[0])
    j1_minute = int(j1_time[1])
    j1_second = int(re.sub(r'\..+Z$', '', j1_time[2]))
    joinDate  = datetime.datetime(year=j1_year, month=j1_month, day=j1_day, hour=j1_hour, minute=j1_minute, second=j1_second)
    return joinDate

async def websocket_process(bot_instance, websocket):
    while True:
        latest = await websocket.recv()
        if latest.isdigit(): pass
        else:
            for char in latest:
                if char.isdigit(): latest = latest.replace(char, '', 1)
                else: break
            data = json.loads(latest)#[1]
            try: recv_type = data['type']
            except: pass
            else:
                if data['type'] == 'ChatMessageCreated':
                    message = Message(data)
                    await bot_instance.trigger_on_message(message=message)

class Bot:
    def __init__(self, command_prefix, **kwargs):
        self.command_prefix = command_prefix
        self.loop           = kwargs.get('loop', asyncio.get_event_loop())
        self.description    = kwargs.get('description', None)
        self.owner_id       = kwargs.get('owner_id')
        # To be assigned upon start
        self.user           = None # ClientUser object
        self.login_cookie   = None
        # Cache
        self.teams          = []
        self.team_groups    = []
        self.text_channels  = []
        self.channels       = []
        self.listeners      = []
        self.commands       = []

    # fetch from the api
    async def fetch_team(self, teamId):
        teamResponse = await session.get(BASE + 'teams/' + teamId)
        teamJson     = (await teamResponse.json())['team']
        return Team(**teamJson)

    # trigger events
    async def trigger_on_message(self, message):
        for f in self.listeners:
            if f.__name__ == 'on_message':
                await f.__call__(message)

        if message.content.startswith(self.command_prefix):
            if message.author.id !=  self.me.id:
                ctx = Context(message, data)
                pass

    async def trigger_on_ready(self):
        for f in self.listeners:
            if f.__name__ == 'on_ready':
                await f.__call__()

    # connection
    async def heartbeat(self, websocket):
        while True:
            try:
                await websocket.send('2')
            except:
                await self.connect(cookie=self.login_cookie)
                await websocket.send('2')
                await self.trigger_on_ready()
            await asyncio.sleep(25)

    async def connect(self, cookie: str):
        websocket = await websockets.connect(WS_URL, extra_headers=[('cookie', cookie)])
        return websocket

    async def login(self, email: str, password: str):
        if session == None: await make_session()
        loginResponse = await session.post(BASE + 'login', json={'email': email, 'password': password})
        responseJson  = (await loginResponse.json())['user']
        joinDate      = make_datetime(responseJson.pop('joinDate'))
        responseJson['joinDate'] = joinDate
        self.user = ClientUser(**responseJson)

        if not 'Set-Cookie' in loginResponse.headers:
            raise KeyError('Missing required information in the returned headers from Guilded. Check your credentials?')
        else:
            self.login_cookie = loginResponse.headers['Set-Cookie']

        return {'cookie': self.login_cookie, 'profile': self.user}

    async def async_run(self, email, password):
        login = await self.login(email=email, password=password)
        ws    = await self.connect(cookie=login['cookie'])
        await self.trigger_on_ready()
        self.loop.create_task(self.heartbeat(websocket=ws))
        self.loop.create_task(websocket_process(bot_instance=self, websocket=ws))

    def run(self, email: str, password: str):
        self.loop.create_task(self.async_run(email=email, password=password))
        self.loop.run_forever()

    # decorators
    def event(self, **kwargs):
        def inner_deco(func):
            return self.listeners.append(func)
        return inner_deco

    def command(self, **kwargs):
        def inner_deco(func):
            return self.commands.append(func)
        return inner_deco

class ClientUser:
    def __init__(self, *args, **kwargs):
        self.id               = kwargs.get('id')
        self.name             = kwargs.get('name')
        self.avatar_url       = kwargs.get('profilePicture')
        self.avatar_url_small = kwargs.get('profilePictureSm')
        self.avatar_url_large = kwargs.get('profilePictureLg')
        self.avatar_url_blur  = kwargs.get('profilePictureBlur')
        self.banner_url_blur  = kwargs.get('profileBannerBlur')
        self.banner_url_large = kwargs.get('profileBannerLg')
        self.joined_at        = kwargs.get('joinDate')
        self.steam            = kwargs.get('steamId')
        self.slug             = kwargs.get('subdomain')
        self.staffstatus      = kwargs.get('moderationstatus')
        self.info             = kwargs.get('aboutInfo')
        self.last_online      = kwargs.get('lastOnline')
        self.aliases          = kwargs.get('aliases')

class Converters:
    class MemberConverter:
        async def convert(self, ctx, to_convert):
            for member in ctx.team.members:
                if member.id == to_convert:
                    return member

class Team:
    def __init__(self, **kwargs):
        self.id                 = kwargs.get('id')
        self.type               = kwargs.get('type')
        self.created_at         = make_datetime(kwargs.get('createdAt'))
        self.owner_id           = kwargs.get('ownerId')
        self.name               = kwargs.get('name')
        self.slug               = kwargs.get('subdomain')
        self.icon_url           = kwargs.get('profilePicture')
        self.dash_image_url     = kwargs.get('teamDashImage')
        self.twitter            = kwargs['socialInfo'].get('twitter')
        self.facebook           = kwargs['socialInfo'].get('facebook')
        self.youtube            = kwargs['socialInfo'].get('youtube')
        self.twitch             = kwargs['socialInfo'].get('twitch')
        self.banner_url_small   = kwargs.get('homeBannerImageSm')
        self.banner_url_med     = kwargs.get('homeBannerImageMd')
        self.banner_url_large   = kwargs.get('homeBannerImageLg')
        self.timezone           = kwargs.get('timezone')
        self.description        = kwargs.get('description')
        self.recruiting         = kwargs.get('isRecruiting')
        self.verified           = kwargs.get('isVerified')
        self.public             = kwargs.get('isPublic')
        self.pro                = kwargs.get('isPro')
        self.sync_discord_roles = kwargs.get('autoSyncDiscordRoles')
        self.games              = kwargs.get('games')
        self.roles              = []
        for role in kwargs.get('roles'): self.roles.append(Role(**role))
        self.home_group         = TeamGroup(**kwargs.get('baseGroup'))
        self.members            = []
        for member in kwargs.get('members'): self.members.append(Member(**member))
        self.bots               = [] # :eyes:
        self.default_role       = Role(**kwargs['rolesById'].get('baseRole'))
        self.follower_count     = kwargs.get('followerCount')
        self.is_applicant       = kwargs.get('isUserApplicant') # is the bot an applicant
        self.is_following       = kwargs.get('userFollowsTeam') # is the bot following the team
        # bunch of weird stats stuff
        measurements                     = kwargs.get('measurements')
        self.member_count                = measurements.get('numMembers')
        self.recent_match_count          = measurements.get('numRecentMatches')
        self.follower_and_member_count   = measurements.get('numFollowersAndMembers')
        self.members_in_last_day_count   = measurements.get('numMembersAddedInLastDay')
        self.members_in_last_week_count  = measurements.get('numMembersAddedInLastWeek')
        self.members_in_last_month_count = measurements.get('numMembersAddedInLastMonth')
        self.latest_member_last_online   = datetime.datetime.utcfromtimestamp(measurements.get('mostRecentMemberLastOnline'))

class TeamGroup:
    def __init__(self, **kwargs):
        self.id             = kwargs.get('id')
        self.name           = kwargs.get('name')
        self.description    = kwargs.get('description')
        self.created_at     = make_datetime(kwargs.get('createdAt'))
        self.team           = kwargs.get('teamId')
        self.game           = kwargs.get('gameId')
        self.role_can_see   = kwargs.get('visibilityTeamRoleId')
        self.role_is_member = kwargs.get('membershipTeamRoleId')
        self.home           = kwargs.get('isBase')
        self.public         = kwargs.get('isPublic')

class Member:
    def __init__(self, **kwargs):
        self.id          = kwargs.get('id')
        self.name        = kwargs.get('name')
        self.nick        = kwargs.get('nickname')
        if self.nick == None: self.display_name = self.name
        else:                 self.display_name = self.nick
        self.xp          = kwargs.get('teamXp')
        self.last_online = make_datetime(kwargs.get('lastOnline'))
        self.joined_at   = make_datetime(kwargs.get('joinDate'))

class Role:
    def __init__(self, **kwargs):
        self.id                  = kwargs.get('id')     # an int :o
        self.name                = kwargs.get('name')
        self.color               = kwargs.get('color')  # hexval
        self.is_default          = kwargs.get('isBase') # is it the default member role (i think?)
        self.team                = kwargs.get('teamId')
        self.created_at          = make_datetime(kwargs.get('createdAt'))
        self.updated_at          = make_datetime(kwargs.get('updatedAt'))
        self.mentionable         = kwargs.get('isMentionable')
        self.discord_id          = kwargs.get('discordRoleId')
        self.self_assignable     = kwargs.get('isSelfAssignable')
        self.discord_last_synced = kwargs.get('discordSyncedAt')
        if self.discord_last_synced != None: self.discord_last_synced = make_datetime(self.discord_last_synced)

class TextChannel:
    def __init__(self, **kwargs):
        self.id         = kwargs.get('id')
        self.type       = kwargs.get('type')
        self.created_at = make_datetime(kwargs.get('createdAt'))
        self.updated_at = make_datetime(kwargs.get('updatedAt'))
        self.created_by = kwargs.get('createdBy')

class Message:
    def __init__(self, **kwargs):
        self.channel    = kwargs.get('channelId')
        self.team       = kwargs.get('teamId')
        self.created_at = make_datetime(kwargs.get('createdAt'))
        msg_dict        = kwargs.get('message')
        self.id         = msg_dict.get('id')
        self.author     = msg_dict.get('createdBy')
        self.content    = msg_dict['content']['nodes'][0]['nodes'][0]['leaves']['text']

class Context:
    def __init__(self, message, **kwargs):
        self.message = message
        self.author  = message.author
        self.channel = message.channel
        self.content = message.content
        self.team    = message.team

    async def send(self, content=None, embed=None, embeds=None):
        #await self.channel.send(content=content, embed=embed, embeds=embeds)
        pass