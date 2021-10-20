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

import datetime
from enum import Enum
import logging
from typing import Optional

from .embed import Embed
from .file import MediaType, Attachment
from .utils import ISO8601, parse_hex_number

log = logging.getLogger(__name__)

class FormType(Enum):
    poll = 'poll'
    form = 'form'

    @classmethod
    def from_str(cls, string):
        return getattr(cls, string, cls.form)

class MessageNode:
    def __init__(self, *, state, data):
        self._state = state

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
        cls.type = FormType.from_str(data.get('type'))
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

class MessageFormInputType(Enum):
    radios = 'Radios'
    checkboxes = 'Checkboxes'

    @classmethod
    def from_str(cls, string):
        return getattr(cls, string)

class MessageFormSection:
    def __init__(self, data):
        self.grow = data.get('grow')  # not sure what this is
        self.input_type = MessageFormInputType.from_str(data.get('type'))
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

class MentionType(Enum):
    user = 'user'
    channel = 'channel'
    role = 'role'

    def __str__(self):
        return self.name

class MessageMention:
    """A mention within a message. Due to how mentions are sent in message
    payloads, you will usually only have :attr:`.id` unless the object was
    cached previous to this object being constructed.

    Attributes
    ------------
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

class Mention(Enum):
    """Used for passing special types of mentions to
    :meth:`~.abc.Messageable.send`\.
    """
    everyone = {'type': 'everyone', 'matcher': '@everyone', 'name': 'everyone', 'description': 'Notify everyone in the channel', 'color': '#ffffff', 'id': 'everyone'}
    here = {'type': 'here', 'matcher': '@here', 'name': 'here', 'description': 'Notify everyone in this channel that is online and not idle', 'color': '#f5c400', 'id': 'here'}

    def __str__(self):
        return f'@{self.name}'

class Link:
    """A link within a message. Basically represents a markdown link."""
    def __init__(self, url, *, name=None, title=None):
        self.url = url
        self.name = name
        self.title = title

    def __str__(self):
        return self.url

class HasContentMixin:
    def __init__(self):
        self.mentions: list = []
        self.emojis: list = []
        self.raw_mentions: list = []
        self.channel_mentions: list = []
        self.raw_channel_mentions: list = []
        self.role_mentions: list = []
        self.raw_role_mentions: list = []
        self.embeds: list = []
        self.attachments: list = []
        self.links: list = []

    def _get_full_content(self, data):
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
                                content += f'<@{mentioned["id"]}>'
                            elif mentioned['type'] == 'person':
                                content += f'<@{mentioned["id"]}>'

                                self.raw_mentions.append(f'<@{mentioned["id"]}>')
                                if self.team_id:
                                    user = self._state._get_team_member(self.team_id, mentioned['id'])
                                else:
                                    user = self._state._get_user(mentioned['id'])

                                if user:
                                    self.mentions.append(user)
                                else:
                                    name = mentioned.get('name')
                                    if mentioned.get('nickname') is True and mentioned.get('matcher') is not None:
                                        name = name.strip('@').strip(name).strip('@')
                                        if not name.strip():
                                            # matcher might be empty, oops - no username is available
                                            name = None
                                    if self.team_id:
                                        self.mentions.append(self._state.create_member(
                                            team=self.team,
                                            data={
                                                'id': mentioned.get('id'),
                                                'name': name,
                                                'profilePicture': mentioned.get('avatar'),
                                                'colour': parse_hex_number(mentioned.get('color', '000000').strip('#')),
                                                'nickname': mentioned.get('name') if mentioned.get('nickname') is True else None,
                                                'bot': self.created_by_bot
                                            }
                                        ))
                                    else:
                                        self.mentions.append(self._state.create_user(data={
                                            'id': mentioned.get('id'),
                                            'name': name,
                                            'profilePicture': mentioned.get('avatar'),
                                            'bot': self.created_by_bot
                                        }))
                            elif mentioned['type'] in ('everyone', 'here'):
                                # grab the actual display content of the node instead of using a static string
                                try:
                                    content += element['nodes'][0]['leaves'][0]['text']
                                except KeyError:
                                    # give up trying to be fancy and use a static string
                                    content += f'@{mentioned["type"]}'

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
                            content += f'<#{channel.get("id")}>'

                            channel = self._state._get_team_channel(self.team_id, channel.get('id'))
                            if channel:
                                self.channel_mentions.append(channel)

                content += '\n'

            elif node_type == 'markdown-plain-text':
                try:
                    content += node['nodes'][0]['leaves'][0]['text']
                except KeyError:
                    # probably an "inline" non-text node - their leaves are another node deeper
                    content += node['nodes'][0]['nodes'][0]['leaves'][0]['text']

                    if 'reaction' in node['nodes'][0].get('data', {}):
                        emoji_id = node['nodes'][0]['data']['reaction']['id']
                        emoji = (
                            self._state._get_emoji(emoji_id) or
                            Emoji(
                                data={'id': emoji_id, 'name': node['nodes'][0]['nodes'][0]['leaves'][0]['text']},
                                state=self._state
                                # we do not pass team here because we have no
                                # way of knowing if the emoji is from the
                                # current team
                            )
                        )
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

class ChatMessage(HasContentMixin):
    """A message in Guilded.

    There is an alias for this class called ``Message``.

    .. container:: operations

        .. describe:: x == y

            Checks if two messages are equal.

        .. describe:: x != y

            Checks if two messages are not equal.

        .. describe:: str(x)

            Returns the string content of the message.

    Attributes
    ------------
    id: :class:`str`
        The message's ID.
    channel: Union[:class:`abc.TeamChannel`, :class:`DMChannel`]
        The channel this message was sent in.
    team: Optional[:class:`Team`]
        The team this message was sent in. ``None`` if the message is in a DM.
    webhook_id: Optional[:class:`str`]
        The webhook's ID that sent the message, if applicable.
    bot_id: Optional[:class:`str`]
        The bot's ID that sent the message, if applicable.
    """
    def __init__(self, *, state, channel, data, **extra):
        super().__init__()
        self._state = state
        self._raw = data

        message = data.get('message', data)
        self.id = data.get('contentId') or message.get('id')
        self.webhook_id = data.get('webhookId')
        self.bot_id = data.get('botId')
        self.channel = channel
        self.channel_id = data.get('channelId') or (channel.id if channel else None)
        self.team_id = data.get('teamId')
        self.team = extra.get('team') or getattr(channel, 'team', None) or self._state._get_team(self.team_id)

        self.created_at = ISO8601(data.get('createdAt'))
        self.edited_at = ISO8601(message.get('editedAt'))
        self.deleted_at = extra.get('deleted_at') or ISO8601(data.get('deletedAt'))

        self.author = extra.get('author')
        self.author_id = data.get('createdBy') or message.get('createdBy')
        if self.author is None:
            if data.get('channelType', '').lower() == 'team' and self.team is not None:
                self.author = self._state._get_team_member(self.team_id, self.author_id)
            elif data.get('channelType', '').lower() == 'dm' or self.team is None:
                self.author = self._state._get_user(self.author_id)
            elif data.get('createdByInfo'):
                self.author = self._state.create_user(data=data['createdByInfo'])

        if self.author is not None:
            self.author.bot = self.created_by_bot

        self.replied_to = []
        self.replied_to_ids = message.get('repliesToIds') or message.get('repliesTo') or []
        self.silent = message.get('isSilent', False)
        self.private = message.get('isPrivate', False)
        if data.get('repliedToMessages'):
            for message_data in data['repliedToMessages']:
                message_ = self._state.create_message(data=message_data)
                self.replied_to.append(message_)
        else:
            for message_id in self.replied_to_ids:
                message_ = self._state._get_message(message_id)
                if not message_:
                    continue
                self.replied_to.append(message_)

        self.content: str = self._get_full_content(message['content'])

    def __str__(self):
        return self.content

    def __eq__(self, other):
        return isinstance(other, ChatMessage) and self.id == other.id

    def __repr__(self):
        return f'<Message id={self.id!r} author={self.author!r} channel={self.channel!r}>'

    @property
    def created_by_bot(self) -> bool:
        return self.author.bot if self.author else (self.webhook_id is not None or self.bot_id is not None)

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
    def guild(self):
        # basic compatibility w/ discord bot code, plan on deprecating in the future
        return self.team

    async def delete(self):
        """|coro|

        Delete this message.
        """
        response = await self._state.delete_message(self.channel_id, self.id)
        self.deleted_at = datetime.datetime.utcnow()

    async def edit(self, *, content: str = None, embed = None, embeds: Optional[list] = None, file = None, files: Optional[list] = None):
        """|coro|

        Edit this message.
        """
        payload = {
            'old_content': self.content,
            'old_embeds': [embed.to_dict() for embed in self.embeds],
            'old_files': [await attachment.to_file() for attachment in self.attachments]
        }
        if content:
            payload['content'] = content
        if embed:
            embeds = [embed, *(embeds or [])]
        if embeds is not None:
            payload['embeds'] = [embed.to_dict() for embed in embeds]
        if file:
            files = [file, *(files or [])]
        if files is not None:
            pl_files = []
            for file in files:
                file.type = MediaType.attachment
                if file.url is None:
                    await file._upload(self._state)
                pl_files.append(file)

            payload['files'] = pl_files

        await self._state.edit_message(self.channel_id, self.id, **payload)

    async def add_reaction(self, emoji):
        """|coro|

        Add a reaction to this message. In the future, will take type Emoji,
        but currently takes an integer (the emoji's id).
        """
        return await self._state.add_message_reaction(self.channel_id, self.id, emoji)

    async def remove_self_reaction(self, emoji):
        """|coro|

        Remove your reaction to this message. In the future, will take type
        Emoji, but currently takes an integer (the emoji's id).
        """
        return await self._state.remove_self_message_reaction(self.channel_id, self.id, emoji)

    async def reply(self, *content, **kwargs):
        """|coro|

        Reply to a message. Functions the same as
        :meth:`abc.Messageable.send`, but with the ``reply_to`` parameter
        already set.
        """
        kwargs['reply_to'] = [self]
        return await self.channel.send(*content, **kwargs)

    async def create_thread(self, *content, **kwargs):
        """|coro|

        Create a thread on this message.

        .. bug::

            This method currently does not work.
        """
        kwargs['message'] = self
        return await self.channel.create_thread(*content, **kwargs)

    async def pin(self):
        """|coro|

        Pin this message.
        """
        await self._state.pin_message(self.channel.id, self.id)

    async def unpin(self):
        """|coro|

        Unpin this message.
        """
        await self._state.unpin_message(self.channel.id, self.id)

Message = ChatMessage
