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

import time
import aiohttp
import asyncio
import concurrent.futures
import json
import logging
import sys
import threading
import traceback
from typing import TYPE_CHECKING, Optional

from .errors import GuildedException, HTTPException
from .channel import *
from .reaction import RawReactionActionEvent, Reaction
from .role import Role
from .user import ClientUser, Member
from .utils import ISO8601
from .webhook import Webhook

if TYPE_CHECKING:
    from typing_extensions import Self

    from .types.gateway import *

    from .client import Client


log = logging.getLogger(__name__)


class WebSocketClosure(Exception):
    """An exception to make up for the fact that aiohttp doesn't signal closure."""
    def __init__(self, message: str, data: Optional[str]):
        self.data: Optional[Dict]
        try:
            self.data = json.loads(data)
        except:
            self.data = None

        super().__init__(message)


class GuildedWebSocket:
    """Implements Guilded's WebSocket gateway.

    Attributes
    ------------
    MISSABLE
        Receieve only. Denotes either a message that could be missed (contains
        a message ID to resume with), or a previously-missed message that is
        being returned to you while resuming.
    WELCOME
        Received upon connecting to the gateway, either initially or after a
        resume.
    RESUMED
        Received after a successful resume. Signals that you are caught up
        with your missed messages, if any.
    INVALID_CURSOR
        Received upon trying to connect with invalid data.
    INTERNAL_ERROR
        Received when Guilded has an internal error.
    socket: :class:`aiohttp.ClientWebSocketResponse`
        The underlying aiohttp websocket instance.
    """

    MISSABLE = 0
    WELCOME = 1
    RESUMED = 2
    INVALID_CURSOR = 8
    INTERNAL_ERROR = 9

    def __init__(
        self,
        socket: aiohttp.ClientWebSocketResponse,
        client: Client,
        *,
        loop: asyncio.AbstractEventLoop
    ):
        self.client = client
        self.loop = loop
        self._heartbeater = None

        # socket
        self.socket: aiohttp.ClientWebSocketResponse = socket
        self._close_code: Optional[int] = None

        # ws
        self._last_message_id: Optional[str] = None

    @property
    def latency(self):
        return float('inf') if self._heartbeater is None else self._heartbeater.latency

    async def poll_event(self) -> Optional[int]:
        msg = await self.socket.receive()

        if msg.type is aiohttp.WSMsgType.TEXT:
            op = await self.received_event(msg.data)
            return op

        elif msg.type is aiohttp.WSMsgType.PONG:
            if self._heartbeater:
                self._heartbeater.record_pong()

        elif msg.type is aiohttp.WSMsgType.ERROR:
            raise msg.data

        elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.CLOSING, aiohttp.WSMsgType.CLOSE):
            raise WebSocketClosure('Socket is in a closed or closing state.', msg.data)

    async def send(self, payload: dict) -> None:
        payload = json.dumps(payload)
        self.client.dispatch('socket_raw_send', payload)
        await self.socket.send_str(payload)

    async def ping(self) -> None:
        log.debug('Sending heartbeat')
        await self.socket.ping()

    async def close(self, code: int = 1000) -> None:
        log.debug('Closing websocket connection with code %s', code)
        if self._heartbeater:
            self._heartbeater.stop()
            self._heartbeater = None

        self._close_code = code
        await self.socket.close(code=code)

    @classmethod
    async def build(cls, client: Client, *, loop: asyncio.AbstractEventLoop = None) -> Self:
        try:
            socket = await client.http.ws_connect()
        except aiohttp.client_exceptions.WSServerHandshakeError as exc:
            log.error('Failed to connect to the gateway: %s', exc)
            return exc
        else:
            log.info('Connected to the gateway')

        ws = cls(socket, client, loop=loop or asyncio.get_event_loop())
        ws._parsers = WebSocketEventParsers(client)
        await ws.ping()

        return ws

    async def received_event(self, payload: str) -> int:
        self.client.dispatch('socket_raw_receive', payload)
        data: EventSkeleton = json.loads(payload)
        log.debug('WebSocket has received %s', data)

        op = data['op']
        t = data.get('t')
        d = data.get('d')
        message_id = data.get('s')
        if message_id is not None:
            self._last_message_id = message_id

        if op == self.WELCOME:
            d: WelcomeEvent
            self._heartbeater = Heartbeater(ws=self, interval=d['heartbeatIntervalMs'] / 1000)
            self._heartbeater.start()
            self._last_message_id = d['lastMessageId']
            self.client.http.user = ClientUser(state=self.client.http, data=d['user'])
            self.client.http.my_id = self.client.http.user.id

        if op == self.MISSABLE:
            d['serverId'] = d.get('serverId')
            try:
                should_fill = self.client.get_server(d['serverId']) is None
                server = await self.client.getch_server(d['serverId'])
            except HTTPException as exc:
                # This shouldn't happen
                log.warn(
                    'Received unfetchable server ID %s (%s: %s). Constructing a partial server instance instead.',
                    d['serverId'],
                    exc.status,
                    exc.message,
                )

                from .server import Server

                d['server'] = Server(
                    state=self.client.http,
                    data={
                        'id': d['serverId'],
                    }
                )
            except:
                server = None

            if server:
                if should_fill:
                    await server.fill_members()

                # For now we add 'new' servers to cache as there is no other
                # way to passively receive all of the client's servers, and we
                # don't want to fetch them every time and slow down bots.
                self.client.http.add_to_server_cache(server)

            event = self._parsers.get(t, d)
            if event is not None:
                # ignore unhandled events
                try:
                    await event
                except GuildedException as e:
                    self.client.dispatch('error', e)
                    raise
                except Exception as e:
                    # wrap error if not already from the lib
                    exc = GuildedException(e)
                    self.client.dispatch('error', exc)
                    raise exc from e

        if op == self.INVALID_CURSOR:
            d: InvalidCursorEvent
            log.error('Invalid cursor: %s', d['message'])

        if op == self.INTERNAL_ERROR:
            d: InternalErrorEvent
            log.error('Internal error: %s', d['message'])

        return op


