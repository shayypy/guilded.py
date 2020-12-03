# For ABCs
import abc

# Socket event parsing
import re
import json
import typing
import inspect
import argparse
import traceback

# Messaging
import uuid
import datetime

# Networking
import aiohttp
import asyncio
import websockets

# From Guilded.py
from .errors import *
from .http   import *


BASE   = 'https://api.guilded.gg/'
WS_URL = 'wss://api.guilded.gg/socket.io/?{args}jwt=undefined&EIO=3&' \
         'transport=websocket'

class internal:
    def __init__(self):
        self.ping    = 25  # default interval
        self.session = None
        self.bot     = None
internal = internal()

async def make_session():
    internal.session = aiohttp.ClientSession()

def iso8601_dt(initial: str):
    # for dates formatted like 2020-07-28T22:28:01.151Z
    #                          yyyy-mm-ssThh:mm:ss.mlsZ
    try:
        return datetime.datetime.strptime(
            str(initial), "%Y-%m-%dT%H:%M:%S.%fZ"
        )
    except ValueError:
        return datetime.datetime(1970, 1, 1)

class Akwargs:
    grammar = r'"[\w\s_]+"|"[\w\s,_"]+"|\d+|[a-zA-Z0-9_]+|\='
    def __init__(self, tokens):
        self.tokens = tokens
        self.args = []
        self.kwargs = {}
        self.parse()

    def parse(self):
        current = next(self.tokens, None)
        if current:
            check_next = next(self.tokens, None)
            if not check_next:
                self.args.append(re.sub('^"+|"+$', '', current))
            else:
                if check_next == '=':
                    last = next(self.tokens, None)
                    if not last:
                        raise ValueError("Expecting kwargs key")
                    self.kwargs[current] = re.sub('^"|"$', '', last)
                else:
                    self.args.extend(list(map(lambda x:re.sub('^"+|"+$', '', x), [current, check_next])))
            self.parse()

