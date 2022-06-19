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

import asyncio
import datetime
from enum import Enum
import logging
from typing import TYPE_CHECKING, Any, Dict, Optional, List, Sequence, Union

from .colour import Colour
from .embed import Embed
from .enums import try_enum, FormType, MessageType, MentionType, MessageFormInputType, MediaType
from .errors import HTTPException
from .file import Attachment
from .utils import ISO8601, MISSING

if TYPE_CHECKING:
    from .types.message import Mention as MentionPayload

    from .abc import Messageable, TeamChannel
    from .emoji import Emoji
    from .file import File
    from .role import Role
    from .team import Team
    from .user import Member, User

log = logging.getLogger(__name__)


class MessageForm:
    def __init__(self, *, state, id):
        self._state = state
        self.id = id

    async def fetch(self):
        data = await self._state.get_form_data(self.id)
        return MessageForm.from_dict(data, state=self._state)

    @classmethod
    def from_dict(cls, data, *, state, responses=None):
        my_response = data.get('customFormResponse') or {}
        cls.my_response = MessageFormResponse(my_response)

        data = data.get('customForm', data)
        if isinstance(responses, dict):
            responses = responses.get('customFormResponses', responses)
        else:
            responses = []

        cls.id = data.get('id')
        cls.title = data.get('title', '')
        cls.description = data.get('description', '')
        cls.type = try_enum(FormType, data.get('type'))
        cls.team_id = data.get('teamId')
        cls.team = state._get_team(cls.team_id)
        cls.author_id = data.get('createdBy')
        cls.author = state._get_team_member(cls.team_id, cls.author_id)
        cls.created_at = ISO8601(data.get('createdAt'))
        cls.updated_at = ISO8601(data.get('updatedAt'))
        cls.response_count = int(data.get('responseCount', 0))
        cls.activity_id = data.get('activityId')

        form_specs = data.get('formSpecs', {})
        cls.valid = form_specs.get('isValid')
        sections = ((form_specs.get('sections') or [{}])[0].get('fieldSpecs') or [{}])
        cls.sections = [MessageFormSection(section) for section in sections]

        cls.public = data.get('isPublic', False)
        cls.deleted = data.get('isDeleted', False)

        return cls

    @property
    def options(self):
        try:
            return self.sections[0].options
        except IndexError:
            return []


class MessageFormSection:
    def __init__(self, data):
        self.grow = data.get('grow')  # not sure what this is
        self.input_type = try_enum(MessageFormInputType, data.get('type'))
        self.label = data.get('label', '')
        self.header = data.get('header', '')
        self.optional = data.get('isOptional')
        self.default_value = data.get('defaultValue')
        self.field_name = data.get('fieldName')

        self.options = [MessageFormOption(option) for option in data.get('options', [])]

    @property
    def name(self):
        return self.label


class MessageFormOption:
    def __init__(self, data):
        pass


class MessageFormResponse:
    def __init__(self, data):
        pass


class MessageMention:
    """A mention within a message. Due to how mentions are sent in message
    payloads, you will usually only have :attr:`.id` unless the object was
    cached prior to this object being constructed.

    Attributes
    -----------
    type: :class:`MentionType`
        The type of object this mention is for.
    id: Union[:class:`str`, :class:`int`]
        The object's ID.
    name: Optional[:class:`str`]
        The object's name, if available.
    """
    def __init__(self, mention_type: MentionType, id, *, name=None):
        self.type = mention_type
        self.id = id
        self.name = name

    def __str__(self):
        return self.name or ''


# This doesn't really need to be how it is and may be changed later.
# This class only exists to store these static values.
class Mention(Enum):
    """Used for passing special types of mentions to :meth:`~.abc.Messageable.send`\."""
    everyone = 'everyone'
    here = 'here'

    def __str__(self):
        return f'@{self.name}'

    def to_node_dict(self) -> Dict[str, Any]:
        if self.value == 'everyone':
            mention_data = {
                'type': 'everyone',
                'matcher': '@everyone',
                'name': 'everyone',
                'description': 'Notify everyone in the channel',
                'color': '#ffffff',
                'id': 'everyone',
            }
        elif self.value == 'here':
            mention_data = {
                'type': 'here',
                'matcher': '@here',
                'name': 'here',
                'description': 'Notify everyone in this channel that is online and not idle',
                'color': '#f5c400',
                'id': 'here',
            }

        return {
            'object': 'inline',
            'type': 'mention',
            'data': {
                'mention': mention_data,
            },
            'nodes': [{
                'object': 'text',
                'leaves': [{
                    'object': 'leaf',
                    'text': str(self),
                    'marks': [],
                }],
            }],
        }


