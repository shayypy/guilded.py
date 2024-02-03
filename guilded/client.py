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

import aiohttp
import asyncio
import logging
import sys
import traceback
from typing import TYPE_CHECKING, Any, Callable, Coroutine, Generator, List, Optional, Type, Union

from .errors import ClientException, HTTPException
from .enums import *
from .events import BaseEvent
from .gateway import GuildedWebSocket, WebSocketClosure
from .http import HTTPClient
from .invite import Invite
from .server import Server
from .user import ClientUser, User
from .utils import MISSING

if TYPE_CHECKING:
    from types import TracebackType
    from typing_extensions import Self

    from .abc import ServerChannel
    from .channel import DMChannel, PartialMessageable
    from .emote import Emote
    from .message import ChatMessage
    from .user import Member

log = logging.getLogger(__name__)

__all__ = (
    'Client',
    'ClientFeatures',
)


class _LoopSentinel:
    __slots__ = ()

    def __getattr__(self, attr: str) -> None:
        msg = (
            'loop attribute cannot be accessed in non-async contexts. '
            'Consider using either an asynchronous main function and passing it to asyncio.run or '
            'using asynchronous initialisation hooks such as Client.setup_hook'
        )
        raise AttributeError(msg)

_loop: Any = _LoopSentinel()


class ClientFeatures:
    """Opt-in or out of Guilded or guilded.py features.

    All parameters are optional.

    Parameters
    -----------
    experimental_event_style: :class:`bool`
        Enables a more simplified event handling interface.
        Read more about this `here <https://www.guilded.gg/guilded-api/blog/updates/Event-style-experiment>`_.
    official_markdown: :class:`bool`
        Enables new (2024) markdown support for requests made by the client
        as well as events received.
    """
    def __init__(
        self,
        *,
        experimental_event_style: bool = False,
        official_markdown: bool = False,
    ) -> None:
        self.experimental_event_style = experimental_event_style
        self.official_markdown = official_markdown