class Bot:
    def __init__(self, command_prefix, **kwargs):
        # ""Settings""
        self.command_prefix = command_prefix
        self.loop           = kwargs.get('loop', asyncio.get_event_loop())
        self.description    = kwargs.get('description', None)
        self.owner_id       = kwargs.get('owner_id')
        # To be assigned upon start
        self.user           = None  # ClientUser object
        self.login_cookie   = None
        ## Internal
        self.listeners      = []
        self.commands       = []
        # Cache
        self.teams          = []
        self.team_groups    = []
        self.text_channels  = []
        self.channels       = []
        self.users          = []

    # grab from cache
    def get_team(self, teamId):
        team = None
        for t in self.teams:
            if t.id == teamId:
                team = t
                break
        return team

    def get_user(self, userId):
        user = None
        for u in self.users:
            if u.id == userId:
                user = t
                break
        return user

    def get_channel(self, channelId):
        channel = None
        for c in self.channels:
            if c.id == channelId:
                channel = c
                break
        return channel

    # fetch from the api
    async def fetch_team(self, teamId):
        try:
            teamResponse = await internal.session.get(BASE + 'teams/' + teamId)
            teamJson     = (await teamResponse.json())['team']
            team         = Team(**teamJson)
            team_ws      = None
            if not [tt for tt in self.teams if tt.id == team.id]:
                # dont want multiple websocket connections, so 
                # check for if the team is already cached (and thus 
                # a websocket is already open)
                team_ws = await self.team_connect(team.id)
                self.loop.create_task(self.team_websocket_process(
                    team_ws, team.id
                ))
                self.loop.create_task(self.team_heartbeat(
                    team_ws, team.id
                ))
            for t in self.teams:
                if t.id == team.id:
                    self.teams.remove(t)
            self.teams.append(team)
            chanResponse = await internal.session.get(
                BASE + 'teams/' + teamId + '/channels'
            )
            chanJson     = (await chanResponse.json())['channels']
            for c in chanJson:
                channel = TextChannel(**c)
                if channel not in self.channels:
                    self.channels.append(channel)
                if channel not in self.text_channels:
                    self.text_channels.append(channel)
            return team
        except:
            traceback.print_exc()

    async def fetch_channel(self, channelId):
        try:
            channelResponse = await internal.session.get(
                BASE + 'channels/' + channelId
            )
            channelJson     = (await channelResponse.json())['channel']
            channel         = TextChannel(**channelJson)
            for c in self.channels:
                if c.id == channel.id:
                    self.channels.remove(c)
            self.channels.append(channel)
            return channel
        except:
            traceback.print_exc()

    async def fetch_user(self, userId):
        userResponse = await internal.session.get(BASE + 'users/' + userId)
        userJson     = (await userResponse.json())['user']
        user         = User(**userJson)
        for u in self.users:
            if u.id == user.id:
                self.users.remove(u)
        self.users.append(user)
        return user

    # on_ready event, obv
    async def trigger_on_ready(self):
        for f in self.listeners:
            if f.__name__ == 'on_ready':
                await f.__call__()

    # team connections
    async def team_connect(self, team_id):
        team_websocket = await websockets.connect(
            WS_URL.format(args='teamId={}'.format(team_id)),
            extra_headers=[('cookie', self.login_cookie)])
        await team_websocket.send('2')
        return team_websocket

    async def team_heartbeat(self, websocket, team_id):
        while True:
            await asyncio.sleep(25)
            try:
                await websocket.send('2')
            except:
                await self.team_connect(team_id=team_id)

    async def team_websocket_process(self, websocket, team_id):
        '''A team websocket connection'''
        while True:
            try:
                latest = await websocket.recv()
            except:
                websocket = await self.team_connect(team_id=team_id)
            await self.global_websocket_processor(latest)

    # connection
    async def heartbeat(self, websocket):
        while True:
            await asyncio.sleep(25)
            try:
                await websocket.send('2')
            except:
                await self.connect(cookie=self.login_cookie)

    async def websocket_process(self, websocket):
        '''Main websocket connection'''
        while True:
            try:
                latest = await websocket.recv()
            except:
                websocket = await self.connect(cookie=self.login_cookie)
            await self.global_websocket_processor(latest)

    async def global_websocket_processor(self, ws_data):
        '''Process input from the global websocket and various team websockets'''
        # event functions
        async def ChatMessageCreated(data):
            mdata           = data['message']
            teamId          = data.get('teamId', mdata.get('teamId', None))
            if teamId:
                mdata['team']  = await self.fetch_team(teamId)
            else:
                mdata['team']  = None
            mdata['author']    = await self.fetch_user(data['createdBy'])
            mdata['channelId'] = data['channelId']
            message = Message(**mdata)

            # on_message event
            onmsg_events = [
                onm for onm in self.listeners if \
                onm.__name__ == 'on_message'
            ]
            for onm_ in onmsg_events: await onm_.__call__(message)

            # commands
            if not message.content:
                return
            if not message.content.startswith(self.command_prefix):
                return
            if not (message.author.id != self.user.id or \
                    message.author.id == self.owner_id):
                return
            # ignore self, but if owner is self,
            # do not ignore self. will add selfbot
            # arg in the future

            data['message'] = message
            ctx = Context(**data)
            ctx.invoked_with = (
                message.content.replace(
                    self.command_prefix, '', 1
                ).split(' '))[0]
            find_args = message.content.replace(
                f'{self.command_prefix}' \
                f'{ctx.invoked_with}', 
                '', 1
            )
            use_args = []
            if find_args:
                tokens   = iter(re.findall(Akwargs.grammar, find_args))
                params   = Akwargs(tokens)
                use_args = params.args

            for c in self.commands:
                if c.__name__ == ctx.invoked_with:
                    ctx.arguments = [ctx, *use_args]

                    argspec   = inspect.getfullargspec(c)
                    func_args = argspec.args

                    while len(func_args) < len(ctx.arguments):
                        del ctx.arguments[-1]
                    await c(*ctx.arguments)

        async def ChatChannelTyping(data):
            # start typing (there is no end typing event)
            data['typer']     = await self.fetch_user(data['userId'])
            event_begintyping = [
                l for l in self.listeners if l.__name__ == 'on_typing'
            ]
            for type_ev in event_begintyping:
                try:    await type_ev.__call__(
                    data['channelId'], 
                    data['typer'], 
                    datetime.datetime.utcnow()
                )
                except: traceback.print_exc()

        async def ChatMessageDeleted(data):
            # delete
            data['team']    = await self.fetch_team(data['teamId'])
            data['id']      = data['message']['id']
            #data['author'] = await self.fetch_user(data['createdBy'])
            # not available, see:
            # https://www.guilded.gg/guilded-api/groups/l3GmAe9d/
            # channels/1688bafa-9ecb-498e-9f6d-313c1cdc7150/docs/729851648
            mdata   = data['message']
            message = Message(**mdata)
            event_delmessage = [
                l for l in self.listeners if \
                l.__name__ == 'on_message_delete'
            ]
            for delmsg_ev in event_delmessage:
                try:    await delmsg_ev.__call__(message)
                except: traceback.print_exc()

        async def ChatPinnedMessageCreated(data):
            # pin
            data['team']   = await self.fetch_team(data['teamId'])
            data['id']     = data['message']['id']
            data['author'] = await self.fetch_user(data['updatedBy'])
            mdata          = data['message']
            message        = Message(**mdata)
            event_pinmsg   = [
                l for l in self.listeners if \
                l.__name__ == 'on_pins_add'
            ]
            for pinmsg_ev in event_pinmsg:
                try:    await pinmsg_ev.__call__(
                    message, data['author']
                ) # message, who_pinned
                except: traceback.print_exc()

        async def ChatPinnedMessageDeleted(data):
            # unpin
            data['team']   = await self.fetch_team(data['teamId'])
            data['id']     = data['message']['id']
            data['author'] = await self.fetch_user(data['updatedBy'])
            mdata          = data['message']
            message        = Message(**mdata)
            event_pinmsg   = [
                l for l in self.listeners if \
                l.__name__ == 'on_pins_remove' or \
                l.__name__ == 'on_unpin'
            ]
            for pinmsg_ev in event_pinmsg:
                try:    await pinmsg_ev.__call__(
                    message, data['author']
                ) # message, who_unpinned
                except: traceback.print_exc()

        async def ChatMessageUpdated(data):
            # edited
            data['team']   = await self.fetch_team(data['teamId'])
            data['author'] = await self.fetch_user(data['updatedBy'])
            mdata          = data['message']
            message        = Message(**mdata)
            onmsg_events   = [
                l for l in self.listeners if \
                l.__name__ == 'on_message_edit'
            ]
            for edit_ev in onmsg_events: 
                # seems like guilded doesnt give you the 
                # previous version :/ 
                # may have to cache messages for that
                try:    await edit_ev.__call__(message)
                except: traceback.print_exc()

        # processor
        dd = [
            dbl for dbl in self.listeners if 
            dbl.__name__ == 'on_socket_raw_receive'
        ]
        try:
            for dbl in dd: await dbl.__call__(ws_data)
        except: 
            traceback.print_exc()

        if ws_data.isdigit(): pass
        else:
            for char in ws_data:
                if char.isdigit(): ws_data = ws_data.replace(char, '', 1)
                else: break
            data = json.loads(ws_data)
            #try:
            #    if 'pingInterval' in data.keys():
            #        internal.pinginterval = data['pingInterval'] * 1000
            #except AttributeError:
            #    pass
            try: recv_type = data[0]
            except: pass
            else:
                data = data[1]
                ddd = [
                    dbl_ for dbl_ in self.listeners if \
                    dbl_.__name__ == 'on_socket_cleaned_receive'
                ]
                try: 
                    for dbl_ in ddd: await dbl_.__call__(data)
                except: 
                    traceback.print_exc()

                events_dict = {
                    'ChatMessageCreated': ChatMessageCreated,
                    'ChatChannelTyping': ChatChannelTyping,
                    'ChatMessageDeleted': ChatMessageDeleted,
                    'ChatPinnedMessageCreated': ChatPinnedMessageCreated,
                    'ChatPinnedMessageDeleted': ChatPinnedMessageDeleted,
                    'ChatMessageUpdated': ChatMessageUpdated
                }

                try:
                    func_from_event = events_dict[recv_type]
                except KeyError:
                    return
                try:
                    await func_from_event(data)
                except:
                    traceback.print_exc()

    async def connect(self, cookie: str):
        websocket = await websockets.connect(
            WS_URL.format(args=''), 
            extra_headers=[('cookie', cookie)]
        )
        await websocket.send('2')
        await self.trigger_on_ready()
        return websocket

    async def login(self, email: str, password: str):
        loginResponse = await internal.session.post(
            BASE + 'login', json={'email': email, 'password': password}
        )
        try:
            responseJson  = (await loginResponse.json())['user']
        except KeyError:
            raise GuildedError('Invalid credentials.')
        joinDate      = iso8601_dt(responseJson.pop('joinDate'))
        responseJson['joinDate'] = joinDate
        self.user = ClientUser(**responseJson)
        if self.owner_id == None:
            self.owner_id = self.user.id

        me = await (await internal.session.get(BASE + 'me')).json()
        for team in me['teams']:
            await self.fetch_team(team['id'])
            # adds to cache as well

        for team in self.teams:
            channels = await internal.session.get(
                BASE + 'teams/' + team.id + '/channels'
            )
            channels = (await channels.json())['channels']
            for channel in channels:
                self.text_channels.append(TextChannel(**channel))
                self.channels.append(TextChannel(**channel))

        if not 'Set-Cookie' in loginResponse.headers:
            raise ValueError('Missing required information in the returned ' \
                             'headers from Guilded. Check your credentials.')
        else:
            self.login_cookie = loginResponse.headers['Set-Cookie']

        return {'cookie': self.login_cookie, 'profile': self.user}

    async def start(self, email, password):
        internal.session = aiohttp.ClientSession()

        login = await self.login(email=email, password=password)
        wsckt = await self.connect(cookie=login['cookie'])
        internal.bot = self
        await asyncio.gather(
            self.websocket_process(websocket=wsckt),
            self.heartbeat(websocket=wsckt),
            loop=self.loop)

        self.loop.run_forever()

    def run(self, email: str, password: str):
        try:
            self.loop.run_until_complete(self.start(
                email=email, 
                password=password
            ))
        except KeyboardInterrupt:
            return

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
        self.steam            = kwargs.get('steamId')
        self.slug             = kwargs.get('subdomain')
        self.staffstatus      = kwargs.get('moderationstatus')
        self.info             = kwargs.get('aboutInfo')
        self.aliases          = kwargs.get('aliases')
        self.joined_at        = iso8601_dt(kwargs.get('joinDate'))
        self.last_online      = iso8601_dt(kwargs.get('lastOnline'))

    def __eq__(self, other):
        try:
            return self.id == other.id
        except AttributeError:
            return False

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
        self.created_at         = iso8601_dt(kwargs.get('createdAt'))
        self.owner_id           = kwargs.get('ownerId')
        self.name               = kwargs.get('name')
        self.slug               = kwargs.get('subdomain')
        self.subdomain          = self.slug
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
        if kwargs.get('roles'):
            for role in kwargs.get('roles'):
                self.roles.append(Role(**role))
        baseg = kwargs.get('baseGroup')
        baseg['team'] = self
        self.home_group         = TeamGroup(**baseg)
        self.members            = []
        for member in kwargs.get('members'):
            member['team'] = self
            self.members.append(Member(**member))
        self.bots               = []  # 👀
        self.default_role       = Role(**kwargs['rolesById'].get('baseRole'))
        self.follower_count     = kwargs.get('followerCount')
        self.is_applicant       = kwargs.get('isUserApplicant') 
                                  # are you an applicant
        self.is_following       = kwargs.get('userFollowsTeam') 
                                  # are you following the team
        # bunch of weird stats stuff
        measurements                     = kwargs.get('measurements')
        self.member_count                = measurements.get('numMembers')
        self.recent_match_count        = measurements.get('numRecentMatches')
        self.follower_and_member_count = measurements.get(
            'numFollowersAndMembers')
        self.follower_count            = self.follower_and_member_count - \
                                         self.member_count
        self.members_in_last_day_count   = measurements.get(
            'numMembersAddedInLastDay')
        self.members_in_last_week_count  = measurements.get(
            'numMembersAddedInLastWeek')
        self.members_in_last_month_count = measurements.get(
            'numMembersAddedInLastMonth')

    def __str__(self):
        return self.name

    def __eq__(self, other):
        try:
            return self.id == other.id
        except AttributeError:
            return False

    def get_member(self, id):
        try:
            member = [m for m in self.members if m.id == id][0]
            return member
        except IndexError:
            return None

