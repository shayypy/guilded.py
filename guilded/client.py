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
import logging
import sys
import traceback

import aiohttp

from .errors import NotFound
from .embed import Embed
from .gateway import GuildedWebSocket, WebSocketClosure
from .http import HTTPClient
from .presence import Presence
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
    """The basic client class for interfacing with Guilded.

    Parameters
    ----------
    max_messages: Optional[:class:`int`]
        The maximum number of messages to store in the internal message cache.
        This defaults to ``1000``. Passing in ``None`` disables the message cache.
    loop: Optional[:class:`asyncio.AbstractEventLoop`]
        The :class:`asyncio.AbstractEventLoop` to use for asynchronous operations.
        Defaults to ``None``, in which case the default event loop is used via
        :func:`asyncio.get_event_loop()`.
    disable_team_websockets: Optional[:class:`bool`]
        Whether to prevent the library from opening team-specific websocket
        connections.

    presence: Optional[:class:`.Presence`]
        A presence to use upon logging in.
    status: Optional[:class:`.Status`]
        A status (game) to use upon logging in.
    Attributes
    -----------
    ws
        The websocket gateway the client is currently connected to. Could be ``None``.
    loop: :class:`asyncio.AbstractEventLoop`
        The event loop that the client uses for HTTP requests and websocket operations.
    """
    def __init__(self, **options):
        # internal
        self.loop = options.pop('loop', asyncio.get_event_loop())
        self.user = None
        self.max_messages = options.pop('max_messages', 1000)
        self.disable_team_websockets = options.pop('disable_team_websockets', False)
        self._login_presence = options.pop('presence', None)
        self._login_status = options.pop('status', None)
        self._listeners = {}

        cache_on_startup = options.pop('cache_on_startup', {})
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
        """List[:class:`.DMChannel`]: The private/dm channels that the connected client can see."""
        return list(self.http._dm_channels.values())

    @property
    def private_channels(self):
        """List[:class:`.DMChannel`]: |dpyattr|

        This is an alias of :attr:`.dm_channels`.
        """
        return self.dm_channels

    @property
    def team_channels(self):
        """List[:class:`.TeamChannel`]: The team channels that the connected client can see."""
        return list(self.http._team_channels.values())

    @property
    def channels(self):
        """List[Union[:class:`.TeamChannel`, :class:`.DMChannel`]]: The channels (Team and DM included) that the connected client can see."""
        return [*self.dm_channels, *self.team_channels]

    @property
    def guilds(self):
        """List[:class:`.Team`]: |dpyattr|

        This is an alias of :attr:`.teams`.
        """
        return self.teams

    @property
    def latency(self):
        return float('nan') if self.ws is None else self.ws.latency

    @property
    def closed(self):
        return self._closed

    def is_ready(self):
        return self._ready.is_set()

    async def wait_until_ready(self):
        await self._ready.wait()

    async def _run_event(self, coro, event_name, *args, **kwargs):
        try:
            await coro(*args, **kwargs)
        except asyncio.CancelledError:
            pass
        except Exception:
            try:
                await self.on_error(event_name, *args, **kwargs)
            except asyncio.CancelledError:
                pass

    def _schedule_event(self, coro, event_name, *args, **kwargs):
        wrapped = self._run_event(coro, event_name, *args, **kwargs)
        # Schedules the task
        return asyncio.create_task(wrapped, name=f'guilded.py: {event_name}')

    def event(self, coro):
        """A decorator to register an event for the library to automatically dispatch when appropriate.

        The events must be a :ref:`coroutine <coroutine>`, if not, :exc:`TypeError` is raised.

        Example
        ---------

        .. code-block:: python3

            @client.event
            async def on_ready():
                print('Ready!')

        Raises
        --------
        TypeError
            The function passed is not actually a coroutine.
        """
        if not asyncio.iscoroutinefunction(coro):
            raise TypeError('Event must be a coroutine.')

        setattr(self, coro.__name__, coro)
        self._listeners[coro.__name__] = coro
        return coro

    def dispatch(self, event_name, *args, **kwargs):
        coro = self._listeners.get(f'on_{event_name}')
        if not coro:
            return
        self.loop.create_task(coro(*args, **kwargs))

    async def start(self, email, password, *, reconnect=True):
        """|coro|

        Login and connect to Guilded using a user account email and password.
        """
        self.http = self.http or HTTPClient(session=aiohttp.ClientSession(loop=self.loop), max_messages=self.max_messages)
        await self.login(email, password)
        await self.connect()

    async def login(self, email, password):
        data = await self.http.login(email, password)
        me = ClientUser(state=self.http, data=data)
        self.http.my_id = me.id
        self.user = me

        for team_data in data.get('teams'):
            team = Team(state=self.http, data=team_data)

            if self.cache_on_startup['members'] is True:
                members = await team.fetch_members()
                for member in members: self.http.add_to_member_cache(member)

            if self.cache_on_startup['channels'] is True:
                channels = await team.fetch_channels()
                for channel in channels:
                    if channel is None:
                        continue
                    self.http.add_to_team_channel_cache(channel)

            self.http.add_to_team_cache(team)

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

            if self._login_presence is not None:
                # we do this here because why bother setting a presence if you won't show up in the online list anyway
                await self.change_presence(self._login_presence)

            #if self._login_presence is Presence.online:
            # todo: start http ping thread
            # no need to do that if you don't want an online presence

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
                        if teamId:
                            build = GuildedWebSocket.build(self, loop=self.loop, teamId=teamId)
                        else:
                            # possible reconnect issues brought up by @8r2y5
                            build = GuildedWebSocket.build(self, loop=self.loop)
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
        """|coro|"""
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
        """Login and connect to Guilded, and start the event loop. This is a
        blocking call, nothing after it will be called until the bot has been
        closed.
        """
        try:
            self.loop.create_task(self.start(
                email=email, 
                password=password
            ))
            self.loop.run_forever()
        except KeyboardInterrupt:
            exit()

    def get_message(self, id: str):
        """Optional[:class:`Message`]: Get a message from your :attr:`.cached_messages`. 
        As messages are often frequently going in and out of cache, you should
        not rely on this method, and instead use :meth:`abc.Messageable.fetch_message`.
        
        Parameters
        ------------
        id: :class:`str`
            the id of the message

        Returns
        ---------
        Optional[:class:`Message`]
            The message from the ID
        """
        return self.http._get_message(id)

    def get_team(self, id: str):
        """Optional[:class:`Team`]: Get a team from your :attr:`.teams`.

        Parameters
        ------------
        id: :class:`str`
            the id of the team

        Returns
        ---------
        Optional[:class:`Team`]
            The team from the ID
        """
        return self.http._get_team(id)

    def get_user(self, id: str):
        """Optional[:class:`User`]: Get a user from your :attr:`.users`.

        Parameters
        ------------
        id: :class:`str`
            the id of the user

        Returns
        ---------
        Optional[:class:`User`]
            The user from the ID
        """
        return self.http._get_user(id)

    def get_channel(self, id: str):
        """Optional[:class:`Messageable`]: Get a user from your :attr:`.channels`.

        Parameters
        ------------
        id: :class:`str`
            the id of the team or dm channel

        Returns
        ---------
        Optional[:class:`abc.Messageable`]
            The channel from the ID
        """
        return self.http._get_global_team_channel(id) or self.http._get_dm_channel(id)

    async def on_error(self, event_method, *args, **kwargs):
        print(f'Ignoring exception in {event_method}:', file=sys.stderr)
        traceback.print_exc()

    async def search_teams(self, query: str):
        """|coro|

        Search Guilded for public teams. Returns an array of partial teams.

        Returns
        ---------
        List[:class:`Team`]
            The teams from the query
        """
        results = await self.http.search_teams(query)
        teams = []
        for team_object in results['results']['teams']:
            team_object['isPublic'] = True  # These results will only have public teams, however this attribute 
                                            # is not present in each object, so this compensates
            teams.append(Team(state=self.http, data=team_object))

        return teams

    async def join_team(self, id: str):
        """|coro|

        Join a public team using its ID.

        Returns
        ---------
        :class:`Team`
            The team you joined from the ID
        """
        await self.http.join_team(id)
        team = await self.http.get_team(id)
        return 

    async def fetch_team(self, id: str):
        """|coro|

        Fetch a team from the API.

        Returns
        ---------
        :class:`Team`
            The team from the ID
        """
        team = await self.http.get_team(id)
        return Team(state=self.http, data=team)

    async def getch_team(self, id: str):
        """|coro|

        Try to get a team from internal cache, and if not found, try to fetch from the API.
        
        Returns
        ---------
        :class:`Team`
            The team from the ID
        """
        return self.get_team(id) or await self.fetch_team(id)

    async def fetch_user(self, id: str):
        """|coro|

        Fetch a user from the API.

        Returns
        ---------
        :class:`User`
            The user from the ID
        """
        user = await self.http.get_user(id)
        return User(state=self.http, data=user)

    async def getch_user(self, id: str):
        """|coro|

        Try to get a user from internal cache, and if not found, try to fetch from the API.
        
        Returns
        ---------
        :class:`User`
            The user from the ID
        """
        return self.get_user(id) or await self.fetch_user(id)

    async def getch_channel(self, id: str, team_id: str = None):
        """|coro|

        Try to get a channel from internal cache, and if not found, try to fetch from the API.

        Returns
        ---------
        Union[:class:`TeamChannel`, :class:`DMChannel`]
            The channel from the ID
        """
        channel = self.get_channel(id)
        if team_id is None and channel is None:
            raise NotFound(id)
        elif team_id is not None and channel is None:
            team = await self.getch_team(team_id)
            channel = team.get_channel(id) or await team.fetch_channel(id)

        return channel

    async def fetch_game(self, id: int):
        """|coro|

        Fetch a game from the `documentation's game list <https://guildedapi.com/resources/user/#transient-status-object>`_ (an incomplete listing of every game Guilded has a registered name for)
        
        Returns
        ---------
        :class:`Game`
            The game with the ID
        """
        if not Game.MAPPING:
            await self.fill_game_list()

        game = Game(id)
        if game.name is None:
            raise ValueError(f'{id} is not a recognized game id.')

        return game

    async def fetch_games(self):
        """|coro|

        Fetch the whole documented game list.
        
        Returns
        ---------
        :class:`dict`
            The whole game list (`viewable here <https://github.com/GuildedAPI/datatables/blob/main/games.json>`_)
        """
        return await self.http.get_game_list()

    async def fill_game_list(self):
        """|coro|

        Fill the internal game list cache from remote data.
        """
        games = await self.fetch_games()
        Game.MAPPING = games

    async def update_privacy_settings(self, *, dms, friend_requests):
        await self.http.set_privacy_settings(dms=dms, friend_requests=friend_requests)

    async def fetch_blocked_users(self):
        """|coro|

        The users the client has blocked.

        Returns
        ---------
        List[:class:`User`]
        """
        settings = await self.http.get_privacy_settings()
        blocked = []
        for user in settings.get('blockedUsers', []):
            blocked.append(User(state=self.http, data=user))

        return blocked

    async def change_presence(self, *args):
        pass

    async def fetch_subdomain(self, subdomain: str):
        """|coro|

        Check if a subdomain (profile/team vanity url) is available.

        Returns
        --------
        Optional[Union[:class:`User`, :class:`Team`]]
            The user or team that is using this subdomain.
        """
        value = await self.http.check_subdomain(subdomain)
        if (value or {}).get('exists') == True:
            # currently this endpoint returns {} if the subdomain does not
            # exist, but just in case it eventually returns 204 or whatever,
            # we check more explicitly instead.
            if value.get('teamId'):
                using_subdomain = await self.getch_team(value.get('teamId'))
            elif value.get('userId'):
                using_subdomain = await self.getch_user(value.get('userId'))

            return using_subdomain

        else:
            return None

    async def fetch_metadata(self, route: str):
        """|coro|

        This is essentially a barebones wrapper method for the Get Metadata
        endpoint; it returns raw JSON data from the metadata route provided.

        Returns
        --------
        :class:`dict`
        """
        data = await self.http.get_metadata(route)
        return data

    async def fetch_link_embed(self, url: str):
        """|coro|

        Fetch the OpenGraph data for a URL. The request made here is to
        Guilded, not directly to the website, so any images will contain
        proxy URLs.

        Returns
        --------
        :class:`Embed`
        """
        data = await self.http.get_embed_for_url(url)
        embed = Embed.from_unfurl_dict(data)
        return embed