class WebSocketEventParsers:
    def __init__(self, client: Client):
        self.client = client
        self._state = client.http

    def get(
        self,
        event_name: str,
        data: Dict[str, Any],
    ):
        coro = getattr(self, event_name, None)
        if not coro:
            return None

        return coro(data)

    async def ChatMessageCreated(self, data: ChatMessageCreatedEvent):
        server_id = data['serverId']
        server = self.client.get_server(server_id)
        message_data = data['message']

        channel = self._state._get_server_channel_or_thread(server_id, message_data['channelId'])
        if channel is None:
            try:
                channel = await server.fetch_channel(message_data['channelId'])
            except HTTPException:
                channel = self._state.create_channel(
                    data={
                        'id': message_data['channelId'],
                        'type': 'chat',
                        'serverId': server_id,
                    },
                    server=server,
                )

        if channel is not None:
            self._state.add_to_server_channel_cache(channel)

        async def user_fallback():
            # This function should really never be needed in the current API
            try:
                user = await self.client.getch_user(author_id)
            except HTTPException:
                # A 4xx should never happen here, but just to be safe we catch all `HTTPException`s
                user = self._state.create_user(
                    data={
                        'id': author_id,
                    }
                )
            else:
                self._state.add_to_user_cache(user)
            return user

        author_id = message_data.get('createdBy')
        if author_id != self._state.GIL_ID:
            if server is not None:
                try:
                    author = await server.getch_member(author_id)
                except HTTPException:
                    author = await user_fallback()
                else:
                    self._state.add_to_member_cache(author)
            else:
                author = await user_fallback()
        else:
            author = None

        message = self._state.create_message(data=data, channel=channel, author=author)
        self._state.add_to_message_cache(message)

        self.client.dispatch('message', message)

    async def ChatMessageUpdated(self, data: ChatMessageUpdatedEvent):
        self.client.dispatch('raw_message_edit', data)
        before = self._state._get_message(data['message']['id'])
        if before is None:
            return

        after = self._state.create_message(data={'serverId': data['serverId'], **data['message']}, channel=before.channel)
        self._state.add_to_message_cache(after)
        self.client.dispatch('message_edit', before, after)

    async def ChatMessageDeleted(self, data: ChatMessageDeletedEvent):
        message = self._state._get_message(data['message']['id'])
        data['cached_message'] = message
        self.client.dispatch('raw_message_delete', data)
        if message is not None:
            self._state._messages.pop(message.id, None)
            message.deleted_at = ISO8601(data['message']['deletedAt'])
            self.client.dispatch('message_delete', message)

    async def TeamMemberJoined(self, data: TeamMemberJoinedEvent):
        server = self.client.get_server(data['serverId'])
        if server is None:
            return

        member = self._state.create_member(data={
            'serverId': server.id,
            **data['member'],
        })
        server._members[member.id] = member

        if member == self._state.user:
            self.client.dispatch('server_join', server)
            self.client.dispatch('guild_join', server)  # discord.py

        self.client.dispatch('member_join', member)

    async def TeamMemberRemoved(self, data: TeamMemberRemovedEvent):
        server = self.client.get_server(data['serverId'])
        if server is None:
            return

        member = self._state._get_server_member(server.id, data['userId'])
        if member:
            self.client.dispatch('member_remove', member)
            if data.get('isBan'):
                self.client.dispatch('member_ban', member)
            if data.get('isKick'):
                self.client.dispatch('member_kick', member)
            if not data.get('isKick') and not data.get('isBan'):
                self.client.dispatch('member_leave', member)

            server._members.pop(data['userId'], None)

    async def TeamMemberUpdated(self, data: TeamMemberUpdatedEvent):
        member_id = data.get('userId') or data['userInfo'].get('id')
        raw_after = self._state.create_member(data={
            'user': {'id': member_id},
            'serverId': data['serverId'],
            **data['userInfo'],
        })
        self.client.dispatch('raw_member_update', raw_after)

        server = self.client.get_server(data['serverId'])
        if server is None:
            return

        member = server.get_member(member_id)
        if member is None:
            self._state.add_to_member_cache(raw_after)
            return

        before = Member._copy(member)
        member._update(data['userInfo'])

        self.client.dispatch('member_update', before, member)

    async def teamRolesUpdated(self, data: TeamRolesUpdatedEvent):
        server = self.client.get_server(data['serverId'])
        if server is None:
            return

        # A member's roles were updated
        for updated in data.get('memberRoleIds') or []:
            for role_id in updated['roleIds']:
                if not server.get_role(role_id):
                    role = Role(state=self._state, data={'id': role_id, 'serverId': server.id})
                    server._roles[role.id] = role

            raw_after = self._state.create_member(data={'id': updated['userId'], 'roleIds': updated['roleIds'], 'serverId': server.id})
            self.client.dispatch('raw_member_update', raw_after)

            member = server.get_member(updated['userId'])
            if not member:
                self._state.add_to_member_cache(raw_after)
                continue

            before = Member._copy(member)
            member._update_roles(updated['roleIds'])
            self._state.add_to_member_cache(member)
            self.client.dispatch('member_update', before, member)

        # The server's roles were updated
        if data.get('rolesById'):
            # Guilded provides us with the entire role list so we reconstruct it
            # with this data since it will undoubtably be the newest available
            server._roles.clear()

            for role_id, updated in data['rolesById'].items():
                if role_id.isdigit():
                    # "baseRole" is included in rolesById, resulting in a
                    # duplicate entry for the base role.
                    role = Role(state=self._state, data=updated, server=server)
                    server._roles[role.id] = role

    async def TeamWebhookCreated(self, data: TeamWebhookEvent):
        webhook = Webhook.from_state(data['webhook'], self._state)
        self.client.dispatch('webhook_create', webhook)

    async def TeamWebhookUpdated(self, data: TeamWebhookEvent):
        webhook = Webhook.from_state(data['webhook'], self._state)
        # Webhooks are not cached so having a `webhook_update` with only `after` doesn't make sense.
        # In the future this may change with the introduction of better caching control.
        self.client.dispatch('raw_webhook_update', webhook)

    async def TeamChannelCreated(self, data: TeamChannelEvent):
        server = self.client.get_server(data['serverId'])
        channel = self._state.create_channel(data=data['channel'], server=server)
        self._state.add_to_server_channel_cache(channel)
        self.client.dispatch('server_channel_create', channel)

    async def TeamChannelUpdated(self, data: TeamChannelEvent):
        server = self.client.get_server(data['serverId'])
        before = server.get_channel(data['channel']['id'])
        if not before:
            return

        after = self._state.create_channel(data=data['channel'], server=server)
        self._state.add_to_server_channel_cache(after)
        self.client.dispatch('server_channel_update', before, after)

    async def TeamChannelDeleted(self, data: TeamChannelEvent):
        server = self.client.get_server(data['serverId'])
        channel = self._state.create_channel(data=data['channel'], server=server)
        channel.server._channels.pop(channel.id, None)
        self.client.dispatch('server_channel_delete', channel)

    async def ChannelMessageReactionCreated(self, data: ChannelMessageReactionEvent):
        server = self.client.get_server(data['serverId'])

        data['reaction']['type'] = 'ChannelMessageReactionCreated'
        payload = RawReactionActionEvent(state=self._state, data=data['reaction'], server=server)
        self.client.dispatch('raw_message_reaction_add', payload)

        message = self._state._get_message(data['reaction']['messageId'])
        if message:
            reaction = Reaction(data=data['reaction'], parent=message)
            self.client.dispatch('message_reaction_add', reaction)

    async def ChannelMessageReactionDeleted(self, data: ChannelMessageReactionEvent):
        server = self.client.get_server(data['serverId'])

        data['reaction']['type'] = 'ChannelMessageReactionDeleted'
        payload = RawReactionActionEvent(state=self._state, data=data['reaction'], server=server)
        self.client.dispatch('raw_message_reaction_remove', payload)

        message = self._state._get_message(data['reaction']['messageId'])
        if message:
            reaction = Reaction(data=data['reaction'], parent=message)
            self.client.dispatch('message_reaction_remove', reaction)

    async def CalendarEventCreated(self, data: CalendarEventEvent):
        server = self.client.get_server(data['serverId'])
        if not server:
            return

        try:
            channel: CalendarChannel = await server.getch_channel(data['calendarEvent']['channelId'])
        except HTTPException:
            return

        event = CalendarEvent(state=self._state, data=data['calendarEvent'], channel=channel)
        self.client.dispatch('calendar_event_create', event)

    # This event's payload isn't hydrated properly
    #async def CalendarEventUpdated(self, data: CalendarEventEvent):
    #    server = self.client.get_server(data['serverId'])
    #    if not server:
    #        return

    #    try:
    #        channel: CalendarChannel = await server.getch_channel(data['calendarEvent']['channelId'])
    #    except HTTPException:
    #        return

    #    event = CalendarEvent(state=self._state, data=data['calendarEvent'], channel=channel)
    #    self.client.dispatch('raw_calendar_event_update', event)

    async def CalendarEventDeleted(self, data: CalendarEventEvent):
        server = self.client.get_server(data['serverId'])
        if not server:
            return

        try:
            channel: CalendarChannel = await server.getch_channel(data['calendarEvent']['channelId'])
        except HTTPException:
            return

        event = CalendarEvent(state=self._state, data=data['calendarEvent'], channel=channel)
        self.client.dispatch('calendar_event_delete', event)

    async def CalendarEventRsvpUpdated(self, data: CalendarEventRsvpEvent):
        server = self.client.get_server(data['serverId'])
        if not server:
            return

        try:
            channel: CalendarChannel = await server.getch_channel(data['calendarEventRsvp']['channelId'])
            event = await channel.fetch_event(data['calendarEventRsvp']['calendarEventId'])
        except HTTPException:
            return

        rsvp = CalendarEventRSVP(data=data['calendarEventRsvp'], event=event)
        self.client.dispatch('raw_calendar_event_rsvp_update', rsvp)

    async def CalendarEventRsvpDeleted(self, data: CalendarEventRsvpEvent):
        server = self.client.get_server(data['serverId'])
        if not server:
            return

        try:
            channel: CalendarChannel = await server.getch_channel(data['calendarEventRsvp']['channelId'])
            event = await channel.fetch_event(data['calendarEventRsvp']['calendarEventId'])
        except HTTPException:
            return

        rsvp = CalendarEventRSVP(data=data['calendarEventRsvp'], event=event)
        self.client.dispatch('calendar_event_rsvp_delete', rsvp)


