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

class MessageLeaf:
    def __init__(self, data):
        self._raw = data.get('data', data)

class MessagePoll(MessageLeaf):
    def __init__(self, data):
        super().__init__(data)

        self.id = self._raw.get('customFormId')

class MessagePollOption:
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

        if self.author is not None:
            self.author.bot = self.created_by_bot

        self.mentions = []
        self.raw_mentions = []
        self.channel_mentions = []
        self.raw_channel_mentions = []
        self.role_mentions = []
        self.raw_role_mentions = []
        self.embeds = []
        self.attachments = []
        self.content = self._get_full_content()

    def __str__(self):
        return self.content

    def __eq__(self, other):
        try:
            return self.id == other.id
        except:
            return False

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

    def _get_full_content(self):
        """Get the content of this message in an easy to use single string.
        Attempts to append mentions, embeds, and attachments to the Message as well.
        
        .. warning::

            Intended for internal use only.
        """
        # if-elsing till the day i die
        # (or until this lib can update to 3.10)
        # (or until i decide to rewrite this to have a handler for each node type)
        try:
            nodes = self._raw.get('message', self._raw)['content']['document']['nodes']
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
                                content += f'<@&{mentioned["id"]}>'
                            elif mentioned['type'] == 'person':
                                content += f'<@{mentioned["id"]}>'
                                #name = mentioned.get('name')
                                #if mentioned.get('nickname') is True and mentioned.get('matcher') is not None:
                                #    name = name.strip('@').strip(name).strip('@')
                                #    if not name.strip():
                                #        # matcher might be empty, oops - no username is available
                                #        name = None

                                self.raw_mentions.append(f'<@{mentioned["id"]}>')
                                member = self._state._get_team_member(self.team_id, mentioned['id'])
                                if member:
                                    self.mentions.append(member)
                                #self.mentions.append(Member(state=self._state, data={
                                #    'name': name,
                                #    'profilePicture': mentioned.get('avatar'),
                                #    'colour': parse_hex_number(mentioned.get('color', '000000').strip('#')),
                                #    'id': mentioned.get('id'),
                                #    'nickname': mentioned.get('name') if mentioned.get('nickname') is True else None
                                #}))
                        elif element['type'] == 'reaction':
                            rtext = element['nodes'][0]['leaves'][0]['text']
                            content += str(rtext)
                        elif element['type'] == 'link':
                            l1 = element['nodes'][0]['leaves'][0]['text']
                            l2 = element['data']['href']
                            content += f'[{l1}]({l2})'
                        elif element['type'] == 'channel':
                            channel = element['data']['channel']
                            content += f'<#{channel.get("id")}>'
                            #self.channel_mentions.append(TeamChannel(state=self._state, group=None, team=self.team, data={
                            #    'name': channel.get('name'),
                            #    'id': channel.get('id')
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
        response = await self._state.delete_message(self.channel_id, self.id)
        self.deleted_at = datetime.datetime.utcnow()

    async def edit(self, *, content: str = None, embed = None, embeds: Optional[list] = None, file = None, files: Optional[list] = None):
        """Edit a message."""
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
        """Add a reaction to a message. In the future, will take type Emoji, but currently takes an integer (the emoji's id)"""
        await self._state.add_message_reaction(self.channel_id, self.id, emoji)

    async def remove_self_reaction(self, emoji):
        """Remove your reaction to a message. In the future, will take type Emoji, but currently takes an integer (the emoji's id)"""
        await self._state.remove_self_message_reaction(self.channel_id, self.id, emoji)

    #async def reply(self, *content, **kwargs):
    #    title = kwargs.pop('title', None)