class TeamGroup:
    def __init__(self, **kwargs):
        self.id              = kwargs.get('id')
        self.name            = kwargs.get('name')
        self.description     = kwargs.get('description')
        self.created_at      = iso8601_dt(kwargs.get('createdAt'))
        self.team            = kwargs.get('team')
        self.game            = kwargs.get('gameId')
        self.role_can_see    = kwargs.get('visibilityTeamRoleId')
        self.role_is_member  = kwargs.get('membershipTeamRoleId')
        self.home            = kwargs.get('isBase')
        self.public          = kwargs.get('isPublic')

    def __str__(self):
        return self.name

class abc:
    class Messageable(metaclass=abc.ABCMeta):
        async def fetch_message(self, id):
            if type(self) == Context:
                self._channelid = self.channel.id
            else:
                self._channelid = self.id
            message = await internal.session.get(
                BASE + 'content/route/metadata?route=//channels/' + 
                self._channelid +'/chat?messageId='+ id
            )
            message = (await message.json())['metadata']
            message['author'] = await internal.bot.fetch_user(message['createdBy'])
            return Message(**message)

        async def send(self, content=None, *, embed=None):
            '''Send a message to a channel'''
            if type(self) == Context:
                self._channelid = self.channel.id
            else:
                self._channelid = self.id

            rand_uuid = str(uuid.uuid1())
            post_json = {
                "messageId": rand_uuid,
                "content": {
                    "object": "value",
                    "document": {
                        "object": "document",
                        "data": {},
                        "nodes": []
                    }
                }
            }
            if content:
                post_json['content']['document']['nodes'].append({
                    "object": "block",
                    "type": "markdown-plain-text",
                    "data": {},
                    "nodes": [{
                        "object":"text",
                        "leaves": [{
                            "object": "leaf",
                            "text": content,
                            "marks": []
                        }]
                    }]
                })
            if embed:
                post_json['content']['document']['nodes'].append({
                    "object": "block",
                    "type": "webhookMessage",
                    "data": {'embeds': [embed.to_dict()]},
                    "nodes": []})

            # POST the message to the channel
            msg = await internal.session.post(
                BASE + 'channels/' + self._channelid + 
                '/messages', json=post_json
            )
            parse_client_response(msg)
            msg = await msg.json()
            post_json['createdAt'] = msg['message']['createdAt']
            post_json['id']        = rand_uuid
            post_json['channelId'] = self._channelid
            post_json['author']    = internal.bot.user.id  
            # ^ will eventually use a reg obj ^
            message = Message(**post_json)
            return message

    class User(Messageable, metaclass=abc.ABCMeta):
        def __init__(self):
            self.display_name   = self.display_name or self.name
            #self.avatar_url_aws = self.avatar_url.replace(
            #   'https://img.guildedcdn.com/', 
            #   'https://s3-us-west-2.amazonaws.com/www.guilded.gg/'
            #)

        def __str__(self):
            return self.name

        def avatar_url_as(self, size: str = 'Large'):#, aws=False):
            if size.lower() not in ['small', 'medium', 'large']:
                raise ValueError('Invalid size. Must be small, ' \
                                 'medium, or large.')
            if not self.avatar:
                return self.avatar_url
            avatar_string = 'https://img.guildedcdn.com/UserAvatar/' \
                            f'{self.avatar}-{size.capitalize()}.png'
            return avatar_string

        def __eq__(self, other):
            try:
                return self.id == other.id
            except AttributeError:
                return False

    class TeamChannel(Messageable, metaclass=abc.ABCMeta):
        def __init__(self, **kwargs):
            self.id         = kwargs.get('id')
            self.name       = kwargs.get('name')
            self.team       = kwargs.get('team')
            self.type       = kwargs.get('type')
            self.created_at = iso8601_dt(kwargs.get('createdAt'))
            self.updated_at = iso8601_dt(kwargs.get('updatedAt'))
            self.created_by = kwargs.get('createdBy')
            self.channel_id = self.id

        def __str__(self):
            return self.name

        async def history(self, limit=50, oldest_first=True):
            if limit == None:
                js = await internal.session.get(
                    BASE + f'channels/{self.id}/messages'
                )
            else:
                js = await internal.session.get(
                    BASE + f'channels/{self.id}/messages?limit={limit}'
                )
            messages = [
                Message(**message
                ) for message in (await js.json())['messages']
            ]
            if oldest_first:
                messages.reverse()
            return messages