class Link:
    """A link within a message. Basically represents a markdown link."""
    def __init__(self, url, *, name=None, title=None):
        self.url = url
        self.name = name
        self.title = title

    def __str__(self):
        return self.url


class Mentions:
    """Represents mentions in Guilded content. This data is determined and
    sent by Guilded rather than being parsed by the library.

    Attributes
    -----------
    everyone: :class:`bool`
        Whether ``@everyone`` was mentioned.
    here: :class:`bool`
        Whether ``@here`` was mentioned.
    """
    def __init__(self, *, state, team: Team, data: MentionPayload):
        self._state = state
        self._team = team
        self._users = data.get('users') or []
        self._channels = data.get('channels') or []
        self._roles = data.get('roles') or []

        self.everyone = data.get('everyone', False)
        self.here = data.get('here', False)

    def __repr__(self) -> str:
        return f'<Mentions users={len(self._users)} channels={len(self._channels)} roles={len(self._roles)} everyone={self.everyone} here={self.here}>'

    @property
    def users(self) -> List[Union[Member, User]]:
        """List[Union[:class:`.Member`, :class:`~guilded.User`]]: The list of members who were mentioned."""
        users = []
        for user_data in self._users:
            user = self._state._get_user(user_data['id'])
            if self._team:
                user = self._state._get_team_member(self._team.id, user_data['id']) or user
            if user:
                users.append(user)

        return users

    @property
    def channels(self) -> List[TeamChannel]:
        """List[:class:`~.abc.TeamChannel`]: The list of channels that were mentioned.

        An empty list is always returned in a DM context.
        """
        if not self._team:
            return []

        channels = []
        for channel_data in self._channels:
            channel = self._state._get_team_channel_or_thread(self._team.id, channel_data['id'])
            if channel:
                channels.append(channel)

        return channels

    @property
    def roles(self) -> List[Role]:
        """List[:class:`.Role`]: The list of roles that were mentioned.

        An empty list is always returned in a DM context.
        """
        if not self._team:
            return []

        roles = []
        for role_data in self._roles:
            role = self._team.get_role(role_data['id'])
            if role:
                roles.append(role)

        return roles

    async def fill(
        self,
        *,
        ignore_cache: bool = False,
        ignore_errors: bool = False,
    ) -> None:
        """|coro|

        Fetch & fill the internal cache with the targets referenced.

        .. note::

            Due to Guilded limitations, this will not fill role information.

        Parameters
        -----------
        ignore_cache: :class:`bool`
            Whether to fetch objects regardless of if they are already cached.
            Defaults to ``False`` if not specified.
        ignore_errors: :class:`bool`
            Whether to ignore :exc:`HTTPException`\s that occur while fetching.
            Defaults to ``False`` if not specified.
        """
        # Bots cannot fetch any role information so they are not handled here.

        # Potential bug here involving old messages that mention former members
        # or deleted accounts - I am unsure whether Guilded includes these
        # cases in their `mentions` property.

        # Just fetch the whole member list instead of fetching >=5 members individually.
        uncached_user_count = len(self._users) - len(self.users)
        if (
            self._team and (
                uncached_user_count >= 5
                or (len(self._users) >= 5 and ignore_cache)
            )
        ):
            # `fill_members` here would cause potentially unwanted/unexpected
            # cache usage, especially in large servers.
            members = await self._team.fetch_members()
            user_ids = [user['id'] for user in self._users]
            for member in members:
                if member.id in user_ids:
                    self._state.add_to_member_cache(member)

        else:
            for user_data in self._users:
                cached_user = self._state._get_user(user_data['id'])
                if self._team:
                    cached_user = self._state._get_team_member(self._team.id, user_data['id']) or cached_user

                if ignore_cache or not cached_user:
                    if self._team:
                        try:
                            user = await self._team.fetch_member(user_data['id'])
                        except HTTPException:
                            if not ignore_errors:
                                raise
                        else:
                            self._state.add_to_member_cache(user)
                    else:
                        try:
                            user = await self._state.get_user(user_data['id'])
                        except HTTPException:
                            if not ignore_errors:
                                raise
                        else:
                            self._state.add_to_user_cache(user)

        for channel_data in self._channels:
            if not self._team:
                # This should never happen
                break

            cached_channel = self._state._get_team_channel_or_thread(self._team.id, channel_data['id'])
            if ignore_cache or not cached_channel:
                try:
                    channel = await self._team.fetch_channel(channel_data['id'])
                except HTTPException:
                    if not ignore_errors:
                        raise
                else:
                    self._state.add_to_team_channel_cache(channel)