class Heartbeater(threading.Thread):
    def __init__(self, ws: GuildedWebSocket, *, interval: float):
        self.ws = ws
        self.interval = interval
        #self.heartbeat_timeout = timeout
        super().__init__()

        self.msg = 'Keeping websocket alive with sequence %s.'
        self.block_msg = 'Websocket heartbeat blocked for more than %s seconds.'
        self.behind_msg = 'Can\'t keep up, websocket is %.1fs behind.'
        self._stop_ev = threading.Event()

        self._last_ping: float = time.perf_counter()
        self._last_pong: float = time.perf_counter()
        self.latency = float('inf')

    def run(self):
        log.debug('Started heartbeat thread')
        while not self._stop_ev.wait(self.interval):
            log.debug('Sending heartbeat')
            coro = self.ws.ping()
            f = asyncio.run_coroutine_threadsafe(coro, loop=self.ws.loop)
            try:
                total = 0
                while True:
                    try:
                        f.result(10)
                        break
                    except concurrent.futures.TimeoutError:
                        total += 10
                        try:
                            frame = sys._current_frames()[self._main_thread_id]
                        except KeyError:
                            msg = self.block_msg
                        else:
                            stack = traceback.format_stack(frame)
                            msg = '%s\nLoop thread traceback (most recent call last):\n%s' % (self.block_msg, ''.join(stack))
                        log.warning(msg, total)

            except Exception:
                self.stop()
            else:
                self._last_ping = time.perf_counter()

    def stop(self) -> None:
        self._stop_ev.set()

    def record_pong(self) -> None:
        self._last_pong = time.perf_counter()
        self.latency = self._last_pong - self._last_ping

        if self.latency > 10:
            log.warning(self.behind_msg, self.latency)
