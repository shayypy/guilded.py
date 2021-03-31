import logging

from .errors import *
#from .user import Member
from .embed import Embed
from .colour import Colour
#from guilded.abc import TeamChannel
from .utils import ISO8601, parse_hex_number

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
        self.id = data.get('contentId', message.get('id'))
        self.webhook_id = data.get('webhookId')
        self.channel = channel
        self.channel_id = data.get('channelId')
        self.team = extra.get('team') or getattr(channel, 'team', None)

        self.created_at = ISO8601(data.get('createdAt'))
        self.edited_at = ISO8601(message.get('editedAt'))

        self.author = extra.get('author')
        self.mentions = []
        self.channel_mentions = []
        self.role_mentions = []
        self.embeds = []
        self.attachments = []
        self.content = self._get_full_content()

    def __str__(self):
        return self.content

    def __eq__(self, other):
        return self.id == other.id

    @property
    def jump_url(self):
        return f'https://guilded.gg/channels/{self.channel.id}/chat?messageId={self.id}'

    @property
    def embed(self):
        return embeds[0] if embeds else None

    @property
    def guild(self):
        # basic compatibility w/ discord bot code, plan on deprecating in the future
        return self.team

    def _get_full_content(self):
        # if-elsing till the day i die (or until this lib can update to 3.10)
        '''Get the content of a message in an easy to use single string. Attempts to append mentions to the Message as well. Intended for internal use only.'''
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
                                        to_mark = to_mark
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
                            content += rtext
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
                content += '> ' + text

        return content

    async def delete(self):
        return await self._state.delete_message(self.channel.id or self.channel_id, self.id)

    async def send(self, *, content: str = None, embed = None, embeds: list = [], file = None, files: list = []):
        '''Send to a Guilded channel.'''
        payload = {
            'old_content': self.content,
            'old_embeds': [embed.to_dict() for embed in self.embeds],
            'old_files': [await attachment.to_file() for attachment in self.attachments]
        }
        if content:
            payload['content'] = content
        if embed:
            embeds.append(embed)
        if embeds:
            payload['embeds'] = [embed.to_dict() for embed in embeds]
        if file:
            files.append(file)
        if files:
            pl_files = []
            for file in files:
                file.type = MediaType.attachment
                if file.url is None:
                    file = await file._upload()
                pl_files.append(file)

            payload['files'] = pl_files

        return await self._state.edit_message(self._channel_id, **payload)

class PartialMessage:
    pass