class HasContentMixin:
    def __init__(self):
        self.emojis: list = []
        self.raw_mentions: list = []
        self.raw_channel_mentions: list = []
        self.raw_role_mentions: list = []
        self._user_mentions: list = []
        self._channel_mentions: list = []
        self._role_mentions: list = []
        self._mentions_everyone: bool = False
        self._mentions_here: bool = False
        self.embeds: list = []
        self.attachments: list = []
        self.links: list = []

    @property
    def user_mentions(self) -> List[Union[Member, User]]:
        """List[Union[:class:`.Member`, :class:`~guilded.User`]]: The list of users who are mentioned in the content."""
        if hasattr(self, '_mentions'):
            return self._mentions.users
        return self._user_mentions

    @property
    def mentions(self) -> List[Union[Member, User]]:
        """List[Union[:class:`.Member`, :class:`~guilded.User`]]: |dpyattr|

        The list of users who are mentioned in the content.
        """
        return self.user_mentions

    @property
    def channel_mentions(self) -> List[TeamChannel]:
        """List[:class:`~.abc.TeamChannel`]: The list of channels that are mentioned in the content."""
        if hasattr(self, '_mentions'):
            return self._mentions.channels
        return self._channel_mentions

    @property
    def role_mentions(self) -> List[Role]:
        """List[:class:`.Role`]: The list of roles that are mentioned in the content."""
        if hasattr(self, '_mentions'):
            return self._mentions.roles
        return self._role_mentions

    @property
    def mention_everyone(self) -> bool:
        """:class:`bool`: Whether the content mentions ``@everyone``\."""
        if hasattr(self, '_mentions'):
            return self._mentions.everyone
        return self._mentions_everyone

    @property
    def mention_here(self) -> bool:
        """:class:`bool`: Whether the content mentions ``@here``\."""
        if hasattr(self, '_mentions'):
            return self._mentions.here
        return self._mentions_here

    def _get_full_content(self, data) -> str:
        try:
            nodes = data['document']['nodes']
        except KeyError:
            # empty message
            return ''

        content = ''
        for node in nodes:
            node_type = node['type']
            if node_type == 'paragraph':
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
                                    elif mark['type'] == 'italic':
                                        to_mark = '*' + to_mark + '*'
                                    elif mark['type'] == 'underline':
                                        to_mark = '__' + to_mark + '__'
                                    elif mark['type'] == 'strikethrough':
                                        to_mark = '~~' + to_mark + '~~'
                                    elif mark['type'] == 'spoiler':
                                        to_mark = '||' + to_mark + '||'
                                    else:
                                        pass
                                content += to_mark.format(
                                    unmarked_content=str(leaf['text'])
                                )
                    if element['object'] == 'inline':
                        if element['type'] == 'mention':
                            mentioned = element['data']['mention']
                            if mentioned['type'] == 'role':
                                self.raw_role_mentions.append(int(mentioned['id']))
                                content += f'<@{mentioned["id"]}>'
                            elif mentioned['type'] == 'person':
                                content += f'<@{mentioned["id"]}>'

                                self.raw_mentions.append(mentioned['id'])
                                if self.team_id:
                                    user = self._state._get_team_member(self.team_id, mentioned['id'])
                                else:
                                    user = self._state._get_user(mentioned['id'])

                                if user:
                                    self._user_mentions.append(user)
                                else:
                                    name = mentioned.get('name')
                                    if mentioned.get('nickname') is True and mentioned.get('matcher') is not None:
                                        name = name.strip('@').strip(name).strip('@')
                                        if not name.strip():
                                            # matcher might be empty, oops - no username is available
                                            name = None
                                    if self.team_id:
                                        self._user_mentions.append(self._state.create_member(
                                            team=self.team,
                                            data={
                                                'id': mentioned.get('id'),
                                                'name': name,
                                                'profilePicture': mentioned.get('avatar'),
                                                'colour': Colour.from_str(mentioned.get('color', '#000')),
                                                'nickname': mentioned.get('name') if mentioned.get('nickname') is True else None,
                                                'type': 'bot' if self.created_by_bot else 'user',
                                            }
                                        ))
                                    else:
                                        self._user_mentions.append(self._state.create_user(data={
                                            'id': mentioned.get('id'),
                                            'name': name,
                                            'profilePicture': mentioned.get('avatar'),
                                            'type': 'bot' if self.created_by_bot else 'user',
                                        }))
                            elif mentioned['type'] in ('everyone', 'here'):
                                # grab the actual display content of the node instead of using a static string
                                try:
                                    content += element['nodes'][0]['leaves'][0]['text']
                                except KeyError:
                                    # give up trying to be fancy and use a static string
                                    content += f'@{mentioned["type"]}'

                                if mentioned['type'] == 'everyone':
                                    self._mentions_everyone = True
                                elif mentioned['type'] == 'here':
                                    self._mentions_here = True

                        elif element['type'] == 'reaction':
                            rtext = element['nodes'][0]['leaves'][0]['text']
                            content += str(rtext)
                        elif element['type'] == 'link':
                            link_text = element['nodes'][0]['leaves'][0]['text']
                            link_href = element['data']['href']
                            link = Link(link_href, name=link_text)
                            self.links.append(link)
                            if link.url != link.name:
                                content += f'[{link.name}]({link.url})'
                            else:
                                content += link.url
                        elif element['type'] == 'channel':
                            channel = element['data']['channel']
                            if channel.get('id'):
                                self.raw_channel_mentions.append(channel["id"])
                                content += f'<#{channel["id"]}>'
                                channel = self._state._get_team_channel(self.team_id, channel['id'])
                                if channel:
                                    self._channel_mentions.append(channel)

                content += '\n'

            elif node_type == 'markdown-plain-text':
                try:
                    content += node['nodes'][0]['leaves'][0]['text']
                except KeyError:
                    # probably an "inline" non-text node - their leaves are another node deeper
                    content += node['nodes'][0]['nodes'][0]['leaves'][0]['text']

                    if 'reaction' in node['nodes'][0].get('data', {}):
                        emoji_id = node['nodes'][0]['data']['reaction']['id']
                        emoji = self._state._get_emoji(emoji_id)
                        if emoji:
                            self.emojis.append(emoji)

            elif node_type == 'webhookMessage':
                if node['data'].get('embeds'):
                    for msg_embed in node['data']['embeds']:
                        self.embeds.append(Embed.from_dict(msg_embed))

            elif node_type == 'block-quote-container':
                quote_content = []
                for quote_node in node['nodes'][0]['nodes']:
                    if quote_node.get('leaves'):
                        text = str(quote_node['leaves'][0]['text'])
                        quote_content.append(text)

                if quote_content:
                    content += '\n> {}\n'.format('\n> '.join(quote_content))

            elif node_type in ['image', 'video']:
                attachment = Attachment(state=self._state, data=node)
                self.attachments.append(attachment)

        content = content.rstrip('\n')
        # strip ending of newlines in case a paragraph node ended without
        # another paragraph node
        return content

    def _create_mentions(self, data: Optional[Dict[str, Any]]) -> Mentions:
        # Bot accounts only
        # This will always be called after setting _state and _team/team_id so this should be safe
        mentions = Mentions(state=self._state, team=self.team, data=data or {})
        return mentions


