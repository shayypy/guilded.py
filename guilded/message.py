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
from .utils import ISO8601

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

class Link:
    """A link within a message. Basically represents a markdown link."""
    def __init__(self, url, *, name=None, title=None):
        self.url = url
        self.name = name
        self.title = title

    def __str__(self):
        return self.url

class Message:
    """A message in Guilded.

    .. container:: operations

        .. describe:: x == y

            Checks if two messages are equal.

        .. describe:: x != y

            Checks if two messages are not equal.

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
        self._state = state
        self._raw = data

        message = data.get('message', data)
        self.id = data.get('contentId') or message.get('id')
        self.webhook_id = data.get('webhookId')
        self.bot_id = data.get('botId')
        self.channel = channel
        self.channel_id = data.get('channelId') or (channel.id if channel else None)
        self.team = extra.get('team') or getattr(channel, 'team', None)
        self.team_id = data.get('teamId')

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
        self.replied_to_ids = message.get('repliesToIds', message.get('repliesTo') or [])
        if data.get('repliedToMessages'):
            for message_data in data['repliedToMessages']:
                message = self._state.create_message(data=message_data)
                self.replied_to.append(message)
        else:
            for message_id in self.replied_to_ids:
                message = self._state._get_message(message_id)
                if not message:
                    continue
                self.replied_to.append(message)

        self.mentions = []
        self.raw_mentions = []
        self.channel_mentions = []
        self.raw_channel_mentions = []
        self.role_mentions = []
        self.raw_role_mentions = []
        self.embeds = []
        self.attachments = []
        self.links = []
        self.content = self._get_full_content(data)

    def __str__(self):
        return self.content

    def __eq__(self, other):
        try:
            return self.id == other.id
        except:
            return False

    def __repr__(self):
        return f'<Message id={repr(self.id)} author={repr(self.author)} channel={repr(self.channel)} team={repr(self.team)}>'

    @property
    def created_by_bot(self):
        return self.author.bot if self.author else (self.webhook_id is not None or self.bot_id is not None)

    @property
    def jump_url(self):
        return f'https://guilded.gg/channels/{self.channel.id}/chat?messageId={self.id}'

    @property
    def embed(self):
        return self.embeds[0] if self.embeds else None

    @property
    def guild(self):
        # basic compatibility w/ discord bot code, plan on deprecating in the future
        return self.team

    def _get_full_content(self, data):
        """Get the content of this message in an easy to use single string.
        Attempts to append mentions, embeds, and attachments to the Message as well.

        .. warning::

            Intended for internal use only.
        """
        try:
            nodes = data.get('message', data)['content']['document']['nodes']
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
                                member = self._state._get_team_member(self.team_id, mentioned['id'])
                                if member:
                                    self.mentions.append(member)
                                else:
                                    name = mentioned.get('name')
                                    if mentioned.get('nickname') is True and mentioned.get('matcher') is not None:
                                        name = name.strip('@').strip(name).strip('@')
                                        if not name.strip():
                                            # matcher might be empty, oops - no username is available
                                            name = None
                                    self.mentions.append(self._state.create_member(data={
                                        'name': name,
                                        'profilePicture': mentioned.get('avatar'),
                                        'colour': parse_hex_number(mentioned.get('color', '000000').strip('#')),
                                        'id': mentioned.get('id'),
                                        'nickname': mentioned.get('name') if mentioned.get('nickname') is True else None
                                    }))
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
                            #self.channel_mentions.append(self._state.create_team_channel(
                            #    group=None,
                            #    team=self.team,
                            #    data={
                            #        'name': channel.get('name'),
                            #        'id': channel.get('id')
                            #}))

            elif node_type == 'markdown-plain-text':
                content += node['nodes'][0]['leaves'][0]['text']

            elif node_type == 'webhookMessage':
                if node['data'].get('embeds'):
                    for msg_embed in node['data']['embeds']:
                        self.embeds.append(Embed.from_dict(msg_embed))

            elif node_type == 'block-quote-container':
                text = str(node['nodes'][0]['nodes'][0]['leaves'][0]['text'])
                content += f'\n> {text}\n'

            elif node_type in ['image', 'video']:
                attachment = Attachment(state=self._state, data=node)
                self.attachments.append(attachment)

        return content

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

        Create a thread on a message.

        .. warning::

            This method currently does not work.
        """
        kwargs['message'] = self
        return await self.channel.create_thread(*content, **kwargs)