class User(abc.User):
    def __init__(self, **kwargs):
        self.id           = kwargs.get('id')
        self.name         = kwargs.get('name')
        self.display_name = self.name
        self.avatar       = kwargs.get('profilePicture')
        self.avatar_url   = 'https://guilded.ga/logo.png'
        #self.avatar_url_aws = self.avatar_url.replace(
        #    'https://img.guildedcdn.com/', 
        #    'https://s3-us-west-2.amazonaws.com/www.guilded.gg/'
        #)
        self.banner       = kwargs.get('profileBannerLg')
        self.banner_url   = None

        if self.avatar:
            self.avatar = re.sub(
                r'^(https:\/\/s3-us-west-2\.amazonaws\.com\/www\.guilded' \
                r'\.gg\/UserAvatar\/)', 
                '',
                re.sub(
                    r'(-(Small|Medium|Large)\.png(\?w=\d+&h=\d+)?)$', 
                    '',
                    self.avatar
                ))
            self.avatar_url = 'https://img.guildedcdn.com/UserAvatar/' \
                              f'{self.avatar}-Large.png'

        if self.banner:
            self.banner = re.sub(
                r'^(https:\/\/s3-us-west-2\.amazonaws\.com\/www\.guilded' \
                r'\.gg\/UserBanner\/)', 
                '',
                re.sub(
                    r'(-Hero\.png(\?w=\d+&h=\d+)?)$', 
                    '',
                    self.banner
                ))
            self.banner_url = 'https://img.guildedcdn.com/UserBanner/' \
                              f'{self.banner}-Hero.png'

        self.display_name = self.name
        self.about        = kwargs.get('aboutInfo')
        self.slug         = kwargs.get('subdomain')
        self.steam        = kwargs.get('steamId')
        self.last_online  = iso8601_dt(kwargs.get('lastOnline'))
        self.created_at   = iso8601_dt(kwargs.get('joinDate'))

