import datetime
import logging
from typing import Optional

from .embed import Embed
from .file import MediaType
from .utils import ISO8601

log = logging.getLogger(__name__)

class MessageContentLeaf:
    def __init__(self, leaf_type, data):
        self.type = leaf_type
        self._raw = data.get('data', data)

class MessagePoll(MessageContentLeaf):
    def __init__(self, leaf_type, data):
        super().__init__(leaf_type, data)

        self.id = self._raw.get('customFormId')

class MessagePollOption:
    def __init__(self, data):
        pass

class Message:
    '''A message in Guilded.

    .. container:: operations

        .. describe:: x == y

            Checks if two messages are equal.

        .. describe:: x != y

            Checks if two messages are not equal.
    '''
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
        self.channel_mentions = []
        self.role_mentions = []
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
        '''Get the content of a message in an easy to use single string. Attempts to append mentions to the Message as well. Intended for internal use only.'''
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
            type = node['type']
            if type == 'paragraph':
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
                                name = mentioned.get('name')
                                if mentioned.get('nickname') is True and mentioned.get('matcher') is not None:
                                    name = name.strip('@').strip(name).strip('@')
                                    if not name.strip():
                                        # matcher might be empty, oops - no username is available
                                        name = None
                                #self.mentions.append(Member(state=self._state, data={
                                #    'name': name,
                                #    'profilePicture': mentioned.get('avatar'),
                                #    'colour': parse_hex_number(mentioned.get('color', '000000').strip('#')),
                                #    'id': mentioned.get('id'),
                                #    'nickname': mentioned.get('name') if mentioned.get('nickname') is True else None
                                #}))
                        if element['type'] == 'reaction':
                            rtext = element['nodes'][0]['leaves'][0]['text']
                            content += str(rtext)
                        if element['type'] == 'link':
                            l1 = element['nodes'][0]['leaves'][0]['text']
                            l2 = element['data']['href']
                            content += f'[{l1}]({l2})'
                        if element['type'] == 'channel':
                            channel = element['data']['channel']
                            content += f'<#{channel.get("id")}>'
                            #self.channel_mentions.append(TeamChannel(state=self._state, group=None, team=self.team, data={
                            #    'name': channel.get('name'),
                            #    'id': channel.get('id')
                            #}))

            if type == 'markdown-plain-text':
                content += node['nodes'][0]['leaves'][0]['text']
            if type == 'webhookMessage':
                for msg_embed in node['data']['embeds']:
                    self.embeds.append(Embed.from_dict(msg_embed))
            if type == 'block-quote-container':
                text = str(node['nodes'][0]['nodes'][0]['leaves'][0]['text'])
                content += f'\n> {text}\n'

        return content

    async def delete(self):
        response = await self._state.delete_message(self.channel_id, self.id)
        self.deleted_at = datetime.datetime.utcnow()

    async def edit(self, *, content: str = None, embed = None, embeds: Optional[list] = None, file = None, files: Optional[list] = None):
        '''Edit a message.'''
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
        '''Add a reaction to a message. In the future, will take type Emoji, but currently takes an integer (the emoji's id)'''
        await self._state.add_message_reaction(self.channel_id, self.id, emoji)

    async def remove_self_reaction(self, emoji):
        '''Add a reaction to a message. In the future, will take type Emoji, but currently takes an integer (the emoji's id)'''
        await self._state.remove_self_message_reaction(self.channel_id, self.id, emoji)

    #async def reply(self, *content, **kwargs):
    #    title = kwargs.pop('title', None)
