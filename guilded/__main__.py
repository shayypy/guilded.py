import re
import abc
import json
import uuid
import shlex
import typing
import aiohttp
import asyncio
import inspect
import datetime
import traceback
import websockets
BASE   = 'https://api.guilded.gg/'
WS_URL = 'wss://api.guilded.gg/socket.io/?jwt=undefined&EIO=3&transport=websocket'

class internal:
    '''internal stuff lol. i know this sucks'''
    pinginterval = 25 # default ping interval

session = None
async def make_session():
    global session
    session = aiohttp.ClientSession()

def make_datetime(initial: str):
    # for dates formatted like 2020-07-28T22:28:01.151Z
    #                          yyyy-mm-ssThh:mm:ss.mlsZ
    try:
        return datetime.datetime.strptime(str(initial), "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError:
        # will make this more.. usable eventually
        return initial

class Bot:
    def __init__(self, command_prefix, **kwargs):
        # ""Settings""
        self.command_prefix = command_prefix
        self.loop           = kwargs.get('loop', asyncio.get_event_loop())
        self.description    = kwargs.get('description', None)
        self.owner_id       = kwargs.get('owner_id')
        # To be assigned upon start
        self.user           = None # ClientUser object
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
            teamResponse = await session.get(BASE + 'teams/' + teamId)
            teamJson     = (await teamResponse.json())['team']
            team         = Team(**teamJson)
            for t in self.teams:
                if t.id == team.id:
                    self.teams.remove(t)
            self.teams.append(team)
            chanResponse = await session.get(BASE + 'teams/' + teamId + '/channels')
            chanJson     = (await chanResponse.json())['channels']
            for c in chanJson:
                channel = TextChannel(**c)
                if channel not in self.channels:
                    self.channels.append(channel)
                if channel not in self.text_channels:
                    self.text_channels.append(channel)
        except:
            traceback.print_exc()
            team = teamId
            # just have an error elsewhere lul
        return team

    async def fetch_channel(self, channelId):
        try:
            channelResponse = await session.get(BASE + 'channels/' + channelId)
            channelJson     = (await channelResponse.json())['channel']
            channel         = TextChannel(**channelJson)
            for c in self.channels:
                if c.id == channel.id:
                    self.channels.remove(c)
            self.channels.append(channel)
        except:
            channel = channelId
            # just have an error elsewhere lul
        return channel

    async def fetch_user(self, userId):
        userResponse = await session.get(BASE + 'users/' + userId)
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

    # connection
    async def heartbeat(self, websocket):
        while True:
            await asyncio.sleep(25) # temp
            try:
                await websocket.send('2')
            except:
                await self.connect(cookie=self.login_cookie)

    async def websocket_process(self, websocket):
        while True:
            try:
                latest = await websocket.recv()
            except:
                websocket = await self.connect(cookie=self.login_cookie)
            dd = [dbl for dbl in self.listeners if dbl.__name__ == 'on_socket_raw_receive']
            for dbl in dd: await dbl.__call__(latest)

            if latest.isdigit(): pass
            else:
                for char in latest:
                    if char.isdigit(): latest = latest.replace(char, '', 1)
                    else: break
                data = json.loads(latest)
                #try:
                #    if 'pingInterval' in data.keys():
                #        internal.pinginterval = data['pingInterval'] * 1000
                #except AttributeError:
                #    pass
                try: recv_type = data[0]
                except: pass
                else:
                    data = data[1]
                    ddd = [dbl_ for dbl_ in self.listeners if dbl_.__name__ == 'on_socket_cleaned_receive']
                    for dbl_ in ddd: await dbl_.__call__(data)

                    if recv_type == 'ChatMessageCreated':
                        mdata              = data['message']
                        mdata['team']      = await self.fetch_team(data['teamId'])
                        mdata['author']    = await self.fetch_user(data['createdBy'])
                        mdata['channelId'] = data['channelId']
                        message = Message(**mdata)
                        # on_message event
                        onmsg_events = [onm for onm in self.listeners if onm.__name__ == 'on_message']
                        for onm_ in onmsg_events: await onm_.__call__(message)

                        # commands
                        if message.content:
                            if message.content.startswith(self.command_prefix):
                                if message.author.id != self.user.id or message.author.id == self.owner_id:
                                    # ignores self, but if the owner is itself, it does not ignore self
                                    # will add selfbot arg in the future
                                    data['message'] = message
                                    ctx = Context(**data)
                                    ctx.invoked_command = (message.content.replace(self.command_prefix, '', 1).split(' '))[0]
                                    ctx.arguments = [ctx]
                                    args = message.content.replace(f'{self.command_prefix}{ctx.invoked_command}', '', 1)
                                    if args != '':
                                        use_args = shlex.split(args)
                                        for a in use_args:
                                            ctx.arguments.append(a)
                                    for c in self.commands:
                                        if c.__name__ == ctx.invoked_command:
                                            argspec   = inspect.getfullargspec(c)
                                            func_args = argspec.args + argspec.kwonlyargs
                                            while len(func_args) < len(ctx.arguments):
                                                del ctx.arguments[-1]
                                            try:
                                                await c(*ctx.arguments)
                                                break
                                            except:
                                                traceback.print_exc()

                    # start typing (there is no end typing event)
                    if recv_type == 'ChatChannelTyping':
                        data['typer']     = await self.fetch_user(data['userId'])
                        event_begintyping = [l for l in self.listeners if l.__name__ == 'on_typing']
                        for type_ev in event_begintyping:
                            try:    await type_ev.__call__(data['channelId'], data['typer'], datetime.datetime.utcnow())
                            except: traceback.print_exc()

                    # delete
                    if recv_type == 'ChatMessageDeleted':
                        data['team']    = await self.fetch_team(data['teamId'])
                        data['id']      = data['message']['id']
                        #data['author'] = await self.fetch_user(data['createdBy'])
                        # not available, see:
                        # https://www.guilded.gg/guilded-api/groups/l3GmAe9d/channels/1688bafa-9ecb-498e-9f6d-313c1cdc7150/docs/729851648
                        mdata   = data['message']
                        message = Message(**mdata)
                        event_delmessage = [l for l in self.listeners if l.__name__ == 'on_message_delete']
                        for delmsg_ev in event_delmessage:
                            try:    await delmsg_ev.__call__(message)
                            except: traceback.print_exc()

                    # pin
                    if recv_type == 'ChatPinnedMessageCreated':
                        data['team']   = await self.fetch_team(data['teamId'])
                        data['id']     = data['message']['id']
                        data['author'] = await self.fetch_user(data['updatedBy'])
                        mdata          = data['message']
                        message        = Message(**mdata)
                        event_pinmsg   = [l for l in self.listeners if l.__name__ == 'on_pins_add']
                        for pinmsg_ev in event_pinmsg:
                            try:    await pinmsg_ev.__call__(message, data['author']) # message, who_pinned
                            except: traceback.print_exc()

                    # unpin
                    if recv_type == 'ChatPinnedMessageDeleted':
                        data['team']   = await self.fetch_team(data['teamId'])
                        data['id']     = data['message']['id']
                        data['author'] = await self.fetch_user(data['updatedBy'])
                        mdata          = data['message']
                        message        = Message(**mdata)
                        event_pinmsg   = [l for l in self.listeners if l.__name__ == 'on_pins_remove' or l.__name__ == 'on_unpin']
                        for pinmsg_ev in event_pinmsg:
                            try:    await pinmsg_ev.__call__(message, data['author']) # message, who_unpinned
                            except: traceback.print_exc()

                    # edited
                    if recv_type == 'ChatMessageUpdated':
                        data['team']   = await self.fetch_team(data['teamId'])
                        data['author'] = await self.fetch_user(data['updatedBy'])
                        mdata          = data['message']
                        message        = Message(**mdata)
                        onmsg_events   = [l for l in self.listeners if l.__name__ == 'on_message_edit']
                        for edit_ev in onmsg_events: # seems like guilded doesnt give you the previous version ://
                            try:    await edit_ev.__call__(message)
                            except: traceback.print_exc()

    async def connect(self, cookie: str):
        websocket = await websockets.connect(WS_URL, extra_headers=[('cookie', cookie)])
        await websocket.send('2')
        await self.trigger_on_ready()
        return websocket

    async def login(self, email: str, password: str):
        if session == None: await make_session()
        loginResponse = await session.post(BASE + 'login', json={'email': email, 'password': password})
        responseJson  = (await loginResponse.json())['user']
        joinDate      = make_datetime(responseJson.pop('joinDate'))
        responseJson['joinDate'] = joinDate
        self.user = ClientUser(**responseJson)
        if self.owner_id == None:
            self.owner_id = self.user.id

        me = await (await session.get(BASE + 'me')).json()
        for team in me['teams']:
            await self.fetch_team(team['id'])
            # adds to cache as well

        for team in self.teams:
            channels = await session.get(BASE + 'teams/' + team.id + '/channels')
            channels = (await channels.json())['channels']
            for channel in channels:
                self.text_channels.append(TextChannel(**channel))
                self.channels.append(TextChannel(**channel))

        if not 'Set-Cookie' in loginResponse.headers:
            raise KeyError('Missing required information in the returned headers from Guilded. Check your credentials?')
        else:
            self.login_cookie = loginResponse.headers['Set-Cookie']

        return {'cookie': self.login_cookie, 'profile': self.user}

    async def async_run(self, email, password):
        login = await self.login(email=email, password=password)
        wsckt = await self.connect(cookie=login['cookie'])
        await asyncio.gather(
            self.websocket_process(websocket=wsckt),
            self.heartbeat(websocket=wsckt),
            loop=self.loop)
        self.loop.run_forever()

    def run(self, email: str, password: str):
        try:
            self.loop.run_until_complete(self.async_run(email=email, password=password))
        except KeyboardInterrupt:
            #await session.close()
            #await self.loop.close()
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
        self.joined_at        = make_datetime(kwargs.get('joinDate'))
        self.last_online      = make_datetime(kwargs.get('lastOnline'))

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
        self.bots               = [] # 👀
        self.default_role       = Role(**kwargs['rolesById'].get('baseRole'))
        self.follower_count     = kwargs.get('followerCount')
        self.is_applicant       = kwargs.get('isUserApplicant') # are you an applicant
        self.is_following       = kwargs.get('userFollowsTeam') # are you following the team
        # bunch of weird stats stuff
        measurements                     = kwargs.get('measurements')
        self.member_count                = measurements.get('numMembers')
        self.recent_match_count          = measurements.get('numRecentMatches')
        self.follower_and_member_count   = measurements.get('numFollowersAndMembers')
        self.follower_count              = self.follower_and_member_count - self.member_count
        self.members_in_last_day_count   = measurements.get('numMembersAddedInLastDay')
        self.members_in_last_week_count  = measurements.get('numMembersAddedInLastWeek')
        self.members_in_last_month_count = measurements.get('numMembersAddedInLastMonth')
        #self.latest_member_last_online   = datetime.datetime.utcfromtimestamp(measurements.get('mostRecentMemberLastOnline'))

class TeamGroup:
    def __init__(self, **kwargs):
        self.id              = kwargs.get('id')
        self.name            = kwargs.get('name')
        self.description     = kwargs.get('description')
        self.created_at      = make_datetime(kwargs.get('createdAt'))
        self.team            = kwargs.get('team')
        self.game            = kwargs.get('gameId')
        self.role_can_see    = kwargs.get('visibilityTeamRoleId')
        self.role_is_member  = kwargs.get('membershipTeamRoleId')
        self.home            = kwargs.get('isBase')
        self.public          = kwargs.get('isPublic')

class abc:
    class Messageable(metaclass=abc.ABCMeta):
        #def __init__(self):
        #    self.channel = self.channel_id

        async def fetch_message(id):
            message = await session.get(BASE + 'content/route/metadata?route=//channels/'+ self.channel +'/chat?messageId='+ id)
            message = (await message.json())['metadata']
            message['author'] = await Bot.fetch_user(message['createdBy']) # does this even work
            return Message(**message)

        async def send(self, content=None, embed=None):
            '''Send a message to a channel'''
            rand_uuid = str(uuid.uuid1())
            post_json = {
                "messageId": rand_uuid,
                "content": {
                    "object": "value",
                    "document": {
                        "object":"document",
                        "data": {},
                        "nodes": []
                    }
                }
            }
            if content != None:
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
            if embed != None:
                post_json['content']['document']['nodes'].append({
                    "object": "block",
                    "type": "webhookMessage",
                    "data": {'embeds': [embed.to_dict()]},
                    "nodes": []})

            if content == None and embed == None:
                raise ValueError('content and embed cannot both be None.')

            # POST the message to the channel
            if type(self) == Context:
                id_to_send = self.channel.id
            else:
                id_to_send = self.id
            msg = await session.post(BASE + 'channels/' + id_to_send + '/messages', json=post_json)
            #msg = await msg.json()
            return 200
            #return Message(**msg['message'])

    class User(Messageable, metaclass=abc.ABCMeta):
        def __init__(self):
            self.display_name   = self.display_name or self.name
            #self.avatar_url_aws = self.avatar_url.replace('https://img.guildedcdn.com/', 'https://s3-us-west-2.amazonaws.com/www.guilded.gg/')

        def avatar_url_as(self, size: str = 'Large'):#, aws=False):
            if size.lower() not in ['small', 'medium', 'large']:
                raise ValueError('Invalid size. Must be small, medium, or large.')
            if not self.avatar:
                return self.avatar_url
            return f'https://img.guildedcdn.com/UserAvatar/{self.avatar}-{size.capitalize()}.png?w=450&h=450'

    class TeamChannel(Messageable, metaclass=abc.ABCMeta):
        def __init__(self, **kwargs):
            self.id         = kwargs.get('id')
            self.team       = kwargs.get('team')
            self.type       = kwargs.get('type')
            self.created_at = make_datetime(kwargs.get('createdAt'))
            self.updated_at = make_datetime(kwargs.get('updatedAt'))
            self.created_by = kwargs.get('createdBy')
            self.channel_id = self.id

        async def history(self, limit=50, oldest_first=True):
            if limit == None:
                js = await session.get(BASE + f'channels/{self.id}/messages')
            else:
                js = await session.get(BASE + f'channels/{self.id}/messages?limit={limit}')
            messages = [Message(**message) for message in (await js.json())['messages']]
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
        #self.avatar_url_aws = self.avatar_url.replace('https://img.guildedcdn.com/', 'https://s3-us-west-2.amazonaws.com/www.guilded.gg/')
        self.banner       = kwargs.get('profileBannerLg')
        self.banner_url   = None

        if self.avatar:
            self.avatar = re.sub(
                r'^(https:\/\/s3-us-west-2\.amazonaws\.com\/www\.guilded\.gg\/UserAvatar\/)', # remove first part
                '',
                re.sub(
                    r'(-(Small|Medium|Large)\.png(\?w=\d+&h=\d+)?)$', # remove size contraints
                    '',
                    self.avatar
                ))
            self.avatar_url = f'https://img.guildedcdn.com/UserAvatar/{self.avatar}-Large.png?w=450&h=450'

        if self.banner:
            self.banner = re.sub(
                r'^(https:\/\/s3-us-west-2\.amazonaws\.com\/www\.guilded\.gg\/UserBanner\/)', # remove first part
                '',
                re.sub(
                    r'(-Hero\.png(\?w=\d+&h=\d+)?)$', # remove size contraints
                    '',
                    self.banner
                ))
            self.banner_url = f'https://img.guildedcdn.com/UserBanner/{self.banner}-Hero.png'

        self.display_name = self.name
        self.about        = kwargs.get('aboutInfo')
        self.slug         = kwargs.get('subdomain')
        self.steam        = kwargs.get('steamId')
        self.last_online  = make_datetime(kwargs.get('lastOnline'))
        self.created_at   = make_datetime(kwargs.get('joinDate'))

class Member(User):
    def __init__(self, **kwargs):
        self.team        = kwargs.get('team')
        self.nick        = kwargs.get('nickname')
        if self.nick:      self.display_name = self.nick
        self.xp          = kwargs.get('teamXp')

    async def edit(self, nick: typing.Optional):
        if nick:
            await session.put(
                BASE + 'teams/' + self.team.id + '/members/' + self.id + '/nickname',
                json={'nickname': nick})

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

class Embed:
    def __init__(self, title=None, description=None, color:int=None, url=None):
        # Timestamps are currently unsupported I'm sorry
        # I'll get off my lazy butt and do it someday
        # Stupid timezones
        self.title       = title
        self.description = description
        self.color       = color
        self.url         = url
        self.author      = None
        self.footer      = None
        self.image       = None
        self.thumbnail   = None
        self.dictionary  = {
            "title": self.title,
            "description": self.description,
            "color": self.color,
            "url": self.url,
            "fields": [], # i don't know if there's a limit to these
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
        self.dictionary['author'] = {'name': name, 'url': url, 'icon_url': icon_url}
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
        '''This function should be called if you want a more up-to-date version of the embed, \
        e.g. its description has been edited after the initial creation of the guilded.Embed object.'''
        return {
            'title': self.title,
            'description': self.description,
            'color': self.color,
            'url': self.url,
            'fields': self.dictionary['fields'],
            'author': self.dictionary['author'],
            'footer': self.dictionary['footer'],
            'image': self.dictionary['image'],
            'thumbnail': self.dictionary['thumbnail']
        }

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
        embed = cls(
            title=title,
            description=description,
            color=color,
            url=url)
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

class Message:
    def __init__(self, **kwargs):
        self.raw        = kwargs
        self.channel    = TextChannel(**{
            'id': kwargs.get('channelId'),
            'team': kwargs.get('team')
        })
        self.team       = kwargs.get('team')
        self.created_at = make_datetime(kwargs.get('createdAt'))
        self.id         = kwargs.get('id')
        self.author     = kwargs.get('author')
        self.mentions   = []
        self.embeds     = []
        self.content    = self.get_full_content()
        #self.content    = ''
        #content0        = kwargs['content']['document']['nodes'][0]['nodes']
        #for aaaHelpMe  in content0:
        #    try:
        #        cont_append = aaaHelpMe['leaves'][0]['text']
        #    except KeyError:
        #        cont_append = aaaHelpMe['nodes'][0]['leaves'][0]['text']
        #    self.content += cont_append

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
                                        # unknown md type
                                        to_mark = to_mark
                                content += to_mark.format(unmarked_content=leaf['text'])
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
                            content += element['nodes'][0]['leaves'][0]['text']
                        if element['type'] == 'link':
                            content += f"[{element['nodes'][0]['leaves'][0]['text']}]({element['data']['href']})"
            if type == 'markdown-plain-text':
                content += node['nodes'][0]['leaves'][0]['text']
            if type == 'webhookMessage':
                for msg_embed in node['data']['embeds']:
                    self.embeds.append(Embed.from_dict(msg_embed))
                #content += node['nodes'][0] # im sure theres somethere here sometimes
            if type == 'block-quote-container':
                content += '> ' + str(node['nodes'][0]['nodes'][0]['leaves'][0]['text'])

        if content == '':
            content = None
        return content

    async def add_reaction(self, emoji_id):
        react = await session.post(BASE + 'channels/' + self.channel + '/messages/' + self.id + '/reactions/' + emoji_id)
        return await react.json()

class Context(abc.Messageable):
    def __init__(self, **kwargs):
        message = kwargs.get('message')
        self.message         = message
        self.author          = message.author
        self.channel         = message.channel
        self.content         = message.content
        self.team            = message.team
        self.invoked_command = None
        self.arguments       = []
        self.channel_id      = self.channel