class Member(User):
    def __init__(self, **kwargs):
        self.team        = kwargs.get('team')
        self.nick        = kwargs.get('nickname')
        if self.nick:      self.display_name = self.nick
        self.xp          = kwargs.get('teamXp')

    async def edit(self, nick: typing.Optional):
        if nick:
            await internal.session.put(
                BASE + 'teams/' + self.team.id + \
                '/members/' + self.id + '/nickname',
                json={'nickname': nick}
            )

class Role:
    def __init__(self, **kwargs):
        self.id                  = kwargs.get('id')
        self.name                = kwargs.get('name')
        self.color               = kwargs.get('color')  
        # hexval
        self.is_default          = kwargs.get('isBase') 
        # is it the default member role (i think?)
        self.team                = kwargs.get('teamId')
        self.created_at          = iso8601_dt(kwargs.get('createdAt'))
        self.updated_at          = iso8601_dt(kwargs.get('updatedAt'))
        self.mentionable         = kwargs.get('isMentionable')
        self.discord_id          = kwargs.get('discordRoleId')
        self.self_assignable     = kwargs.get('isSelfAssignable')
        self.discord_last_synced = kwargs.get('discordSyncedAt')
        if self.discord_last_synced != None: 
            self.discord_last_synced = iso8601_dt(self.discord_last_synced)

    def __str__(self):
        return self.name