class Client:
    """The basic client class for interfacing with Guilded.

    Parameters
    -----------
    internal_server_id: Optional[:class:`str`]
        The ID of the bot's internal server.
    max_messages: Optional[:class:`int`]
        The maximum number of messages to store in the internal message cache.
        This defaults to ``1000``. Passing in ``None`` disables the message cache.
    features: Optional[:class:`.ClientFeatures`]
        Client features to opt in or out of.

    Attributes
    -----------
    loop: :class:`asyncio.AbstractEventLoop`
        The event loop that the client uses for HTTP requests and websocket
        operations.
    ws: Optional[:class:`GuildedWebsocket`]
        The websocket gateway the client is currently connected to. Could be
        ``None``.
    internal_server_id: Optional[:class:`str`]
        The ID of the bot's internal server.
    max_messages: Optional[:class:`int`]
        The maximum number of messages to store in the internal message cache.
        This defaults to ``1000``. Passing in ``None`` disables the message cache.
    features: :class:`.ClientFeatures`
        The features that are enabled or disabled for the client.
    """

    def __init__(
        self,
        *,
        internal_server_id: Optional[str] = None,
        max_messages: Optional[int] = MISSING,
        features: Optional[ClientFeatures] = None,
        **options,
    ):
        # internal
        self.loop: asyncio.AbstractEventLoop = _loop
        self.max_messages: int = 1000 if max_messages is MISSING else max_messages
        self._listeners = {}

        self.features = features or ClientFeatures()
        # This option is deprecated
        if options.get('experimental_event_style') is not None:
            log.info("The `experimental_event_style` client parameter is deprecated, please switch to using ClientFeatures instead.")
            self.features.experimental_event_style = options.pop('experimental_event_style', False)

        # state
        self._closed: bool = False
        self._ready: asyncio.Event = MISSING

        self.internal_server_id = internal_server_id
        self.ws: Optional[GuildedWebSocket] = None
        self.http: HTTPClient = HTTPClient(
            max_messages=self.max_messages,
            features=self.features,
        )

    async def __aenter__(self) -> Self:
        await self._async_setup_hook()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        await self.close()

    @property
    def user(self) -> Optional[ClientUser]:
        """Optional[:class:`.ClientUser`]: The in-Guilded user data of the client.
        ``None`` if not logged in."""
        return self.http.user

    @property
    def user_id(self) -> Optional[str]:
        return self.http.my_id

    @property
    def cached_messages(self) -> List[ChatMessage]:
        """List[:class:`.ChatMessage`]: The list of cached messages that the client has seen recently."""
        return list(self.http._messages.values())

    @property
    def emotes(self) -> List[Emote]:
        """List[:class:`.Emote`]: The list of emotes that the client can see."""
        return list(self.http._emotes.values())

    @property
    def servers(self) -> List[Server]:
        """List[:class:`.Server`]: The list of servers that the client can see."""
        return list(self.http._servers.values())

    @property
    def users(self) -> List[User]:
        """List[:class:`~guilded.User`]: The list of users that the client can see.
        A user is not the same as a member, which is a server-specific representation.
        To get all members, use :meth:`.get_all_members`\."""
        return list(self.http._users.values())

    @property
    def dm_channels(self) -> List[DMChannel]:
        """List[:class:`.DMChannel`]: The private/DM channels that the client can see."""
        return list(self.http._dm_channels.values())

    @property
    def private_channels(self) -> List[DMChannel]:
        """List[:class:`DMChannel`]: |dpyattr|

        This is an alias of :attr:`.dm_channels`.

        The private/DM channels that the client can see.
        """
        return self.dm_channels

    @property
    def guilds(self) -> List[Server]:
        """List[:class:`.Server`]: |dpyattr|

        This is an alias of :attr:`.servers`.

        The list of servers that the client can see.
        """
        return self.servers

    @property
    def latency(self) -> float:
        return float('nan') if self.ws is None else self.ws.latency

    @property
    def closed(self) -> bool:
        return self._closed

    def is_ready(self) -> bool:
        return self._ready.is_set()

    def get_all_channels(self) -> Generator[ServerChannel, None, None]:
        """A generator that retrieves every :class:`~.abc.ServerChannel` the client can see.

        This is equivalent to: ::

            for server in client.servers:
                for channel in server.channels:
                    yield channel

        Yields
        ------
        :class:`~.abc.ServerChannel`
            A channel the client can see.
        """

        for server in self.servers:
            yield from server.channels

    def get_all_members(self) -> Generator[Member, None, None]:
        """Returns a generator yielding every :class:`.Member` that the client can see.

        This is equivalent to: ::

            for server in client.servers:
                for member in server.members:
                    yield member

        Yields
        -------
        :class:`.Member`
            A member the client can see.
        """
        for server in self.servers:
            yield from server.members

    async def wait_until_ready(self) -> None:
        """|coro|

        Waits until the client's internal cache is all ready.
        """
        await self._ready.wait()

    async def _async_setup_hook(self) -> None:
        self.loop = asyncio.get_running_loop()
        self._ready = asyncio.Event()

    async def setup_hook(self) -> None:
        """|coro|

        A coroutine to be called to setup the bot, by default this is blank.
        To perform asynchronous setup after the bot is logged in but before
        it has connected to the Websocket, overwrite this method.

        This is only called once, in :meth:`login`, and will be called before
        any events are dispatched, making it a better solution than doing such
        setup in the :func:`~.on_ready` event.

        .. warning::

            Since this is called *before* the websocket connection is made therefore
            anything that waits for the websocket will deadlock, this includes things
            like :meth:`.wait_for` and :meth:`.wait_until_ready`.
        """
        pass

    def wait_for(
        self,
        event: str,
        *,
        check: Optional[Callable[..., bool]] = None,
        timeout: Optional[float] = None,
    ) -> Any:
        """|coro|

        Waits for a WebSocket event to be dispatched.

        This could be used to wait for a user to reply to a message,
        or to react to a message, or to edit a message in a self-contained
        way.

        The ``timeout`` parameter is passed onto :func:`asyncio.wait_for`. By
        default, it does not timeout. Note that this does propagate the
        :exc:`asyncio.TimeoutError` for you in case of timeout and is provided
        for ease of use.

        In case the event returns multiple arguments, a :class:`tuple`
        containing those arguments is returned instead. Please check the
        :ref:`documentation <guilded-api-events>` for a list of events and
        their parameters.

        This function returns the **first event that meets the requirements**.

        Examples
        ---------

        Waiting for a user reply: ::

            @client.event
            async def on_message(message):
                if message.content.startswith('$greet'):
                    channel = message.channel
                    await channel.send('Say hello!')

                    def check(m):
                        return m.content == 'hello' and m.channel == channel

                    msg = await client.wait_for('message', check=check)
                    await channel.send(f'Hello {msg.author}!')

        Waiting for a thumbs up reaction from the message author: ::

            @client.event
            async def on_message(message):
                if message.content.startswith('$thumb'):
                    channel = message.channel
                    await channel.send('Send me that \N{THUMBS UP SIGN} reaction, mate')

                    def check(reaction):
                        return reaction.user == message.author and reaction.emote.id == 90001164  # https://gist.github.com/shayypy/8e492ad2d8801bfd38415986f68a547e

                    try:
                        reaction = await client.wait_for('message_reaction_add', timeout=60.0, check=check)
                    except asyncio.TimeoutError:
                        await channel.send('\N{THUMBS DOWN SIGN}')
                    else:
                        await channel.send('\N{THUMBS UP SIGN}')


        Parameters
        -----------
        event: :class:`str`
            The event name, similar to the :ref:`event reference <guilded-api-events>`,
            but without the ``on_`` prefix, to wait for.
        check: Optional[Callable[..., :class:`bool`]]
            A predicate to check what to wait for. The arguments must meet the
            parameters of the event being waited for.
        timeout: Optional[:class:`float`]
            The number of seconds to wait before timing out and raising
            :exc:`asyncio.TimeoutError`.

        Raises
        -------
        asyncio.TimeoutError
            If a timeout is provided and it was reached.

        Returns
        --------
        Any
            Returns no arguments, a single argument, or a :class:`tuple` of multiple
            arguments that mirrors the parameters passed in the
            :ref:`event reference <guilded-api-events>`.
        """

        future = self.loop.create_future()
        if check is None:

            def _check(*args):
                return True

            check = _check

        ev = event.lower()
        try:
            listeners = self._listeners[ev]
        except KeyError:
            listeners = []
            self._listeners[ev] = listeners

        listeners.append((future, check))
        return asyncio.wait_for(future, timeout)

    async def _run_event(self, coro: Coroutine, event_name: str, *args: Any, **kwargs: Any) -> None:
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
        return self.loop.create_task(wrapped, name=f'guilded.py: {event_name}')

    def event(self, coro: Coroutine) -> Coroutine:
        """A decorator to register an event for the library to automatically dispatch when appropriate.

        You can find more info about the events on the :ref:`documentation below <guilded-api-events>`.

        The events must be a :ref:`coroutine <coroutine>`, if not, :exc:`TypeError` is raised.

        Example
        --------

        .. code-block:: python3

            @client.event
            async def on_ready():
                print('Ready!')

        Raises
        -------
        :class:`TypeError`
            The function passed is not actually a coroutine.
        """

        if not asyncio.iscoroutinefunction(coro):
            raise TypeError('Event must be a coroutine.')

        setattr(self, coro.__name__, coro)
        log.debug('%s has successfully been registered as an event', coro.__name__)
        return coro

    def dispatch(self, event: Union[str, BaseEvent], *args: Any, **kwargs: Any) -> None:
        if isinstance(event, BaseEvent):
            event_name = event.__dispatch_event__
            args = (event,)
        else:
            event_name = event

        log.debug('Dispatching event %s', event_name)
        method = 'on_' + event_name

        listeners = self._listeners.get(event_name)
        if listeners:
            removed = []
            for i, (future, condition) in enumerate(listeners):
                if future.cancelled():
                    removed.append(i)
                    continue

                try:
                    result = condition(*args)
                except Exception as exc:
                    future.set_exception(exc)
                    removed.append(i)
                else:
                    if result:
                        if len(args) == 0:
                            future.set_result(None)
                        elif len(args) == 1:
                            future.set_result(args[0])
                        else:
                            future.set_result(args)
                        removed.append(i)

            if len(removed) == len(listeners):
                self._listeners.pop(event_name)
            else:
                for idx in reversed(removed):
                    del listeners[idx]

        try:
            coro = getattr(self, method)
        except AttributeError:
            pass
        else:
            self._schedule_event(coro, method, *args, **kwargs)

    def get_partial_messageable(
        self,
        id: str,
        *,
        server_id: str = None,
        group_id: str = None,
        type: ChannelType = None,
        guild_id: str = None,
    ) -> PartialMessageable:
        """Returns a partial messageable with the given channel ID.

        This is useful if you have a channel ID but don't want to do an API
        call to send messages to it.

        .. versionadded:: 1.4

        Parameters
        -----------
        id: :class:`str`
            The channel ID to create a partial messageable for.
        server_id: Optional[:class:`str`]
            The server ID that the channel is in.
            This is not required to send messages, but it is necessary for the
            :attr:`~PartialMessageable.jump_url` and :attr:`~PartialMessageable.server`
            properties to work properly.
        group_id: Optional[:class:`str`]
            The group ID that the channel is in.
            This is not required to send messages, but when combined with ``server_id``, it helps
            the :attr:`~PartialMessageable.jump_url` property to render properly in the client,
            and it allows the :attr:`~PartialMessageable.group` property to work properly.
        type: Optional[:class:`ChannelType`]
            The underlying channel type for the partial messageable.
            This does not have to be a messageable type, but Guilded will reject
            the request if you attempt to send to a non-messageable channel.

        Returns
        --------
        :class:`PartialMessageable`
            The partial messageable that was created.

        Raises
        -------
        ValueError
            Cannot provide both ``server_id`` and ``guild_id``
        """

        if server_id and guild_id:
            raise ValueError('Cannot provide both server_id and guild_id')

        from .channel import PartialMessageable

        return PartialMessageable(
            state=self.http,
            id=id,
            server_id=server_id or guild_id,
            group_id=group_id,
            type=type,
        )

    def get_message(self, message_id: str, /) -> Optional[ChatMessage]:
        """Optional[:class:`.ChatMessage`]: Get a message from your :attr:`.cached_messages`. 

        As messages frequently enter and exit cache, you generally should not rely on this method.
        Instead, use :meth:`.abc.Messageable.fetch_message`.
        """
        return self.http._get_message(message_id)

    def get_server(self, server_id: str, /) -> Optional[Server]:
        """Optional[:class:`.Server`]: Get a server from your :attr:`.servers`."""
        return self.http._get_server(server_id)

    def get_user(self, user_id: str, /) -> Optional[User]:
        """Optional[:class:`~guilded.User`]: Get a user from your :attr:`.users`."""
        return self.http._get_user(user_id)

    def get_channel(self, channel_id: str, /) -> Optional[ServerChannel]:
        """Optional[:class:`~.abc.ServerChannel`]: Get a server channel or DM
        channel from your channels."""
        return self.http._get_global_server_channel(channel_id) or self.http._get_dm_channel(channel_id)

    def get_emote(self, emote_id: int, /) -> Optional[Emote]:
        """Optional[:class:`.Emote`]: Get an emote from your :attr:`.emotes`."""
        for server in self.servers:
            emote = server.get_emote(emote_id)
            if emote:
                return emote

        return None

    async def fetch_user(self, user_id: str, /) -> User:
        """|coro|

        Fetch a user from the API.

        Returns
        --------
        :class:`~guilded.User`
            The user from the ID.
        """

        data = await self.http.get_user(user_id)
        return User(state=self.http, data=data['user'])

    async def getch_user(self, user_id: str, /) -> User:
        """|coro|

        Try to get a user from internal cache, and if not found, try to fetch from the API.

        Returns
        --------
        :class:`~guilded.User`
            The user from the ID.
        """
        return self.get_user(user_id) or await self.fetch_user(user_id)

    async def fetch_public_server(self, server_id: str, /) -> Server:
        """|coro|

        Fetch a public server from the API.

        The client does not need to be a member of the server to use this method,
        but the server must have "Discoverable" enabled in its :ghelp:`privacy settings <4805347381655>`.

        This method will be limiting for you if you are a member of the server and are permitted to see non-public information.
        If this is the case, use :meth:`.fetch_server` instead.

        Returns
        --------
        :class:`.Server`
            The server from the ID.

        Raises
        -------
        NotFound
            The server does not exist or it is private.
        """

        data = await self.http.get_team_info(server_id)
        return Server(state=self.http, data=data['team'])

    async def fetch_server(self, server_id: str, /) -> Server:
        """|coro|

        Fetch a server from the API.

        Returns
        --------
        :class:`.Server`
            The server from the ID.
        """

        data = await self.http.get_server(server_id)
        return Server(state=self.http, data=data['server'], member_count=data.get("serverMemberCount"))

    async def getch_server(self, server_id: str, /) -> Server:
        """|coro|

        Try to get a server from internal cache, and if not found, try to fetch from the API.

        Returns
        --------
        :class:`.Server`
            The server from the ID.
        """
        return self.get_server(server_id) or await self.fetch_server(server_id)

    async def fetch_servers(self) -> List[Server]:
        """|coro|

        Fetch your list of servers from the API.

        .. versionadded:: 1.8

        Returns
        --------
        List[:class:`.Server`]
            The servers you are a member of.
        """

        data = await self.http.get_my_servers()
        return [Server(state=self.http, data=server_data) for server_data in data['servers']]

    async def fetch_channel(self, channel_id: str) -> ServerChannel:
        """|coro|

        Fetch a channel from the API.

        Returns
        --------
        :class:`~.abc.ServerChannel`
            The channel from the ID.
        """
        data = await self.http.get_channel(channel_id)
        channel = self.http.create_channel(data=data['channel'])
        return channel

    async def getch_channel(self, channel_id: str) -> ServerChannel:
        """|coro|

        Try to get a channel from internal cache, and if not found, try to fetch from the API.

        Returns
        --------
        :class:`~.abc.ServerChannel`
            The channel from the ID.
        """
        return self.get_channel(channel_id) or await self.fetch_channel(channel_id)

    async def fetch_invite(self, invite_id: str) -> Invite:
        """|coro|

        Fetch an invite from the API.

        .. note::

            This method does not support vanity invites or full URLs.

        Returns
        --------
        :class:`.Invite`
            The invite from the ID.
        """

        data = await self.http.get_metadata(f'/i/{invite_id}')
        invite = Invite(
            data=data['metadata']['inviteInfo'],
            canonical=data['metadata'].get('canonicalUrl'),
            state=self.http,
        )
        return invite

    async def set_status(self, emote: Emote, *, content: Optional[str] = MISSING) -> None:
        """|coro|

        Update your custom status.

        This method cannot be used to remove your status.
        Instead, use :meth:`.remove_status`.

        .. versionadded: 1.9

        Parameters
        -----------
        emote: :class:`Emote`
            The emote displayed to the left of the content.

            .. note::

                Perhaps unexpectedly, this parameter is required by Guilded.
                If you do not wish to provide it, ``90002547`` is the default
                emote ID used by the desktop client.

        content: Optional[:class:`str`]
            The text content of the status.
        """

        emote_id: int = getattr(emote, 'id', emote)
        payload = {
            'emoteId': emote_id,
        }

        if content is not MISSING:
            payload['content'] = content

        await self.http.update_my_status(payload)

    async def remove_status(self) -> None:
        """|coro|

        Remove your custom status.

        .. versionadded: 1.9
        """
        await self.http.delete_my_status()

    async def on_error(self, event_method, *args, **kwargs) -> None:
        print(f'Ignoring exception in {event_method}:', file=sys.stderr)
        traceback.print_exc()

    async def start(self, token: str = None, *, reconnect: bool = True) -> None:
        self.http.token = token or self.http.token
        if not self.http.token:
            raise ClientException(
                'You must provide a token to this method explicitly, or have '
                'it already set in this Client\'s HTTPClient beforehand.'
            )

        self.http.session = aiohttp.ClientSession()

        await self._async_setup_hook()
        await self.setup_hook()

        # The gateway does not send the client's servers upon connecting
        servers = await self.fetch_servers()
        for server in servers:
            self.http.add_to_server_cache(server)

        if self.internal_server_id and not self.get_server(self.internal_server_id):
            log.warn(
                'Internal server (ID: %s) was not found in the list of client servers.',
                self.internal_server_id,
            )

        await self.connect(token, reconnect=reconnect)

    async def connect(self, token: str = None, *, reconnect: bool = True) -> None:
        self.http.token = token or self.http.token
        if not self.http.token:
            raise ClientException(
                'You must provide a token to this method explicitly, or have '
                'it already set in this Client\'s HTTPClient beforehand.'
            )

        while not self.closed:
            ws_build = GuildedWebSocket.build(self, loop=self.loop)
            gws = await asyncio.wait_for(ws_build, timeout=60)
            if type(gws) != GuildedWebSocket:
                self.dispatch('error', gws)
                return

            self.ws = gws
            self.http.ws = self.ws
            self.dispatch('connect')

            async def listen_socks(ws: GuildedWebSocket):
                next_backoff_time = 5
                while True and ws is not None:
                    try:
                        op = await ws.poll_event()
                    except WebSocketClosure as exc:
                        self.dispatch('disconnect')

                        code = ws._close_code or ws.socket.close_code
                        if code == 1000:
                            break

                        if reconnect is False:
                            log.warning('Websocket closed with code %s. Last message ID was %s', code, ws._last_message_id)
                            await self.close()
                            break

                        if exc.data and exc.data.get('op') == GuildedWebSocket.INVALID_CURSOR:
                            ws._last_message_id = None

                        if ws._last_message_id:
                            log.warning('Websocket closed with code %s, attempting to reconnect in %s seconds with last message ID %s', code, next_backoff_time, ws._last_message_id)
                        else:
                            log.warning('Websocket closed with code %s, attempting to reconnect in %s seconds', code, next_backoff_time)

                        await asyncio.sleep(next_backoff_time)

                        build = GuildedWebSocket.build(self, loop=self.loop)
                        try:
                            ws = await asyncio.wait_for(build, timeout=60)
                        except asyncio.TimeoutError:
                            log.warning('Timed out trying to reconnect.')
                            next_backoff_time += 5
                        else:
                            if type(ws) != GuildedWebSocket:
                                self.dispatch('error', ws)
                                await self.close()
                                break
                            else:
                                self.ws = ws
                                self.http.ws = self.ws
                                self.dispatch('connect')
                    else:
                        next_backoff_time = 5
                        if op == GuildedWebSocket.WELCOME:
                            # Because of how the gateway works currently, most of our initial cache
                            # is filled before connecting. The exception to this is `client.user`,
                            # which depends on the gateway WELCOME event. Thusly, after received_event
                            # finishes handling a WELCOME, we know that the client is ready.

                            # This handling will cause the ready event to be fired multiple times if
                            # a reconnection happens, but this is to be expected with discord.py as well.
                            self._ready.set()
                            self.dispatch('ready')

            await listen_socks(self.ws)

    async def close(self) -> None:
        """|coro|

        Close the current connection.
        """
        if self._closed:
            return

        await self.http.close()
        self._closed = True

        try:
            await self.ws.close(code=1000)
        except Exception:
            # it's probably already closed, but catch all anyway
            pass

        self._ready.clear()

    def run(self, token: str, *, reconnect=True) -> None:
        """Connect to Guilded's gateway and start the event loop. This is a
        blocking call; nothing after it will be called until the bot has been
        closed.

        Parameters
        -----------
        token: :class:`str`
            The bot's auth token.
        reconnect: Optional[:class:`bool`]
            Whether to reconnect on loss/interruption of gateway connection.
        """

        async def runner():
            async with self:
                await self.start(
                    token,
                    reconnect=reconnect,
                )

        try:
            asyncio.run(runner())
        except KeyboardInterrupt:
            return
