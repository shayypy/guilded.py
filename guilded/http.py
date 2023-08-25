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
import sys

import aiohttp
import asyncio
from collections.abc import Iterable
import datetime
import json
import logging
from typing import TYPE_CHECKING, Any, Dict, List, NamedTuple, Optional, Sequence, Type, TypeVar, Union

from . import __version__, channel
from .abc import ServerChannel
from .embed import Embed
from .enums import try_enum, ChannelType
from .errors import Forbidden, GuildedServerError, HTTPException, NotFound
from .message import ChatMessage
from .user import User, Member
from .utils import MISSING

log = logging.getLogger(__name__)


if TYPE_CHECKING:
    from typing_extensions import Self
    from types import TracebackType

    from .types.channel import ServerChannel as ServerChannelPayload

    from .asset import Asset
    from .category import Category
    from .channel import DMChannel, Thread
    from .emote import Emote
    from .file import Attachment, File
    from .gateway import GuildedWebSocket
    from .role import Role
    from .server import Server
    from .user import ClientUser

    T = TypeVar('T')
    BE = TypeVar('BE', bound=BaseException)


# This is mostly for webhooks but I expect the bot API to be somewhat compliant
# with this in the future, at which point other parts of the library will start
# using this as well.

class MultipartParameters(NamedTuple):
    payload: Optional[Dict[str, Any]]
    multipart: Optional[List[Dict[str, Any]]]
    files: Optional[Sequence[File]]

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BE]],
        exc: Optional[BE],
        traceback: Optional[TracebackType],
    ) -> None:
        if self.files:
            for file in self.files:
                file.close()


def handle_message_parameters(
    content: Optional[str] = MISSING,
    *,
    username: str = MISSING,
    avatar_url: Any = MISSING,
    file: File = MISSING,
    files: Sequence[File] = MISSING,
    embed: Optional[Embed] = MISSING,
    embeds: Sequence[Embed] = MISSING,
    reply_to: Sequence[str] = MISSING,
    silent: Optional[bool] = None,
    private: Optional[bool] = None,
) -> MultipartParameters:
    if files is not MISSING and file is not MISSING:
        raise TypeError('Cannot mix file and files keyword arguments.')
    if embeds is not MISSING and embed is not MISSING:
        raise TypeError('Cannot mix embed and embeds keyword arguments.')

    if file is not MISSING:
        files = [file]

    payload = {}
    if embeds is not MISSING:
        if len(embeds) > 10:
            raise ValueError('embeds has a maximum of 10 elements.')
        payload['embeds'] = [e.to_dict() for e in embeds]

    if embed is not MISSING:
        if embed is None:
            payload['embeds'] = []
        else:
            payload['embeds'] = [embed.to_dict()]

    if content is not MISSING:
        if content is not None:
            payload['content'] = str(content)
        else:
            payload['content'] = None

    if reply_to is not MISSING:
        payload['replyMessageIds'] = reply_to

    if silent is not None:
        payload['isSilent'] = silent

    if private is not None:
        payload['isPrivate'] = private

    if username:
        payload['username'] = username

    if avatar_url:
        payload['avatar_url'] = str(avatar_url)

    multipart = []
    if files:
        multipart.append({'name': 'payload_json', 'value': json.dumps(payload)})
        payload = None
        for index, file in enumerate(files):
            multipart.append(
                {
                    'name': f'files[{index}]',
                    'value': file.fp,
                    'filename': file.filename,
                    'content_type': file.content_type,
                }
            )

    return MultipartParameters(payload=payload, multipart=multipart, files=files)


async def json_or_text(response: aiohttp.ClientResponse) -> Union[Dict[str, Any], str]:
    text = await response.text(encoding='utf-8')
    try:
        if response.headers['content-type'] == 'application/json':
            return json.loads(text)
    except KeyError:
        # Thanks Cloudflare
        pass

    return text


class Route:
    BASE = 'https://www.guilded.gg/api/v1'
    USER_BASE = 'https://www.guilded.gg/api'
    WEBSOCKET_BASE = 'wss://www.guilded.gg/websocket/v1'
    MEDIA_BASE = 'https://media.guilded.gg'
    CDN_BASE = 'https://s3-us-west-2.amazonaws.com/www.guilded.gg'
    NO_BASE = ''

    def __init__(self, method: str, path: str, *, override_base: str = None):
        self.method = method
        self.path = path

        if override_base is not None:
            self.BASE = override_base

        self.url = self.BASE + path


