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
import json
import logging
import re
from typing import Any, Dict, Union

from . import utils
from . import channel
from .abc import User as abc_User
from .abc import TeamChannel
from .embed import Embed
from .emoji import Emoji
from .errors import ClientException, HTTPException, error_mapping
from .file import File, MediaType
from .message import ChatMessage, Mention
from .role import Role
from .user import User, Member
from .utils import new_uuid

log = logging.getLogger(__name__)

class UserbotRoute:
    BASE = 'https://www.guilded.gg/api'
    MEDIA_BASE = 'https://media.guilded.gg'
    CDN_BASE = 'https://s3-us-west-2.amazonaws.com/www.guilded.gg'
    NO_BASE = ''
    def __init__(self, method, path, *, override_base=None):
        self.method = method
        self.path = path

        if override_base is not None:
            self.BASE = override_base

        self.url = self.BASE + path


class Route(UserbotRoute):
    BASE = 'https://www.guilded.gg/api/v1'
    WEBSOCKET_BASE = 'wss://api.guilded.gg/v1/websocket'


class UserbotVoiceRoute(UserbotRoute):
    def __init__(self, voice_endpoint, method, path):
        self.BASE = f'https://{voice_endpoint}'
        self.method = method
        self.path = path

        self.url = self.BASE + path


class HTTPClientBase:
    GIL_ID = 'Ann6LewA'
    def __init__(self, *, session, max_messages=1000):
        self.session = session
        self._max_messages = max_messages

        self.ws = None

        self._users = {}
        self._teams = {}
        self._messages = {}

        self._threads = {}
        self._dm_channels = {}

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

    # /teams

    def get_team(self, team_id: str):
        return self.request(UserbotRoute('GET', f'/teams/{team_id}'))

    def get_team_members(self, team_id: str):
        return self.request(UserbotRoute('GET', f'/teams/{team_id}/members'))

    def get_detailed_team_members(self, team_id: str, user_ids: list):
        return self.request(UserbotRoute('POST', f'/teams/{team_id}/members/detail'), json={'userIds': user_ids})

    def get_team_member(self, team_id: str, user_id: str, *, as_object=False):
        if as_object is False:
            return self.get_detailed_team_members(team_id, [user_id])
        else:
            async def get_team_member_as_object():
                data = await self.get_detailed_team_members(team_id, [user_id])
                return Member(state=self, data=data[user_id])
            return get_team_member_as_object()

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

    def get_channel(self, channel_id: str):
        return self.get_metadata(f'//channels/{channel_id}/chat')

    # one-off

    def execute_webhook(self, webhook_id: str, webhook_token: str, data: dict):
        return self.request(Route('POST', f'/webhooks/{webhook_id}/{webhook_token}', override_base=UserbotRoute.MEDIA_BASE), json=data)

    def read_filelike_data(self, filelike):
        return self.request(Route('GET', filelike.url, override_base=UserbotRoute.NO_BASE))