class Embed:
    def __init__(self, 
        title=None, description=None, 
        color:int=None, url=None,
        timestamp:datetime.datetime=None
    ):  # :(
        self.utcnow = self.now

        self.title       = title
        self.description = description
        self.color       = color
        self.url         = url
        self.timestamp   = None
        if timestamp:
            self.timestamp = timestamp.isoformat('T')
        self.author      = None
        self.footer      = None
        self.image       = None
        self.thumbnail   = None
        self.dictionary  = {
            "title": self.title,
            "description": self.description,
            "color": self.color,
            "url": self.url,
            "timestamp": self.timestamp,
            "fields": [],  # i don't know if there's a limit to these
            "author": {
                "name": None,
                "url": None,
                "icon_url": None
            },
            "footer": {
                "text": None,
                "icon_url": None
            },
            "image": {
                "url": None
            },
            "thumbnail": {
                "url": None
            }
        }

    def set_author(self, name: str, url: str = None, icon_url: str = None):
        self.dictionary['author'] = {
            'name': name, 
            'url': url, 
            'icon_url': icon_url
        }
        class author:
            self.name     = name
            self.url      = url
            self.icon_url = icon_url
        self.author = author
        return self

    def set_footer(self, text: str, icon_url: str = None):
        self.dictionary['footer'] = {'text': text, 'icon_url': icon_url}
        return self

    def set_image(self, url: str):
        self.dictionary['image'] = {'url': url}
        return self

    def set_thumbnail(self, url: str):
        self.dictionary['thumbnail'] = {'url': url}
        return self

    def add_field(self, name: str, value: str, inline=True):
        self.dictionary['fields'].append({
            'name': name,
            'value': value,
            'inline': inline
        })
        return self

    def to_dict(self):
        '''This function should be called if you want a more up-to-date \
        version of the embed, e.g. its description has been edited after \
        the initial creation of the guilded.Embed object.'''
        return {
            'title': self.title,
            'description': self.description,
            'color': self.color,
            'url': self.url,
            'timestamp': self.timestamp,
            'fields': self.dictionary['fields'],
            'author': self.dictionary['author'],
            'footer': self.dictionary['footer'],
            'image': self.dictionary['image'],
            'thumbnail': self.dictionary['thumbnail']
        }

    @classmethod
    def now(cls):
        return datetime.datetime.utcnow()

    @classmethod
    def from_dict(cls, embed_dict: dict):
        try:             title = embed_dict['title']
        except KeyError: title = None
        try:             description = embed_dict['description']
        except KeyError: description = None
        try:             color = embed_dict['color']
        except KeyError: color = None
        try:             url = embed_dict['url']
        except KeyError: url = None
        try:
            ts = embed_dict['timestamp']
            if ts:
                if not ts.endswith('Z'): ts += 'Z'
                timestamp = iso8601_dt(ts)
            else:
                timestamp = None
        except KeyError: 
            timestamp = None
        embed = cls(
            title=title,
            description=description,
            color=color,
            url=url,
            timestamp=timestamp)
        try:
            embed.set_author(
                name=embed_dict['author']['name'],
                url=embed_dict['author']['url'],
                icon_url=embed_dict['author']['icon_url'])
        except KeyError: pass
        try:
            embed.set_footer(
                text=embed_dict['footer']['text'],
                icon_url=embed_dict['footer']['icon_url'])
        except KeyError: pass
        try: embed.set_image(url=embed_dict['image']['url'])
        except KeyError: pass
        try: embed.set_thumbnail(url=embed_dict['thumbnail']['url'])
        except KeyError: pass
        return embed

