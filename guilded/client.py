import asyncio
import logging
import sys
import traceback

import aiohttp

from .errors import NotFound
from .gateway import GuildedWebSocket, WebSocketClosure
from .http import HTTPClient
from .status import Game
from .team import Team
from .user import ClientUser, User

log = logging.getLogger(__name__)

def _cancel_tasks(loop):
    try:
        task_retriever = asyncio.Task.all_tasks
    except AttributeError:
        # future proofing for 3.9 I guess
        task_retriever = asyncio.all_tasks

    tasks = {t for t in task_retriever(loop=loop) if not t.done()}

    if not tasks:
        return

    log.info('Cleaning up after %d tasks.', len(tasks))
    for task in tasks:
        task.cancel()

    loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
    log.info('All tasks finished cancelling.')

    for task in tasks:
        if task.cancelled():
            continue
        if task.exception() is not None:
            loop.call_exception_handler({
                'message': 'Unhandled exception during Client.run shutdown.',
                'exception': task.exception(),
                'task': task
            })

def _cleanup_loop(loop):
    try:
        _cancel_tasks(loop)
        if sys.version_info >= (3, 6):
            loop.run_until_complete(loop.shutdown_asyncgens())
    finally:
        log.info('Closing the event loop.')
        loop.close()

class Client:
    '''The basic client class for interfacing with Guilded.'''
    def __init__(self, *, loop: asyncio.AbstractEventLoop = None, max_messages: int = 1000, disable_team_websockets=False, cache_on_startup=None):
        # internal
        self.loop = loop or asyncio.get_event_loop()
        self.user = None
        self.max_messages = max_messages
        self.disable_team_websockets = disable_team_websockets
        self._listeners = {}

        cache_on_startup = cache_on_startup or {}
        self.cache_on_startup = {
            'members': cache_on_startup.get('members') or True,
            'channels': cache_on_startup.get('channels') or True
        }

        # state
        self.http = None
        self._closed = False
        self._ready = asyncio.Event()

    @property
    def cached_messages(self):
        return list(self.http._messages.values())

    @property
    def emojis(self):
        return list(self.http._emojis.values())

    @property
    def teams(self):
        return list(self.http._teams.values())

    @property
    def users(self):
        return list(self.http._users.values())

    @property
    def members(self):
        return list(self.http._team_members.values())

    @property
    def dm_channels(self):
        return list(self.http._dm_channels.values())

    @property
    def private_channels(self):
        return self.dm_channels

    @property
    def team_channels(self):
        return list(self.http._team_channels.values())

    @property
    def channels(self):
        return [*self.dm_channels, *self.team_channels]

    @property
    def guilds(self):
        '''A placeholder property for Discord bot compensation. Will be removed in a later version.'''
        return self.teams

    @property
    def latency(self):
        return self.http.ws.latency

    @property
    def closed(self):
        return self._closed

    def is_ready(self):
        return self._ready.is_set()

    async def wait_until_ready(self):
        await self._ready.wait()

    def event(self, coro):
        '''Register an event for the library to automatically dispatch when appropriate.'''
        if not asyncio.iscoroutinefunction(coro):
            raise TypeError('Event must be a coroutine.')

        setattr(self, coro.__name__, coro)
        self._listeners[coro.__name__] = coro
        return coro

    def dispatch(self, event_name, *args, **kwargs):
        '''Dispatch a registered event.'''
        coro = self._listeners.get(f'on_{event_name}')
        if not coro:
            return
        self.loop.create_task(coro(*args, **kwargs))

    async def start(self, email, password, *, reconnect=True):
        '''Login and connect to Guilded using a user account email and password.'''
        self.http = self.http or HTTPClient(session=aiohttp.ClientSession(loop=self.loop), max_messages=self.max_messages)
        self.user = await self.login(email, password)
        await self.connect()

    async def login(self, email, password):
        data = await self.http.login(email, password)
        me = ClientUser(state=self.http, data=data)
        self.http.my_id = me.id

        for team_data in data.get('teams'):
            team = Team(state=self.http, data=team_data)

            if self.cache_on_startup['members'] is True:
                members = await team.fetch_members()
                for member in members: self.http.add_to_member_cache(member)

            if self.cache_on_startup['channels'] is True:
                team.channels = await team.fetch_channels()
                for channel in team.channels: self.http.add_to_team_channel_cache(channel)

            self.http.add_to_team_cache(team)

        return me

    async def connect(self):
        while not self.closed:
            ws_build = GuildedWebSocket.build(self, loop=self.loop)
            gws = await asyncio.wait_for(ws_build, timeout=60)
            if type(gws) != GuildedWebSocket:
                self.dispatch('error', gws)
                return

            self.ws = gws
            self.http.ws = self.ws
            self.dispatch('connect')

            if not self.disable_team_websockets:
                for team in self.teams:
                    team_ws_build = GuildedWebSocket.build(self, loop=self.loop, teamId=team.id)
                    team_ws = await asyncio.wait_for(team_ws_build, timeout=60)
                    if type(team_ws) == GuildedWebSocket:
                        team.ws = team_ws
                        self.dispatch('team_connect', team)

            async def listen_socks(ws, team=None):
                teamId = team.id if team is not None else None
                next_backoff_time = 5
                while True and ws is not None:
                    try:
                        await ws.poll_event()
                    except WebSocketClosure as exc:
                        code = ws._close_code or ws.socket.close_code
                        if teamId:
                            log.warning('Team %s\'s websocket closed with code %s, attempting to reconnect in %s seconds', teamId, code, next_backoff_time)
                            self.dispatch('team_disconnect', teamId)
                        else:
                            log.warning('Websocket closed with code %s, attempting to reconnect in %s seconds', code, next_backoff_time)
                            self.dispatch('disconnect')
                        await asyncio.sleep(next_backoff_time)
                        build = GuildedWebSocket.build(self, loop=self.loop, teamId=teamId)
                        try:
                            ws = await asyncio.wait_for(build, timeout=60)
                        except asyncio.TimeoutError:
                            log.warning('Timed out trying to reconnect.')
                            next_backoff_time += 5
                    else:
                        next_backoff_time = 5

            self._ready.set()
            self.dispatch('ready')

            await asyncio.gather(
                listen_socks(self.ws), *[listen_socks(team.ws, team) for team in self.teams]
            )

    async def close(self):
        if self._closed: return

        await self.http.logout()
        for ws in [self.ws] + [team.ws for team in self.teams if team.ws is not None]:
            try:
                await ws.close(code=1000)
            except Exception:
                # it's probably already closed, but catch all anyway
                pass

        self._closed = True
        self._ready.clear()

    def run(self, email: str, password: str):
        '''Login and connect to Guilded, and start the event loop.'''
        try:
            self.loop.create_task(self.start(
                email=email, 
                password=password
            ))
            self.loop.run_forever()
        except KeyboardInterrupt:
            exit()

    def get_message(self, id: str):
        '''Get a message from your :attr:Client.cached_messages. 
        As messages are often frequently going in and out of cache, you should not rely on this method, and instead use :class:Messageable.fetch_message.
        
        Parameters
        ==========
        id
            the id of the message

        Returns
        =======
        Optional[:class:`Message`]
        '''
        return self.http._get_message(id)

    def get_team(self, id: str):
        '''Get a team from your :attr:Client.teams.

        Parameters
        ==========
        id
            the id of the team

        Returns
        =======
        Optional[:class:`Team`]
        '''
        return self.http._get_team(id)

    def get_user(self, id: str):
        '''Get a user from your :attr:Client.users.

        Parameters
        ==========
        id
            the id of the user

        Returns
        =======
        Optional[:class:`User`]
        '''
        return self.http._get_user(id)

    def get_channel(self, id: str):
        '''Get a user from your :attr:Client.channels.

        Parameters
        ==========
        id
            the id of the team or dm channel

        Returns
        =======
        Optional[:class:`Messageable`]
        '''
        return self.http._get_team_channel(id) or self.http._get_dm_channel(id)

    async def on_error(self, event_method, *args, **kwargs):
        print(f'Ignoring exception in {event_method}:', file=sys.stderr)
        traceback.print_exc()

    async def search_teams(self, query: str):
        '''Search Guilded for public teams. Returns an array of partial :class:`Team`s.'''
        results = await self.http.search_teams(query)
        teams = []
        for team_object in results['results']['teams']:
            team_object['isPublic'] = True  # These results will only have public teams, however this attribute 
                                            # is not present in each object, so this compensates
            teams.append(Team(state=self.http, data=team_object))

        return teams

    async def join_team(self, id: str):
        '''Join a public team using its ID.

        Returns
        =======
        :class:Team - the team that you joined'''
        await self.http.join_team(id)
        team = await self.http.get_team(id)
        return 

    async def fetch_team(self, id: str):
        '''Fetch a team from the API.'''
        team = await self.http.get_team(id)
        return Team(state=self.http, data=team)

    async def getch_team(self, id: str):
        '''Try to get a team from internal cache, and if not found, try to fetch from the API.

        Equivalent to:

            team = client.get_team(id) or await client.fetch_team(id)

        '''
        return self.get_team(id) or await self.fetch_team(id)

    async def fetch_user(self, id: str):
        '''Fetch a user from the API.'''
        user = await self.http.get_user(id)
        return User(state=self.http, data=user)

    async def getch_user(self, id: str):
        '''Try to get a user from internal cache, and if not found, try to fetch from the API.

        Equivalent to:

            user = client.get_user(id) or await client.fetch_user(id)

        '''
        return self.get_user(id) or await self.fetch_user(id)

    async def getch_channel(self, id: str, team_id: str = None):
        '''Try to get a channel from internal cache, and if not found, try to fetch from the API.

        Roughly equivalent to:

            channel = client.get_channel(id) or await team.fetch_channel(id)

        '''
        channel = self.get_channel(id)
        if team_id is None and channel is None:
            raise NotFound(id)
        elif team_id is not None and channel is None:
            team = await self.getch_team(team_id)
            channel = team.get_channel(id) or await team.fetch_channel(id)

        return channel

    async def fetch_game(self, id: int):
        games = await self.http.get_game_list()
        name = games.get(str(id))
        if name is None:
            raise ValueError(f'{id} is not a recognized game id.')

        return name

    async def fetch_games(self):
        '''Fetch the whole documented game list.'''
        return await self.http.get_game_list()

    async def fill_game_list(self):
        '''Fill the internal game list cache from remote data.'''
        games = await self.fetch_games()
        Game.MAPPING = games
