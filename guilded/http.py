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
import datetime
import json
import logging
from typing import TYPE_CHECKING, Any, Dict, List, NamedTuple, Optional, Sequence, Type, TypeVar, Union

from . import utils
from . import channel
from .abc import User as abc_User, TeamChannel
from .embed import _EmptyEmbed, Embed
from .emoji import Emoji
from .enums import try_enum, ChannelType, MediaType
from .errors import ClientException, HTTPException, error_mapping
from .file import File
from .message import ChatMessage, Mention
from .role import Role
from .user import User, Member
from .utils import MISSING, new_uuid

log = logging.getLogger(__name__)


if TYPE_CHECKING:
    from typing_extensions import Self
    from types import TracebackType

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


class UserbotRoute:
    BASE = 'https://www.guilded.gg/api'
    MEDIA_BASE = 'https://media.guilded.gg'
    CDN_BASE = 'https://s3-us-west-2.amazonaws.com/www.guilded.gg'
    NO_BASE = ''
    def __init__(self, method: str, path: str, *, override_base: str = None):
        self.method = method
        self.path = path

        if override_base is not None:
            self.BASE = override_base

        self.url = self.BASE + path


class Route(UserbotRoute):
    BASE = 'https://www.guilded.gg/api/v1'
    WEBSOCKET_BASE = 'wss://api.guilded.gg/v1/websocket'


class UserbotVoiceRoute(UserbotRoute):
    def __init__(self, voice_endpoint: str, method: str, path: str):
        self.BASE = f'https://{voice_endpoint}'
        self.method = method
        self.path = path

        self.url = self.BASE + path


class HTTPClientBase:
    GIL_ID = 'Ann6LewA'
    def __init__(self, *, max_messages=1000):
        self.session = None
        self._max_messages = max_messages

        self.ws = None
        self.user = None
        self.my_id = None

        self._users = {}
        self._teams = {}
        self._messages = {}

        self._threads = {}
        self._dm_channels = {}

    async def close(self):
        if self.session:
            await self.session.close()

    def _get_user(self, id):
        return self._users.get(id)

    def _get_team(self, id):
        return self._teams.get(id)

    def _get_message(self, id):
        return self._messages.get(id)

    def _get_dm_channel(self, id):
        return self._dm_channels.get(id)

    def _get_thread(self, id):
        return self._threads.get(id)

    def _get_team_channel(self, team_id, id):
        if self._get_team(team_id):
            return self._get_team(team_id).get_channel(id)

    def _get_team_channel_or_thread(self, team_id, id):
        if self._get_team(team_id):
            return self._get_team(team_id).get_channel_or_thread(id)

    @property
    def _all_team_channels(self):
        all_channels = {}
        for team in self._teams.values():
            all_channels = {**all_channels, **team._channels}

        return all_channels

    def _get_global_team_channel(self, id):
        return self._all_team_channels.get(id)

    def _get_team_thread(self, team_id, id):
        if self._get_team(team_id):
            return self._get_team(team_id).get_thread(id)

    def _get_team_member(self, team_id, id):
        if self._get_team(team_id):
            return self._get_team(team_id).get_member(id)

    @property
    def _emojis(self):
        emojis = {}
        for team in self._teams.values():
            emojis = {**emojis, **team._emojis}

        return emojis

    def _get_emoji(self, id):
        return self._emojis.get(id)

    def add_to_message_cache(self, message):
        if self._max_messages is None:
            return
        self._messages[message.id] = message
        while len(self._messages) > self._max_messages:
            del self._messages[list(self._messages.keys())[0]]

    def add_to_team_cache(self, team):
        self._teams[team.id] = team

    def add_to_member_cache(self, member):
        team = member.team or self._get_team(member.team_id)
        if team:
            team._members[member.id] = member

    def remove_from_member_cache(self, team_id, member_id):
        if self._get_team(team_id):
            self._get_team(team_id)._members.pop(member_id, None)

    def add_to_team_channel_cache(self, channel):
        team = channel.team or self._get_team(channel.team_id)
        if team:
            team._channels[channel.id] = channel

    def remove_from_team_channel_cache(self, team_id, channel_id):
        if self._get_team(team_id):
            self._get_team(team_id)._channels.pop(channel_id, None)

    def add_to_dm_channel_cache(self, channel):
        self._dm_channels[channel.id] = channel

    def remove_from_dm_channel_cache(self, channel_id):
        self._dm_channels.pop(channel_id, None)

    def add_to_user_cache(self, user):
        self._users[user.id] = user

    def remove_from_user_cache(self, user_id):
        self._users.pop(user_id, None)

    def compatible_content(
        self,
        content: Sequence[Union[str, Embed, File, abc_User, Emoji, Mention, Role, TeamChannel]],
        /,
    ) -> Dict[str, Any]:
        """Formats list-content (ususally from :meth:`.process_list_content`) into API-compatible nodes"""

        compatible = {'object': 'value', 'document': {'object': 'document', 'data': {}, 'nodes': []}}

        for node in content:
            blank_node = {
                'object': 'block',
                'type': None,
                'data': {},
                'nodes': []
            }

            if isinstance(node, (Embed, File)):
                # block content
                blank_node = node.to_node_dict()

            else:
                # inline text content
                if isinstance(node, (
                    abc_User,
                    Emoji,
                    Mention,
                    Role,
                    TeamChannel,
                )):
                    raw_node = node.to_node_dict()

                else:
                    raw_node = {
                        'object': 'text',
                        'leaves': [{'object': 'leaf', 'text': str(node), 'marks': []}]
                    }

                previous_node = None
                try:
                    previous_node = compatible['document']['nodes'][-1]
                except IndexError:
                    pass

                if (previous_node and previous_node['type'] not in ('paragraph', 'markdown-plain-text')) or not previous_node:
                    # use a new node; the previous one is not suitable for
                    # inline content or it does not exist
                    blank_node['type'] = 'markdown-plain-text'
                else:
                    # append to the previous node for inline object usage
                    blank_node = previous_node

                blank_node['nodes'].append(raw_node)

            if blank_node not in compatible['document']['nodes']:
                # we don't want to duplicate the node in the case of inline content
                compatible['document']['nodes'].append(blank_node)

        return compatible

    async def process_list_content(
        self,
        pos_content: tuple,
        *,
        file: File = None,
        files: List[File] = None,
        embed: Embed = None,
        embeds: List[Embed] = None,
    ):
        content = list(pos_content)

        if file:
            if not isinstance(file, File):
                raise TypeError('file must be type File, not %s' % file.__class__.__name__)

            file.set_media_type(MediaType.attachment)
            if file.url is None:
                await file._upload(self)

            content.append(file)

        for file in (files or []):
            if not isinstance(file, File):
                raise TypeError('file must be type File, not %s' % file.__class__.__name__)

            file.set_media_type(MediaType.attachment)
            if file.url is None:
                await file._upload(self)

            content.append(file)

        def replace_attachment_uris(embed):
            # pseudo-support attachment:// URI for use in embeds
            for slot in [('image', 'url'), ('thumbnail', 'url'), ('author', 'icon_url'), ('footer', 'icon_url')]:
                url = getattr(getattr(embed, slot[0]), slot[1])
                if isinstance(url, _EmptyEmbed):
                    continue

                if url.startswith('attachment://'):
                    filename = url.strip('attachment://')
                    for node in content:
                        if isinstance(node, File) and node.filename == filename:
                            getattr(embed, f'_{slot[0]}')[slot[1]] = node.url
                            content.remove(node)  # Don't keep it in the message content
                            break

            return embed

        # upload Files passed positionally
        for node in content:
            if isinstance(node, File) and node.url is None:
                node.set_media_type(MediaType.attachment)
                await node._upload(self)

        # handle attachment URIs for Embeds passed positionally
        # this is a separate loop to ensure that all files are uploaded first
        for node in content:
            if isinstance(node, Embed):
                content[content.index(node)] = replace_attachment_uris(node)

        if embed:
            content.append(replace_attachment_uris(embed))

        for embed in (embeds or []):
            content.append(replace_attachment_uris(embed))

        return content

    def valid_ISO8601(self, timestamp):
        """Manually construct a datetime's ISO8601 representation so that
        Guilded will accept it. Guilded rejects isoformat()'s 6-digit
        microseconds and UTC offset (+00:00)."""
        # Valid example: 2021-10-15T23:58:44.537Z
        return timestamp.strftime('%Y-%m-%dT%H:%M:%S.000Z')

    # /teams

    def get_team_info(self, team_id: str):
        return self.request(UserbotRoute('GET', f'/teams/{team_id}/info'))

    def get_team_members(self, team_id: str):
        return self.request(UserbotRoute('GET', f'/teams/{team_id}/members'))

    def get_detailed_team_members(self, team_id: str, user_ids: list = None, ids_for_basic_info: list = None):
        payload = {
            'userIds': user_ids or [],
            'idsForBasicInfo': ids_for_basic_info or [],
        }
        return self.request(UserbotRoute('POST', f'/teams/{team_id}/members/detail'), json=payload)

    def get_team_member(self, team_id: str, user_id: str, *, as_object=False):
        if as_object is False:
            return self.get_detailed_team_members(team_id, [user_id])
        else:
            async def get_team_member_as_object():
                data = await self.get_detailed_team_members(team_id, [user_id])
                return Member(state=self, data=data[user_id])
            return get_team_member_as_object()

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

        return self.request(UserbotRoute('GET', f'/teams/{team_id}/customReactions'), params=params)

    # /users

    def get_user(self, user_id: str, *, as_object=False):
        if as_object is False:
            return self.request(UserbotRoute('GET', f'/users/{user_id}'))
        else:
            async def get_user_as_object():
                data = await self.request(UserbotRoute('GET', f'/users/{user_id}'))
                return User(state=self, data=data)
            return get_user_as_object()

    # /content

    def get_metadata(self, route: str):
        return self.request(UserbotRoute('GET', '/content/route/metadata'), params={'route': route})

    # media.guilded.gg

    def upload_file(self, file: File):
        return self.request(UserbotRoute('POST', '/media/upload', override_base=UserbotRoute.MEDIA_BASE),
            data={'file': file.fp},
            params={'dynamicMediaTypeId': str(file.type)}
        )

    # one-off

    def read_filelike_data(self, filelike):
        return self.request(Route('GET', filelike.url, override_base=UserbotRoute.NO_BASE))