class HTTPClientBase:
    GIL_ID = 'Ann6LewA'
    def __init__(self, *, max_messages: int = 1000, experimental_event_style: bool = False):
        self.session: Optional[aiohttp.ClientSession] = None
        self._max_messages = max_messages
        self._experimental_event_style = experimental_event_style

        self.ws: Optional[GuildedWebSocket] = None
        self.user: Optional[ClientUser] = None
        self.my_id: Optional[str] = None

        self._users = {}
        self._servers = {}
        self._messages = {}

        self._threads = {}
        self._dm_channels = {}

    async def close(self) -> None:
        if self.session:
            await self.session.close()

    def _get_user(self, user_id: str) -> Optional[User]:
        return self._users.get(user_id)

    def _get_server(self, server_id: str) -> Optional[Server]:
        return self._servers.get(server_id)

    def _get_message(self, message_id: str) -> Optional[ChatMessage]:
        return self._messages.get(message_id)

    def _get_dm_channel(self, dm_channel_id: str) -> Optional[DMChannel]:
        return self._dm_channels.get(dm_channel_id)

    def _get_thread(self, thread_id: str) -> Optional[Thread]:
        return self._threads.get(thread_id)

    def _get_server_channel(self, server_id: str, channel_id: str) -> Optional[ServerChannel]:
        if self._get_server(server_id):
            return self._get_server(server_id).get_channel(channel_id)

    def _get_server_channel_or_thread(self, server_id: str, channel_id: str) -> Optional[Union[ServerChannel, Thread]]:
        if self._get_server(server_id):
            return self._get_server(server_id).get_channel_or_thread(channel_id)

    def _get_server_category(self, server_id: str, category_id: int) -> Optional[Category]:
        if self._get_server(server_id):
            return self._get_server(server_id).get_category(category_id)

    @property
    def _all_server_channels(self) -> Dict[str, ServerChannel]:
        all_channels = {}
        for server in self._servers.values():
            all_channels = {**all_channels, **server._channels}

        return all_channels

    def _get_global_server_channel(self, channel_id: str) -> Optional[ServerChannel]:
        return self._all_server_channels.get(channel_id)

    def _get_server_thread(self, server_id: str, thread_id: str) -> Optional[Thread]:
        if self._get_server(server_id):
            return self._get_server(server_id).get_thread(thread_id)

    def _get_server_member(self, server_id: str, user_id: str) -> Optional[Member]:
        if self._get_server(server_id):
            return self._get_server(server_id).get_member(user_id)

    def _get_server_role(self, server_id: str, role_id: int) -> Optional[Role]:
        if self._get_server(server_id):
            return self._get_server(server_id).get_role(role_id)

    @property
    def _emotes(self) -> Dict[int, Emote]:
        emotes = {}
        for server in self._servers.values():
            emotes = {**emotes, **server._emotes}

        return emotes

    def _get_emote(self, id) -> Optional[Emote]:
        return self._emotes.get(id)

    def add_to_message_cache(self, message: ChatMessage) -> None:
        if self._max_messages is None:
            return
        self._messages[message.id] = message
        while len(self._messages) > self._max_messages:
            del self._messages[list(self._messages.keys())[0]]

    def add_to_server_cache(self, server: Server):
        self._servers[server.id] = server

    def remove_from_server_cache(self, server_id: str):
        self._servers.pop(server_id, None)

    def add_to_member_cache(self, member: Member):
        server = member.server or self._get_server(member.server_id)
        if server:
            server._members[member.id] = member

    def remove_from_member_cache(self, server_id: str, member_id: str):
        if self._get_server(server_id):
            self._get_server(server_id)._members.pop(member_id, None)

    def add_to_role_cache(self, role: Role):
        server = role.server
        if server:
            server._roles[role.id] = role

    def remove_from_role_cache(self, server_id: str, role_id: int):
        if self._get_server(server_id):
            self._get_server(server_id)._roles.pop(role_id, None)

    def add_to_server_channel_cache(self, channel):
        server = channel.server or self._get_server(channel.server_id)
        if server:
            server._channels[channel.id] = channel

    def remove_from_server_channel_cache(self, server_id, channel_id):
        if self._get_server(server_id):
            self._get_server(server_id)._channels.pop(channel_id, None)

    def add_to_category_cache(self, category: Category):
        server = category.server or self._get_server(category.server_id)
        if server:
            server._categories[category.id] = category

    def remove_from_category_cache(self, server_id: str, category_id: int):
        if self._get_server(server_id):
            self._get_server(server_id)._categories.pop(category_id, None)

    def add_to_dm_channel_cache(self, channel):
        self._dm_channels[channel.id] = channel

    def remove_from_dm_channel_cache(self, channel_id):
        self._dm_channels.pop(channel_id, None)

    def add_to_user_cache(self, user):
        self._users[user.id] = user

    def remove_from_user_cache(self, user_id):
        self._users.pop(user_id, None)

    def valid_ISO8601(self, timestamp: datetime.datetime) -> str:
        """Manually construct a datetime's ISO8601 representation so that
        Guilded will accept it. Guilded rejects isoformat()'s 6-digit
        microseconds and UTC offset (+00:00)."""
        # Valid example: 2021-10-15T23:58:44.537Z
        return timestamp.strftime('%Y-%m-%dT%H:%M:%S.000Z')

    # /teams

    def get_team_info(self, team_id: str):
        return self.request(Route('GET', f'/teams/{team_id}/info', override_base=Route.USER_BASE))

    def get_team_members(self, team_id: str):
        return self.request(Route('GET', f'/teams/{team_id}/members', override_base=Route.USER_BASE))

    def get_detailed_team_members(
        self,
        team_id: str,
        user_ids: list = None,
        ids_for_basic_info: list = None,
    ):
        payload = {
            'userIds': user_ids or [],
            'idsForBasicInfo': ids_for_basic_info or [],
        }
        return self.request(Route('POST', f'/teams/{team_id}/members/detail', override_base=Route.USER_BASE), json=payload)

    def get_team_emojis(self, team_id: str, *,
        limit=None,
        search=None,
        created_by=None,
        when_upper=None,
        when_lower=None,
        created_before=None
    ):
        params = {}

        if limit is not None:
            params['maxItems'] = limit
        else:
            params['maxItems'] = ''
        if search is not None:
            params['searchTerm'] = search
        if created_by is not None:
            params['createdBy'] = created_by.id
        if when_upper is not None:
            params['when[upperValue]'] = self.valid_ISO8601(when_upper)
        if when_lower is not None:
            params['when[lowerValue]'] = self.valid_ISO8601(when_lower)
        if created_before is not None:
            params['beforeId'] = created_before.id

        return self.request(Route('GET', f'/teams/{team_id}/customReactions', override_base=Route.USER_BASE), params=params)

    # /users

    def get_user(self, user_id: str):
        return self.request(Route('GET', f'/users/{user_id}', override_base=Route.USER_BASE))

    def get_my_user(self):
        return self.request(Route('GET', '/users/@me'))

    def get_my_servers(self):
        return self.request(Route('GET', '/users/@me/servers'))

    def update_my_status(self, payload: Dict[str, Any]):
        return self.request(Route('PUT', '/users/@me/status'), json=payload)

    def delete_my_status(self):
        return self.request(Route('DELETE', '/users/@me/status'))

    # /content

    def get_metadata(self, route: str):
        params = {
            'route': route,
        }
        return self.request(Route('GET', '/content/route/metadata', override_base=Route.USER_BASE), params=params)

    # media.guilded.gg

    def upload_media(self, file: File):
        return self.request(Route('POST', '/media/upload', override_base=Route.MEDIA_BASE),
            data={'file': file.fp},
            params={'dynamicMediaTypeId': str(file.type)}
        )

    def upload_file(self, file: File):
        return self.request(Route('POST', '/media/file_upload', override_base=Route.MEDIA_BASE),
            data={'file': file.fp},
            params={'dynamicMediaTypeId': str(file.type)}
        )

    # one-off

    def read_filelike_data(self, filelike: Union[Attachment, Asset, File]):
        return self.request(Route('GET', filelike.url, override_base=Route.NO_BASE))

    def get_game_list(self):
        return self.request(Route('GET', 'https://raw.githubusercontent.com/GuildedAPI/datatables/main/games.json', override_base=Route.NO_BASE))

    def get_stripped_reaction_list(self):
        return self.request(Route('GET', 'https://raw.githubusercontent.com/GuildedAPI/datatables/main/reactions-stripped.json', override_base=Route.NO_BASE))


