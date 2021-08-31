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
from typing import Union

from . import utils
from . import channel
from .embed import Embed
from .errors import ClientException, HTTPException, error_mapping
from .file import File
from .message import ChatMessage
from .user import User, Member

log = logging.getLogger(__name__)

class Route:
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

class HTTPClient:
    def __init__(self, *, session, max_messages=1000):
        self.session = session
        self.ws = None
        self.my_id = None

        self.email = None
        self.password = None
        self.cookie = None

        self._max_messages = max_messages
        self._users = {}
        self._teams = {}
        self._emojis = {}
        self._messages = {}
        self._team_members = {}
        self._team_channels = {}
        self._team_threads = {}
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
        return self._team_channels.get(team_id, {}).get(id)

    @property
    def _all_team_channels(self):
        all_channels = {}
        for team in self._team_channels.values():
            for channel_id, channel in team.items():
                all_channels[channel_id] = channel

        return all_channels

    def _get_global_team_channel(self, id):
        return self._all_team_channels.get(id)

    def _get_team_thread(self, team_id, id):
        return self._team_threads.get(team_id, {}).get(id)

    def _get_team_member(self, team_id, id):
        return self._team_members.get(team_id, {}).get(id)

    def add_to_message_cache(self, message):
        if self._max_messages is None:
            return
        self._messages[message.id] = message
        while len(self._messages) > self._max_messages:
            del self._messages[list(self._messages.keys())[0]]

    def add_to_team_cache(self, team):
        self._teams[team.id] = team

    def add_to_member_cache(self, member):
        self._team_members[member.team_id] = self._team_members.get(member.team_id, {})
        self._team_members[member.team_id][member.id] = member

    def remove_from_member_cache(self, team_id, member_id):
        try: del self._team_members[team_id][member_id]
        except KeyError: pass

    def add_to_team_channel_cache(self, channel):
        self._team_channels[channel.team_id] = self._team_channels.get(channel.team_id, {})
        self._team_channels[channel.team_id][channel.id] = channel

    def remove_from_team_channel_cache(self, channel_id):
        try: del self._team_channels[channel_id]
        except KeyError: pass

    def add_to_dm_channel_cache(self, channel):
        self._dm_channels[channel.id] = channel

    @property
    def credentials(self):
        return {'email': self.email, 'password': self.password}

    async def request(self, route, **kwargs):
        url = route.url
        method = route.method

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
                    retry_after = response.headers.get('Retry-After')
                    log.warning(
                        'Rate limited on %s. Retrying in %s seconds',
                        route.path,
                        retry_after or 5
                    )
                    if retry_after:
                        await asyncio.sleep(retry_after)
                        data = await perform()
                    else:
                        await asyncio.sleep(5)
                        data = await perform()
                        #raise TooManyRequests(response)

                elif response.status >= 400:
                    exception = error_mapping.get(response.status, HTTPException)
                    raise exception(response, data)

            return data if route.path != '/login' else response

        return await perform()

    # state

    async def login(self, email, password):
        self.email = email
        self.password = password
        response = await self.request(Route('POST', '/login'), json=self.credentials)
        self.cookie = response.cookies['guilded_mid'].value
        data = await self.request(Route('GET', '/me'))
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

    def logout(self):
        return self.request(Route('POST', '/logout'))

    def ping(self):
        return self.request(Route('PUT', '/users/me/ping'))

    # /channels
    # (message interfacing)

    def send_message(self, channel_id: str, content, extra_payload=None, share_urls=None):
        route = Route('POST', f'/channels/{channel_id}/messages')
        payload = {
            'messageId': utils.new_uuid(),
            'content': {'object': 'value', 'document': {'object': 'document', 'data': {}, 'nodes': []}},
            **(extra_payload or {})
        }

        if share_urls:
            payload['content']['document']['data']['shareUrls'] = share_urls

        for node in content:
            blank_node = {
                'object': 'block',
                'type': None,
                'data': {},
                'nodes': []
            }
            if isinstance(node, Embed):
                blank_node['type'] = 'webhookMessage'
                blank_node['data'] = {'embeds': [node.to_dict()]}

            elif isinstance(node, File):
                blank_node['type'] = node.file_type
                blank_node['data'] = {'src': node.url}

            else:
                # stringify anything else, similar to prev. behavior
                blank_node['type'] = 'markdown-plain-text'
                blank_node['nodes'].append({'object':'text', 'leaves': [{'object': 'leaf', 'text': str(node), 'marks': []}]})

            payload['content']['document']['nodes'].append(blank_node)

        return self.request(route, json=payload), payload

    def edit_message(self, channel_id: str, message_id: str, **fields):
        route = Route('PUT', f'/channels/{channel_id}/messages/{message_id}')
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
        return self.request(Route('DELETE', f'/channels/{channel_id}/messages/{message_id}'))

    def add_message_reaction(self, channel_id: str, message_id: str, emoji_id: int):
        return self.request(Route('POST', f'/channels/{channel_id}/messages/{message_id}/reactions/{emoji_id}'))

    def remove_self_message_reaction(self, channel_id: str, message_id: str, emoji_id: int):
        return self.request(Route('DELETE', f'/channels/{channel_id}/messages/{message_id}/reactions/{emoji_id}'))

    def get_channel_messages(self, channel_id: str, *, limit: int):
        return self.request(Route('GET', f'/channels/{channel_id}/messages'), params={'limit': limit})

    def create_thread(self, channel_id: str, message_content, *, name: str, initial_message=None):
        route = Route('POST', f'/channels/{channel_id}/threads')
        thread_id = utils.new_uuid()
        payload = {
            'name': name,
            'channelId': thread_id,
            'confirmed': False,
            'contentType': 'chat',
            'message': {
                'id': utils.new_uuid(),
                'channelId': thread_id,
                'content': {'object': 'value', 'document': {'object': 'document', 'data': {}, 'nodes': []}}
            }
        }

        for node in message_content:
            blank_node = {
                'object': 'block',
                'type': None,
                'data': {},
                'nodes': []
            }
            if isinstance(node, Embed):
                blank_node['type'] = 'webhookMessage'
                blank_node['data'] = {'embeds': [node.to_dict()]}

            elif isinstance(node, File):
                blank_node['type'] = node.file_type
                blank_node['data'] = {'src': node.url}

            else:
                # stringify anything else, similar to prev. behavior
                blank_node['type'] = 'markdown-plain-text'
                blank_node['nodes'].append({'object':'text', 'leaves': [{'object': 'leaf', 'text': str(node), 'marks': []}]})

            payload['message']['content']['document']['nodes'].append(blank_node)

        if initial_message:
            payload['initialThreadMessage'] = initial_message._raw.get('message', initial_message._raw).copy()
            payload['initialThreadMessage']['botId'] = initial_message.bot_id
            payload['initialThreadMessage']['webhookId'] = initial_message.webhook_id
            payload['initialThreadMessage']['channelId'] = initial_message.channel_id
            payload['initialThreadMessage']['isOptimistic'] = False

        return self.request(route, json=payload)

    # /teams

    def join_team(self, team_id):
        return self.request(Route('PUT', f'/teams/{team_id}/members/{self.my_id}/join'))

    def create_team_invite(self, team_id):
        return self.request(Route('POST', f'/teams/{team_id}/invites'), json={'teamId': team_id})

    def delete_team_emoji(self, team_id: str, emoji_id: int):
        return self.request(Route('DELETE', f'/teams/{team_id}/emoji/{emoji_id}'))

    def get_team(self, team_id: str):
        return self.request(Route('GET', f'/teams/{team_id}'))

    def get_team_members(self, team_id: str):
        return self.request(Route('GET', f'/teams/{team_id}/members'))

    def get_detailed_team_members(self, team_id: str, user_ids: list):
        return self.request(Route('POST', f'/teams/{team_id}/members/detail'), json={'userIds': user_ids})

    def get_team_member(self, team_id: str, user_id: str, *, as_object=False):
        if as_object is False:
            return self.get_detailed_team_members(team_id, [user_id])
        else:
            async def get_team_member_as_object():
                data = await self.get_detailed_team_members(team_id, [user_id])
                return Member(state=self, data=data[user_id])
            return get_team_member_as_object()

    def get_team_channels(self, team_id: str):
        return self.request(Route('GET', f'/teams/{team_id}/channels'))

    def get_public_team_channel(self, team_id: str, channel_id: str):
        return self.request(Route('GET', f'/teams/{team_id}/channels/{channel_id}'))

    def change_team_member_nickname(self, team_id: str, user_id: str, nickname: str):
        return self.request(Route('GET', f'/teams/{team_id}/members/{user_id}/nickname'), json={'nickname': nickname})

    def reset_team_member_nickname(self, team_id: str, user_id: str):
        return self.request(Route('DELETE', f'/teams/{team_id}/members/{user_id}/nickname'))

    def create_team_group(self, team_id: str, *,
        name: str, description: str, icon_url: str = None, game_id: int = None,
        membership_role_id: int = None,  additional_membership_role_ids: list = [],
        emoji_id: int = None, public: bool = True, base: bool = False, users: list = []
    ):
        return self.request(
            Route('POST', f'/teams{team_id}/groups'),
            json={
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
        )

    def update_team_group(self, team_id: str, group_id: str, *,
        name: str, description: str, icon_url: str = None, game_id: int = None,
        membership_role_id: int = None,  additional_membership_role_ids: list = [],
        emoji_id: int = None, public: bool = True, base: bool = False, users: list = []
    ):
        return self.request(
            Route('PUT', f'/teams{team_id}/groups/{group_id}'),
            json={
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
        )

    def delete_team_group(self, team_id: str, group_id: str):
        return self.request(Route('DELETE', f'/teams/{team_id}/groups/{group_id}'))

    def delete_team_channel(self, team_id: str, group_id: str, channel_id: str):
        return self.request(Route('DELETE', f'/teams/{team_id}/groups/{group_id or "undefined"}/channels/{channel_id}'))

    def create_team_ban(self, team_id: str, user_id: str, *, reason: str = None, after: datetime.datetime = None):
        payload = {'memberId': user_id, 'teamId': team_id, 'reason': reason or ''}

        if isinstance(after, datetime.datetime):
            payload['afterDate'] = after.isoformat()
        elif after is not None:
            raise TypeError('after must be type datetime.datetime, not %s' % after.__class__.__name__)
        else:
            payload['afterDate'] = None

        return self.request(Route('DELETE', f'/teams/{team_id}/members/ban'), json=payload)

    def remove_team_ban(self, team_id: str, user_id: str):
        payload = {'memberId': user_id, 'teamId': team_id}
        return self.request(Route('PUT', f'/teams/{team_id}/members/{user_id}/ban'), json=payload)

    def get_team_bans(self, team_id: str):
        return self.request(Route('GET', f'/teams/{team_id}/members/ban'))

    def remove_team_member(self, team_id: str, user_id: str):
        return self.request(Route('DELETE', f'/teams/{team_id}/members/{user_id}'))

    def leave_team(self, team_id: str):
        return self.remove_team_member(team_id, self.my_id)

    def set_team_member_xp(self, team_id: str, user_id: str, xp: int):
        if not isinstance(xp, int):
            raise TypeError('xp must be type int, not %s' % xp.__class__.__name__)

        return self.request(Route('PUT', f'/teams/{team_id}/members/{user_id}/xp'), json={'amount': xp})

    def archive_team_thread(self, team_id: str, group_id: str, thread_id: str):
        return self.request(Route('PUT', f'/teams/{team_id}/groups/{group_id or "undefined"}/channels/{thread_id}/archive'))

    def restore_team_thread(self, team_id: str, group_id: str, thread_id: str):
        return self.request(Route('PUT', f'/teams/{team_id}/groups/{group_id or "undefined"}/channels/{thread_id}/restore'))

    # /users

    def get_user(self, user_id: str, *, as_object=False):
        if as_object is False:
            return self.request(Route('GET', f'/users/{user_id}'))
        else:
            async def get_user_as_object():
                data = await self.request(Route('GET', f'/users/{user_id}'))
                return User(state=self, data=data)
            return get_user_as_object()

    def get_privacy_settings(self):
        return self.request(Route('GET', '/users/me/privacysettings'))

    def set_privacy_settings(self, dms, friend_requests):
        return self.request(Route('PUT', '/users/me/privacysettings', json={
            'allowDMsFrom': str(dms),
            'allowFriendRequestsFrom': str(friend_requests)
        }))

    def update_activity(self, activity, *, expires: Union[int, datetime.datetime] = 0):
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
                'text': activity.details,
                'marks': []
            }]
        })
        if activity.emoji:
            payload['customReactionId'] = activity.emoji.id
            payload['customReaction'] = activity.emoji._raw
        if type(expires) == datetime.datetime:
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=datetime.timezone.utc)
            now = datetime.datetime.now(datetime.timezone.utc)
            expires = (expires - now).total_seconds()

        payload['expireInMs'] = expires * 1000

        return self.request(Route('POST', '/users/me/status'), json=payload)

    def leave_thread(self, thread_id: str):
        return self.request(Route('DELETE', f'/users/{self.my_id}/channels/{thread_id}'))

    def set_profile_images(self, image_url: str):
        return self.request(Route('POST', '/users/me/profile/images'), json={'imageUrl': image_url})

    def set_profile_banner(self, image_url: str):
        return self.request(Route('POST', '/users/me/profile/images/banner'), json={'imageUrl': image_url})

    def get_friends(self):
        return self.request(Route('GET', '/users/me/friends'))

    def create_friend_request(self, user_ids: list):
        return self.request(Route('POST', '/users/me/friendrequests'), json={'friendUserIds': user_ids})

    def delete_friend_request(self, user_id: str):
        return self.request(Route('DELETE', '/users/me/friendrequests'), json={'friendUserId': user_id})

    def decline_friend_request(self, user_id: str):
        return self.request(Route('PUT', '/users/me/friendrequests'), json={'friendUserId': user_id, 'friendStatus': 'declined'})

    def accept_friend_request(self, user_id: str):
        return self.request(Route('PUT', '/users/me/friendrequests'), json={'friendUserId': user_id, 'friendStatus': 'accepted'})

    def block_user(self, user_id: str):
        return self.request(Route('POST', f'/users/{user_id}/block'))

    def unblock_user(self, user_id: str):
        return self.request(Route('POST', f'/users/{user_id}/unblock'))

    # /content

    def get_metadata(self, route: str):
        return self.request(Route('GET', '/content/route/metadata'), params={'route': route})

    async def get_channel_message(self, channel_id: str, message_id: str):
        metadata = await self.get_metadata(f'//channels/{channel_id}/chat?messageId={message_id}')
        channel = self.create_channel(data=metadata['metadata']['channel'])
        message = self.create_message(data=metadata['metadata']['message'], channel=channel)
        return message

    def get_channel(self, channel_id: str):
        return self.get_metadata(f'//channels/{channel_id}/chat')

    def get_embed_for_url(self, url: str):
        return self.request(Route('GET', '/content/embed_info'), params={'url': url})

    def get_form_data(self, form_id: int):
        if not isinstance(form, int):
            raise TypeError('form_id must be type int, not %s' % form_id.__class__.__name__)
        return self.request(Route('GET', f'/content/custom_forms/{form_id}'))

    #def submit_form_response(self, form_id: int, *options):
    #    #payload = {'responseSpecs': 'values': {}}
    #    #for option in options:
    #    #    if option.type is None:pass

    #    return self.request(Route('PUT', f'/content/custom_forms/{form_id}/responses'), json=payload)

    # media.guilded.gg

    def upload_file(self, file):
        return self.request(Route('POST', '/media/upload', override_base=Route.MEDIA_BASE),
            data={'file': file._bytes},
            params={'dynamicMediaTypeId': str(file.type)}
        )

    def execute_webhook(self, webhook_id: str, webhook_token: str, data: dict):
        return self.request(Route('POST', f'/webhooks/{webhook_id}/{webhook_token}', override_base=Route.MEDIA_BASE), json=data)

    # one-off

    def check_subdomain(self, subdomain: str):
        return self.request(Route('GET', f'/subdomains/{subdomain}'))

    def search(self, query: str, *, entity_type: str, max_results: int = 20, exclude: list = None):
        params = {
            'query': query,
            'entityType': entity_type,
            'maxResultsPerType': max_results,
            'excludedEntityIds': ','.join(exclude or [])
        }
        return self.request(Route('GET', '/search'), params=params)

    def get_game_list(self):
        return self.request(Route('GET', 'https://raw.githubusercontent.com/GuildedAPI/datatables/main/games.json', override_base=Route.NO_BASE))

    def accept_invite(self, invite_code):
        return self.request(Route('PUT', f'/invites/{invite_code}'), json={'type': 'consume'})

    def read_filelike_data(self, filelike):
        return self.request(Route('GET', filelike.url, override_base=Route.NO_BASE))

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
        data['group'] = data.get('group')
        if channel_data.get('type', '').lower() == 'team':
            ctype = channel.ChannelType.from_str(channel_data.get('contentType', 'chat'))
            if ctype is channel.ChannelType.chat:
                if 'threadMessageId' in channel_data:
                    # we assume here that only threads will have this attribute
                    # so from this we can reasonably know whether a channel is
                    # a thread
                    channel_data['threadMessageId']
                    return channel.Thread(state=self, **data)
                else:
                    return channel.ChatChannel(state=self, **data)
            elif ctype is channel.ChannelType.voice:
                return channel.VoiceChannel(state=self, **data)
        else:
            return channel.DMChannel(state=self, **data)

    def create_message(self, **data):
        data['channel'] = data.get('channel')
        return ChatMessage(state=self, **data)