class UserbotHTTPClient(HTTPClientBase):
    def __init__(self, *, max_messages=1000):
        self.userbot = True
        super().__init__(max_messages=max_messages)

        self.email = None
        self.password = None
        self.cookie = None

    def insert_reply_header(self, message, reply_to):
        message['document']['nodes'].insert(0, {
            'object': 'block',
            'type': 'replying-to-user-header',
            'data': {
                'createdBy': reply_to.author_id,
                'postId': reply_to.id,
                'type': 'reply'
            },
            'nodes': [{'object': 'text', 'leaves': [{'object': 'leaf', 'text': '', 'marks': []}]}]
        })

    @property
    def credentials(self):
        return {'email': self.email, 'password': self.password}

    async def request(self, route, **kwargs):
        url = route.url
        method = route.method
        kwargs['headers'] = kwargs.pop('headers', {})
        if self.cookie is not None:
            kwargs['headers']['guilded-client-id'] = self.cookie

        async def perform():
            log_data = ''
            if kwargs.get('json'):
                log_data = f' with {kwargs["json"]}'
            elif kwargs.get('data'):
                log_data = f' with {kwargs["data"]}'
            log_args = ''
            if kwargs.get('params'):
                log_args = '?' + '&'.join([f'{key}={val}' for key, val in kwargs['params'].items()])
            log.info('%s %s%s%s', method, route.url, log_args, log_data)
            response = await self.session.request(method, url, **kwargs)
            log.info('Guilded responded with HTTP %s', response.status)
            if response.status == 204:
                return None

            try:
                data_txt = await response.text()
            except UnicodeDecodeError:
                data = await response.read()
                log.debug('Response data: bytes')
            else:
                try:
                    data = json.loads(data_txt)
                except json.decoder.JSONDecodeError:
                    data = data_txt
                log.debug(f'Response data: {data}')
            if response.status != 200:

                if response.status == 429:
                    retry_after = response.headers.get('retry-after')
                    log.warning(
                        'Rate limited on %s. Retrying in %s seconds',
                        route.path,
                        retry_after or 5
                    )
                    if retry_after:
                        await asyncio.sleep(float(retry_after))
                        data = await perform()
                    else:
                        await asyncio.sleep(5)
                        data = await perform()

                elif response.status >= 400:
                    exception = error_mapping.get(response.status, HTTPException)
                    raise exception(response, data)

            return data if route.path != '/login' else response

        return await perform()

    # state

    async def login(self, email, password):
        self.session = self.session if self.session and not self.session.closed else aiohttp.ClientSession()

        self.email = email
        self.password = password
        response = await self.request(UserbotRoute('POST', '/login'), json=self.credentials)
        self.cookie = response.cookies['guilded_mid'].value
        data = await self.request(UserbotRoute('GET', '/me'))
        return data

    async def ws_connect(self, cookie=None, **gateway_args):
        cookie = cookie or self.cookie
        if not cookie:
            raise ClientException(
                'No authentication cookies available. Get these from '
                'logging into the REST API at least once '
                'on this Client.'
            )

        gateway_args = {
            **gateway_args,
            'jwt': 'undefined',
            'EIO': '3',
            'transport': 'websocket',
            'guildedClientId': cookie,
        }

        return await self.session.ws_connect(
            'wss://api.guilded.gg/socket.io/?{}'.format(
                '&'.join([f'{key}={val}' for key, val in gateway_args.items()])
            ),
            autoping=False,
        )

    async def voice_ws_connect(self, endpoint, channel_id, token, cookie=None):
        cookie = cookie or self.cookie
        if not cookie:
            raise ClientException(
                'No authentication cookies available. Get these from '
                'logging into the REST API at least once '
                'on this Client.'
            )
        gateway_args = {
            'channelId': channel_id,
            'guildedClientId': cookie,
            'token': token,
            'type': 'voice',
            'EIO': '3',
            'transport': 'websocket'
        }

        return await self.session.ws_connect(
            f'wss://{endpoint}' + '/socket.io/?{}'.format(
                '&'.join([f'{key}={val}' for key, val in gateway_args.items()])
            )
        )

    def logout(self):
        return self.request(UserbotRoute('POST', '/logout'))

    def ping(self):
        return self.request(UserbotRoute('PUT', '/users/me/ping'))

    # /channels

    def send_message(self, channel_id: str, *, payload: Dict[str, Any]):
        route = UserbotRoute('POST', f'/channels/{channel_id}/messages')
        payload = {
            'messageId': utils.new_uuid(),
            **payload,
        }

        return self.request(route, json=payload)

    def edit_message(self, channel_id: str, message_id: str, *, content: Dict[str, Any]):
        route = UserbotRoute('PUT', f'/channels/{channel_id}/messages/{message_id}')
        payload = {
            'content': content,
        }
        return self.request(route, json=payload)

    def delete_message(self, channel_id: str, message_id: str):
        return self.request(UserbotRoute('DELETE', f'/channels/{channel_id}/messages/{message_id}'))

    def add_message_reaction(self, channel_id: str, message_id: str, emoji_id: int):
        return self.request(UserbotRoute('POST', f'/channels/{channel_id}/messages/{message_id}/reactions/{emoji_id}'))

    def remove_self_message_reaction(self, channel_id: str, message_id: str, emoji_id: int):
        return self.request(UserbotRoute('DELETE', f'/channels/{channel_id}/messages/{message_id}/reactions/{emoji_id}'))

    def get_channel(self, channel_id: str):
        return self.get_metadata(f'//channels/{channel_id}/chat')

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
            params['beforeDate'] = self.valid_ISO8601(before)

        if after is not None:
            params['afterDate'] = self.valid_ISO8601(after)

        if limit is not None:
            params['limit'] = limit

        return self.request(UserbotRoute('GET', f'/channels/{channel_id}/messages'), params=params)

    def create_thread(self, channel_id: str, message_content, *, name: str, initial_message=None):
        route = UserbotRoute('POST', f'/channels/{channel_id}/threads')
        thread_id = utils.new_uuid()
        payload = {
            'name': name,
            'channelId': thread_id,
            'confirmed': False,
            'contentType': 'chat',
            'message': {
                'id': utils.new_uuid(),
                'channelId': thread_id,
                'content': self.compatible_content(message_content)
            }
        }

        if initial_message:
            payload['initialThreadMessage'] = initial_message._raw.get('message', initial_message._raw).copy()
            payload['initialThreadMessage']['botId'] = initial_message.user_id
            payload['initialThreadMessage']['webhookId'] = initial_message.webhook_id
            payload['initialThreadMessage']['channelId'] = initial_message.channel_id
            payload['initialThreadMessage']['isOptimistic'] = False

        return self.request(route, json=payload)

    def get_pinned_messages(self, channel_id: str):
        return self.request(UserbotRoute('GET', f'/channels/{channel_id}/pins'))

    def pin_message(self, channel_id: str, message_id: str):
        payload = {'messageId': message_id}
        return self.request(UserbotRoute('POST', f'/channels/{channel_id}/pins'), json=payload)

    def unpin_message(self, channel_id: str, message_id: str):
        return self.request(UserbotRoute('DELETE', f'/channels/{channel_id}/pins/{message_id}'))

    def get_voice_connection_info(self, channel_id: str):
        return self.request(UserbotRoute('GET', f'/channels/{channel_id}/connection'))

    def get_voice_lobby(self, endpoint: str, channel_id: str):
        return self.request(UserbotVoiceRoute(endpoint, 'GET', f'/channels/{channel_id}/voicegroups/lobby'))

    def connect_to_voice_lobby(self, endpoint: str, channel_id: str, *,
        rtp_capabilities: dict,
        moved: bool = False,
        supports_video: bool = False,
        restarting: bool = False,
        previous_channel_id: str = None
    ):
        route = UserbotVoiceRoute(endpoint, 'POST', f'/channels/{channel_id}/voicegroups/lobby/connect')
        payload = {
            'rtpCapabilities': rtp_capabilities,  # data from Get Voice Lobby
            'wasMoved': moved,
            'supportsVideo': supports_video,
            'appType': 'Desktop App',
            'isRestarting': restarting,
            'channelIdFromPreviousConnections': previous_channel_id
        }
        return self.request(route, json=payload)

    def connect_to_voice_transport(self, endpoint: str, channel_id: str, *,
        transport_id: str,
        dtls_parameters: dict
    ):
        route = UserbotVoiceRoute(endpoint, 'POST', f'/channels/{channel_id}/voicegroups/lobby/transport')
        payload = {
            # data from Connect to Voice Lobby
            'transportId': transport_id,
            'dtlsParameters': dtls_parameters
        }
        return self.request(route, json=payload)

    def get_voice_producers(self, endpoint: str, channel_id: str, *,
        transport_id: str,
        rtp_parameters: dict
    ):
        route = UserbotVoiceRoute(endpoint, 'POST', f'/channels/{channel_id}/voicegroups/lobby/transport')
        payload = {
            'kind': 'audio',
            'transportId': transport_id,
            'rtpParameters': rtp_parameters
        }
        return self.request(route, json=payload)

    def leave_voice_channel(self, endpoint: str, channel_id: str):
        route = UserbotVoiceRoute(endpoint, 'POST', f'/channels/{channel_id}/voicegroups/lobby/leave')
        return self.request(route, json={})

    def get_forum_topics(self, channel_id: str, *, limit: int, page: int, before: datetime.datetime):
        route = UserbotRoute('GET', f'/channels/{channel_id}/forums')
        params = {
            'maxItems': limit,
            'page': page,
            'beforeDate': self.valid_ISO8601(before)
        }
        return self.request(route, params=params)

    def get_forum_topic(self, channel_id: str, topic_id: int):
        route = UserbotRoute('GET', f'/channels/{channel_id}/forums/{topic_id}')
        return self.request(route)

    def create_forum_topic(self, channel_id: str, *, title: str, message: Dict[str, Any]):
        route = UserbotRoute('POST', f'/channels/{channel_id}/forums')
        payload = {
            # The client passes an ID here but it is optional
            'title': title,
            'message': message,
        }
        return self.request(route, json=payload)

    def delete_forum_topic(self, channel_id: str, topic_id: int):
        route = UserbotRoute('DELETE', f'/channels/{channel_id}/forums/{topic_id}')
        return self.request(route)

    def update_forum_topic(self, channel_id: str, topic_id: int, *, payload: Dict[str, Any]):
        route = UserbotRoute('PUT', f'/channels/{channel_id}/forums/{topic_id}')
        payload['message'] = self.compatible_content(payload.pop('content'))
        return self.request(route, json=payload)

    def move_forum_topic(self, channel_id: str, topic_id: int, to_channel_id: str):
        route = UserbotRoute('PUT', f'/channels/{channel_id}/forums/{topic_id}/move')
        payload = {'moveToChannelId': to_channel_id}
        return self.request(route, json=payload)

    def sticky_forum_topic(self, channel_id: str, topic_id: int):
        route = UserbotRoute('PUT', f'/channels/{channel_id}/forums/{topic_id}/sticky')
        payload = {'isSticky': True}
        return self.request(route, json=payload)

    def unsticky_forum_topic(self, channel_id: str, topic_id: int):
        route = UserbotRoute('PUT', f'/channels/{channel_id}/forums/{topic_id}/sticky')
        payload = {'isSticky': False}
        return self.request(route, json=payload)

    def lock_forum_topic(self, channel_id: str, topic_id: int):
        route = UserbotRoute('PUT', f'/channels/{channel_id}/forums/{topic_id}/lock')
        payload = {'isLocked': True}
        return self.request(route, json=payload)

    def unlock_forum_topic(self, channel_id: str, topic_id: int):
        route = UserbotRoute('PUT', f'/channels/{channel_id}/forums/{topic_id}/lock')
        payload = {'isLocked': False}
        return self.request(route, json=payload)

    def get_forum_topic_replies(self, channel_id: str, topic_id: int, *, limit: int):
        route = UserbotRoute('GET', f'/channels/{channel_id}/forums/{topic_id}/replies')
        params = {'maxItems': limit}
        return self.request(route, params=params)

    def create_forum_topic_reply(self, channel_id: str, forum_id: int, *, content, reply_to=None):
        route = UserbotRoute('POST', f'/channels/{channel_id}/forums/{forum_id}/replies')
        payload = {
            # The client passes an ID here but it is optional
            'message': self.compatible_content(content)
        }
        if reply_to is not None:
            self.insert_reply_header(payload['message'], reply_to)

        return self.request(route, json=payload)

    def delete_forum_topic_reply(self, channel_id: str, topic_id: int, reply_id: int):
        route = UserbotRoute('DELETE', f'/channels/{channel_id}/forums/{topic_id}/replies/{reply_id}')
        return self.request(route)

    def create_doc(self, channel_id: str, *, payload: Dict[str, Any]):
        payload['content'] = self.compatible_content(payload['content'])
        return self.request(UserbotRoute('POST', f'/channels/{channel_id}/docs'), json=payload)

    def delete_doc(self, channel_id: str, doc_id: int):
        return self.request(UserbotRoute('DELETE', f'/channels/{channel_id}/docs/{doc_id}'))

    def move_doc(self, channel_id: str, doc_id: int, to_channel_id: str):
        route = UserbotRoute('PUT', f'/channels/{channel_id}/docs/{doc_id}/move')
        payload = {'moveToChannelId': to_channel_id}
        return self.request(route, json=payload)

    def get_docs(self, channel_id: str, *, limit: int = 50, before: datetime.datetime = None):
        params = {
            'maxItems': limit,
        }
        if before is not None:
            params['beforeDate'] = self.valid_ISO8601(before)

        return self.request(UserbotRoute('GET', f'/channels/{channel_id}/docs'), params=params)

    def get_doc(self, channel_id: str, doc_id: int):
        return self.request(UserbotRoute('GET', f'/channels/{channel_id}/docs/{doc_id}'))

    def update_doc(self, channel_id: str, doc_id: int, *, payload: Dict[str, Any]):
        payload['content'] = self.compatible_content(payload['content'])
        return self.request(UserbotRoute('PUT', f'/channels/{channel_id}/docs/{doc_id}'), json=payload)

    def create_announcement(self, channel_id: str, title: str, content, game_id: int, dont_send_notifications: bool):
        payload = {
            'title': title,
            'content': self.compatible_content(content),
            'gameId': game_id,
            'dontSendNotifications': dont_send_notifications
        }
        return self.request(UserbotRoute('POST', f'/channels/{channel_id}/announcements'), json=payload)

    def get_announcement(self, channel_id: str, announcement_id: str):
        return self.request(UserbotRoute('GET', f'/channels/{channel_id}/announcements/{announcement_id}'))

    def get_announcements(self, channel_id: str, *, limit: int, before: datetime.datetime):
        params = {
            'maxItems': limit,
            'beforeDate': self.valid_ISO8601(before)
        }
        return self.request(UserbotRoute('GET', f'/channels/{channel_id}/announcements'), params=params)

    def get_pinned_announcements(self, channel_id: str):
        return self.request(UserbotRoute('GET', f'/channels/{channel_id}/pinnedannouncements'))

    def toggle_announcement_pin(self, channel_id: str, announcement_id: str, *, pinned: bool):
        route = UserbotRoute('PUT', f'/channels/{channel_id}/toggleannouncementpin/{announcement_id}')
        payload = {
            'isPinned': pinned
        }
        return self.request(route, json=payload)

    def delete_announcement(self, channel_id: str, announcement_id: str):
        return self.request(UserbotRoute('DELETE', f'/channels/{channel_id}/announcements/{announcement_id}'))

    def update_announcement(self, channel_id: str, announcement_id: str, *, payload: Dict[str, Any]):
        route = UserbotRoute('PUT', f'/channels/{channel_id}/announcements/{announcement_id}')
        payload['content'] = self.compatible_content(payload['content'])
        return self.request(route, json=payload)

    def get_media(self, channel_id: str, media_id: int):
        return self.request(UserbotRoute('GET', f'/channels/{channel_id}/media/{media_id}'))

    def get_medias(self, channel_id: str, *, limit: int):
        params = {
            'pageSize': limit
        }
        return self.request(UserbotRoute('GET', f'/channels/{channel_id}/media'), params=params)

    def create_media(self, channel_id: str, *, payload):
        return self.request(UserbotRoute('POST', f'/channels/{channel_id}/media'), json=payload)

    def move_media(self, channel_id: str, media_id: int, to_channel_id: str):
        route = UserbotRoute('PUT', f'/channels/{channel_id}/media/{media_id}/move')
        payload = {'moveToChannelId': to_channel_id}
        return self.request(route, json=payload)

    def delete_media(self, channel_id: str, media_id: int):
        return self.request(UserbotRoute('DELETE', f'/channels/{channel_id}/media/{media_id}'))

    def create_list_item(self, channel_id: str, *, message: str, note: str, parent_id: str, position: int, send_notifications: bool):
        route = UserbotRoute('POST', f'/channels/{channel_id}/listitems')
        payload = {
            'id': new_uuid(),
            'message': self.compatible_content(message),
            'note': (self.compatible_content(note) if note else None),
            'parentId': parent_id,
            'priority': position
        }
        params = {
            'notifyAllClients': str(send_notifications).lower()
        }
        return self.request(route, json=payload, params=params)
    
    def get_list_item(self, channel_id: str, item_id: str):
        return self.request(UserbotRoute('GET', f'/channels/{channel_id}/listitems/{item_id}'))

    def get_list_items(self, channel_id: str):
        return self.request(UserbotRoute('GET', f'/channels/{channel_id}/listitems'))

    def delete_list_item(self, channel_id: str, item_id: str):
        return self.request(UserbotRoute('DELETE', f'/channels/{channel_id}/listitems/{item_id}'))

    def edit_list_item_message(self, channel_id: str, item_id: str, payload):
        route = UserbotRoute('PUT', f'/channels/{channel_id}/listitems/{item_id}/message')
        return self.request(route, json=payload)

    def edit_list_item_priority(self, channel_id: str, new_orders):
        route = UserbotRoute('PUT', f'/channels/{channel_id}/listitems/priority')
        payload = {
            'orderedListItemIds': new_orders
        }
        return self.request(route, json=payload)

    def move_list_item(self, channel_id: str, item_id: str, to_channel_id: str):
        route = UserbotRoute('PUT', f'/channels/{channel_id}/listitems/{item_id}/move')
        payload = {'moveToChannelId': to_channel_id}
        return self.request(route, json=payload)

    def list_item_is_complete(self, channel_id: str, item_id: str, is_complete: bool):
        route = UserbotRoute('PUT', f'/channels/{channel_id}/listitems/{item_id}/iscomplete')
        payload = {'isComplete': is_complete}
        return self.request(route, json=payload)

    def mark_channel_seen(self, channel_id: str, clear_all_badges: bool = False):
        payload = {
            'clearAllBadges': clear_all_badges
        }
        return self.request(UserbotRoute('PUT', f'/channels/{channel_id}/seen'), json=payload)

    def get_availabilities(self, channel_id: str):
        return self.request(UserbotRoute('GET', f'/channels/{channel_id}/availability'))

    def create_availability(self, channel_id: str, *, start: datetime.datetime, end: datetime.datetime):
        payload = {
            'startDate': self.valid_ISO8601(start),
            'endDate': self.valid_ISO8601(end),
        }
        return self.request(UserbotRoute('POST', f'/channels/{channel_id}/availability'), json=payload)

    def update_availability(self, channel_id: str, availability_id: int, *, payload: Dict[str, datetime.datetime]):
        return self.request(UserbotRoute('PUT', f'/channels/{channel_id}/availability/{availability_id}'), json=payload)

    def delete_availability(self, channel_id: str, availability_id: int):
        return self.request(UserbotRoute('DELETE', f'/channels/{channel_id}/availability/{availability_id}'))

    # /reactions

    def add_content_reaction(self, content_type: str, content_id, emoji_id: int, *, reply: bool = False):
        route = UserbotRoute('PUT', f'/reactions/{content_type}/{content_id}/undefined')
        payload = {
            'customReactionId': emoji_id
        }
        params = {}
        if reply is True:
            # Guilded will throw a 500 if this is specified as false, even if
            # that value is correct
            params['isContentReply'] = 'true'
        return self.request(route, json=payload, params=params)

    def remove_self_content_reaction(self, content_type: str, content_id, emoji_id: int, *, reply: bool = False):
        route = UserbotRoute('DELETE', f'/reactions/{content_type}/{content_id}/undefined')
        payload = {
            'customReactionId': emoji_id
        }
        params = {}
        if reply is True:
            # Guilded will throw a 500 if this is specified as false, even if
            # that value is correct
            params['isContentReply'] = 'true'
        return self.request(route, json=payload, params=params)

    # /teams

    def join_team(self, team_id, invite_id=None):
        payload = {
            'inviteId': invite_id,
        }
        return self.request(UserbotRoute('PUT', f'/teams/{team_id}/members/{self.my_id}/join'), json=payload)

    def create_team_invite(self, team_id):
        return self.request(UserbotRoute('POST', f'/teams/{team_id}/invites'), json={'teamId': team_id})

    def delete_team_emoji(self, team_id: str, emoji_id: int):
        return self.request(UserbotRoute('DELETE', f'/teams/{team_id}/emoji/{emoji_id}'))

    def create_team_channel(
        self,
        team_id: str,
        *,
        payload: Dict[str, Any],
    ):
        group_id = payload.pop('groupId', None)
        route = UserbotRoute('POST', f'/teams/{team_id}/groups/{group_id or "undefined"}/channels')
        return self.request(route, json=payload)

    def get_team_channels(self, team_id: str):
        return self.request(UserbotRoute('GET', f'/teams/{team_id}/channels'))

    def get_public_team_channel(self, team_id: str, channel_id: str):
        return self.request(UserbotRoute('GET', f'/teams/{team_id}/channels/{channel_id}'))

    def change_team_member_nickname(self, team_id: str, user_id: str, nickname: str):
        return self.request(UserbotRoute('GET', f'/teams/{team_id}/members/{user_id}/nickname'), json={'nickname': nickname})

    def reset_team_member_nickname(self, team_id: str, user_id: str):
        return self.request(UserbotRoute('DELETE', f'/teams/{team_id}/members/{user_id}/nickname'))

    def get_team_groups(self, team_id: str):
        return self.request(UserbotRoute('GET', f'/teams/{team_id}/groups'))

    def get_team_group(self, team_id: str, group_id: str):
        return self.request(UserbotRoute('GET', f'/teams/{team_id}/groups/{group_id}'))

    def create_team_group(self, team_id: str, *,
        name: str, description: str, icon_url: str = None, game_id: int = None,
        membership_role_id: int = None,  additional_membership_role_ids: list = [],
        emoji_id: int = None, public: bool = True, base: bool = False, users: list = []
    ):
        payload = {
            'name': name,
            'description': description,
            'avatar': icon_url,
            'gameId': game_id,
            'membershipTeamRoleId': membership_role_id,
            'additionalMembershipTeamRoleIds': additional_membership_role_ids,
            'customReactionId': emoji_id,
            'isPublic': public,
            'isBase': base,
            'users': users
        }
        return self.request(UserbotRoute('POST', f'/teams{team_id}/groups'), json=payload)

    def update_team_group(self, team_id: str, group_id: str, *,
        name: str, description: str, icon_url: str = None, game_id: int = None,
        membership_role_id: int = None,  additional_membership_role_ids: list = [],
        emoji_id: int = None, public: bool = True, base: bool = False, users: list = []
    ):
        payload = {
            'name': name,
            'description': description,
            'avatar': icon_url,
            'gameId': game_id,
            'membershipTeamRoleId': membership_role_id,
            'additionalMembershipTeamRoleIds': additional_membership_role_ids,
            'customReactionId': emoji_id,
            'isPublic': public,
            'isBase': base,
            'users': users
        }
        return self.request(UserbotRoute('PUT', f'/teams{team_id}/groups/{group_id}'), json=payload)

    def delete_team_group(self, team_id: str, group_id: str):
        return self.request(UserbotRoute('DELETE', f'/teams/{team_id}/groups/{group_id}'))

    def delete_team_channel(self, team_id: str, group_id: str, channel_id: str):
        return self.request(UserbotRoute('DELETE', f'/teams/{team_id}/groups/{group_id or "undefined"}/channels/{channel_id}'))

    def create_team_ban(self, team_id: str, user_id: str, *, reason: str = None, after: datetime.datetime = None):
        payload = {'memberId': user_id, 'teamId': team_id, 'reason': reason or ''}

        if isinstance(after, datetime.datetime):
            payload['afterDate'] = self.valid_ISO8601(after)
        elif after is not None:
            raise TypeError('after must be type datetime.datetime, not %s' % after.__class__.__name__)
        else:
            payload['afterDate'] = None

        return self.request(UserbotRoute('DELETE', f'/teams/{team_id}/members/{user_id}/ban'), json=payload)

    def remove_team_ban(self, team_id: str, user_id: str):
        payload = {'memberId': user_id, 'teamId': team_id}
        return self.request(UserbotRoute('PUT', f'/teams/{team_id}/members/{user_id}/ban'), json=payload)

    def get_team_bans(self, team_id: str):
        return self.request(UserbotRoute('GET', f'/teams/{team_id}/members/ban'))

    def remove_team_member(self, team_id: str, user_id: str):
        return self.request(UserbotRoute('DELETE', f'/teams/{team_id}/members/{user_id}'))

    def leave_team(self, team_id: str):
        return self.remove_team_member(team_id, self.my_id)

    def set_team_member_xp(self, team_id: str, user_id: str, xp: int):
        if not isinstance(xp, int):
            raise TypeError('xp must be type int, not %s' % xp.__class__.__name__)

        return self.request(UserbotRoute('PUT', f'/teams/{team_id}/members/{user_id}/xp'), json={'amount': xp})

    def archive_team_thread(self, team_id: str, group_id: str, thread_id: str):
        return self.request(UserbotRoute('PUT', f'/teams/{team_id}/groups/{group_id or "undefined"}/channels/{thread_id}/archive'))

    def restore_team_thread(self, team_id: str, group_id: str, thread_id: str):
        return self.request(UserbotRoute('PUT', f'/teams/{team_id}/groups/{group_id or "undefined"}/channels/{thread_id}/restore'))

    def assign_role_to_member(self, team_id: str, user_id: str, role_id: int):
        return self.request(UserbotRoute('PUT', f'/teams/{team_id}/roles/{role_id}/users/{user_id}'))

    def remove_role_from_member(self, team_id: str, user_id: str, role_id: int):
        return self.request(UserbotRoute('DELETE', f'/teams/{team_id}/roles/{role_id}/users/{user_id}'))

    def update_team_channel_info(self, team_id: str, group_id: str, channel_id: str, payload: dict):
        route = UserbotRoute('PUT', f'/teams/{team_id}/groups/{group_id or "undefined"}/channels/{channel_id}/info')
        return self.request(route, json=payload)

    def update_team_channel_settings(self, team_id: str, group_id: str, channel_id: str, payload: dict):
        route = UserbotRoute('PUT', f'/teams/{team_id}/groups/{group_id or "undefined"}/channels/{channel_id}/settings')
        return self.request(route, json=payload)

    def get_channel_webhooks(self, team_id: str, channel_id: str = None):
        # This endpoint is probably deprecated; it returns an empty list
        return self.request(UserbotRoute('GET', f'/teams/{team_id}/channels/{channel_id}/webhooks'))

    def get_detailed_webhooks(self, team_id: str, webhook_ids: List[str]):
        payload = {
            'webhookIds': webhook_ids,
        }
        return self.request(UserbotRoute('POST', f'/teams/{team_id}/webhooks/detail'), json=payload)

    # /users

    def get_user_profile(self, user_id: str, *, v: int = 3):
        return self.request(UserbotRoute('GET', f'/users/{user_id}/profilev{v}'))

    def get_privacy_settings(self):
        return self.request(UserbotRoute('GET', '/users/me/privacysettings'))

    def set_privacy_settings(
        self,
        *,
        allow_friend_requests_from: str,
        allow_contact_from: str,
        allow_profile_posts_from: str,
    ):
        payload = {
            'userPrivacySettings': {
                'allowDMsFrom': allow_contact_from,
                'allowFriendRequestsFrom': allow_friend_requests_from,
                'allowProfilePostsFrom': allow_profile_posts_from,
            },
        }
        return self.request(UserbotRoute('PUT', '/users/me/privacysettings'), json=payload)

    def set_presence(self, presence):
        payload = {'status': presence}
        return self.request(UserbotRoute('POST', '/users/me/presence'), json=payload)

    def set_transient_status(self, game_id: int):
        payload = {
            'id': 1661,
            'gameId': game_id,
            'type': 'gamepresence'
        }
        return self.request(UserbotRoute('POST', '/users/me/status/transient'), json=payload)

    def delete_transient_status(self):
        return self.request(UserbotRoute('DELETE', '/users/me/status/transient'))

    def set_custom_status(self, status, *, expires: Union[int, datetime.datetime] = 0):
        payload = {
            'content': {'document': {
                'object': 'document',
                'data': [],
                'nodes': []
            }}
        }
        payload['content']['document']['nodes'].append({
            'object': 'text',
            'leaves': [{
                'object': 'leaf',
                'text': status.details,
                'marks': []
            }]
        })
        if status.emoji:
            payload['customReactionId'] = status.emoji.id
            payload['customReaction'] = status.emoji._raw
        if type(expires) == datetime.datetime:
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=datetime.timezone.utc)
            now = datetime.datetime.now(datetime.timezone.utc)
            expires = (expires - now).total_seconds()

        payload['expireInMs'] = expires * 1000

        return self.request(UserbotRoute('POST', '/users/me/status'), json=payload)

    def leave_thread(self, thread_id: str):
        return self.request(UserbotRoute('DELETE', f'/users/{self.my_id}/channels/{thread_id}'))

    def set_profile_images(self, image_url: str):
        return self.request(UserbotRoute('POST', '/users/me/profile/images'), json={'imageUrl': image_url})

    def set_profile_banner(self, image_url: str):
        return self.request(UserbotRoute('POST', '/users/me/profile/images/banner'), json={'imageUrl': image_url})

    def get_friends(self):
        return self.request(UserbotRoute('GET', '/users/me/friends'))

    def create_friend_request(self, user_ids: list):
        return self.request(UserbotRoute('POST', '/users/me/friendrequests'), json={'friendUserIds': user_ids})

    def delete_friend_request(self, user_id: str):
        return self.request(UserbotRoute('DELETE', '/users/me/friendrequests'), json={'friendUserId': user_id})

    def decline_friend_request(self, user_id: str):
        return self.request(UserbotRoute('PUT', '/users/me/friendrequests'), json={'friendUserId': user_id, 'friendStatus': 'declined'})

    def accept_friend_request(self, user_id: str):
        return self.request(UserbotRoute('PUT', '/users/me/friendrequests'), json={'friendUserId': user_id, 'friendStatus': 'accepted'})

    def block_user(self, user_id: str):
        return self.request(UserbotRoute('POST', f'/users/{user_id}/block'))

    def unblock_user(self, user_id: str):
        return self.request(UserbotRoute('POST', f'/users/{user_id}/unblock'))

    def get_referral_statistics(self):
        return self.request(UserbotRoute('GET', '/users/me/referrals'))

    def get_dm_channels(self):
        return self.request(UserbotRoute('GET', f'/users/{self.my_id}/channels'))

    def create_dm_channel(self, user_ids: list):
        payload = {'users': [{'id': user_id} for user_id in user_ids]}
        return self.request(UserbotRoute('POST', f'/users/{self.my_id}/channels'), json=payload)

    def hide_dm_channel(self, channel_id: str):
        return self.request(UserbotRoute('PUT', f'/users/{self.my_id}/channels/{channel_id}/hide'))

    def get_emojis(self):
        return self.request(UserbotRoute('GET', '/users/me/custom_reactions'))

    def get_recovery_info(self):
        return self.request(UserbotRoute('GET', '/users/me/recoveryInfo'))

    def get_verification_status(self):
        return self.request(UserbotRoute('GET', '/users/me/verification'))

    def send_verification_email(self):
        return self.request(UserbotRoute('POST', '/users/me/verify'))

    # /webhooks

    def create_webhook(self, name: str, channel_id:  str):
        payload = {
            'name': name,
            'channelId': channel_id,
        }
        return self.request(Route('POST', f'/webhooks'), json=payload)

    def update_webhook(self, webhook_id: str, *, payload: Dict[str, Any]):
        return self.request(Route('PUT', f'/webhooks/{webhook_id}'), json=payload)

    def delete_webhook(self, webhook_id: str):
        return self.request(Route('DELETE', f'/webhooks/{webhook_id}'))

    # /content

    def get_channel_message(self, channel_id: str, message_id: str):
        return self.get_metadata(f'//channels/{channel_id}/chat?messageId={message_id}')

    def get_embed_for_url(self, url: str):
        return self.request(UserbotRoute('GET', '/content/embed_info'), params={'url': url})

    def get_form_data(self, form_id: int):
        if not isinstance(form_id, int):
            raise TypeError('form_id must be type int, not %s' % form_id.__class__.__name__)
        return self.request(UserbotRoute('GET', f'/content/custom_forms/{form_id}'))

    #def submit_form_response(self, form_id: int, *options):
    #    #payload = {'responseSpecs': 'values': {}}
    #    #for option in options:
    #    #    if option.type is None:pass

    #    return self.request(UserbotRoute('PUT', f'/content/custom_forms/{form_id}/responses'), json=payload)

    def get_content_replies(self, content_type: str, content_id: int):
        return self.request(UserbotRoute('GET', f'/content/{content_type}/{content_id}/replies'))

    def get_content_reply(self, content_type: str, channel_id: str, content_id, reply_id: int):
        return self.get_metadata(f'//channels/{channel_id}/{content_type}/{content_id}?replyId={reply_id}')

    def create_content_reply(self, content_type: str, team_id: str, content_id, *, content, reply_to=None):
        payload = {
            'message': self.compatible_content(content),
            'teamId': team_id
        }
        if reply_to is not None:
            self.insert_reply_header(payload['message'], reply_to)

        return self.request(UserbotRoute('POST', f'/content/{content_type}/{content_id}/replies'), json=payload)

    def delete_content_reply(self, content_type: str, team_id: str, content_id: int, reply_id: int):
        payload = {
            'teamId': team_id
        }
        return self.request(UserbotRoute('DELETE', f'/content/{content_type}/{content_id}/replies/{reply_id}'), json=payload)

    def update_content_reply(self, content_type: str, content_id: str, reply_id: int, *, content):
        payload = {
            'message': self.compatible_content(content),
        }
        return self.request(UserbotRoute('PUT', f'/content/{content_type}/{content_id}/replies/{reply_id}'), json=payload)

    # media.guilded.gg

    def upload_third_party_media(self, url):
        route = UserbotRoute('PUT', '/media/upload/third_party_media', override_base=UserbotRoute.MEDIA_BASE)
        payload = {
            'mediaInfo': {'src': url},
            'dynamicMediaTypeId': str(MediaType.media_channel_upload)
        }
        return self.request(route, json=payload)

    # one-off

    def check_subdomain(self, subdomain: str):
        return self.request(UserbotRoute('GET', f'/subdomains/{subdomain}'))

    def search(self, query: str, *, entity_type: str, max_results: int = 20, exclude: list = None):
        params = {
            'query': query,
            'entityType': entity_type,
            'maxResultsPerType': max_results,
            'excludedEntityIds': ','.join(exclude or [])
        }
        return self.request(UserbotRoute('GET', '/search'), params=params)

    def get_game_list(self):
        return self.request(UserbotRoute('GET', 'https://raw.githubusercontent.com/GuildedAPI/datatables/main/games.json', override_base=UserbotRoute.NO_BASE))

    def accept_invite(self, invite_code):
        payload = {'type': 'consume'}
        return self.request(UserbotRoute('PUT', f'/invites/{invite_code}'), json=payload)

    # websocket

    def trigger_typing(self, channel_id: str):
        return self.ws.send(['ChatChannelTyping', {'channelId': channel_id}])

    # create objects from data

    def create_user(self, **data):
        return User(state=self, **data)

    def create_member(self, **data):
        return Member(state=self, **data)

    def create_channel(self, **data):
        channel_data = data.get('data', data)
        if channel_data.get('type', '').lower() == 'team':
            data['group'] = data.get('group')
            type_ = try_enum(ChannelType, channel_data.get('contentType', 'chat'))
            if type_ is ChannelType.announcement:
                return channel.AnnouncementChannel(state=self, **data)
            elif type_ is ChannelType.chat:
                if 'threadMessageId' in channel_data:
                    # we assume here that only threads will have this attribute
                    # so from this we can reasonably know whether a channel is
                    # a thread
                    return channel.Thread(state=self, **data)
                else:
                    return channel.ChatChannel(state=self, **data)
            elif type_ is ChannelType.doc:
                return channel.DocsChannel(state=self, **data)
            elif type_ is ChannelType.forum:
                return channel.ForumChannel(state=self, **data)
            elif type_ is ChannelType.list:
                return channel.ListChannel(state=self, **data)
            elif type_ is ChannelType.media:
                return channel.MediaChannel(state=self, **data)
            elif type_ is ChannelType.scheduling:
                return channel.SchedulingChannel(state=self, **data)
            elif type_ is ChannelType.voice:
                return channel.VoiceChannel(state=self, **data)
            else:
                return TeamChannel(state=self, **data)
        else:
            return channel.DMChannel(state=self, **data)

    def create_message(self, **data):
        data['channel'] = data.get('channel')
        return ChatMessage(state=self, **data)