class HTTPClient(HTTPClientBase):
    def __init__(self, *, max_messages=1000, experimental_event_style=False):
        super().__init__(max_messages=max_messages, experimental_event_style=experimental_event_style)

        self.token: Optional[str] = None

        user_agent = 'guilded.py/{0} (https://github.com/shayypy/guilded.py) Python/{1[0]}.{1[1]} aiohttp/{2}'
        self.user_agent: str = user_agent.format(__version__, sys.version_info, aiohttp.__version__)

    async def request(self, route, **kwargs):
        url = route.url
        method = route.method

        # create headers
        headers: Dict[str, str] = {
            'User-Agent': self.user_agent,
        }

        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        if 'json' in kwargs:
            headers['Content-Type'] = 'application/json'
            kwargs['data'] = json.dumps(kwargs.pop('json'))

        kwargs['headers'] = headers

        # route.url doesn't include params since we don't pass them to the Route
        log_url = url
        if kwargs.get('params'):
            if isinstance(kwargs['params'], dict):
                log_url += '?' + '&'.join([f'{key}={val}' for key, val in kwargs['params'].items()])
            elif isinstance(kwargs['params'], Iterable):
                log_url += '?' + '&'.join([f'{param[0]}={param[1]}' for param in kwargs['params']])

        log_headers = headers.copy()
        if 'Authorization' in log_headers:
            log_headers['Authorization'] = 'Bearer [removed]'

        response: Optional[aiohttp.ClientResponse] = None
        data: Optional[Union[Dict[str, Any], str]] = None
        for tries in range(5):
            try:
                response = await self.session.request(method, url, **kwargs)
            except OSError as exc:
                # Connection reset by peer
                if tries < 4 and exc.errno in (54, 10054):
                    await asyncio.sleep(1 + tries * 2)
                    continue
                raise

            log.debug('%s %s with data %s, headers %s, has returned %s', method, log_url, kwargs.get('data'), log_headers, response.status)

            authenticated_as = response.headers.get('authenticated-as')
            if authenticated_as and authenticated_as != self.my_id and authenticated_as != 'None':
                log.debug('Response provided a new user ID. Previous: %s, New: %s', self.my_id, authenticated_as)
                last_user = self._users.pop(self.my_id, None)
                self.my_id = authenticated_as

                # Update the ClientUser
                if last_user:
                    last_user.id = self.my_id
                    self._users[self.my_id] = last_user

            if response.headers.get('Content-Type', '').startswith(('image/', 'video/')):
                data = await response.read()
            else:
                data = await json_or_text(response)
                log.debug('%s %s has received %s', method, url, data)

            # The request was successful so just return the text/json
            if 300 > response.status >= 200:
                return data

            if response.status == 429:
                retry_after = response.headers.get('retry-after')
                retry_after = float(retry_after) if retry_after is not None else (1 + tries * 2)

                log.warning(
                    'Rate limited on %s. Retrying in %s seconds',
                    route.path,
                    retry_after,
                )
                await asyncio.sleep(retry_after)
                log.debug('Done sleeping for the rate limit. Retrying...')

                continue

            # We've received a 500, 502, 504, or 524, unconditional retry
            if response.status in {500, 502, 504, 524}:
                await asyncio.sleep(1 + tries * 2)
                continue

            if response.status == 403:
                raise Forbidden(response, data)
            elif response.status == 404:
                raise NotFound(response, data)
            elif response.status >= 500:
                raise GuildedServerError(response, data)
            else:
                raise HTTPException(response, data)

        if response is not None:
            # We've run out of retries
            if response.status >= 500:
                raise GuildedServerError(response, data)

            raise HTTPException(response, data)

        raise RuntimeError('Unreachable code in HTTP handling')

    # state

    async def ws_connect(self) -> aiohttp.ClientWebSocketResponse:
        self.session = self.session if self.session and not self.session.closed else aiohttp.ClientSession()

        headers = {
            'Authorization': f'Bearer {self.token}',
            'User-Agent': self.user_agent,
        }
        if self.ws and self.ws._last_message_id:
            # We have connected before, resume and catch up with missed messages
            headers['guilded-last-message-id'] = self.ws._last_message_id

        log_headers = headers.copy()
        log_headers['Authorization'] = 'Bearer [removed]'
        log.debug('Connecting to the gateway with %s', log_headers)

        return await self.session.ws_connect(Route.WEBSOCKET_BASE, headers=headers, autoping=False)

    # /channels

    def create_server_channel(
        self,
        server_id: str,
        content_type: str,
        *,
        name: str,
        topic: Optional[str] = None,
        visibility: Optional[str] = None,
        category_id: Optional[int] = None,
        group_id: Optional[str] = None,
        parent_id: Optional[str] = None,
        message_id: Optional[str] = None,
    ):
        payload = {
            'serverId': server_id,
            'type': content_type,
            'name': name,
        }

        if topic is not None:
            payload['topic'] = topic

        if visibility is not None:
            payload['visibility'] = visibility

        if category_id is not None:
            payload['categoryId'] = category_id

        if group_id is not None:
            payload['groupId'] = group_id

        if parent_id is not None:
            payload['parentId'] = parent_id

        if message_id is not None:
            payload['messageId'] = message_id

        return self.request(Route('POST', f'/channels'), json=payload)

    def update_channel(
        self,
        channel_id: str,
        *,
        payload: Dict[str, Any],
    ):
        return self.request(Route('PATCH', f'/channels/{channel_id}'), json=payload)

    def get_channel(self, channel_id: str):
        return self.request(Route('GET', f'/channels/{channel_id}'))

    def delete_channel(self, channel_id: str):
        return self.request(Route('DELETE', f'/channels/{channel_id}'))

    def archive_channel(self, channel_id: str):
        return self.request(Route('PUT', f'/channels/{channel_id}/archive'))

    def restore_channel(self, channel_id: str):
        return self.request(Route('DELETE', f'/channels/{channel_id}/archive'))

    def create_channel_message(self, channel_id: str, *, payload: Dict[str, Any]):
        route = Route('POST', f'/channels/{channel_id}/messages')
        return self.request(route, json=payload)

    def update_channel_message(self, channel_id: str, message_id: str, *, payload: Dict[str, Any]):
        route = Route('PUT', f'/channels/{channel_id}/messages/{message_id}')
        return self.request(route, json=payload)

    def delete_channel_message(self, channel_id: str, message_id: str):
        return self.request(Route('DELETE', f'/channels/{channel_id}/messages/{message_id}'))

    def get_channel_message(self, channel_id: str, message_id: str):
        return self.request(Route('GET', f'/channels/{channel_id}/messages/{message_id}'))

    def get_channel_messages(self,
        channel_id: str,
        *,
        include_private: bool = False,
        before: datetime.datetime = None,
        after: datetime.datetime = None,
        limit: int = None,
    ):
        params = {
            'includePrivate': str(include_private).lower(),
        }
        if before is not None:
            params['before'] = self.valid_ISO8601(before)
        if after is not None:
            params['after'] = self.valid_ISO8601(after)
        if limit is not None:
            params['limit'] = limit

        return self.request(Route('GET', f'/channels/{channel_id}/messages'), params=params)

    def add_channel_message_reaction(self, channel_id: str, message_id: str, emote_id: int):
        return self.request(Route('PUT', f'/channels/{channel_id}/messages/{message_id}/emotes/{emote_id}'))

    def remove_channel_message_reaction(self, channel_id: str, message_id: str, emote_id: int, user_id: Optional[str] = None):
        params = {}
        if user_id:
            params['userId'] = user_id

        return self.request(Route('DELETE', f'/channels/{channel_id}/messages/{message_id}/emotes/{emote_id}'), params=params)

    def remove_channel_message_reactions(self, channel_id: str, message_id: str, emote_id: int = None):
        params = {}
        if emote_id is not None:
            params['emoteId'] = emote_id

        return self.request(Route('DELETE', f'/channels/{channel_id}/messages/{message_id}/emotes'), params=params)

    def pin_channel_message(self, channel_id: str, message_id: str):
        return self.request(Route('POST', f'/channels/{channel_id}/messages/{message_id}/pin'))

    def unpin_channel_message(self, channel_id: str, message_id: str):
        return self.request(Route('DELETE', f'/channels/{channel_id}/messages/{message_id}/pin'))

    def create_forum_topic(self, channel_id: str, *, title: str, content: str):
        payload = {
            'title': title,
            'content': content,
        }

        return self.request(Route('POST', f'/channels/{channel_id}/topics'), json=payload)

    def get_forum_topic(self, channel_id: str, topic_id: int):
        return self.request(Route('GET', f'/channels/{channel_id}/topics/{topic_id}'))

    def get_forum_topics(
        self,
        channel_id: str,
        *,
        before: Optional[datetime.datetime] = None,
        limit: Optional[int] = None,
    ):
        params = {}
        if before is not None:
            params['before'] = self.valid_ISO8601(before)
        if limit is not None:
            params['limit'] = limit

        return self.request(Route('GET', f'/channels/{channel_id}/topics'), params=params)

    def update_forum_topic(self, channel_id: str, topic_id: int, *, payload: Dict[str, Any]):
        return self.request(Route('PATCH', f'/channels/{channel_id}/topics/{topic_id}'), json=payload)

    def delete_forum_topic(self, channel_id: str, topic_id: int):
        return self.request(Route('DELETE', f'/channels/{channel_id}/topics/{topic_id}'))

    def pin_forum_topic(self, channel_id: str, topic_id: int):
        return self.request(Route('PUT', f'/channels/{channel_id}/topics/{topic_id}/pin'))

    def unpin_forum_topic(self, channel_id: str, topic_id: int):
        return self.request(Route('DELETE', f'/channels/{channel_id}/topics/{topic_id}/pin'))

    def lock_forum_topic(self, channel_id: str, topic_id: int):
        return self.request(Route('PUT', f'/channels/{channel_id}/topics/{topic_id}/lock'))

    def unlock_forum_topic(self, channel_id: str, topic_id: int):
        return self.request(Route('DELETE', f'/channels/{channel_id}/topics/{topic_id}/lock'))

    def create_forum_topic_comment(self, channel_id: str, topic_id: int, *, content: str):
        payload = {
            'content': content,
        }
        return self.request(Route('POST', f'/channels/{channel_id}/topics/{topic_id}/comments'), json=payload)

    def get_forum_topic_comment(self, channel_id: str, topic_id: int, comment_id: int):
        return self.request(Route('GET', f'/channels/{channel_id}/topics/{topic_id}/comments/{comment_id}'))

    def get_forum_topic_comments(self, channel_id: str, topic_id: int):
        return self.request(Route('GET', f'/channels/{channel_id}/topics/{topic_id}/comments'))

    def update_forum_topic_comment(self, channel_id: str, topic_id: int, comment_id: int, *, payload: Dict[str, Any]):
        return self.request(Route('PATCH', f'/channels/{channel_id}/topics/{topic_id}/comments/{comment_id}'), json=payload)

    def delete_forum_topic_comment(self, channel_id: str, topic_id: int, comment_id: int):
        return self.request(Route('DELETE', f'/channels/{channel_id}/topics/{topic_id}/comments/{comment_id}'))

    def add_forum_topic_reaction(self, channel_id: str, topic_id: int, emote_id: int):
        return self.request(Route('PUT', f'/channels/{channel_id}/topics/{topic_id}/emotes/{emote_id}'))

    def remove_forum_topic_reaction(self, channel_id: str, topic_id: int, emote_id: int):
        return self.request(Route('DELETE', f'/channels/{channel_id}/topics/{topic_id}/emotes/{emote_id}'))

    def add_forum_topic_comment_reaction(self, channel_id: str, topic_id: int, comment_id: int, emote_id: int):
        return self.request(Route('PUT', f'/channels/{channel_id}/topics/{topic_id}/comments/{comment_id}/emotes/{emote_id}'))

    def remove_forum_topic_comment_reaction(self, channel_id: str, topic_id: int, comment_id: int, emote_id: int):
        return self.request(Route('DELETE', f'/channels/{channel_id}/topics/{topic_id}/comments/{comment_id}/emotes/{emote_id}'))

    def create_list_item(self, channel_id: str, *, message: str, note_content: Optional[str] = None):
        payload = {
            'message': message,
        }
        if note_content is not None:
            payload['note'] = {
                'content': note_content,
            }

        return self.request(Route('POST', f'/channels/{channel_id}/items'), json=payload)

    def get_list_item(self, channel_id: str, item_id: str):
        return self.request(Route('GET', f'/channels/{channel_id}/items/{item_id}'))

    def get_list_items(self, channel_id: str):
        return self.request(Route('GET', f'/channels/{channel_id}/items'))

    def update_list_item(self, channel_id: str, item_id: str, *, payload: Dict[str, Any]):
        return self.request(Route('PATCH', f'/channels/{channel_id}/items/{item_id}'), json=payload)

    def delete_list_item(self, channel_id: str, item_id: str):
        return self.request(Route('DELETE', f'/channels/{channel_id}/items/{item_id}'))

    def complete_list_item(self, channel_id: str, item_id: str):
        return self.request(Route('POST', f'/channels/{channel_id}/items/{item_id}/complete'))

    def uncomplete_list_item(self, channel_id: str, item_id: str):
        return self.request(Route('DELETE', f'/channels/{channel_id}/items/{item_id}/complete'))

    def create_announcement(self, channel_id: str, *, title: str, content: str):
        payload = {
            'title': title,
            'content': content,
        }

        return self.request(Route('POST', f'/channels/{channel_id}/announcements'), json=payload)

    def get_announcements(self, channel_id: str, *, limit: int = None, before: datetime.datetime = None):
        params = {}
        if limit is not None:
            params['limit'] = limit
        if before is not None:
            params['before'] = self.valid_ISO8601(before)

        return self.request(Route('GET', f'/channels/{channel_id}/announcements'), params=params)

    def get_announcement(self, channel_id: str, announcement_id: str):
        return self.request(Route('GET', f'/channels/{channel_id}/announcements/{announcement_id}'))

    def update_announcement(self, channel_id: str, announcement_id: str, *, payload: Dict[str, Any]):
        return self.request(Route('PUT', f'/channels/{channel_id}/announcements/{announcement_id}'), json=payload)

    def delete_announcement(self, channel_id: str, announcement_id: str):
        return self.request(Route('DELETE', f'/channels/{channel_id}/announcements/{announcement_id}'))

    def add_announcement_reaction(self, channel_id: str, announcement_id: str, emote_id: int):
        return self.request(Route('PUT', f'/channels/{channel_id}/announcements/{announcement_id}/emotes/{emote_id}'))

    def remove_announcement_reaction(self, channel_id: str, announcement_id: str, emote_id: int):
        return self.request(Route('DELETE', f'/channels/{channel_id}/announcements/{announcement_id}/emotes/{emote_id}'))

    def create_announcement_comment(self, channel_id: str, announcement_id: str, *, content: str):
        payload = {
            'content': content,
        }
        return self.request(Route('POST', f'/channels/{channel_id}/announcements/{announcement_id}/comments'), json=payload)

    def get_announcement_comment(self, channel_id: str, announcement_id: str, comment_id: int):
        return self.request(Route('GET', f'/channels/{channel_id}/announcements/{announcement_id}/comments/{comment_id}'))

    def get_announcement_comments(self, channel_id: str, announcement_id: str):
        return self.request(Route('GET', f'/channels/{channel_id}/announcements/{announcement_id}/comments'))

    def update_announcement_comment(self, channel_id: str, announcement_id: str, comment_id: int, *, payload: Dict[str, Any]):
        return self.request(Route('PATCH', f'/channels/{channel_id}/announcements/{announcement_id}/comments/{comment_id}'), json=payload)

    def delete_announcement_comment(self, channel_id: str, announcement_id: str, comment_id: int):
        return self.request(Route('DELETE', f'/channels/{channel_id}/announcements/{announcement_id}/comments/{comment_id}'))

    def add_announcement_comment_reaction(self, channel_id: str, announcement_id: str, comment_id: int, emote_id: int):
        return self.request(Route('PUT', f'/channels/{channel_id}/announcements/{announcement_id}/comments/{comment_id}/emotes/{emote_id}'))

    def remove_announcement_comment_reaction(self, channel_id: str, announcement_id: str, comment_id: int, emote_id: int):
        return self.request(Route('DELETE', f'/channels/{channel_id}/announcements/{announcement_id}/comments/{comment_id}/emotes/{emote_id}'))

    def create_doc(self, channel_id: str, *, title: str, content: str):
        payload = {
            'title': title,
            'content': content,
        }

        return self.request(Route('POST', f'/channels/{channel_id}/docs'), json=payload)

    def get_docs(self, channel_id: str, *, limit: int = None, before: datetime.datetime = None):
        params = {}
        if limit is not None:
            params['limit'] = limit
        if before is not None:
            params['before'] = self.valid_ISO8601(before)

        return self.request(Route('GET', f'/channels/{channel_id}/docs'), params=params)

    def get_doc(self, channel_id: str, doc_id: int):
        return self.request(Route('GET', f'/channels/{channel_id}/docs/{doc_id}'))

    def update_doc(self, channel_id: str, doc_id: int, *, payload: Dict[str, Any]):
        return self.request(Route('PUT', f'/channels/{channel_id}/docs/{doc_id}'), json=payload)

    def delete_doc(self, channel_id: str, doc_id: int):
        return self.request(Route('DELETE', f'/channels/{channel_id}/docs/{doc_id}'))

    def add_doc_reaction(self, channel_id: str, doc_id: int, emote_id: int):
        return self.request(Route('PUT', f'/channels/{channel_id}/docs/{doc_id}/emotes/{emote_id}'))

    def remove_doc_reaction(self, channel_id: str, doc_id: int, emote_id: int):
        return self.request(Route('DELETE', f'/channels/{channel_id}/docs/{doc_id}/emotes/{emote_id}'))

    def create_doc_comment(self, channel_id: str, doc_id: int, *, content: str):
        payload = {
            'content': content,
        }
        return self.request(Route('POST', f'/channels/{channel_id}/docs/{doc_id}/comments'), json=payload)

    def get_doc_comment(self, channel_id: str, doc_id: int, comment_id: int):
        return self.request(Route('GET', f'/channels/{channel_id}/docs/{doc_id}/comments/{comment_id}'))

    def get_doc_comments(self, channel_id: str, doc_id: int):
        return self.request(Route('GET', f'/channels/{channel_id}/docs/{doc_id}/comments'))

    def update_doc_comment(self, channel_id: str, doc_id: int, comment_id: int, *, payload: Dict[str, Any]):
        return self.request(Route('PATCH', f'/channels/{channel_id}/docs/{doc_id}/comments/{comment_id}'), json=payload)

    def delete_doc_comment(self, channel_id: str, doc_id: int, comment_id: int):
        return self.request(Route('DELETE', f'/channels/{channel_id}/docs/{doc_id}/comments/{comment_id}'))

    def add_doc_comment_reaction(self, channel_id: str, doc_id: int, comment_id: int, emote_id: int):
        return self.request(Route('PUT', f'/channels/{channel_id}/docs/{doc_id}/comments/{comment_id}/emotes/{emote_id}'))

    def remove_doc_comment_reaction(self, channel_id: str, doc_id: int, comment_id: int, emote_id: int):
        return self.request(Route('DELETE', f'/channels/{channel_id}/docs/{doc_id}/comments/{comment_id}/emotes/{emote_id}'))

    def create_calendar_event(self, channel_id: str, *, payload: Dict[str, Any]):
        return self.request(Route('POST', f'/channels/{channel_id}/events'), json=payload)

    def get_calendar_events(self, channel_id: str, *, limit: int = None, before: datetime.datetime = None, after: datetime.datetime = None):
        params = {}
        if limit is not None:
            params['limit'] = limit
        if before is not None:
            params['before'] = self.valid_ISO8601(before)
        if after is not None:
            params['after'] = self.valid_ISO8601(after)

        return self.request(Route('GET', f'/channels/{channel_id}/events'), params=params)

    def get_calendar_event(self, channel_id: str, event_id: int):
        return self.request(Route('GET', f'/channels/{channel_id}/events/{event_id}'))

    def update_calendar_event(self, channel_id: str, event_id: int, *, payload: Dict[str, Any]):
        return self.request(Route('PATCH', f'/channels/{channel_id}/events/{event_id}'), json=payload)

    def delete_calendar_event(self, channel_id: str, event_id: int, *, delete_series: Optional[str] = None):
        payload = {}
        if delete_series:
            payload['deleteSeries'] = delete_series

        return self.request(Route('DELETE', f'/channels/{channel_id}/events/{event_id}'), json=payload)

    def add_calendar_event_reaction(self, channel_id: str, event_id: int, emote_id: int):
        return self.request(Route('PUT', f'/channels/{channel_id}/events/{event_id}/emotes/{emote_id}'))

    def remove_calendar_event_reaction(self, channel_id: str, event_id: int, emote_id: int):
        return self.request(Route('DELETE', f'/channels/{channel_id}/events/{event_id}/emotes/{emote_id}'))

    def create_calendar_event_comment(self, channel_id: str, event_id: int, *, content: str):
        payload = {
            'content': content,
        }
        return self.request(Route('POST', f'/channels/{channel_id}/events/{event_id}/comments'), json=payload)

    def get_calendar_event_comment(self, channel_id: str, event_id: int, comment_id: int):
        return self.request(Route('GET', f'/channels/{channel_id}/events/{event_id}/comments/{comment_id}'))

    def get_calendar_event_comments(self, channel_id: str, event_id: int):
        return self.request(Route('GET', f'/channels/{channel_id}/events/{event_id}/comments'))

    def update_calendar_event_comment(self, channel_id: str, event_id: int, comment_id: int, *, payload: Dict[str, Any]):
        return self.request(Route('PATCH', f'/channels/{channel_id}/events/{event_id}/comments/{comment_id}'), json=payload)

    def delete_calendar_event_comment(self, channel_id: str, event_id: int, comment_id: int):
        return self.request(Route('DELETE', f'/channels/{channel_id}/events/{event_id}/comments/{comment_id}'))

    def add_calendar_event_comment_reaction(self, channel_id: str, event_id: int, comment_id: int, emote_id: int):
        return self.request(Route('PUT', f'/channels/{channel_id}/events/{event_id}/comments/{comment_id}/emotes/{emote_id}'))

    def remove_calendar_event_comment_reaction(self, channel_id: str, event_id: int, comment_id: int, emote_id: int):
        return self.request(Route('DELETE', f'/channels/{channel_id}/events/{event_id}/comments/{comment_id}/emotes/{emote_id}'))

    def get_calendar_event_rsvp(self, channel_id: str, event_id: int, user_id: str):
        return self.request(Route('GET', f'/channels/{channel_id}/events/{event_id}/rsvps/{user_id}'))

    def get_calendar_event_rsvps(self, channel_id: str, event_id: int):
        return self.request(Route('GET', f'/channels/{channel_id}/events/{event_id}/rsvps'))

    def put_calendar_event_rsvp(
        self,
        channel_id: str,
        event_id: int,
        user_id: str,
        *,
        status: str,
    ):
        # This endpoint is used for creation and updating
        payload = {
            'status': status
        }
        return self.request(Route('PUT', f'/channels/{channel_id}/events/{event_id}/rsvps/{user_id}'), json=payload)

    def upsert_calendar_event_rsvps(
        self,
        channel_id: str,
        event_id: int,
        user_ids: List[str],
        *,
        status: str,
    ):
        # This endpoint is used for creation and updating
        payload = {
            'userIds': user_ids,
            'status': status,
        }
        return self.request(Route('PUT', f'/channels/{channel_id}/events/{event_id}/rsvps'), json=payload)

    def delete_calendar_event_rsvp(self, channel_id: str, event_id: int, user_id: str):
        return self.request(Route('DELETE', f'/channels/{channel_id}/events/{event_id}/rsvps/{user_id}'))

    # /servers

    def get_server(self, server_id: str):
        return self.request(Route('GET', f'/servers/{server_id}'))

    def bulk_award_member_xp(self, server_id: str, user_ids: List[str], amount: int):
        payload = {
            'userIds': user_ids,
            'amount': amount,
        }
        return self.request(Route('POST', f'/servers/{server_id}/xp'), json=payload)

    def bulk_set_member_xp(self, server_id: str, user_ids: List[str], total: int):
        payload = {
            'userIds': user_ids,
            'total': total,
            # There is currently a bug where `total` is ignored and `amount`
            # is required instead.
            'amount': total,
        }
        return self.request(Route('PUT', f'/servers/{server_id}/xp'), json=payload)

    def get_member_roles(self, server_id: str, user_id: str):
        return self.request(Route('GET', f'/servers/{server_id}/members/{user_id}/roles'))

    def assign_role_to_member(self, server_id: str, user_id: str, role_id: int):
        return self.request(Route('PUT', f'/servers/{server_id}/members/{user_id}/roles/{role_id}'))

    def remove_role_from_member(self, server_id: str, user_id: str, role_id: int):
        return self.request(Route('DELETE', f'/servers/{server_id}/members/{user_id}/roles/{role_id}'))

    def update_member_nickname(self, server_id: str, user_id: str, nickname: str):
        payload = {
            'nickname': nickname,
        }
        return self.request(Route('PUT', f'/servers/{server_id}/members/{user_id}/nickname'), json=payload)

    def delete_member_nickname(self, server_id: str, user_id: str):
        return self.request(Route('DELETE', f'/servers/{server_id}/members/{user_id}/nickname'))

    def get_member(self, server_id: str, user_id: str):
        return self.request(Route('GET', f'/servers/{server_id}/members/{user_id}'))

    def kick_member(self, server_id: str, user_id: str):
        return self.request(Route('DELETE', f'/servers/{server_id}/members/{user_id}'))

    def get_members(self, server_id: str):
        return self.request(Route('GET', f'/servers/{server_id}/members'))

    def get_member_social_links(self, server_id: str, user_id: str, type: str):
        return self.request(Route('GET', f'/servers/{server_id}/members/{user_id}/social-links/{type}'))

    def award_member_xp(self, server_id: str, user_id: str, amount: int):
        payload = {
            'amount': amount,
        }
        return self.request(Route('POST', f'/servers/{server_id}/members/{user_id}/xp'), json=payload)

    def set_member_xp(self, server_id: str, user_id: str, total: int):
        payload = {
            'total': total,
        }
        return self.request(Route('PUT', f'/servers/{server_id}/members/{user_id}/xp'), json=payload)

    def get_member_permissions(self, server_id: str, user_id: str, *, ids: List[str] = None):
        params = {}
        if ids is not None:
            params['ids'] = ','.join(ids)

        return self.request(Route('GET', f'/servers/{server_id}/members/{user_id}/permissions'), params=params)

    def award_role_xp(self, server_id: str, role_id: int, amount: int):
        payload = {
            'amount': amount,
        }
        return self.request(Route('POST', f'/servers/{server_id}/roles/{role_id}/xp'), json=payload)

    def create_role(self, server_id: str, *, payload: Dict[str, Any]):
        return self.request(Route('POST', f'/servers/{server_id}/roles'), json=payload)

    def get_role(self, server_id: str, role_id: int):
        return self.request(Route('GET', f'/servers/{server_id}/roles/{role_id}'))

    def get_roles(self, server_id: str):
        return self.request(Route('GET', f'/servers/{server_id}/roles'))

    def update_role(self, server_id: str, role_id: int, *, payload: Dict[str, Any]):
        return self.request(Route('PATCH', f'/servers/{server_id}/roles/{role_id}'), json=payload)

    def update_role_permissions(self, server_id: str, role_id: int, *, permissions: Dict[str, bool]):
        payload = {
            'permissions': permissions,
        }
        return self.request(Route('PATCH', f'/servers/{server_id}/roles/{role_id}/permissions'), json=payload)

    def delete_role(self, server_id: str, role_id: int):
        return self.request(Route('DELETE', f'/servers/{server_id}/roles/{role_id}'))

    def ban_server_member(self, server_id: str, user_id: str, *, reason: str = None):
        payload = {}
        if reason is not None:
            payload['reason'] = reason

        return self.request(Route('POST', f'/servers/{server_id}/bans/{user_id}'), json=payload)

    def unban_server_member(self, server_id: str, user_id: str):
        return self.request(Route('DELETE', f'/servers/{server_id}/bans/{user_id}'))

    def get_server_ban(self, server_id: str, user_id: str):
        return self.request(Route('GET', f'/servers/{server_id}/bans/{user_id}'))

    def get_server_bans(self, server_id: str):
        return self.request(Route('GET', f'/servers/{server_id}/bans'))

    def create_webhook(self, server_id: str, *, name: str, channel_id:  str):
        payload = {
            'name': name,
            'channelId': channel_id,
        }
        return self.request(Route('POST', f'/servers/{server_id}/webhooks'), json=payload)

    def get_server_webhook(self, server_id: str, webhook_id: str):
        return self.request(Route('GET', f'/servers/{server_id}/webhooks/{webhook_id}'))

    def get_server_webhooks(self, server_id: str, channel_id: str):
        params = {
            'channelId': channel_id,
        }

        return self.request(Route('GET', f'/servers/{server_id}/webhooks'), params=params)

    def update_webhook(self, server_id: str, webhook_id: str, *, payload: Dict[str, Any]):
        return self.request(Route('PUT', f'/servers/{server_id}/webhooks/{webhook_id}'), json=payload)

    def delete_webhook(self, server_id: str, webhook_id: str):
        return self.request(Route('DELETE', f'/servers/{server_id}/webhooks/{webhook_id}'))

    # groups

    def create_group(self, server_id: str, *, payload: Dict[str, Any]):
        return self.request(Route('POST', f'/servers/{server_id}/groups'), json=payload)

    def get_group(self, server_id: str, group_id: str):
        return self.request(Route('GET', f'/servers/{server_id}/groups/{group_id}'))

    def get_groups(self, server_id: str):
        return self.request(Route('GET', f'/servers/{server_id}/groups'))

    def update_group(self, server_id: str, group_id: str, *, payload: Dict[str, Any]):
        return self.request(Route('PATCH', f'/servers/{server_id}/groups/{group_id}'), json=payload)

    def delete_group(self, server_id: str, group_id: str):
        return self.request(Route('DELETE', f'/servers/{server_id}/groups/{group_id}'))

    def add_group_member(self, group_id: str, user_id: str):
        return self.request(Route('PUT', f'/groups/{group_id}/members/{user_id}'))

    def remove_group_member(self, group_id: str, user_id: str):
        return self.request(Route('DELETE', f'/groups/{group_id}/members/{user_id}'))

    # categories

    def create_category(
        self,
        server_id: str,
        *,
        name: str,
        group_id: Optional[str] = None,
    ):
        payload = {
            'name': name,
        }

        if group_id is not None:
            payload['groupId'] = group_id

        return self.request(Route('POST', f'/servers/{server_id}/categories'), json=payload)

    def update_category(
        self,
        server_id: str,
        category_id: int,
        *,
        payload: Dict[str, Any],
    ):
        return self.request(Route('PATCH', f'/servers/{server_id}/categories/{category_id}'), json=payload)

    def get_category(self, server_id: str, category_id: int):
        return self.request(Route('GET', f'/servers/{server_id}/categories/{category_id}'))

    def delete_category(self, server_id: str, category_id: int):
        return self.request(Route('DELETE', f'/servers/{server_id}/categories/{category_id}'))

    # subscriptions

    def get_subscription_tier(self, server_id: str, tier_type: str):
        return self.request(Route('GET', f'/servers/{server_id}/subscriptions/tiers/{tier_type}'))

    def get_subscription_tiers(self, server_id: str):
        return self.request(Route('GET', f'/servers/{server_id}/subscriptions/tiers'))

    # create objects from data

    def create_user(self, **data) -> User:
        return User(state=self, **data)

    def create_member(self, **data) -> Member:
        return Member(state=self, **data)

    def create_channel(self, *, data: ServerChannelPayload, **extra) -> ServerChannel:
        if data.get('serverId') is None:
            return channel.DMChannel(state=self, **extra)

        data['group'] = data.get('group')
        if 'parentId' in data:
            # Only threads have parent channels or parent threads.
            # Their type is still 'chat' so this is the only way we can differentiate them.
            cls = channel.Thread
        else:
            types = {
                ChannelType.announcements: channel.AnnouncementChannel,
                ChannelType.calendar: channel.CalendarChannel,
                ChannelType.chat: channel.ChatChannel,
                ChannelType.docs: channel.DocsChannel,
                ChannelType.forums: channel.ForumChannel,
                ChannelType.list: channel.ListChannel,
                ChannelType.media: channel.MediaChannel,
                ChannelType.scheduling: channel.SchedulingChannel,
                ChannelType.stream: channel.StreamChannel,
                ChannelType.voice: channel.VoiceChannel,
            }
            cls = types.get(try_enum(ChannelType, data['type']))
            if cls is None:
                cls = ServerChannel

        return cls(state=self, data=data, **extra)

    def create_message(self, **data) -> ChatMessage:
        data['channel'] = data.get('channel')
        return ChatMessage(state=self, **data)