class TextChannel(abc.TeamChannel):
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')

    def __str__(self):
        return self.name

    def __eq__(self, other):
        try:
            return self.id == other.id
        except AttributeError:
            return False

class AnnouncementChannel(abc.TeamChannel):
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.teamId = kwargs.get('team')

    async def send(self, title: str, content: str):
        announcement = {
            "title": title,
            "content": {
                "object": "value",
                "document": {
                    "object": "document",
                    "data": {},
                    "nodes": [{
                        "object": "block",
                        "type": "markdown-plain-text",
                        "data": {},
                        "nodes": [{
                            "object": "text",
                            "leaves": [{
                                "object": "leaf",
                                "text": content,
                                "marks": []
                            }]
                        }]
                    }]
                }
            },
            "teamId": self.teamId,
            "gameId": None}
        returned_announcement = await internal.session.post(
            BASE + 'channels/' + self.id + '/announcements'
        )
        ann_json = (await returned_announcement.json())
        print(ann_json)
        #['announcement']
        return AnnouncementMessage(**ann_json)

    @classmethod
    def construct(cls, **kwargs):
        return cls(**kwargs)

class AnnouncementMessage:
    def __init__(self, **kwargs):
        self.id         = kwargs.get('id')
        self.created_at = iso8601_dt(kwargs.get('createdAt'))
        self.title      = kwargs.get('title')
        self.raw        = {'content': kwargs.get('content')}
        self.content    = Message.get_full_content(self)
        self.channel    = TextChannel(**{'id': kwargs.get('channelId')})

