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
import logging
import re
from typing import TYPE_CHECKING, Any, Dict, Optional, List, Sequence, Tuple, Union

from .colour import Colour
from .embed import Embed
from .enums import ChannelVisibility, FileType, try_enum, MessageType
from .errors import HTTPException
from .file import Attachment
from .mixins import Hashable
from .utils import ISO8601, MISSING, valid_video_extensions

if TYPE_CHECKING:
    from .types.channel import Mentions as MentionsPayload

    from .abc import Messageable, ServerChannel, User as abc_User
    from .channel import Thread
    from .emote import Emote
    from .group import Group
    from .role import Role
    from .server import Server
    from .user import Member, User

log = logging.getLogger(__name__)

__all__ = (
    'ChatMessage',
    'Mentions',
    'Message',
)


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

    def __init__(self, *, state, server: Server, data: MentionsPayload):
        self._state = state
        self._server = server
        self._users = data.get('users') or []
        self._channels = data.get('channels') or []
        self._roles = data.get('roles') or []

        self.everyone = data.get('everyone', False)
        self.here = data.get('here', False)

    def __repr__(self) -> str:
        return f'<Mentions users={len(self._users)} channels={len(self._channels)} roles={len(self._roles)} everyone={self.everyone} here={self.here}>'

    @property
    def users(self) -> List[Union[Member, User]]:
        """List[Union[:class:`.Member`, :class:`~guilded.User`]]: The list of users who were mentioned."""
        users = []
        for user_data in self._users:
            user = self._state._get_user(user_data['id'])
            if self._server:
                user = self._state._get_server_member(self._server.id, user_data['id']) or user
            if user:
                users.append(user)

        return users

    @property
    def channels(self) -> List[ServerChannel]:
        """List[:class:`~.abc.ServerChannel`]: The list of channels that were mentioned.

        An empty list is always returned in a DM context.
        """
        if not self._server:
            return []

        channels = []
        for channel_data in self._channels:
            channel = self._state._get_server_channel_or_thread(self._server.id, channel_data['id'])
            if channel:
                channels.append(channel)

        return channels

    @property
    def roles(self) -> List[Role]:
        """List[:class:`.Role`]: The list of roles that were mentioned.

        An empty list is always returned in a DM context.
        """
        if not self._server:
            return []

        roles = []
        for role_data in self._roles:
            role = self._server.get_role(role_data['id'])
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

        Parameters
        -----------
        ignore_cache: :class:`bool`
            Whether to fetch objects even if they are already cached.
            Defaults to ``False`` if not specified.
        ignore_errors: :class:`bool`
            Whether to ignore :exc:`HTTPException`\s that occur while fetching.
            Defaults to ``False`` if not specified.
        """
        # Bots cannot fetch any role information so they are not handled here.

        # Potential bug here involving old messages that mention former members
        # or deleted accounts - I am unsure whether Guilded includes these
        # cases in their `Mentions` model.

        # Just fetch the whole member list instead of fetching >=5 members individually.
        uncached_user_count = len(self._users) - len(self.users)
        if (
            self._server and (
                uncached_user_count >= 5
                or (len(self._users) >= 5 and ignore_cache)
            )
        ):
            # `fill_members` here would cause potentially unwanted/unexpected
            # cache usage, especially in large servers.
            members = await self._server.fetch_members()
            user_ids = [user['id'] for user in self._users]
            for member in members:
                if member.id in user_ids:
                    self._state.add_to_member_cache(member)

        else:
            for user_data in self._users:
                cached_user = self._state._get_user(user_data['id'])
                if self._server:
                    cached_user = self._state._get_server_member(self._server.id, user_data['id']) or cached_user

                if ignore_cache or not cached_user:
                    if self._server:
                        try:
                            user = await self._server.fetch_member(user_data['id'])
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

        # Just fetch the whole role list instead of fetching >=5 roles individually.
        uncached_role_count = len(self._roles) - len(self.roles)
        if (
            self._server and (
                uncached_role_count >= 5
                or (len(self._roles) >= 5 and ignore_cache)
            )
        ):
            # `fill_roles` here would cause potentially unwanted/unexpected
            # cache usage, especially in large servers.
            roles = await self._server.fetch_roles()
            role_ids = [role['id'] for role in self._roles]
            for role in roles:
                if role.id in role_ids:
                    self._state.add_to_role_cache(role)

        else:
            for role_data in self._roles:
                cached_role = self._state._get_server_role(self._server.id, role_data['id'])
                if self._server and (ignore_cache or not cached_role):
                    try:
                        role = await self._server.fetch_role(role_data['id'])
                    except HTTPException:
                        if not ignore_errors:
                            raise
                    else:
                        self._state.add_to_role_cache(role)

        for channel_data in self._channels:
            if not self._server:
                # This should never happen
                break

            cached_channel = self._state._get_server_channel_or_thread(self._server.id, channel_data['id'])
            if ignore_cache or not cached_channel:
                try:
                    channel = await self._server.fetch_channel(channel_data['id'])
                except HTTPException:
                    if not ignore_errors:
                        raise
                else:
                    self._state.add_to_server_channel_cache(channel)


ATTACHMENT_REGEX = re.compile(r'!\[(?P<caption>.+)?\]\((?P<url>https:\/\/(?:s3-us-west-2\.amazonaws\.com\/www\.guilded\.gg|img\.guildedcdn\.com)\/(?:ContentMediaGenericFiles|WebhookPrimaryMedia)\/[a-zA-Z0-9]+-Full\.(?P<extension>webp|jpeg|jpg|png|gif|apng)(?:\?.+)?)\)')

class HasContentMixin:
    def __init__(self):
        self.emotes: list = []
        self._raw_user_mentions: list = []
        self._raw_channel_mentions: list = []
        self._raw_role_mentions: list = []
        self._user_mentions: list = []
        self._channel_mentions: list = []
        self._role_mentions: list = []
        self._mentions_everyone: bool = False
        self._mentions_here: bool = False
        self.embeds: List[Embed] = []
        self.attachments: List[Attachment] = []

    @property
    def user_mentions(self) -> List[Union[Member, User]]:
        """List[Union[:class:`.Member`, :class:`~guilded.User`]]: The list of users who are mentioned in the content."""
        if hasattr(self, '_mentions'):
            return self._mentions.users
        return self._user_mentions

    @property
    def raw_user_mentions(self) -> List[str]:
        """List[:class:`str`]: A list of user IDs for the users that are
        mentioned in the content.

        This is useful if you need the users that are mentioned but do not
        care about their resolved data.
        """
        if hasattr(self, '_mentions'):
            return [obj['id'] for obj in self._mentions._users]
        return self._raw_user_mentions

    @property
    def mentions(self) -> List[Union[Member, User]]:
        """List[Union[:class:`.Member`, :class:`~guilded.User`]]: |dpyattr|

        The list of users who are mentioned in the content.
        """
        return self.user_mentions

    @property
    def raw_mentions(self) -> List[str]:
        """List[:class:`str`]: |dpyattr|

        A list of user IDs for the users that are mentioned in the content.

        This is useful if you need the users that are mentioned but do not
        care about their resolved data.
        """
        return self.raw_user_mentions

    @property
    def channel_mentions(self) -> List[ServerChannel]:
        """List[:class:`~.abc.ServerChannel`]: The list of channels that are
        mentioned in the content."""
        if hasattr(self, '_mentions'):
            return self._mentions.channels
        return self._channel_mentions

    @property
    def raw_channel_mentions(self) -> List[str]:
        """List[:class:`str`]: A list of channel IDs for the channels that are
        mentioned in the content.

        This is useful if you need the channels that are mentioned but do not
        care about their resolved data.
        """
        if hasattr(self, '_mentions'):
            return [obj['id'] for obj in self._mentions._channels]
        return self._raw_channel_mentions

    @property
    def role_mentions(self) -> List[Role]:
        """List[:class:`.Role`]: The list of roles that are mentioned in the content."""
        if hasattr(self, '_mentions'):
            return self._mentions.roles
        return self._role_mentions

    @property
    def raw_role_mentions(self) -> List[int]:
        """List[:class:`int`]: A list of role IDs for the roles that are
        mentioned in the content.

        This is useful if you need the roles that are mentioned but do not
        care about their resolved data.
        """
        if hasattr(self, '_mentions'):
            return [obj['id'] for obj in self._mentions._roles]
        return self._raw_role_mentions

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

    def _get_full_content(self, data: Dict[str, Any]) -> str:
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
                                self._raw_role_mentions.append(int(mentioned['id']))
                                content += f'<@{mentioned["id"]}>'
                            elif mentioned['type'] == 'person':
                                content += f'<@{mentioned["id"]}>'

                                self._raw_user_mentions.append(mentioned['id'])
                                if self.server_id:
                                    user = self._state._get_server_member(self.server_id, mentioned['id'])
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
                                    if self.server_id:
                                        self._user_mentions.append(self._state.create_member(
                                            server=self.server,
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
                            if link_href != link_text:
                                content += f'[{link_text}]({link_href})'
                            else:
                                content += link_href

                        elif element['type'] == 'channel':
                            channel = element['data']['channel']
                            if channel.get('id'):
                                self._raw_channel_mentions.append(channel["id"])
                                content += f'<#{channel["id"]}>'
                                channel = self._state._get_server_channel(self.server_id, channel['id'])
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
                        emote_id = node['nodes'][0]['data']['reaction']['id']
                        emote = self._state._get_emote(emote_id)
                        if emote:
                            self.emotes.append(emote)

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

            elif node_type in {'image', 'video', 'fileUpload'}:
                attachment = Attachment(state=self._state, data=node)
                self.attachments.append(attachment)

        content = content.rstrip('\n')
        # strip ending of newlines in case a paragraph node ended without
        # another paragraph node
        return content

    def _create_mentions(self, data: Optional[Dict[str, Any]]) -> Mentions:
        # This will always be called after setting _state and _server/server_id so this should be safe
        mentions = Mentions(state=self._state, server=self.server, data=data or {})
        return mentions

    def _extract_attachments(self, content: str) -> None:
        if content is None:
            content = ''
        elif not isinstance(content, str):
            raise TypeError(f'expected str for content, not {content.__class__.__name__}')

        self.attachments.clear()

        matches: List[Tuple[str, str, str]] = re.findall(ATTACHMENT_REGEX, content)
        for match in matches:
            caption, url, extension = match
            attachment = Attachment(
                state=self._state,
                data={
                    'type': FileType.video if extension in valid_video_extensions else FileType.image,
                    'caption': caption or None,
                    'url': url,
                },
            )
            self.attachments.append(attachment)


class ChatMessage(Hashable, HasContentMixin):
    """A message in Guilded.

    There is an alias for this class called ``Message``.

    .. container:: operations

        .. describe:: x == y

            Checks if two messages are equal.

        .. describe:: x != y

            Checks if two messages are not equal.

        .. describe:: hash(x)

            Returns the message's hash.

    Attributes
    -----------
    id: :class:`str`
        The message's ID.
    content: :class:`str`
        The text content of the message.
    embeds: List[:class:`.Embed`]
        The list of embeds in the message.
        This does not include link unfurl embeds.
    attachments: List[:class:`.Attachment`]
        The list of media attachments in the message.
    channel: :class:`~.abc.ServerChannel`
        The channel this message was sent in.
    webhook_id: Optional[:class:`str`]
        The webhook's ID that sent the message, if applicable.
    replied_to_ids: List[:class:`str`]
        A list of message IDs that the message replied to, up to 5.
    private: :class:`bool`
        Whether the message was sent so that only server moderators and users
        mentioned in the message can see it.
    silent: :class:`bool`
        Whether the message was sent silently, i.e., if this is true then
        users mentioned in the message were not sent a notification.
    pinned: :class:`bool`
        Whether the message is pinned in its channel.
    hidden_preview_urls: List[:class:`str`]
        URLs in ``content`` that have been prevented from unfurling as a link
        preview when displayed in Guilded.
    """

    __slots__ = (
        '_state',
        'channel',
        'channel_id',
        'server_id',
        'group_id',
        'id',
        'type',
        'webhook_id',
        'author_id',
        'created_at',
        'updated_at',
        'deleted_at',
        'replied_to_ids',
        'silent',
        'private',
        'pinned',
        'content',
        'embeds',
        'hidden_preview_urls',
    )

    def __init__(self, *, state, channel: Messageable, data, **extra: Any):
        super().__init__()
        self._state = state
        data = data.get('message', data)

        self.channel = channel
        self._author = extra.get('author')
        self._webhook = extra.get('webhook')

        self.channel_id: str = data.get('channelId')
        self.server_id: str = data.get('serverId') or data.get('teamId')
        self.group_id: Optional[str] = data.get('groupId')

        self.id: str = data['id']
        self.type: MessageType = try_enum(MessageType, data.get('type'))

        self.replied_to_ids: List[str] = data.get('replyMessageIds') or data.get('repliesToIds') or []
        self.author_id: str = data.get('createdBy')
        self.webhook_id: Optional[str] = data.get('createdByWebhookId') or data.get('webhookId')
        self._webhook_username: Optional[str] = None
        self._webhook_avatar_url: Optional[str] = None
        self.hidden_preview_urls: List[str] = data.get('hiddenLinkPreviewUrls') or []

        self.created_at: datetime.datetime = ISO8601(data.get('createdAt'))
        self.updated_at: Optional[datetime.datetime] = ISO8601(data.get('updatedAt') or data.get('editedAt'))

        self.silent: bool = data.get('isSilent') or False
        self.private: bool = data.get('isPrivate') or False
        self.pinned: bool = data.get('isPinned') or False

        if isinstance(data.get('content'), dict):
            # Webhook execution responses
            self.content: str = self._get_full_content(data['content'])
            hidden_embed_urls: Optional[Dict[str, bool]] = data['content'].get('document', {}).get('data', {}).get('hiddenEmbedUrls')
            if hidden_embed_urls:
                self.hidden_preview_urls = [key for [key, value] in hidden_embed_urls.items() if value]

            profile: Optional[Dict[str, str]] = data['content'].get('document', {}).get('data', {}).get('profile')
            if profile:
                self._webhook_username = profile.get('name')
                self._webhook_avatar_url = profile.get('profilePicture')

        else:
            self.content: str = data.get('content') or ''
            self._mentions = self._create_mentions(data.get('mentions'))
            self.embeds: List[Embed] = [
                Embed.from_dict(embed) for embed in (data.get('embeds') or [])
            ]
            self._extract_attachments(self.content)

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} id={self.id!r} author={self.author!r} channel={self.channel!r}>'

    @property
    def server(self) -> Server:
        """Optional[:class:`.Server`]: The server this message was sent in."""
        return self._state._get_server(self.server_id)

    @property
    def guild(self) -> Server:
        """Optional[:class:`.Server`]: |dpyattr|

        This is an alias of :attr:`.server`.

        The server this message was sent in.
        """
        return self.server

    @property
    def group(self) -> Group:
        """Optional[:class:`.Group`]: The group that the message is in."""
        return self.channel.group

    @property
    def author(self) -> Optional[Union[Member, User]]:
        """Optional[Union[:class:`.Member`, :class:`~guilded.User`]]: The user that created this message, if they are cached."""
        if self._author:
            return self._author

        user = None
        if self.server:
            user = self.server.get_member(self.author_id)

        if not user:
            user = self._state._get_user(self.author_id)

        if self.webhook_id or self._webhook:
            data = {
                'id': self.author_id,
                'type': 'bot',
            }
            # FIll in webhook defaults if available & then profile overrides if available
            if self._webhook:
                data['name'] = self._webhook.name
                data['profilePicture'] = self._webhook.avatar.url if self._webhook.avatar else None
            if self._webhook_username:
                data['name'] = self._webhook_username
            if self._webhook_avatar_url:
                data['profilePicture'] = self._webhook_avatar_url

            user = self._state.create_user(data=data)

        return user

    @property
    def created_by_bot(self) -> bool:
        """:class:`bool`: Whether this message's author is a bot or webhook."""
        return self.author.bot if self.author else self.webhook_id is not None

    @property
    def share_url(self) -> str:
        """:class:`str`: The share URL of the message."""
        if self.channel:
            return f'{self.channel.share_url}?messageId={self.id}'
        return None

    @property
    def jump_url(self) -> str:
        """:class:`str`: |dpyattr|

        This is an alias of :attr:`.share_url`.

        The share URL of the message.
        """
        return self.share_url

    @property
    def replied_to(self) -> List[ChatMessage]:
        """List[:class:`.ChatMessage`]: The list of messages that the message replied to.

        This property relies on message cache. If you need a list of IDs,
        consider :attr:`.replied_to_ids` instead.
        """
        messages = [self._state._get_message(message_id) for message_id in self.replied_to_ids]
        return [m for m in messages if m is not None]

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

        coro = self._state.delete_channel_message(self.channel_id, self.id)

        if delay is not None:

            async def delete(delay: float):
                await asyncio.sleep(delay)
                try:
                    await coro
                except HTTPException:
                    pass

            asyncio.create_task(delete(delay))

        else:
            await coro

    async def edit(
        self,
        content: Optional[str] = MISSING,
        *,
        embed: Optional[Embed] = MISSING,
        embeds: Optional[Sequence[Embed]] = MISSING,
        # hide_preview_urls: Optional[Sequence[str]] = MISSING,
    ) -> ChatMessage:
        """|coro|

        Edit this message.

        .. warning::

            This method **overwrites** all content previously in the message
            using the new payload.

        Parameters
        -----------
        content: :class:`str`
            The text content of the message.
        embed: :class:`.Embed`
            An embed in the message.
            This parameter cannot be meaningfully combined with ``embeds``.
        embeds: List[:class:`.Embed`]
            A list of embeds in the message.
            At present, this can contain at most 1 value.
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
        """

        from .http import handle_message_parameters

        params = handle_message_parameters(
            content=content,
            embed=embed,
            embeds=embeds,
            # hide_preview_urls=hide_preview_urls,
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

    async def add_reaction(self, emote: Emote, /) -> None:
        """|coro|

        Add a reaction to this message.

        Parameters
        -----------
        emote: :class:`.Emote`
            The emote to add.
        """
        emote_id: int = getattr(emote, 'id', emote)
        await self._state.add_channel_message_reaction(self.channel_id, self.id, emote_id)

    async def remove_reaction(self, emote: Emote, member: Optional[abc_User] = None) -> None:
        """|coro|

        Remove a reaction from this message.

        If the reaction is not your own then :attr:`~Permissions.manage_messages` is required.

        .. versionadded:: 1.9

        Parameters
        -----------
        emote: :class:`.Emote`
            The emote to remove.
        member: Optional[:class:`~.abc.User`]
            The member whose reaction to remove.
            If this is not specified, the client's reaction will be removed instead.
        """
        emote_id: int = getattr(emote, 'id', emote)
        await self._state.remove_channel_message_reaction(self.channel.id, self.id, emote_id, member.id if member else None)

    async def remove_self_reaction(self, emote: Emote, /) -> None:
        """|coro|

        Remove one of your reactions from this message.

        .. deprecated:: 1.9
            Use :meth:`.remove_reaction` instead.

        Parameters
        -----------
        emote: :class:`.Emote`
            The emote to remove.
        """
        await self.remove_reaction(emote)

    async def clear_reaction(self, emote: Emote, /) -> None:
        """|coro|

        Bulk remove reactions from this message based on their emote.

        To remove individual reactions from specific users, see :meth:`.remove_reaction`.

        .. versionadded:: 1.9

        Parameters
        -----------
        emote: :class:`.Emote`
            The emote to remove.
        """
        emote_id: int = getattr(emote, 'id', emote)
        await self._state.remove_channel_message_reactions(self.channel.id, self.id, emote_id)

    async def clear_reactions(self) -> None:
        """|coro|

        Bulk remove all the reactions from this message.

        .. versionadded:: 1.9
        """
        await self._state.remove_channel_message_reactions(self.channel.id, self.id)

    async def reply(
        self,
        content: Optional[str] = MISSING,
        *,
        embed: Optional[Embed] = MISSING,
        embeds: Optional[Sequence[Embed]] = MISSING,
        reference: Optional[ChatMessage] = MISSING,
        reply_to: Optional[Sequence[ChatMessage]] = MISSING,
        mention_author: Optional[bool] = None,
        silent: Optional[bool] = None,
        private: bool = False,
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
            # list unfortunately; it is always sorted chronologically.
            reply_to.append(self)

        return await self.channel.send(
            content=content,
            embed=embed,
            embeds=embeds,
            reference=reference,
            reply_to=reply_to,
            mention_author=mention_author,
            silent=silent,
            private=private,
            delete_after=delete_after,
        )

    async def create_thread(self, name: str, *, visibility: ChannelVisibility = None) -> Thread:
        """|coro|

        Create a new thread under the message.

        .. warning::

            Be careful with this method!
            It is very easy to accidentally cause a loop if you create a
            thread on a message that caused the creation of its thread.

        Depending on the type of the parent channel, this method requires
        different permissions:

        +------------------------------+-----------------------------------+
        |         Parent Type          |             Permission            |
        +------------------------------+-----------------------------------+
        | :attr:`~.ChannelType.chat`   | :attr:`Permissions.read_messages` |
        +------------------------------+-----------------------------------+
        | :attr:`~.ChannelType.voice`  | :attr:`Permissions.hear_voice`    |
        +------------------------------+-----------------------------------+
        | :attr:`~.ChannelType.stream` | :attr:`Permissions.view_streams`  |
        +------------------------------+-----------------------------------+

        .. versionadded:: 1.9

        Parameters
        -----------
        name: :class:`str`
            The thread's name. Can include spaces.
        visibility: Optional[:class:`.ChannelVisibility`]
            What users can access the channel. Currently, this can only be
            :attr:`~.ChannelVisibility.private` or ``None``.

            .. versionadded:: 1.10

        Returns
        --------
        :class:`.Thread`
            The created thread.

        Raises
        -------
        NotFound
            The server, channel, or message does not exist.
        Forbidden
            You are not allowed to create a thread in this channel.
        HTTPException
            Failed to create a thread.
        """
        return await self.channel.create_thread(name=name, message=self, visibility=visibility)

    async def pin(self) -> None:
        """|coro|

        Pin this message.

        .. versionadded:: 1.10

        Raises
        -------
        NotFound
            The channel or message does not exist.
        Forbidden
            You are not allowed to pin messages in this channel.
        HTTPException
            Failed to pin the message.
        """
        await self._state.pin_channel_message(self.channel.id, self.id)

    async def unpin(self) -> None:
        """|coro|

        Unpin this message.

        .. versionadded:: 1.10

        Raises
        -------
        NotFound
            The channel or message does not exist.
        Forbidden
            You are not allowed to unpin messages in this channel.
        HTTPException
            Failed to unpin the message.
        """
        await self._state.unpin_channel_message(self.channel.id, self.id)

Message = ChatMessage