class ChatMessage(HasContentMixin):
    """A message in Guilded.

    There is an alias for this class called ``Message``.

    .. container:: operations

        .. describe:: x == y

            Checks if two messages are equal.

        .. describe:: x != y

            Checks if two messages are not equal.

    Attributes
    -----------
    id: :class:`str`
        The message's ID.
    channel: Union[:class:`abc.TeamChannel`, :class:`DMChannel`]
        The channel this message was sent in.
    webhook_id: Optional[:class:`str`]
        The webhook's ID that sent the message, if applicable.
    """

    __slots__ = (
        '_state',
        '_raw',
        'channel',
        '_team',
        'team_id',
        '_author',
        '_webhook',
        'id',
        'type',
        'webhook_id',
        'channel_id',
        'author_id',
        'created_at',
        'edited_at',
        'deleted_at',
        '_replied_to',
        'replied_to_ids',
        'silent',
        'private',
        'content',
    )

    def __init__(self, *, state, channel, data, **extra):
        super().__init__()
        self._state = state
        self._raw = data
        self.channel: Messageable = channel
        message = data.get('message', data)

        self._team = extra.get('team') or extra.get('server')
        self.team_id: Optional[str] = data.get('teamId') or data.get('serverId')

        self._author = extra.get('author')
        self._webhook = extra.get('webhook')

        if state.userbot:
            self.id: str = data.get('contentId') or message.get('id')
            self.type: MessageType = try_enum(MessageType, message.get('type'))
            self.webhook_id: Optional[str] = data.get('webhookId')
            self.channel_id: str = data.get('channelId') or (channel.id if channel else None)
            self.author_id: str = data.get('createdBy') or message.get('createdBy')

            self.created_at: datetime.datetime = ISO8601(data.get('createdAt'))
            self.edited_at: Optional[datetime.datetime] = ISO8601(message.get('editedAt'))
            self.deleted_at: Optional[datetime.datetime] = extra.get('deleted_at') or ISO8601(data.get('deletedAt'))

            self._replied_to = []
            self.replied_to_ids: List[str] = message.get('repliesToIds') or message.get('repliesTo') or []
            self.silent: bool = message.get('isSilent', False)
            self.private: bool = message.get('isPrivate', False)
            if data.get('repliedToMessages'):
                for message_data in data['repliedToMessages']:
                    message_ = self._state.create_message(data=message_data)
                    self._replied_to.append(message_)
            else:
                for message_id in self.replied_to_ids:
                    message_ = self._state._get_message(message_id)
                    if not message_:
                        continue
                    self._replied_to.append(message_)

            self.content: str = self._get_full_content(message['content'])

        else:
            self.id: str = message['id']
            self.type: MessageType = try_enum(MessageType, message['type'])
            self.channel_id: str = message['channelId']
            self.embeds: List[Embed] = [Embed.from_dict(embed) for embed in (message.get('embeds') or [])]

            self.author_id: str = message.get('createdBy')
            self.webhook_id: Optional[str] = message.get('createdByWebhookId')

            self.created_at: datetime.datetime = ISO8601(message.get('createdAt'))
            self.edited_at: Optional[datetime.datetime] = ISO8601(message.get('updatedAt'))
            self.deleted_at: Optional[datetime.datetime] = None

            self._replied_to = []
            self.replied_to_ids: List[str] = message.get('replyMessageIds') or []
            self.private: bool = message.get('isPrivate') or False
            self.silent: bool = message.get('isSilent') or False
            self._mentions = self._create_mentions(message.get('mentions'))

            self.content: str
            if isinstance(message['content'], dict):
                # Webhook execution responses
                self.content = self._get_full_content(message['content'])
            else:
                self.content = message['content']

    def __eq__(self, other) -> bool:
        return isinstance(other, ChatMessage) and self.id == other.id

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} id={self.id!r} author={self.author!r} channel={self.channel!r}>'

    @property
    def team(self):
        """Optional[:class:`.Team`]: The team this message was sent in. ``None`` if the message is in a DM."""
        return self._team or self._state._get_team(self.team_id)

    @property
    def server(self):
        """Optional[:class:`.Team`]: This is an alias of :attr:`.team`.

        The team this message was sent in. ``None`` if the message is in a DM.
        """
        return self.team

    @property
    def guild(self):
        """Optional[:class:`.Team`]: |dpyattr|

        This is an alias of :attr:`.team`.

        The team this message was sent in. ``None`` if the message is in a DM.
        """
        return self.team

    @property
    def author(self):
        """Optional[:class:`~.abc.User`]: The user that created this message, if they are cached."""
        if self._author:
            return self._author

        user = None
        if self.team:
            user = self.team.get_member(self.author_id)

        if not user:
            user = self._state._get_user(self.author_id)

        if self.webhook_id or self._webhook:
            data = {
                'id': self.author_id,
                'type': 'bot',
            }
            if self._webhook:
                data['name'] = self._webhook.name
                data['profilePicture'] = self._webhook.avatar.url if self._webhook.avatar else None

            user = self._state.create_user(data=data)

        return user

    @property
    def created_by_bot(self) -> bool:
        return self.author.bot if self.author else self.webhook_id is not None

    @property
    def share_url(self) -> str:
        if self.channel:
            return f'{self.channel.share_url}?messageId={self.id}'
        return None

    @property
    def jump_url(self) -> str:
        return self.share_url

    @property
    def embed(self):
        return self.embeds[0] if self.embeds else None

    @property
    def replied_to(self):
        return self._replied_to or [self._state._get_message(message_id) for message_id in self.replied_to_ids]

    async def delete(self, *, delay: Optional[float] = None) -> None:
        """|coro|

        Delete this message.

        Parameters
        -----------
        delay: Optional[:class:`float`]
            If provided, the number of seconds to wait in the background before
            deleting this message. If the deletion fails, then it is silently ignored.

        Raises
        -------
        Forbidden
            You do not have proper permissions to delete this message.
        NotFound
            This message has already been deleted.
        HTTPException
            Deleting this message failed.
        """

        if self._state.userbot:
            coro = self._state.delete_message(self.channel_id, self.id)
        else:
            coro = self._state.delete_channel_message(self.channel_id, self.id)

        if delay is not None:

            async def delete(delay: float):
                await asyncio.sleep(delay)
                try:
                    await coro
                except HTTPException:
                    pass
                else:
                    self.deleted_at = datetime.datetime.utcnow()

            asyncio.create_task(delete(delay))

        else:
            await coro
            self.deleted_at = datetime.datetime.utcnow()

    async def edit(
        self,
        *pos_content: Optional[Union[str, Embed, File, Emoji]],
        content: Optional[str] = MISSING,
        file: Optional[File] = MISSING,
        files: Optional[Sequence[File]] = MISSING,
        embed: Optional[Embed] = MISSING,
        embeds: Optional[Sequence[Embed]] = MISSING,
    ) -> ChatMessage:
        """|coro|

        Edit a message.

        .. note::

            For user accounts, Guilded supports content elements in any order,
            which is not practically possible with keyword arguments.
            For this reason, it is recommended that you pass arguments positionally in these environments.
            However, if the client is a bot account, you **must** use keyword arguments for non-text content.

        .. warning::

            Unlike perhaps-expected ``PATCH`` behavior, this method overwrites
            all content previously in the message using the new payload.

        Parameters
        -----------
        \*pos_content: Union[:class:`str`, :class:`.Embed`, :class:`.File`, :class:`.Emoji`, :class:`.Member`]
            An argument list of the message content, passed in the order that
            each element should display in the message.
            You can have at most 4,000 characters of text content.
            If the client is a bot account, only the first value is used as content.
            This parameter cannot be combined with ``content``.
        content: :class:`str`
            The text content to send with the message.
            This parameter exists so that text content can be passed using a keyword argument.
            This parameter cannot be combined with ``pos_content``.
        embed: :class:`.Embed`
            An embed to send with the message.
            This parameter cannot be meaningfully combined with ``embeds``.
        embeds: List[:class:`.Embed`]
            A list of embeds to send with the message.
            If the client is a bot account, this can contain at most 1 value.
            Otherwise, this has no hard limit.
            This parameter cannot be meaningfully combined with ``embed``.

        Returns
        --------
        :class:`.ChatMessage`
            The edited message.

        Raises
        -------
        NotFound
            The message does not exist.
        Forbidden
            The message is not owned by you or it is in a channel you cannot access.
        HTTPException
            Could not edit the message.
        ValueError
            Cannot provide both ``content`` and ``pos_content``\.
        """

        if content is not MISSING and pos_content:
            raise ValueError('Cannot provide both content and pos_content')

        if self._state.userbot:
            if content is not MISSING:
                pos_content = (content,)

            content = await self._state.process_list_content(
                pos_content,
                embed=embed,
                embeds=embeds,
                file=file,
                files=files,
            )
            content = self._state.compatible_content(content)

            message_data = await self._state.edit_message(
                self.channel_id,
                self.id,
                content=content,
            )
            message_data = message_data.get('message', message_data)
            message_data['channelId'] = self.channel_id
            message_data['teamId'] = self.team_id
            message = self._state.create_message(data=message_data, channel=self.channel)

        else:
            from .http import handle_message_parameters

            if pos_content:
                content = pos_content[0]

            params = handle_message_parameters(
                content=content,
                file=file,
                files=files,
                embed=embed,
                embeds=embeds,
            )

            data = await self._state.update_channel_message(
                self.channel_id,
                self.id,
                payload=params.payload,
            )
            message = self._state.create_message(
                data=data['message'],
                channel=self.channel,
            )

        return message

    async def add_reaction(self, emoji: Emoji) -> None:
        """|coro|

        Add a reaction to this message.

        Parameters
        -----------
        :class:`.Emoji`
            The emoji to react with.
        """
        if self._state.userbot:
            await self._state.add_message_reaction(self.channel_id, self.id, emoji.id)
        elif hasattr(emoji, 'id'):
            await self._state.add_reaction_emote(self.channel_id, self.id, emoji.id)
        else:
            await self._state.add_reaction_emote(self.channel_id, self.id, emoji)

    async def remove_self_reaction(self, emoji: Emoji) -> None:
        """|coro|

        Remove one of your reactions from this message.

        Parameters
        -----------
        :class:`.Emoji`
            The emoji to remove.
        """
        if self._state.userbot:
            await self._state.remove_self_message_reaction(self.channel_id, self.id, emoji.id)
        else:
            emoji_id: int = getattr(emoji, 'id', emoji)
            await self._state.remove_reaction_emote(self.channel.id, self.id, emoji_id)

    async def reply(
        self,
        *pos_content: Optional[Union[str, Embed, File, Emoji]],
        content: Optional[str] = MISSING,
        file: Optional[File] = MISSING,
        files: Optional[Sequence[File]] = MISSING,
        embed: Optional[Embed] = MISSING,
        embeds: Optional[Sequence[Embed]] = MISSING,
        reference: Optional[ChatMessage] = MISSING,
        reply_to: Optional[Sequence[ChatMessage]] = MISSING,
        mention_author: Optional[bool] = None,
        silent: Optional[bool] = None,
        private: bool = False,
        share: Optional[ChatMessage] = MISSING,
        delete_after: Optional[float] = None,
    ) -> ChatMessage:
        """|coro|

        Reply to this message.
        This is identical to :meth:`abc.Messageable.send`, but the
        ``reply_to`` parameter already includes this message.
        """

        reply_to = reply_to if reply_to is not MISSING else []
        if self not in reply_to:
            # We don't have a say in where the message appears in the reply
            # list unfortunately; it is sorted chronologically.
            reply_to.append(self)

        return await self.channel.send(
            *pos_content,
            content=content,
            file=file,
            files=files,
            embed=embed,
            embeds=embeds,
            reference=reference,
            reply_to=reply_to,
            mention_author=mention_author,
            silent=silent,
            private=private,
            share=share,
            delete_after=delete_after,
        )

    async def create_thread(self, *content, **kwargs):
        """|coro|

        |onlyuserbot|

        Create a thread on this message.

        .. warning::

            This method currently does not work.
        """
        kwargs['message'] = self
        return await self.channel.create_thread(*content, **kwargs)

    async def pin(self):
        """|coro|

        |onlyuserbot|

        Pin this message.
        """
        await self._state.pin_message(self.channel.id, self.id)

    async def unpin(self):
        """|coro|

        |onlyuserbot|

        Unpin this message.
        """
        await self._state.unpin_message(self.channel.id, self.id)

    async def ack(self, clear_all_badges: bool = False) -> None:
        """|coro|

        |dpyattr|

        |onlyuserbot|

        Mark this message's channel as seen; acknowledge all unread messages
        within it.

        There is no endpoint for acknowledging just one message and as such
        this method is identical to :meth:`~.abc.Messageable.seen`.
        """
        return await self.channel.seen(clear_all_badges=clear_all_badges)

Message = ChatMessage