class Message:
    def __init__(self, **kwargs):
        self.raw        = kwargs
        self.id         = kwargs.get('id')
        self.channel    = TextChannel(**{
            'id': kwargs.get('channelId'),
            'team': kwargs.get('team')
        })
        if self.channel.id and self.id:
            self.jump_url = 'https://guilded.gg/channels/' + self.channel.id + '/chat?messageId=' + self.id
        else:
            self.jump_url = None
        self.webhook_id = kwargs.get('webhookId')
        self.team       = kwargs.get('team')
        self.guild      = self.team
        self.created_at = iso8601_dt(kwargs.get('createdAt'))
        self.author     = kwargs.get('author')
        self.mentions   = []
        self.embeds     = []
        self.embed      = None  # the first embed
        self.content    = self.get_full_content()
        if self.embeds:
            self.embed  = self.embeds[0]
        #self.content    = ''
        #content0        = kwargs['content']['document']['nodes'][0]['nodes']
        #for aaaHelpMe  in content0:
        #    try:
        #        cont_append = aaaHelpMe['leaves'][0]['text']
        #    except KeyError:
        #        cont_append = aaaHelpMe['nodes'][0]['leaves'][0]['text']
        #    self.content += cont_append

    def __str__(self):
        return str(self.content) # can be None

    def __eq__(self, other):
        try:
            return self.id == other.id
        except AttributeError:
            return False

    def get_full_content(self):
        try:
            nodes   = self.raw['content']['document']['nodes']
        except KeyError:
            # there's no content
            return None
        content = ''
        for node in nodes:
            type = node['type']
            if type == 'paragraph':
                for element in node['nodes']:
                    if element['object'] == 'text':
                        for leaf in element['leaves']:
                            if not leaf['marks']:
                                content += leaf['text']
                            else:
                                to_mark = '{unmarked_content}'
                                marks = leaf['marks']
                                for mark in marks:
                                    if mark['type'] == 'bold':
                                        to_mark = '**' + to_mark + '**'
                                    if mark['type'] == 'italic':
                                        to_mark = '*' + to_mark + '*'
                                    if mark['type'] == 'underline':
                                        to_mark = '__' + to_mark + '__'
                                    if mark['type'] == 'strikethrough':
                                        to_mark = '~~' + to_mark + '~~'
                                    if mark['type'] == 'spoiler':
                                        to_mark = '||' + to_mark + '||'
                                    else:
                                        to_mark = to_mark
                                content += to_mark.format(
                                    unmarked_content=leaf['text']
                                )
                    if element['object'] == 'inline':
                        if element['type'] == 'mention':
                            person   = element['data']['mention']
                            content += '<@' + person['id'] + '>'
                            self.mentions.append(Member(**{
                                'name': person['name'],
                                'avatar_url': person['avatar'],
                                'color': person['color'],
                                'id': person['id']
                            }))
                        if element['type'] == 'reaction':
                            rtext = element['nodes'][0]['leaves'][0]['text']
                            content += rtext
                        if element['type'] == 'link':
                            l1 = element['nodes'][0]['leaves'][0]['text']
                            l2 = element['data']['href']
                            content += f'[{l1}]({l2})'
            if type == 'markdown-plain-text':
                content += node['nodes'][0]['leaves'][0]['text']
            if type == 'webhookMessage':
                for msg_embed in node['data']['embeds']:
                    self.embeds.append(Embed.from_dict(msg_embed))
            if type == 'block-quote-container':
                text = str(node['nodes'][0]['nodes'][0]['leaves'][0]['text'])
                content += '> ' + text

        if content == '':
            content = None
        return content

    async def add_reaction(self, emoji_id):
        react = await internal.session.post(
            BASE + 'channels/' + self.channel.id + 
            '/messages/' + self.id + '/reactions/' + emoji_id
        )
        return await react.json()

    async def delete(self, *, delay: float = None):
        if delay:
            await asyncio.sleep(delay)

        response = await internal.session.delete(
            BASE + 'channels/' + self.channel.id + 
            '/messages/' + self.id
        )
        if delay:
            return None  # silently end func whether or not it failed

        return parse_client_response(response)

    async def edit(self, *, content: str = None, embed: Embed = None):
        post_json = {
            "content": {
                "object": "value",
                "document": {
                    "object": "document",
                    "data": {},
                    "nodes": []
                }
            }
        }
        if content is not None:
            post_json['content']['document']['nodes'].append({
                "object": "block",
                "type": "markdown-plain-text",
                "data": {},
                "nodes": [{
                    "object":"text",
                    "leaves": [{
                        "object": "leaf",
                        "text": content,
                        "marks": []
                    }]
                }]
            })
        if embed is not None:
            post_json['content']['document']['nodes'].append({
                "object": "block",
                "type": "webhookMessage",
                "data": {'embeds': [embed.to_dict()]},
                "nodes": []})

        response = await internal.session.put(
            BASE + 'channels/' + self.channel.id +
            '/messages/' + self.id,
            json=post_json
        )
        parse_client_response(response)

        if embed is not None:
            self.embed = embed
        if content is not None:
            self.content = content

        self.edited_at = datetime.datetime.utcnow()
        return None

class Context(abc.Messageable):
    def __init__(self, **kwargs):
        message = kwargs.get('message')
        self.message         = message
        self.author          = message.author
        self.channel         = message.channel
        self.content         = message.content
        self.team            = message.team
        self.invoked_with    = None
        self.arguments       = []
        self.channel_id      = self.channel