class UserbotHTTPClient(HTTPClientBase):
    def __init__(self, *, session, max_messages=1000):
        self.userbot = True
        super().__init__(session=session, max_messages=max_messages)

        self.my_id = None

        self.email = None
        self.password = None
        self.cookie = None

    def compatible_content(self, content):
        compatible = {'object': 'value', 'document': {'object': 'document', 'data': {}, 'nodes': []}}

        for node in content:
            blank_node = {
                'object': 'block',
                'type': None,
                'data': {},
                'nodes': []
            }
            blank_mention_node = blank_node.copy()
            blank_mention_node['object'] = 'inline'
            blank_mention_node['type'] = 'mention'
            blank_mention_node['nodes'] = [{'object': 'text', 'leaves': [{'object': 'leaf', 'text': None, 'marks': []}]}]

            blank_channel_node = blank_mention_node.copy()
            blank_channel_node['type'] = 'channel'

            if isinstance(node, Embed):
                blank_node['type'] = 'webhookMessage'
                blank_node['data'] = {'embeds': [node.to_dict()]}

            elif isinstance(node, File):
                blank_node['type'] = node.file_type
                blank_node['data'] = {'src': node.url}

            else:
                # inline text content
                if isinstance(node, Emoji):
                    raw_node = {
                        'object': 'inline',
                        'type': 'reaction',
                        'data': {'reaction': {'id': node.id, 'customReactionId': node.id}},
                        'nodes': [{'object': 'text', 'leaves': [{'object': 'leaf', 'text': f':{node.name}:', 'marks': []}]}]
                    }

                elif isinstance(node, abc_User):
                    raw_node = blank_mention_node
                    raw_node['data']['mention'] = {
                        'type': 'person',
                        'id': node.id,
                        'matcher': f'@{node.display_name}',
                        'name': node.display_name,
                        'avatar': str(node.avatar_url),
                        'color': str(node.colour),
                        'nickname': node.nickname == node.name
                    }
                    raw_node['nodes'][0]['leaves'][0]['text'] = f'@{node.display_name}'

                elif isinstance(node, Mention):
                    raw_node = blank_mention_node
                    raw_node['data']['mention'] = node.value
                    raw_node['nodes'][0]['leaves'][0]['text'] = str(node)

                elif isinstance(node, Role):
                    raw_node = blank_mention_node
                    raw_node['data']['mention'] = {
                        'type': 'role',
                        'id': node.id,
                        'matcher': f'@{node.name}',
                        'name': node.name,
                        'color': str(node.colour) if node.colour else 'transparent'
                    }
                    raw_node['nodes'][0]['leaves'][0]['text'] = f'@{node.name}'

                elif isinstance(node, TeamChannel):
                    raw_node = blank_channel_node
                    raw_node['data']['channel'] = {
                        'id': node.id,
                        'matcher': f'#{node.name}',
                        'name': node.name
                    }
                    raw_node['nodes'][0]['leaves'][0]['text'] = f'#{node.name}'

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

    def valid_ISO8601(self, timestamp):
        """Manually construct a datetime's ISO8601 representation so that
        Guilded will accept it. Guilded rejects isoformat()'s 6-digit
        microseconds and UTC offset (+00:00)."""
        # Valid example: 2021-10-15T23:58:44.537Z
        return timestamp.strftime('%Y-%m-%dT%H:%M:%S.000Z')

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
        gateway_args = {**gateway_args,
            'jwt': 'undefined',
            'EIO': '3',
            'transport': 'websocket',
            'guildedClientId': cookie
        }

        return await self.session.ws_connect(
            'wss://api.guilded.gg/socket.io/?{}'.format(
                '&'.join([f'{key}={val}' for key, val in gateway_args.items()])
            )
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

    def send_message(self, channel_id: str, content, extra_payload=None, share_urls=None):
        route = UserbotRoute('POST', f'/channels/{channel_id}/messages')
        payload = {
            'messageId': utils.new_uuid(),
            'content': self.compatible_content(content),
            **(extra_payload or {})
        }

        if share_urls:
            payload['content']['document']['data']['shareUrls'] = share_urls

        return self.request(route, json=payload), payload

    def edit_message(self, channel_id: str, message_id: str, **fields):
        route = UserbotRoute('PUT', f'/channels/{channel_id}/messages/{message_id}')
        payload = {'content': {'object': 'value', 'document': {'object': 'document', 'data': {}, 'nodes': []}}}

        try:
            content = fields['content']
        except KeyError:
            if fields.get('old_content'):
                content = fields.get('old_content')
                payload['content']['document']['nodes'].append({
                    'object': 'block', 
                    'type': 'markdown-plain-text', 
                    'data': {},
                    'nodes': [{'object':'text', 'leaves': [{'object': 'leaf', 'text': str(content), 'marks': []}]}]
                })
        else:
            payload['content']['document']['nodes'].append({
                'object': 'block', 
                'type': 'markdown-plain-text', 
                'data': {},
                'nodes': [{'object':'text', 'leaves': [{'object': 'leaf', 'text': str(content), 'marks': []}]}]
            })

        try:
            embeds = fields['embeds']
        except KeyError:
            if fields.get('old_embeds'):
                embeds = fields.get('old_embeds')
                payload['content']['document']['nodes'].append({
                    'object': 'block',
                    'type': 'webhookMessage',
                    'data': {'embeds': embeds},
                    'nodes': []
                })
        else:
            payload['content']['document']['nodes'].append({
                'object': 'block',
                'type': 'webhookMessage',
                'data': {'embeds': embeds},
                'nodes': []
            })

        try:
            files = fields['files']
        except KeyError:
            if fields.get('old_files'):
                files = fields.get('old_files')
                for file in files:
                    payload['content']['document']['nodes'].append({
                        'object': 'block',
                        'type': str(file.file_type),
                        'data': {'src': file.url},
                        'nodes': []
                    })
        else:
            for file in files:
                payload['content']['document']['nodes'].append({
                    'object': 'block',
                    'type': file.file_type,
                    'data': {'src': file.url},
                    'nodes': []
                })

        return self.request(route, json=payload)

    def delete_message(self, channel_id: str, message_id: str):
        return self.request(UserbotRoute('DELETE', f'/channels/{channel_id}/messages/{message_id}'))

    def add_message_reaction(self, channel_id: str, message_id: str, emoji_id: int):
        return self.request(UserbotRoute('POST', f'/channels/{channel_id}/messages/{message_id}/reactions/{emoji_id}'))

    def remove_self_message_reaction(self, channel_id: str, message_id: str, emoji_id: int):
        return self.request(UserbotRoute('DELETE', f'/channels/{channel_id}/messages/{message_id}/reactions/{emoji_id}'))

    def get_channel_messages(self, channel_id: str, *, limit: int):
        return self.request(UserbotRoute('GET', f'/channels/{channel_id}/messages'), params={'limit': limit})

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
                'content': compatible_content(message_content)
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

    def create_forum_topic(self, channel_id: str, *, title, content):
        route = UserbotRoute('POST', f'/channels/{channel_id}/forums')
        payload = {
            # The client passes an ID here but it is optional
            'title': title,
            'message': self.compatible_content(content)
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

    def join_team(self, team_id):
        return self.request(UserbotRoute('PUT', f'/teams/{team_id}/members/{self.my_id}/join'))

    def create_team_invite(self, team_id):
        return self.request(UserbotRoute('POST', f'/teams/{team_id}/invites'), json={'teamId': team_id})

    def delete_team_emoji(self, team_id: str, emoji_id: int):
        return self.request(UserbotRoute('DELETE', f'/teams/{team_id}/emoji/{emoji_id}'))

    def create_team_channel(self, team_id: str, name: str, content_type: str, group_id: str = None, category_id: int = None, public: bool = False):
        payload = {
            'name': name,
            'channelCategoryId': category_id,
            'contentType': content_type,
            'isPublic': public
        }
        return self.request(UserbotRoute('POST', f'/teams/{team_id}/groups/{group_id or "undefined"}/channels'), json=payload)

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

    # /users

    def get_user_profile(self, user_id: str, *, v: int = 3):
        return self.request(UserbotRoute('GET', f'/users/{user_id}/profilev{v}'))

    def get_privacy_settings(self):
        return self.request(UserbotRoute('GET', '/users/me/privacysettings'))

    def set_privacy_settings(self, dms, friend_requests):
        return self.request(UserbotRoute('PUT', '/users/me/privacysettings', json={
            'allowDMsFrom': str(dms),
            'allowFriendRequestsFrom': str(friend_requests)
        }))

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

    # /content

    async def get_channel_message(self, channel_id: str, message_id: str):
        metadata = await self.get_metadata(f'//channels/{channel_id}/chat?messageId={message_id}')
        channel = self.create_channel(data=metadata['metadata']['channel'])
        message = self.create_message(data=metadata['metadata']['message'], channel=channel)
        return message

    def get_embed_for_url(self, url: str):
        return self.request(UserbotRoute('GET', '/content/embed_info'), params={'url': url})

    def get_form_data(self, form_id: int):
        if not isinstance(form, int):
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

    def upload_file(self, file):
        return self.request(UserbotRoute('POST', '/media/upload', override_base=UserbotRoute.MEDIA_BASE),
            data={'file': file._bytes},
            params={'dynamicMediaTypeId': str(file.type)}
        )

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
        return self.request(UserbotRoute('PUT', f'/invites/{invite_code}'), json={'type': 'consume'})

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
            ctype = channel.ChannelType.from_str(channel_data.get('contentType', 'chat'))
            if ctype is channel.ChannelType.announcements:
                return channel.AnnouncementChannel(state=self, **data)
            elif ctype is channel.ChannelType.chat:
                if 'threadMessageId' in channel_data:
                    # we assume here that only threads will have this attribute
                    # so from this we can reasonably know whether a channel is
                    # a thread
                    return channel.Thread(state=self, **data)
                else:
                    return channel.ChatChannel(state=self, **data)
            elif ctype is channel.ChannelType.docs:
                return channel.DocsChannel(state=self, **data)
            elif ctype is channel.ChannelType.forum:
                return channel.ForumChannel(state=self, **data)
            elif ctype is channel.ChannelType.list:
                return channel.ListChannel(state=self, **data)
            elif ctype is channel.ChannelType.media:
                return channel.MediaChannel(state=self, **data)
            elif ctype is channel.ChannelType.scheduling:
                return channel.SchedulingChannel(state=self, **data)
            elif ctype is channel.ChannelType.voice:
                return channel.VoiceChannel(state=self, **data)
        else:
            return channel.DMChannel(state=self, **data)

    def create_message(self, **data):
        data['channel'] = data.get('channel')
        return ChatMessage(state=self, **data)


class HTTPClient(HTTPClientBase):
    def __init__(self, *, session, user_id, max_messages=1000):
        self.userbot = False
        super().__init__(session=session, max_messages=max_messages)

        self.my_id = user_id
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

    async def ws_connect(self):
        headers = self.credentials.copy()
        if self.ws:
            # we have connected before
            if self.ws._last_message_id:
                # catching up with missed messages
                headers['guilded-last-message-id'] = self.ws._last_message_id

        return await self.session.ws_connect(Route.WEBSOCKET_BASE, headers=headers)

    # /channels

    def create_channel_message(self, channel_id: str, *, content: str, private: bool = None, reply_to_ids: list = None):
        route = Route('POST', f'/channels/{channel_id}/messages')

        payload = {}
        if content is not None:
            payload['content'] = str(content)
        if private is not None:
            payload['isPrivate'] = private
        if reply_to_ids:
            payload['replyMessageIds'] = reply_to_ids

        return self.request(route, json=payload)

    def update_channel_message(self, channel_id: str, message_id: str, *, content: str):
        route = Route('PUT', f'/channels/{channel_id}/messages/{message_id}')
        payload = {
            'content': content,
        }

        return self.request(route, json=payload)

    def delete_channel_message(self, channel_id: str, message_id: str):
        return self.request(Route('DELETE', f'/channels/{channel_id}/messages/{message_id}'))

    def get_channel_message(self, channel_id: str, message_id: str):
        return self.request(Route('GET', f'/channels/{channel_id}/messages/{message_id}'))

    def get_channel_messages(self, channel_id: str, *, include_private: bool = False):
        params = {
            'includePrivate': str(include_private).lower()
        }
        return self.request(Route('GET', f'/channels/{channel_id}/messages'), params=params)

    def create_forum_thread(self, channel_id: str, *, title: str, content: str):
        payload = {
            'title': title,
            'content': content,
        }
        return self.request(Route('POST', f'/channels/{channel_id}/forum'), json=payload)

    def create_list_item(self, channel_id: str, *, message: str, note: str = None):
        payload = {
            'message': message,
            'note': note,
        }
        return self.request(Route('POST', f'/channels/{channel_id}/list'), json=payload)

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
        if channel_data.get('type', '').lower() == 'dm':
            return channel.DMChannel(state=self, **data)

        data['group'] = data.get('group')
        ctype = channel.ChannelType.from_str(channel_data.get('contentType', 'chat'))
        if ctype is channel.ChannelType.announcements:
            return channel.AnnouncementChannel(state=self, **data)
        elif ctype is channel.ChannelType.chat:
            if 'threadMessageId' in channel_data:
                # we assume here that only threads will have this attribute
                # so from this we can reasonably know whether a channel is
                # a thread
                return channel.Thread(state=self, **data)
            else:
                return channel.ChatChannel(state=self, **data)
        elif ctype is channel.ChannelType.docs:
            return channel.DocsChannel(state=self, **data)
        elif ctype is channel.ChannelType.forum:
            return channel.ForumChannel(state=self, **data)
        elif ctype is channel.ChannelType.list:
            return channel.ListChannel(state=self, **data)
        elif ctype is channel.ChannelType.media:
            return channel.MediaChannel(state=self, **data)
        elif ctype is channel.ChannelType.scheduling:
            return channel.SchedulingChannel(state=self, **data)
        elif ctype is channel.ChannelType.voice:
            return channel.VoiceChannel(state=self, **data)

    def create_message(self, **data):
        data['channel'] = data.get('channel')
        return ChatMessage(state=self, **data)