class HTTPClient(HTTPClientBase):
    def __init__(self, *, max_messages=1000):
        self.userbot = False
        super().__init__(max_messages=max_messages)

        self.token = None

    @property
    def credentials(self):
        return {'Authorization': f'Bearer {self.token}'}

    async def request(self, route, **kwargs):
        url = route.url
        method = route.method
        kwargs['headers'] = kwargs.pop('headers', {})
        if self.token:
            kwargs['headers'] = {
                **kwargs['headers'],
                **self.credentials,
            }

        async def perform():
            log_data = ''
            if kwargs.get('json'):
                log_data = f' with {kwargs["json"]}'
            elif kwargs.get('data'):
                log_data = f' with {kwargs["data"]}'
            log_args = ''
            if kwargs.get('params'):
                log_args = '?' + '&'.join([f'{key}={val}' for key, val in kwargs['params'].items()])
            log.info('%s %s%s%s', method, route.url, log_args, log_data)
            response = await self.session.request(method, url, **kwargs)
            log.info('Guilded responded with HTTP %s', response.status)

            authenticated_as = response.headers.get('authenticated-as')
            if authenticated_as and authenticated_as != self.my_id and authenticated_as != 'None':
                log.debug('Response provided a new user ID. Previous: %s, New: %s', self.my_id, authenticated_as)
                last_user = self._users.pop(self.my_id, None)
                self.my_id = authenticated_as

                # Update the ClientUser
                if last_user:
                    last_user.id = self.my_id
                    self._users[self.my_id] = last_user

            if response.status == 204:
                return None

            try:
                data_txt = await response.text()
            except UnicodeDecodeError:
                data = await response.read()
                log.debug('Response data: bytes')
            else:
                try:
                    data = json.loads(data_txt)
                except json.decoder.JSONDecodeError:
                    data = data_txt
                log.debug(f'Response data: {data}')
            if response.status != 200:

                if response.status == 429:
                    retry_after = response.headers.get('retry-after')
                    log.warning(
                        'Rate limited on %s. Retrying in %s seconds',
                        route.path,
                        retry_after if retry_after is not None else 5
                    )
                    if retry_after is not None:
                        await asyncio.sleep(float(retry_after))
                        data = await perform()
                    else:
                        await asyncio.sleep(5)
                        data = await perform()

                elif response.status >= 400:
                    exception = error_mapping.get(response.status, HTTPException)
                    raise exception(response, data)

            return data if route.path != '/login' else response

        return await perform()

    # state

    async def ws_connect(self):
        self.session = self.session if self.session and not self.session.closed else aiohttp.ClientSession()

        headers = self.credentials.copy()
        if self.ws:
            # We have connected before
            if self.ws._last_message_id:
                # Catch up with missed messages
                headers['guilded-last-message-id'] = self.ws._last_message_id

        return await self.session.ws_connect(Route.WEBSOCKET_BASE, headers=headers, autoping=False)

    # /channels

    def create_team_channel(
        self,
        server_id: str,
        *,
        payload: Dict[str, Any],
    ):
        payload['serverId'] = server_id
        return self.request(Route('POST', f'/channels'), json=payload)

    def get_channel(self, channel_id: str):
        return self.request(Route('GET', f'/channels/{channel_id}'))

    def delete_channel(self, channel_id: str):
        return self.request(Route('DELETE', f'/channels/{channel_id}'))

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

    def create_forum_topic(self, channel_id: str, *, title: str, content: str):
        payload = {
            'title': title,
            'content': content,
        }
        return self.request(Route('POST', f'/channels/{channel_id}/topics'), json=payload)

    def create_list_item(self, channel_id: str, *, message: str, note: str = None):
        payload = {
            'message': message,
        }
        if note is not None:
            payload['note'] = {'content': note}

        return self.request(Route('POST', f'/channels/{channel_id}/items'), json=payload)

    def get_list_item(self, channel_id: str, item_id: str):
        return self.request(Route('GET', f'/channels/{channel_id}/items/{item_id}'))

    def get_list_items(self, channel_id: str):
        return self.request(Route('GET', f'/channels/{channel_id}/items'))

    def update_list_item(self, channel_id: str, item_id: str, *, payload: Dict[str, Any]):
        return self.request(Route('PUT', f'/channels/{channel_id}/items/{item_id}'), json=payload)

    def delete_list_item(self, channel_id: str, item_id: str):
        return self.request(Route('DELETE', f'/channels/{channel_id}/items/{item_id}'))

    def create_doc(self, channel_id: str, *, title: str, content: str):
        payload = {
            'title': title,
            'content': content,
        }
        return self.request(Route('POST', f'/channels/{channel_id}/docs'), json=payload)

    def get_docs(self, channel_id: str):
        return self.request(Route('GET', f'/channels/{channel_id}/docs'))

    def get_doc(self, channel_id: str, doc_id: int):
        return self.request(Route('GET', f'/channels/{channel_id}/docs/{doc_id}'))

    def update_doc(self, channel_id: str, doc_id: int, *, payload: Dict[str, Any]):
        return self.request(Route('PUT', f'/channels/{channel_id}/docs/{doc_id}'), json=payload)

    def delete_doc(self, channel_id: str, doc_id: int):
        return self.request(Route('DELETE', f'/channels/{channel_id}/docs/{doc_id}'))

    def add_reaction_emote(self, channel_id: str, content_id: str, emoji_id: int):
        return self.request(Route('PUT', f'/channels/{channel_id}/content/{content_id}/emotes/{emoji_id}'))

    # /servers

    def get_server(self, server_id: str):
        return self.request(Route('GET', f'/servers/{server_id}'))

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

    def award_role_xp(self, server_id: str, role_id: int, amount: int):
        payload = {
            'amount': amount,
        }
        return self.request(Route('POST', f'/servers/{server_id}/roles/{role_id}/xp'), json=payload)

    def ban_server_member(self, server_id: str, user_id: str, *, reason: str = None):
        payload = {}
        if reason is not None:
            payload['reason'] = reason

        return self.request(Route('POST', f'/servers/{server_id}/bans/{user_id}'), json=payload)

    def unban_server_member(self, server_id: str, user_id: str):
        return self.request(Route('DELETE', f'/servers/{server_id}/bans/{user_id}'))

    def get_server_bans(self, server_id: str):
        return self.request(Route('GET', f'/servers/{server_id}/bans'))

    def create_webhook(self, server_id: str, *, name: str, channel_id:  str):
        payload = {
            'name': name,
            'channelId': channel_id,
        }
        return self.request(Route('POST', f'/servers/{server_id}/webhooks'), json=payload)

    def get_webhook(self, server_id: str, webhook_id: str):
        return self.request(Route('GET', f'/servers/{server_id}/webhooks/{webhook_id}'))

    def get_channel_webhooks(self, server_id: str, channel_id: str):
        params = {
            'channelId': channel_id,
        }

        return self.request(Route('GET', f'/servers/{server_id}/webhooks'), params=params)

    def update_webhook(self, server_id: str, webhook_id: str, *, payload: Dict[str, Any]):
        return self.request(Route('PUT', f'/servers/{server_id}/webhooks/{webhook_id}'), json=payload)

    def delete_webhook(self, server_id: str, webhook_id: str):
        return self.request(Route('DELETE', f'/servers/{server_id}/webhooks/{webhook_id}'))

    # /groups

    def add_member_to_group(self, group_id: str, user_id: str):
        return self.request(Route('PUT', f'/groups/{group_id}/members/{user_id}'))

    def remove_member_from_group(self, group_id: str, user_id: str):
        return self.request(Route('DELETE', f'/groups/{group_id}/members/{user_id}'))

    # create objects from data

    def create_user(self, **data):
        return User(state=self, **data)

    def create_member(self, **data):
        return Member(state=self, **data)

    def create_channel(self, **data):
        channel_data = data.get('data', data)
        if channel_data.get('serverId') is None:
            return channel.DMChannel(state=self, **data)

        data['group'] = data.get('group')
        type_ = try_enum(ChannelType, channel_data['type'])
        if type_ is ChannelType.announcements:
            return channel.AnnouncementChannel(state=self, **data)
        elif type_ is ChannelType.chat:
            if 'parentId' in channel_data:
                # We assume that only threads will have this attribute so that
                # we can reasonably know whether a channel is a thread
                return channel.Thread(state=self, **data)
            else:
                return channel.ChatChannel(state=self, **data)
        elif type_ is ChannelType.docs:
            return channel.DocsChannel(state=self, **data)
        elif type_ is ChannelType.forums:
            return channel.ForumChannel(state=self, **data)
        elif type_ is ChannelType.list:
            return channel.ListChannel(state=self, **data)
        elif type_ is ChannelType.media:
            return channel.MediaChannel(state=self, **data)
        elif type_ is ChannelType.scheduling:
            return channel.SchedulingChannel(state=self, **data)
        elif type_ is ChannelType.voice:
            return channel.VoiceChannel(state=self, **data)
        else:
            return TeamChannel(state=self, **data)

    def create_message(self, **data):
        data['channel'] = data.get('channel')
        return ChatMessage(state=self, **data)
