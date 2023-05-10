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
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional, Tuple, Union

import datetime

from .channel import (
    Announcement,
    AnnouncementChannel,
    CalendarChannel,
    CalendarEvent,
    CalendarEventRSVP,
    ChatChannel,
    Doc,
    DMChannel,
    ForumTopic,
    ListItem,
    Thread,
    VoiceChannel,
)
from .emote import Emote
from .group import Group
from .message import ChatMessage
from .reply import AnnouncementReply, CalendarEventReply, DocReply, ForumTopicReply
from .user import Member, MemberBan, SocialLink
from .utils import ISO8601
from .webhook.async_ import Webhook

if TYPE_CHECKING:
    from .types import gateway as gw

    from .abc import ServerChannel
    from .channel import (
        CalendarChannel,
        DocsChannel,
        ForumChannel,
        ListChannel,
    )
    from .server import Server
    from .user import User


__all__ = (
    'BaseEvent',
    'ServerEvent',
    'MessageEvent',
    'MessageUpdateEvent',
    'MessageDeleteEvent',
    'BotAddEvent',
    'BotRemoveEvent',
    'MemberJoinEvent',
    'MemberRemoveEvent',
    'BanCreateEvent',
    'BanDeleteEvent',
    'MemberUpdateEvent',
    'BulkMemberRolesUpdateEvent',
    'MemberSocialLinkCreateEvent',
    'MemberSocialLinkUpdateEvent',
    'MemberSocialLinkDeleteEvent',
    'BulkMemberXpAddEvent',
    'ServerChannelCreateEvent',
    'ServerChannelUpdateEvent',
    'ServerChannelDeleteEvent',
    'WebhookCreateEvent',
    'WebhookUpdateEvent',
    'AnnouncementCreateEvent',
    'AnnouncementUpdateEvent',
    'AnnouncementDeleteEvent',
    'AnnouncementReactionAddEvent',
    'AnnouncementReactionRemoveEvent',
    'AnnouncementReplyCreateEvent',
    'AnnouncementReplyUpdateEvent',
    'AnnouncementReplyDeleteEvent',
    'AnnouncementReplyReactionAddEvent',
    'AnnouncementReplyReactionRemoveEvent',
    'DocCreateEvent',
    'DocUpdateEvent',
    'DocDeleteEvent',
    'DocReactionAddEvent',
    'DocReactionRemoveEvent',
    'DocReplyCreateEvent',
    'DocReplyUpdateEvent',
    'DocReplyDeleteEvent',
    'DocReplyReactionAddEvent',
    'DocReplyReactionRemoveEvent',
    'CalendarEventCreateEvent',
    'CalendarEventUpdateEvent',
    'CalendarEventDeleteEvent',
    'CalendarEventReactionAddEvent',
    'CalendarEventReactionRemoveEvent',
    'CalendarEventReplyCreateEvent',
    'CalendarEventReplyUpdateEvent',
    'CalendarEventReplyDeleteEvent',
    'RsvpUpdateEvent',
    'RsvpDeleteEvent',
    'BulkRsvpCreateEvent',
    'ForumTopicCreateEvent',
    'ForumTopicUpdateEvent',
    'ForumTopicDeleteEvent',
    'ForumTopicPinEvent',
    'ForumTopicUnpinEvent',
    'ForumTopicLockEvent',
    'ForumTopicUnlockEvent',
    'ForumTopicReactionAddEvent',
    'ForumTopicReactionRemoveEvent',
    'ForumTopicReplyCreateEvent',
    'ForumTopicReplyUpdateEvent',
    'ForumTopicReplyDeleteEvent',
    'ForumTopicReplyReactionAddEvent',
    'ForumTopicReplyReactionRemoveEvent',
    'GroupCreateEvent',
    'GroupUpdateEvent',
    'GroupDeleteEvent',
    'ListItemCreateEvent',
    'ListItemUpdateEvent',
    'ListItemDeleteEvent',
    'ListItemCompleteEvent',
    'ListItemUncompleteEvent',
    'MessageReactionAddEvent',
    'MessageReactionRemoveEvent',
    'BulkMessageReactionRemoveEvent',
)


class BaseEvent:
    """Represents a Gateway event for dispatching to event handlers.

    All events inherit from this class, and thus have the following attributes:

    Attributes
    -----------
    __gateway_event__: :class:`str`
        The Guilded event name that the event corresponds to.
    __dispatch_event__: :class:`str`
        The internal Pythonic event name to dispatch the event with.
        This is often, but not always, just a snake_case version of
        :attr:`.__gateway_event__` in present tense rather than past
        (e.g. ``resource_create`` vs. ``ResourceCreated``).
    """

    __gateway_event__: str
    __dispatch_event__: str


class ServerEvent(BaseEvent):
    """Represents any event that happens strictly within a server.

    All events inheriting from this class have the following attributes:

    Attributes
    -----------
    server_id: :class:`str`
        The ID of the server that the event happened in.
    server: :class:`Server`
        The server that the event happened in.
    """

    __slots__: Tuple[str, ...] = (
        'server_id',
        'server',
    )

    def __init__(self, state, data: gw._ServerEvent, /) -> None:
        self.server_id: str = data.get('serverId')
        self.server: Server = state._get_server(self.server_id)


class MessageEvent(BaseEvent):
    """Represents a :gdocs:`ChatMessageCreated <websockets/ChatMessageCreated>` event for dispatching to event handlers.

    Attributes
    -----------
    server_id: Optional[:class:`str`]
        The ID of the server that the message was sent in.
    server: Optional[:class:`Server`]
        The server that the message was sent in.
    message: :class:`ChatMessage`
        The message that was sent.
    """

    __gateway_event__ = 'ChatMessageCreated'
    __dispatch_event__ = 'message'
    __slots__: Tuple[str, ...] = (
        'server_id',
        'server',
        'message',
    )

    def __init__(
        self,
        state,
        data: gw.ChatMessageCreatedEvent,
        /,
        channel: Union[ChatChannel, VoiceChannel, Thread, DMChannel],
    ) -> None:
        self.server_id: Optional[str] = data.get('serverId')
        self.server: Optional[Server] = state._get_server(self.server_id)

        self.message = ChatMessage(state=state, channel=channel, data=data['message'])


class MessageUpdateEvent(BaseEvent):
    """Represents a :gdocs:`ChatMessageUpdated <websockets/ChatMessageUpdated>` event for dispatching to event handlers.

    Attributes
    -----------
    server_id: Optional[:class:`str`]
        The ID of the server that the message was sent in.
    server: Optional[:class:`Server`]
        The server that the message was sent in.
    before: Optional[:class:`ChatMessage`]
        The message before modification, if it was cached.
    after: :class:`ChatMessage`
        The message after modification.
    """

    __gateway_event__ = 'ChatMessageUpdated'
    __dispatch_event__ = 'message_update'
    __slots__: Tuple[str, ...] = (
        'server_id',
        'server',
        'before',
        'after',
    )

    def __init__(
        self,
        state,
        data: gw.ChatMessageUpdatedEvent,
        /,
        before: Optional[ChatMessage],
        channel: Union[ChatChannel, VoiceChannel, Thread, DMChannel],
    ) -> None:
        self.server_id: Optional[str] = data.get('serverId')
        self.server: Optional[Server] = state._get_server(self.server_id)

        self.before = before
        self.after = ChatMessage(state=state, channel=channel, data=data['message'])


class MessageDeleteEvent(BaseEvent):
    """Represents a :gdocs:`ChatMessageDeleted <websockets/ChatMessageDeleted>` event for dispatching to event handlers.

    Attributes
    -----------
    server_id: Optional[:class:`str`]
        The ID of the server that the message was sent in.
    server: Optional[:class:`Server`]
        The server that the message was sent in.
    channel: Optional[:class:`ChatMessage`]
        The channel that the message was sent in.
    message: Optional[:class:`ChatMessage`]
        The message from cache, if available.
    message_id: :class:`str`
        The ID of the message that was deleted.
    channel_id: :class:`str`
        The ID of the message's channel.
    deleted_at: :class:`datetime.datetime`
        When the message was deleted.
    private: :class:`bool`
        Whether the message was private.
    """

    __gateway_event__ = 'ChatMessageDeleted'
    __dispatch_event__ = 'message_delete'
    __slots__: Tuple[str, ...] = (
        'server_id',
        'server',
        'channel',
        'message',
        'message_id',
        'channel_id',
        'deleted_at',
        'private',
    )

    def __init__(
        self,
        state,
        data: gw.ChatMessageDeletedEvent,
        /,
        channel: Union[ChatChannel, VoiceChannel, Thread, DMChannel],
        message: Optional[ChatMessage],
    ) -> None:
        self.server_id: Optional[str] = data.get('serverId')
        self.server: Optional[Server] = state._get_server(self.server_id)

        self.channel = channel
        self.message = message

        message_data = data['message']
        self.message_id = message_data['id']
        self.channel_id = message_data['channelId']
        self.deleted_at: datetime.datetime = ISO8601(message_data['deletedAt'])
        self.private = message_data.get('isPrivate') or False


class BotAddEvent(ServerEvent):
    """Represents a :gdocs:`BotServerMembershipCreated <websockets/BotServerMembershipCreated>` event for dispatching to event handlers.

    .. versionadded:: 1.5

    Attributes
    -----------
    server_id: :class:`str`
        The ID of the server that the bot was added to.
    server: :class:`Server`
        The server that the bot was added to.
    member_id: :class:`str`
        The ID of the member that added the bot to the server.
    member: Optional[:class:`Member`]
        The member that added the bot to the server.
    """

    __gateway_event__ = 'BotServerMembershipCreated'
    __dispatch_event__ = 'bot_add'
    __slots__: Tuple[str, ...] = (
        'member_id',
        'member',
    )

    def __init__(
        self,
        state,
        data: gw.BotServerMembershipCreatedEvent,
        /,
    ) -> None:
        super().__init__(state, data)

        self.member_id = data['createdBy']
        self.member = self.server.get_member(data['createdBy'])


class BotRemoveEvent(ServerEvent):
    """Represents a :gdocs:`BotServerMembershipDeleted <websockets/BotServerMembershipDeleted>` event for dispatching to event handlers.

    .. versionadded:: 1.6

    Attributes
    -----------
    server_id: :class:`str`
        The ID of the server that the bot was removed from.
    server: :class:`Server`
        The server that the bot was removed from.
    member_id: :class:`str`
        The ID of the member that removed the bot from the server.
    member: Optional[:class:`Member`]
        The member that removed the bot from the server.
    """

    __gateway_event__ = 'BotServerMembershipDeleted'
    __dispatch_event__ = 'bot_remove'
    __slots__: Tuple[str, ...] = (
        'member_id',
        'member',
    )

    def __init__(
        self,
        state,
        data: gw.BotServerMembershipDeletedEvent,
        /,
    ) -> None:
        super().__init__(state, data)

        self.member_id = data['deletedBy']
        self.member = self.server.get_member(data['deletedBy'])


class MemberJoinEvent(ServerEvent):
    """Represents a :gdocs:`ServerMemberJoined <websockets/ServerMemberJoined>` event for dispatching to event handlers.

    Attributes
    -----------
    server_id: :class:`str`
        The ID of the server that the member joined.
    server: :class:`Server`
        The server that the member joined.
    member: :class:`Member`
        The member that joined.
    """

    __gateway_event__ = 'ServerMemberJoined'
    __dispatch_event__ = 'member_join'
    __slots__: Tuple[str, ...] = (
        'member',
    )

    def __init__(
        self,
        state,
        data: gw.ServerMemberJoinedEvent,
        /,
    ) -> None:
        super().__init__(state, data)

        self.member = Member(state=state, data=data['member'], server=self.server)


class MemberRemoveEvent(ServerEvent):
    """Represents a :gdocs:`ServerMemberRemoved <websockets/ServerMemberRemoved>` event for dispatching to event handlers.

    Attributes
    -----------
    server_id: :class:`str`
        The ID of the server that the member was removed from.
    server: :class:`Server`
        The server that the member was removed from.
    member: Optional[:class:`Member`]
        The member that was removed, from cache, if available.
    user_id: :class:`str`
        The ID of the member that was removed.
    kicked: :class:`bool`
        Whether this removal was the result of a kick.
    banned: :class:`bool`
        Whether this removal was the result of a ban.
    """

    __gateway_event__ = 'ServerMemberRemoved'
    __dispatch_event__ = 'member_remove'
    __slots__: Tuple[str, ...] = (
        'member',
        'user_id',
        'kicked',
        'banned',
    )

    def __init__(
        self,
        state,
        data: gw.ServerMemberRemovedEvent,
        /,
    ) -> None:
        super().__init__(state, data)

        self.user_id = data['userId']
        self.kicked = data.get('isKick') or False
        self.banned = data.get('isBan') or False

        self.member = self.server.get_member(self.user_id)


class _BanEvent(ServerEvent):
    __slots__: Tuple[str, ...] = (
        'ban',
        'member',
    )

    def __init__(
        self,
        state,
        data: gw.ServerMemberBanEvent,
        /,
    ) -> None:
        super().__init__(state, data)

        self.ban = MemberBan(state=state, data=data['serverMemberBan'], server=self.server)
        self.member = self.server.get_member(self.ban.user.id)


class BanCreateEvent(_BanEvent):
    """Represents a :gdocs:`ServerMemberBanned <websockets/ServerMemberBanned>` event for dispatching to event handlers.

    Attributes
    -----------
    server_id: :class:`str`
        The ID of the server that the member was banned from.
    server: :class:`Server`
        The server that the member was banned from.
    ban: :class:`MemberBan`
        The ban entry that was created.
    member: Optional[:class:`Member`]
        The member that was banned, from cache, if available.
    """

    __gateway_event__ = 'ServerMemberBanned'
    __dispatch_event__ = 'ban_create'


class BanDeleteEvent(_BanEvent):
    """Represents a :gdocs:`ServerMemberUnbanned <websockets/ServerMemberUnbanned>` event for dispatching to event handlers.

    Attributes
    -----------
    server_id: :class:`str`
        The ID of the server that the member was unbanned from.
    server: :class:`Server`
        The server that the member was unbanned from.
    ban: :class:`MemberBan`
        The ban entry that was deleted.
    member: Optional[:class:`Member`]
        The member that was unbanned, from cache, if available.
    """

    __gateway_event__ = 'ServerMemberUnbanned'
    __dispatch_event__ = 'ban_delete'


class MemberUpdateEvent(ServerEvent):
    """Represents a :gdocs:`ServerMemberUpdated <websockets/ServerMemberUpdated>` event for dispatching to event handlers.

    Attributes
    -----------
    server_id: :class:`str`
        The ID of the server that the member is in.
    server: :class:`Server`
        The server that the member is in.
    before: Optional[:class:`Member`]
        The member before modification, if they were cached.
    after: :class:`Member`
        The member after modification.
        If ``before`` is ``None``, this will be a partial :class:`Member`
        containing only the data that was modified and the ID of the user.
    modified: Set[:class:`str`]
        A set of attributes that were modified for the member.
        This is useful if you need to know if a value was modified,
        but you do not care about what the previous value was.
    """

    __gateway_event__ = 'ServerMemberUpdated'
    __dispatch_event__ = 'member_update'
    __slots__: Tuple[str, ...] = (
        'before',
        'after',
        # 'modified',
    )

    def __init__(
        self,
        state,
        data: gw.ServerMemberUpdatedEvent,
        /,
    ) -> None:
        super().__init__(state, data)

        before = self.server.get_member(data['userInfo']['id'])
        self.before = before
        self.after: Member

        if before is None:
            member_data = {
                'serverId': self.server_id,
                'user': {
                    'id': data['userInfo']['id'],
                },
                'nickname': data['userInfo'].get('nickname'),
            }
            self.after = Member(state=state, data=member_data, server=self.server)

        else:
            self.before = Member._copy(before)
            self.after = before
            self.after._update(data['userInfo'])

        # self.modified = {key for key in data['userInfo'].keys() if key != 'id'}
        # This is not currently how I would like it since it doesn't transform keys to what the user expects.


class BulkMemberRolesUpdateEvent(ServerEvent):
    """Represents a :gdocs:`ServerRolesUpdated <websockets/ServerRolesUpdated>` event for dispatching to event handlers.

    This particular class only handles updates to role membership, not server roles.

    Attributes
    -----------
    server_id: :class:`str`
        The ID of the server that the members are in.
    server: :class:`Server`
        The server that the members are in.
    before: List[:class:`Member`]
        The members before their roles were updated, if they were cached.
        Not all members in ``after`` are guaranteed to be in ``before``.
    after: List[:class:`Member`]
        The members after their roles were updated.
    """

    __gateway_event__ = 'ServerRolesUpdated'
    __dispatch_event__ = 'bulk_member_roles_update'
    __slots__: Tuple[str, ...] = (
        'before',
        'after',
    )

    def __init__(
        self,
        state,
        data: gw.ServerRolesUpdatedEvent,
        /,
    ) -> None:
        super().__init__(state, data)

        self.before: List[Member] = []
        self.after: List[Member] = []

        for update in data['memberRoleIds']:
            before_member = self.server.get_member(update['userId'])

            if before_member is None:
                member_data = {
                    'serverId': self.server_id,
                    'user': {
                        'id': update['userId'],
                    },
                    'roleIds': update['roleIds'],
                }
                after_member = Member(state=state, data=member_data, server=self.server)
                self.after.append(after_member)

            else:
                self.before.append(Member._copy(before_member))
                after_member = before_member
                after_member._update_roles(update['roleIds'])
                self.after.append(after_member)


class _MemberSocialLinkEvent(ServerEvent):
    __slots__: Tuple[str, ...] = (
        'social_link',
    )

    def __init__(
        self,
        state,
        data: gw.ServerMemberSocialLinkEvent,
        /,
    ) -> None:
        super().__init__(state, data)

        user_id = data['socialLink']['userId']
        user: Union[Member, User] = (
            self.server.get_member(user_id)
            or state._get_user(user_id)
            # This usually shouldn't happen
            or Member(
                state=state,
                data={
                    'serverId': self.server_id,
                    'user': {
                        'id': user_id,
                    },
                },
                server=self.server
            )
        )
        self.social_link = SocialLink(user, data['socialLink'])


class MemberSocialLinkCreateEvent(_MemberSocialLinkEvent):
    """Represents a :gdocs:`ServerMemberSocialLinkCreated <websockets/ServerMemberSocialLinkCreated>` event for dispatching to event handlers.

    Attributes
    -----------
    server_id: :class:`str`
        The ID of the server that the member is in.
    server: :class:`Server`
        The server that the member is in.
    social_link: :class:`SocialLink`
        The social link that was created.
    """

    __gateway_event__ = 'ServerMemberSocialLinkCreated'
    __dispatch_event__ = 'member_social_link_create'


class MemberSocialLinkUpdateEvent(_MemberSocialLinkEvent):
    """Represents a :gdocs:`ServerMemberSocialLinkUpdated <websockets/ServerMemberSocialLinkUpdated>` event for dispatching to event handlers.

    Attributes
    -----------
    server_id: :class:`str`
        The ID of the server that the member is in.
    server: :class:`Server`
        The server that the member is in.
    social_link: :class:`SocialLink`
        The social link after modification.
    """

    __gateway_event__ = 'ServerMemberSocialLinkUpdated'
    __dispatch_event__ = 'member_social_link_update'


class MemberSocialLinkDeleteEvent(_MemberSocialLinkEvent):
    """Represents a :gdocs:`ServerMemberSocialLinkDeleted <websockets/ServerMemberSocialLinkDeleted>` event for dispatching to event handlers.

    Attributes
    -----------
    server_id: :class:`str`
        The ID of the server that the member is in.
    server: :class:`Server`
        The server that the member is in.
    social_link: :class:`SocialLink`
        The social link that was deleted.
    """

    __gateway_event__ = 'ServerMemberSocialLinkDeleted'
    __dispatch_event__ = 'member_social_link_delete'


class BulkMemberXpAddEvent(ServerEvent):
    """Represents a :gdocs:`ServerXpAdded <websockets/ServerXpAdded>` event for dispatching to event handlers.

    This event is usually the result of flowbot actions like those provided in :ghelp:`XP Bot <5449718490903>`.

    Attributes
    -----------
    server_id: :class:`str`
        The ID of the server that the members are in.
    server: :class:`Server`
        The server that the members are in.
    user_ids: List[:class:`str`]
        The IDs of the members that gained XP.
    amount: :class:`int`
        The amount of XP that was added to each member.
    members: List[:class:`Member`]
        The updated members with their XP modified.
        If a member was not found in cache, this list will contain fewer items than :attr:`.user_ids`.
    """

    __gateway_event__ = 'ServerXpAdded'
    __dispatch_event__ = 'bulk_member_xp_add'
    __slots__: Tuple[str, ...] = (
        'user_ids',
        'amount',
        'members',
    )

    def __init__(
        self,
        state,
        data: gw.ServerXpAddedEvent,
        /,
        members: List[Member],
    ) -> None:
        super().__init__(state, data)

        self.user_ids = data['userIds']
        self.amount = data['amount']
        self.members = members


class _ServerChannelEvent(ServerEvent):
    __slots__: Tuple[str, ...] = (
        'channel',
    )

    def __init__(
        self,
        state,
        data: gw.ServerChannelEvent,
        /,
    ) -> None:
        super().__init__(state, data)

        self.channel: ServerChannel = state.create_channel(data=data['channel'], server=self.server)


class ServerChannelCreateEvent(_ServerChannelEvent):
    """Represents a :gdocs:`ServerChannelCreated <websockets/ServerChannelCreated>` event for dispatching to event handlers.

    Attributes
    -----------
    server_id: :class:`str`
        The ID of the server that the channel is in.
    server: :class:`Server`
        The server that the channel is in.
    channel: :class:`.abc.ServerChannel`
        The channel that was created.
    """

    __gateway_event__ = 'ServerChannelCreated'
    __dispatch_event__ = 'server_channel_create'


class ServerChannelUpdateEvent(ServerEvent):
    """Represents a :gdocs:`ServerChannelUpdated <websockets/ServerChannelUpdated>` event for dispatching to event handlers.

    Attributes
    -----------
    server_id: :class:`str`
        The ID of the server that the channel is in.
    server: :class:`Server`
        The server that the channel is in.
    before: Optional[:class:`.abc.ServerChannel`]
        The channel before modification, if it was cached.
    after: :class:`.abc.ServerChannel`
        The channel after modification.
    """

    __gateway_event__ = 'ServerChannelUpdated'
    __dispatch_event__ = 'server_channel_update'
    __slots__: Tuple[str, ...] = (
        'before',
        'after',
    )

    def __init__(
        self,
        state,
        data: gw.ServerChannelEvent,
        /,
    ) -> None:
        super().__init__(state, data)

        self.before = self.server.get_channel_or_thread(data['channel']['id'])
        self.channel: ServerChannel = state.create_channel(data=data['channel'], server=self.server)


class ServerChannelDeleteEvent(_ServerChannelEvent):
    """Represents a :gdocs:`ServerChannelDeleted <websockets/ServerChannelDeleted>` event for dispatching to event handlers.

    Attributes
    -----------
    server_id: :class:`str`
        The ID of the server that the channel was in.
    server: :class:`Server`
        The server that the channel was in.
    channel: :class:`.abc.ServerChannel`
        The channel that was deleted.
    """

    __gateway_event__ = 'ServerChannelDeleted'
    __dispatch_event__ = 'server_channel_delete'


class _WebhookEvent(ServerEvent):
    __slots__: Tuple[str, ...] = (
        'webhook',
    )

    def __init__(
        self,
        state,
        data: gw.ServerWebhookEvent,
        /,
    ) -> None:
        super().__init__(state, data)

        self.webhook = Webhook.from_state(data['webhook'], state)


class WebhookCreateEvent(_WebhookEvent):
    """Represents a :gdocs:`ServerWebhookCreated <websockets/ServerWebhookCreated>` event for dispatching to event handlers.

    Attributes
    -----------
    server_id: :class:`str`
        The ID of the server that the webhook is in.
    server: :class:`Server`
        The server that the webhook is in.
    webhook: :class:`Webhook`
        The webhook that was created.
    """

    __gateway_event__ = 'ServerWebhookCreated'
    __dispatch_event__ = 'webhook_create'


class WebhookUpdateEvent(_WebhookEvent):
    """Represents a :gdocs:`ServerWebhookUpdated <websockets/ServerWebhookUpdated>` event for dispatching to event handlers.

    Attributes
    -----------
    server_id: :class:`str`
        The ID of the server that the webhook is in.
    server: :class:`Server`
        The server that the webhook is in.
    webhook: :class:`Webhook`
        The webhook after modification.
        If :attr:`Webhook.deleted_at` is set, then this event indicates that
        the webhook was deleted.
    """

    __gateway_event__ = 'ServerWebhookUpdated'
    __dispatch_event__ = 'webhook_update'


class _AnnouncementEvent(ServerEvent):
    __slots__: Tuple[str, ...] = (
        'channel',
        'announcement',
    )

    def __init__(
        self,
        state,
        data: gw.AnnouncementEvent,
        /,
        channel: AnnouncementChannel,
    ) -> None:
        super().__init__(state, data)

        self.channel = channel
        self.announcement = Announcement(state=state, data=data['announcement'], channel=channel)


class AnnouncementCreateEvent(_AnnouncementEvent):
    """Represents an :gdocs:`AnnouncementCreated <websockets/AnnouncementCreated>` event for dispatching to event handlers.

    .. versionadded:: 1.8

    Attributes
    -----------
    server_id: :class:`str`
        The ID of the server that the announcement is in.
    server: :class:`Server`
        The server that the announcement is in.
    channel: :class:`AnnouncementChannel`
        The channel that the announcement is in.
    announcement: :class:`Announcement`
        The announcement that was created.
    """

    __gateway_event__ = 'AnnouncementCreated'
    __dispatch_event__ = 'announcement_create'


class AnnouncementUpdateEvent(_AnnouncementEvent):
    """Represents an :gdocs:`AnnouncementUpdated <websockets/AnnouncementUpdated>` event for dispatching to event handlers.

    .. versionadded:: 1.8

    Attributes
    -----------
    server_id: :class:`str`
        The ID of the server that the announcement is in.
    server: :class:`Server`
        The server that the announcement is in.
    channel: :class:`AnnouncementChannel`
        The channel that the announcement is in.
    announcement: :class:`Announcement`
        The announcement after modification.
    """

    __gateway_event__ = 'AnnouncementUpdated'
    __dispatch_event__ = 'announcement_update'


class AnnouncementDeleteEvent(_AnnouncementEvent):
    """Represents an :gdocs:`AnnouncementDeleted <websockets/AnnouncementDeleted>` event for dispatching to event handlers.

    .. versionadded:: 1.8

    Attributes
    -----------
    server_id: :class:`str`
        The ID of the server that the announcement was in.
    server: :class:`Server`
        The server that the announcement was in.
    channel: :class:`AnnouncementChannel`
        The channel that the announcement was in.
    announcement: :class:`Announcement`
        The announcement that was deleted.
    """

    __gateway_event__ = 'AnnouncementDeleted'
    __dispatch_event__ = 'announcement_delete'


class _AnnouncementReactionEvent(ServerEvent):
    __slots__: Tuple[str, ...] = (
        'channel_id',
        'announcement_id',
        'user_id',
        'emote',
        'channel',
        'member',
    )

    def __init__(
        self,
        state,
        data: gw.AnnouncementReactionEvent,
        /,
        channel: AnnouncementChannel,
    ) -> None:
        super().__init__(state, data)

        self.channel_id = data['reaction']['channelId']
        self.announcement_id = data['reaction']['announcementId']
        self.user_id = data['reaction']['createdBy']
        self.emote = Emote(state=state, data=data['reaction']['emote'])

        self.channel = channel
        self.member = self.server.get_member(self.user_id)


class AnnouncementReactionAddEvent(_AnnouncementReactionEvent):
    """Represents an :gdocs:`AnnouncementReactionCreated <websockets/AnnouncementReactionCreated>` event for dispatching to event handlers.

    .. versionadded:: 1.8

    Attributes
    -----------
    server_id: :class:`str`
        The ID of the server that the reaction is in.
    server: :class:`Server`
        The server that the reaction is in.
    channel: :class:`AnnouncementChannel`
        The channel that the reaction is in.
    member: Optional[:class:`Member`]
        The member that added the reaction, if they are cached.
    channel_id: :class:`str`
        The ID of the channel that the reaction is in.
    announcement_id: :class:`int`
        The ID of the announcement that the reaction is on.
    user_id: :class:`str`
        The ID of the user that added the reaction.
    emote: :class:`Emote`
        The emote that the reaction shows.
    """

    __gateway_event__ = 'AnnouncementReactionCreated'
    __dispatch_event__ = 'announcement_reaction_add'


class AnnouncementReactionRemoveEvent(_AnnouncementReactionEvent):
    """Represents an :gdocs:`AnnouncementReactionDeleted <websockets/AnnouncementReactionDeleted>` event for dispatching to event handlers.

    .. versionadded:: 1.8

    Attributes
    -----------
    server_id: :class:`str`
        The ID of the server that the reaction is in.
    server: :class:`Server`
        The server that the reaction is in.
    channel: :class:`AnnouncementChannel`
        The channel that the reaction is in.
    member: Optional[:class:`Member`]
        The member that added the reaction, if they are cached.
    channel_id: :class:`str`
        The ID of the channel that the reaction is in.
    announcement_id: :class:`int`
        The ID of the announcement that the reaction is on.
    user_id: :class:`str`
        The ID of the user that added the reaction.
    emote: :class:`Emote`
        The emote that the reaction shows.
    """

    __gateway_event__ = 'AnnouncementReactionDeleted'
    __dispatch_event__ = 'announcement_reaction_remove'


class _AnnouncementCommentEvent(ServerEvent):
    __slots__: Tuple[str, ...] = (
        'channel',
        'announcement',
        'reply',
    )

    def __init__(
        self,
        state,
        data: gw.AnnouncementCommentEvent,
        /,
        announcement: Announcement,
    ) -> None:
        super().__init__(state, data)

        self.channel = announcement.channel
        self.announcement = announcement
        self.reply = AnnouncementReply(state=state, data=data['announcementComment'], parent=announcement)


class AnnouncementReplyCreateEvent(_AnnouncementCommentEvent):
    """Represents an :gdocs:`AnnouncementCommentCreated <websockets/AnnouncementCommentCreated>` event for dispatching to event handlers.

    .. versionadded:: 1.8

    Attributes
    -----------
    server_id: :class:`str`
        The ID of the server that the reply is in.
    server: :class:`Server`
        The server that the reply is in.
    channel: :class:`AnnouncementChannel`
        The channel that the reply is in.
    announcement: :class:`Announcement`
        The announcement that the reply is under.
    reply: :class:`AnnouncementReply`
        The reply that was created.
    """

    __gateway_event__ = 'AnnouncementCommentCreated'
    __dispatch_event__ = 'announcement_reply_create'


class AnnouncementReplyUpdateEvent(_AnnouncementCommentEvent):
    """Represents an :gdocs:`AnnouncementCommentUpdated <websockets/AnnouncementCommentUpdated>` event for dispatching to event handlers.

    .. versionadded:: 1.8

    Attributes
    -----------
    server_id: :class:`str`
        The ID of the server that the reply is in.
    server: :class:`Server`
        The server that the reply is in.
    channel: :class:`AnnouncementChannel`
        The channel that the reply is in.
    announcement: :class:`Announcement`
        The announcement that the reply is under.
    reply: :class:`AnnouncementReply`
        The reply that was updated.
    """

    __gateway_event__ = 'AnnouncementCommentUpdated'
    __dispatch_event__ = 'announcement_reply_update'


class AnnouncementReplyDeleteEvent(_AnnouncementCommentEvent):
    """Represents an :gdocs:`AnnouncementCommentDeleted <websockets/AnnouncementCommentDeleted>` event for dispatching to event handlers.

    .. versionadded:: 1.8

    Attributes
    -----------
    server_id: :class:`str`
        The ID of the server that the reply was in.
    server: :class:`Server`
        The server that the reply was in.
    channel: :class:`AnnouncementChannel`
        The channel that the reply was in.
    announcement: :class:`Announcement`
        The announcement that the reply was under.
    reply: :class:`AnnouncementReply`
        The reply that was deleted.
    """

    __gateway_event__ = 'AnnouncementCommentDeleted'
    __dispatch_event__ = 'announcement_reply_delete'


class _AnnouncementReplyReactionEvent(ServerEvent):
    __slots__: Tuple[str, ...] = (
        'channel_id',
        'announcement_id',
        'reply_id',
        'user_id',
        'emote',
        'channel',
        'member',
    )

    def __init__(
        self,
        state,
        data: gw.AnnouncementCommentReactionEvent,
        /,
        channel: AnnouncementChannel,
    ) -> None:
        super().__init__(state, data)

        self.channel_id = data['reaction']['channelId']
        self.announcement_id = data['reaction']['announcementId']
        self.reply_id = data['reaction']['announcementCommentId']
        self.user_id = data['reaction']['createdBy']
        self.emote = Emote(state=state, data=data['reaction']['emote'])

        self.channel = channel
        self.member = self.server.get_member(self.user_id)


class AnnouncementReplyReactionAddEvent(_AnnouncementReplyReactionEvent):
    """Represents an :gdocs:`AnnouncementCommentReactionCreated <websockets/AnnouncementCommentReactionCreated>` event for dispatching to event handlers.

    .. versionadded:: 1.8

    Attributes
    -----------
    server_id: :class:`str`
        The ID of the server that the reaction is in.
    server: :class:`Server`
        The server that the reaction is in.
    channel: :class:`AnnouncementChannel`
        The channel that the reaction is in.
    member: Optional[:class:`Member`]
        The member that added the reaction, if they are cached.
    channel_id: :class:`str`
        The ID of the channel that the reaction is in.
    announcement_id: :class:`int`
        The ID of the calendar event that the reply is under.
    reply_id: :class:`int`
        The ID of the reply that the reaction is on.
    user_id: :class:`str`
        The ID of the user that added the reaction.
    emote: :class:`Emote`
        The emote that the reaction shows.
    """

    __gateway_event__ = 'AnnouncementCommentReactionCreated'
    __dispatch_event__ = 'announcement_reply_reaction_add'


class AnnouncementReplyReactionRemoveEvent(_AnnouncementReplyReactionEvent):
    """Represents an :gdocs:`AnnouncementCommentReactionDeleted <websockets/AnnouncementCommentReactionDeleted>` event for dispatching to event handlers.

    .. versionadded:: 1.8

    Attributes
    -----------
    server_id: :class:`str`
        The ID of the server that the reaction is in.
    server: :class:`Server`
        The server that the reaction is in.
    channel: :class:`AnnouncementChannel`
        The channel that the reaction is in.
    member: Optional[:class:`Member`]
        The member that added the reaction, if they are cached.
    channel_id: :class:`str`
        The ID of the channel that the reaction is in.
    announcement_id: :class:`int`
        The ID of the calendar event that the reply is under.
    reply_id: :class:`int`
        The ID of the reply that the reaction is on.
    user_id: :class:`str`
        The ID of the user that added the reaction.
    emote: :class:`Emote`
        The emote that the reaction shows.
    """

    __gateway_event__ = 'AnnouncementCommentReactionDeleted'
    __dispatch_event__ = 'announcement_reply_reaction_remove'


class _DocEvent(ServerEvent):
    __slots__: Tuple[str, ...] = (
        'channel',
        'doc',
    )

    def __init__(
        self,
        state,
        data: gw.DocEvent,
        /,
        channel: DocsChannel,
    ) -> None:
        super().__init__(state, data)

        self.channel = channel
        self.doc = Doc(state=state, data=data['doc'], channel=channel)


class DocCreateEvent(_DocEvent):
    """Represents a :gdocs:`DocCreated <websockets/DocCreated>` event for dispatching to event handlers.

    Attributes
    -----------
    server_id: :class:`str`
        The ID of the server that the doc is in.
    server: :class:`Server`
        The server that the doc is in.
    channel: :class:`DocsChannel`
        The channel that the doc is in.
    doc: :class:`Doc`
        The doc that was created.
    """

    __gateway_event__ = 'DocCreated'
    __dispatch_event__ = 'doc_create'


class DocUpdateEvent(_DocEvent):
    """Represents a :gdocs:`DocUpdated <websockets/DocUpdated>` event for dispatching to event handlers.

    Attributes
    -----------
    server_id: :class:`str`
        The ID of the server that the doc is in.
    server: :class:`Server`
        The server that the doc is in.
    channel: :class:`DocsChannel`
        The channel that the doc is in.
    doc: :class:`Doc`
        The doc after modification.
    """

    __gateway_event__ = 'DocUpdated'
    __dispatch_event__ = 'doc_update'


class DocDeleteEvent(_DocEvent):
    """Represents a :gdocs:`DocDeleted <websockets/DocDeleted>` event for dispatching to event handlers.

    Attributes
    -----------
    server_id: :class:`str`
        The ID of the server that the doc was in.
    server: :class:`Server`
        The server that the doc was in.
    channel: :class:`DocsChannel`
        The channel that the doc was in.
    doc: :class:`Doc`
        The doc that was deleted.
    """

    __gateway_event__ = 'DocDeleted'
    __dispatch_event__ = 'doc_delete'


class _DocReactionEvent(ServerEvent):
    __slots__: Tuple[str, ...] = (
        'channel_id',
        'doc_id',
        'user_id',
        'emote',
        'channel',
        'member',
    )

    def __init__(
        self,
        state,
        data: gw.DocReactionEvent,
        /,
        channel: DocsChannel,
    ) -> None:
        super().__init__(state, data)

        self.channel_id = data['reaction']['channelId']
        self.doc_id = data['reaction']['docId']
        self.user_id = data['reaction']['createdBy']
        self.emote = Emote(state=state, data=data['reaction']['emote'])

        self.channel = channel
        self.member = self.server.get_member(self.user_id)


class DocReactionAddEvent(_DocReactionEvent):
    """Represents a :gdocs:`DocReactionCreated <websockets/DocReactionCreated>` event for dispatching to event handlers.

    .. versionadded:: 1.7

    Attributes
    -----------
    server_id: :class:`str`
        The ID of the server that the reaction is in.
    server: :class:`Server`
        The server that the reaction is in.
    channel: :class:`DocsChannel`
        The channel that the reaction is in.
    member: Optional[:class:`Member`]
        The member that added the reaction, if they are cached.
    channel_id: :class:`str`
        The ID of the channel that the reaction is in.
    doc_id: :class:`int`
        The ID of the doc that the reaction is on.
    user_id: :class:`str`
        The ID of the user that added the reaction.
    emote: :class:`Emote`
        The emote that the reaction shows.
    """

    __gateway_event__ = 'DocReactionCreated'
    __dispatch_event__ = 'doc_reaction_add'


class DocReactionRemoveEvent(_DocReactionEvent):
    """Represents a :gdocs:`DocReactionDeleted <websockets/DocReactionDeleted>` event for dispatching to event handlers.

    .. versionadded:: 1.7

    Attributes
    -----------
    server_id: :class:`str`
        The ID of the server that the reaction is in.
    server: :class:`Server`
        The server that the reaction is in.
    channel: :class:`DocsChannel`
        The channel that the reaction is in.
    member: Optional[:class:`Member`]
        The member that added the reaction, if they are cached.
    channel_id: :class:`str`
        The ID of the channel that the reaction is in.
    doc_id: :class:`int`
        The ID of the doc that the reaction is on.
    user_id: :class:`str`
        The ID of the user that added the reaction.
    emote: :class:`Emote`
        The emote that the reaction shows.
    """

    __gateway_event__ = 'DocReactionDeleted'
    __dispatch_event__ = 'doc_reaction_remove'


class _DocCommentEvent(ServerEvent):
    __slots__: Tuple[str, ...] = (
        'channel',
        'doc',
        'reply',
    )

    def __init__(
        self,
        state,
        data: gw.DocCommentEvent,
        /,
        doc: Doc,
    ) -> None:
        super().__init__(state, data)

        self.channel = doc.channel
        self.doc = doc
        self.reply = DocReply(state=state, data=data['docComment'], parent=doc)


class DocReplyCreateEvent(_DocCommentEvent):
    """Represents a :gdocs:`DocCommentCreated <websockets/DocCommentCreated>` event for dispatching to event handlers.

    .. versionadded:: 1.7

    Attributes
    -----------
    server_id: :class:`str`
        The ID of the server that the reply is in.
    server: :class:`Server`
        The server that the reply is in.
    channel: :class:`DocsChannel`
        The channel that the reply is in.
    doc: :class:`Doc`
        The doc that the reply is under.
    reply: :class:`DocReply`
        The reply that was created.
    """

    __gateway_event__ = 'DocCommentCreated'
    __dispatch_event__ = 'doc_reply_create'


class DocReplyUpdateEvent(_DocCommentEvent):
    """Represents a :gdocs:`DocCommentUpdated <websockets/DocCommentUpdated>` event for dispatching to event handlers.

    .. versionadded:: 1.7

    Attributes
    -----------
    server_id: :class:`str`
        The ID of the server that the reply is in.
    server: :class:`Server`
        The server that the reply is in.
    channel: :class:`DocsChannel`
        The channel that the reply is in.
    doc: :class:`Doc`
        The doc that the reply is under.
    reply: :class:`DocReply`
        The reply that was updated.
    """

    __gateway_event__ = 'DocCommentUpdated'
    __dispatch_event__ = 'doc_reply_update'


class DocReplyDeleteEvent(_DocCommentEvent):
    """Represents a :gdocs:`DocCommentDeleted <websockets/DocCommentDeleted>` event for dispatching to event handlers.

    .. versionadded:: 1.7

    Attributes
    -----------
    server_id: :class:`str`
        The ID of the server that the reply was in.
    server: :class:`Server`
        The server that the reply was in.
    channel: :class:`DocsChannel`
        The channel that the reply was in.
    doc: :class:`Doc`
        The doc that the reply was under.
    reply: :class:`DocReply`
        The reply that was deleted.
    """

    __gateway_event__ = 'DocCommentDeleted'
    __dispatch_event__ = 'doc_reply_delete'


class _DocReplyReactionEvent(ServerEvent):
    __slots__: Tuple[str, ...] = (
        'channel_id',
        'doc_id',
        'reply_id',
        'user_id',
        'emote',
        'channel',
        'member',
    )

    def __init__(
        self,
        state,
        data: gw.DocCommentReactionEvent,
        /,
        channel: DocsChannel,
    ) -> None:
        super().__init__(state, data)

        self.channel_id = data['reaction']['channelId']
        self.doc_id = data['reaction']['docId']
        self.reply_id = data['reaction']['docCommentId']
        self.user_id = data['reaction']['createdBy']
        self.emote = Emote(state=state, data=data['reaction']['emote'])

        self.channel = channel
        self.member = self.server.get_member(self.user_id)


class DocReplyReactionAddEvent(_DocReplyReactionEvent):
    """Represents a :gdocs:`DocCommentReactionCreated <websockets/DocCommentReactionCreated>` event for dispatching to event handlers.

    .. versionadded:: 1.7

    Attributes
    -----------
    server_id: :class:`str`
        The ID of the server that the reaction is in.
    server: :class:`Server`
        The server that the reaction is in.
    channel: :class:`DocsChannel`
        The channel that the reaction is in.
    member: Optional[:class:`Member`]
        The member that added the reaction, if they are cached.
    channel_id: :class:`str`
        The ID of the channel that the reaction is in.
    doc_id: :class:`int`
        The ID of the calendar event that the reply is under.
    reply_id: :class:`int`
        The ID of the reply that the reaction is on.
    user_id: :class:`str`
        The ID of the user that added the reaction.
    emote: :class:`Emote`
        The emote that the reaction shows.
    """

    __gateway_event__ = 'DocCommentReactionCreated'
    __dispatch_event__ = 'doc_reply_reaction_add'


class DocReplyReactionRemoveEvent(_DocReplyReactionEvent):
    """Represents a :gdocs:`DocCommentReactionDeleted <websockets/DocCommentReactionDeleted>` event for dispatching to event handlers.

    .. versionadded:: 1.7

    Attributes
    -----------
    server_id: :class:`str`
        The ID of the server that the reaction is in.
    server: :class:`Server`
        The server that the reaction is in.
    channel: :class:`DocsChannel`
        The channel that the reaction is in.
    member: Optional[:class:`Member`]
        The member that added the reaction, if they are cached.
    channel_id: :class:`str`
        The ID of the channel that the reaction is in.
    doc_id: :class:`int`
        The ID of the calendar event that the reply is under.
    reply_id: :class:`int`
        The ID of the reply that the reaction is on.
    user_id: :class:`str`
        The ID of the user that added the reaction.
    emote: :class:`Emote`
        The emote that the reaction shows.
    """

    __gateway_event__ = 'DocCommentReactionDeleted'
    __dispatch_event__ = 'doc_reply_reaction_remove'


class _CalendarEventEvent(ServerEvent):
    __slots__: Tuple[str, ...] = (
        'channel',
        'calendar_event',
    )

    def __init__(
        self,
        state,
        data: gw.CalendarEventEvent,
        /,
        channel: CalendarChannel,
    ) -> None:
        super().__init__(state, data)

        self.channel = channel
        self.calendar_event = CalendarEvent(state=state, data=data['calendarEvent'], channel=channel)


class CalendarEventCreateEvent(_CalendarEventEvent):
    """Represents a :gdocs:`CalendarEventCreated <websockets/CalendarEventCreated>` event for dispatching to event handlers.

    Attributes
    -----------
    server_id: :class:`str`
        The ID of the server that the calendar event is in.
    server: :class:`Server`
        The server that the calendar event is in.
    channel: :class:`CalendarChannel`
        The channel that the calendar event is in.
    calendar_event: :class:`CalendarEvent`
        The calendar event that was created.
    """

    __gateway_event__ = 'CalendarEventCreated'
    __dispatch_event__ = 'calendar_event_create'


class CalendarEventUpdateEvent(_CalendarEventEvent):
    """Represents a :gdocs:`CalendarEventUpdated <websockets/CalendarEventUpdated>` event for dispatching to event handlers.

    Attributes
    -----------
    server_id: :class:`str`
        The ID of the server that the calendar event is in.
    server: :class:`Server`
        The server that the calendar event is in.
    channel: :class:`CalendarChannel`
        The channel that the calendar event is in.
    calendar_event: :class:`CalendarEvent`
        The calendar event after modification.
    """

    __gateway_event__ = 'CalendarEventUpdated'
    __dispatch_event__ = 'calendar_event_update'


class CalendarEventDeleteEvent(_CalendarEventEvent):
    """Represents a :gdocs:`CalendarEventDeleted <websockets/CalendarEventDeleted>` event for dispatching to event handlers.

    Attributes
    -----------
    server_id: :class:`str`
        The ID of the server that the calendar event was in.
    server: :class:`Server`
        The server that the calendar event was in.
    channel: :class:`CalendarChannel`
        The channel that the calendar event was in.
    calendar_event: :class:`CalendarEvent`
        The calendar event that was deleted.
    """

    __gateway_event__ = 'CalendarEventDeleted'
    __dispatch_event__ = 'calendar_event_delete'


class _CalendarEventReactionEvent(ServerEvent):
    __slots__: Tuple[str, ...] = (
        'channel_id',
        'event_id',
        'user_id',
        'emote',
        'channel',
        'member',
    )

    def __init__(
        self,
        state,
        data: gw.CalendarEventReactionEvent,
        /,
        channel: CalendarChannel,
    ) -> None:
        super().__init__(state, data)

        self.channel_id = data['reaction']['channelId']
        self.event_id = data['reaction']['calendarEventId']
        self.user_id = data['reaction']['createdBy']
        self.emote = Emote(state=state, data=data['reaction']['emote'])

        self.channel = channel
        self.member = self.server.get_member(self.user_id)


class CalendarEventReactionAddEvent(_CalendarEventReactionEvent):
    """Represents a :gdocs:`CalendarEventReactionCreated <websockets/CalendarEventReactionCreated>` event for dispatching to event handlers.

    .. versionadded:: 1.7

    Attributes
    -----------
    server_id: :class:`str`
        The ID of the server that the reaction is in.
    server: :class:`Server`
        The server that the reaction is in.
    channel: :class:`CalendarChannel`
        The channel that the reaction is in.
    member: Optional[:class:`Member`]
        The member that added the reaction, if they are cached.
    channel_id: :class:`str`
        The ID of the channel that the reaction is in.
    event_id: :class:`int`
        The ID of the calendar event that the reaction is on.
    user_id: :class:`str`
        The ID of the user that added the reaction.
    emote: :class:`Emote`
        The emote that the reaction shows.
    """

    __gateway_event__ = 'CalendarEventReactionCreated'
    __dispatch_event__ = 'calendar_event_reaction_add'


class CalendarEventReactionRemoveEvent(_CalendarEventReactionEvent):
    """Represents a :gdocs:`CalendarEventReactionDeleted <websockets/CalendarEventReactionDeleted>` event for dispatching to event handlers.

    .. versionadded:: 1.7

    Attributes
    -----------
    server_id: :class:`str`
        The ID of the server that the reaction is in.
    server: :class:`Server`
        The server that the reaction is in.
    channel: :class:`CalendarChannel`
        The channel that the reaction is in.
    member: Optional[:class:`Member`]
        The member that added the reaction, if they are cached.
    channel_id: :class:`str`
        The ID of the channel that the reaction is in.
    event_id: :class:`int`
        The ID of the calendar event that the reaction is on.
    user_id: :class:`str`
        The ID of the user that added the reaction.
    emote: :class:`Emote`
        The emote that the reaction shows.
    """

    __gateway_event__ = 'CalendarEventReactionDeleted'
    __dispatch_event__ = 'calendar_event_reaction_remove'


class _CalendarEventCommentEvent(ServerEvent):
    __slots__: Tuple[str, ...] = (
        'channel',
        'calendar_event',
        'reply',
    )

    def __init__(
        self,
        state,
        data: gw.CalendarEventCommentEvent,
        /,
        event: CalendarEvent,
    ) -> None:
        super().__init__(state, data)

        self.channel = event.channel
        self.calendar_event = event
        self.reply = CalendarEventReply(state=state, data=data['calendarEventComment'], parent=event)


class CalendarEventReplyCreateEvent(_CalendarEventCommentEvent):
    """Represents a :gdocs:`CalendarEventCommentCreated <websockets/CalendarEventCommentCreated>` event for dispatching to event handlers.

    .. versionadded:: 1.7

    Attributes
    -----------
    server_id: :class:`str`
        The ID of the server that the reply is in.
    server: :class:`Server`
        The server that the reply is in.
    channel: :class:`CalendarChannel`
        The channel that the reply is in.
    calendar_event: :class:`CalendarEvent`
        The event that the reply is under.
    reply: :class:`CalendarEventReply`
        The reply that was created.
    """

    __gateway_event__ = 'CalendarEventCommentCreated'
    __dispatch_event__ = 'calendar_event_reply_create'


class CalendarEventReplyUpdateEvent(_CalendarEventCommentEvent):
    """Represents a :gdocs:`CalendarEventCommentUpdated <websockets/CalendarEventCommentUpdated>` event for dispatching to event handlers.

    .. versionadded:: 1.7

    Attributes
    -----------
    server_id: :class:`str`
        The ID of the server that the reply is in.
    server: :class:`Server`
        The server that the reply is in.
    channel: :class:`CalendarChannel`
        The channel that the reply is in.
    calendar_event: :class:`CalendarEvent`
        The event that the reply is under.
    reply: :class:`CalendarEventReply`
        The reply that was updated.
    """

    __gateway_event__ = 'CalendarEventCommentUpdated'
    __dispatch_event__ = 'calendar_event_reply_update'


class CalendarEventReplyDeleteEvent(_CalendarEventCommentEvent):
    """Represents a :gdocs:`CalendarEventCommentDeleted <websockets/CalendarEventCommentDeleted>` event for dispatching to event handlers.

    .. versionadded:: 1.7

    Attributes
    -----------
    server_id: :class:`str`
        The ID of the server that the reply was in.
    server: :class:`Server`
        The server that the reply was in.
    channel: :class:`CalendarChannel`
        The channel that the reply was in.
    calendar_event: :class:`CalendarEvent`
        The event that the reply was under.
    reply: :class:`CalendarEventReply`
        The reply that was deleted.
    """

    __gateway_event__ = 'CalendarEventCommentDeleted'
    __dispatch_event__ = 'calendar_event_reply_delete'


class _CalendarEventReplyReactionEvent(ServerEvent):
    __slots__: Tuple[str, ...] = (
        'channel_id',
        'event_id',
        'reply_id',
        'user_id',
        'emote',
        'channel',
        'member',
    )

    def __init__(
        self,
        state,
        data: gw.CalendarEventCommentReactionEvent,
        /,
        channel: CalendarChannel,
    ) -> None:
        super().__init__(state, data)

        self.channel_id = data['reaction']['channelId']
        self.event_id = data['reaction']['calendarEventId']
        self.reply_id = data['reaction']['calendarEventCommentId']
        self.user_id = data['reaction']['createdBy']
        self.emote = Emote(state=state, data=data['reaction']['emote'])

        self.channel = channel
        self.member = self.server.get_member(self.user_id)


class CalendarEventReplyReactionAddEvent(_CalendarEventReplyReactionEvent):
    """Represents a :gdocs:`CalendarEventCommentReactionCreated <websockets/CalendarEventCommentReactionCreated>` event for dispatching to event handlers.

    .. versionadded:: 1.7

    Attributes
    -----------
    server_id: :class:`str`
        The ID of the server that the reaction is in.
    server: :class:`Server`
        The server that the reaction is in.
    channel: :class:`CalendarChannel`
        The channel that the reaction is in.
    member: Optional[:class:`Member`]
        The member that added the reaction, if they are cached.
    channel_id: :class:`str`
        The ID of the channel that the reaction is in.
    event_id: :class:`int`
        The ID of the calendar event that the reply is under.
    reply_id: :class:`int`
        The ID of the reply that the reaction is on.
    user_id: :class:`str`
        The ID of the user that added the reaction.
    emote: :class:`Emote`
        The emote that the reaction shows.
    """

    __gateway_event__ = 'CalendarEventCommentReactionCreated'
    __dispatch_event__ = 'calendar_event_reply_reaction_add'


class CalendarEventReplyReactionRemoveEvent(_CalendarEventReplyReactionEvent):
    """Represents a :gdocs:`CalendarEventCommentReactionDeleted <websockets/CalendarEventCommentReactionDeleted>` event for dispatching to event handlers.

    .. versionadded:: 1.7

    Attributes
    -----------
    server_id: :class:`str`
        The ID of the server that the reaction is in.
    server: :class:`Server`
        The server that the reaction is in.
    channel: :class:`CalendarChannel`
        The channel that the reaction is in.
    member: Optional[:class:`Member`]
        The member that added the reaction, if they are cached.
    channel_id: :class:`str`
        The ID of the channel that the reaction is in.
    event_id: :class:`int`
        The ID of the calendar event that the reply is under.
    reply_id: :class:`int`
        The ID of the reply that the reaction is on.
    user_id: :class:`str`
        The ID of the user that added the reaction.
    emote: :class:`Emote`
        The emote that the reaction shows.
    """

    __gateway_event__ = 'CalendarEventCommentReactionDeleted'
    __dispatch_event__ = 'calendar_event_reply_reaction_remove'


class _CalendarEventRsvpEvent(ServerEvent):
    __slots__: Tuple[str, ...] = (
        'event',
        'channel',
        'rsvp',
    )

    def __init__(
        self,
        state,
        data: gw.CalendarEventRsvpEvent,
        /,
        event: CalendarEvent,
    ) -> None:
        super().__init__(state, data)

        self.event = event
        self.channel = event.channel
        self.rsvp = CalendarEventRSVP(data=data['calendarEventRsvp'], event=event)


class RsvpUpdateEvent(_CalendarEventRsvpEvent):
    """Represents a :gdocs:`CalendarEventRsvpUpdated <websockets/CalendarEventRsvpUpdated>` event for dispatching to event handlers.

    Attributes
    -----------
    server_id: :class:`str`
        The ID of the server that the RSVP is in.
    server: :class:`Server`
        The server that the RSVP is in.
    channel: :class:`CalendarChannel`
        The channel that the RSVP is in.
    rsvp: :class:`CalendarEventRsvp`
        The RSVP that was created or updated.
    """

    __gateway_event__ = 'CalendarEventRsvpUpdated'
    __dispatch_event__ = 'rsvp_update'


class RsvpDeleteEvent(_CalendarEventRsvpEvent):
    """Represents a :gdocs:`CalendarEventRsvpDeleted <websockets/CalendarEventRsvpDeleted>` event for dispatching to event handlers.

    Attributes
    -----------
    server_id: :class:`str`
        The ID of the server that the RSVP was in.
    server: :class:`Server`
        The server that the RSVP was in.
    channel: :class:`CalendarChannel`
        The channel that the RSVP was in.
    rsvp: :class:`CalendarEventRsvp`
        The RSVP that was deleted.
    """

    __gateway_event__ = 'CalendarEventRsvpDeleted'
    __dispatch_event__ = 'rsvp_delete'


class BulkRsvpCreateEvent(ServerEvent):
    """Represents a :gdocs:`CalendarEventRsvpManyUpdated <websockets/CalendarEventRsvpManyUpdated>` event for dispatching to event handlers.

    Attributes
    -----------
    server_id: :class:`str`
        The ID of the server that the RSVPs are in.
    server: :class:`Server`
        The server that the RSVPs are in.
    channel: :class:`CalendarChannel`
        The channel that the RSVPs are in.
    rsvps: List[:class:`CalendarEventRsvp`]
        The RSVPs that were created.
    """

    __gateway_event__ = 'CalendarEventRsvpManyUpdated'
    __dispatch_event__ = 'bulk_rsvp_create'
    __slots__: Tuple[str, ...] = (
        'event',
        'channel',
        'rsvps',
    )

    def __init__(
        self,
        state,
        data: gw.CalendarEventRsvpManyUpdatedEvent,
        /,
        event: CalendarEvent,
    ) -> None:
        super().__init__(state, data)

        self.event = event
        self.channel = event.channel
        self.rsvps = [CalendarEventRSVP(data=rsvp_data, event=event) for rsvp_data in data['calendarEventRsvps']]


class _ForumTopicEvent(ServerEvent):
    __slots__: Tuple[str, ...] = (
        'channel',
        'topic',
    )

    def __init__(
        self,
        state,
        data: gw.ForumTopicEvent,
        /,
        channel: ForumChannel,
    ) -> None:
        super().__init__(state, data)

        self.channel = channel
        self.topic = ForumTopic(state=state, data=data['forumTopic'], channel=channel)


class ForumTopicCreateEvent(_ForumTopicEvent):
    """Represents a :gdocs:`ForumTopicCreated <websockets/ForumTopicCreated>` event for dispatching to event handlers.

    Attributes
    -----------
    server_id: :class:`str`
        The ID of the server that the forum topic is in.
    server: :class:`Server`
        The server that the forum topic is in.
    channel: :class:`ForumChannel`
        The channel that the forum topic is in.
    topic: :class:`ForumTopic`
        The forum topic that was created.
    """

    __gateway_event__ = 'ForumTopicCreated'
    __dispatch_event__ = 'forum_topic_create'


class ForumTopicUpdateEvent(_ForumTopicEvent):
    """Represents a :gdocs:`ForumTopicUpdated <websockets/ForumTopicUpdated>` event for dispatching to event handlers.

    Attributes
    -----------
    server_id: :class:`str`
        The ID of the server that the forum topic is in.
    server: :class:`Server`
        The server that the forum topic is in.
    channel: :class:`ForumChannel`
        The channel that the forum topic is in.
    topic: :class:`ForumTopic`
        The forum topic after modification.
    """

    __gateway_event__ = 'ForumTopicUpdated'
    __dispatch_event__ = 'forum_topic_update'


class ForumTopicDeleteEvent(_ForumTopicEvent):
    """Represents a :gdocs:`ForumTopicDeleted <websockets/ForumTopicDeleted>` event for dispatching to event handlers.

    Attributes
    -----------
    server_id: :class:`str`
        The ID of the server that the forum topic was in.
    server: :class:`Server`
        The server that the forum topic was in.
    channel: :class:`ForumChannel`
        The channel that the forum topic was in.
    topic: :class:`ForumTopic`
        The forum topic that was deleted.
    """

    __gateway_event__ = 'ForumTopicDeleted'
    __dispatch_event__ = 'forum_topic_delete'


class ForumTopicPinEvent(_ForumTopicEvent):
    """Represents a :gdocs:`ForumTopicPinned <websockets/ForumTopicPinned>` event for dispatching to event handlers.

    Attributes
    -----------
    server_id: :class:`str`
        The ID of the server that the forum topic is in.
    server: :class:`Server`
        The server that the forum topic is in.
    channel: :class:`ForumChannel`
        The channel that the forum topic is in.
    topic: :class:`ForumTopic`
        The forum topic that was pinned.
    """

    __gateway_event__ = 'ForumTopicPinned'
    __dispatch_event__ = 'forum_topic_pin'


class ForumTopicUnpinEvent(_ForumTopicEvent):
    """Represents a :gdocs:`ForumTopicUnpinned <websockets/ForumTopicUnpinned>` event for dispatching to event handlers.

    Attributes
    -----------
    server_id: :class:`str`
        The ID of the server that the forum topic is in.
    server: :class:`Server`
        The server that the forum topic is in.
    channel: :class:`ForumChannel`
        The channel that the forum topic is in.
    topic: :class:`ForumTopic`
        The forum topic that was unpinned.
    """

    __gateway_event__ = 'ForumTopicUnpinned'
    __dispatch_event__ = 'forum_topic_unpin'


class ForumTopicLockEvent(_ForumTopicEvent):
    """Represents a :gdocs:`ForumTopicLocked <websockets/ForumTopicLocked>` event for dispatching to event handlers.

    Attributes
    -----------
    server_id: :class:`str`
        The ID of the server that the forum topic is in.
    server: :class:`Server`
        The server that the forum topic is in.
    channel: :class:`ForumChannel`
        The channel that the forum topic is in.
    topic: :class:`ForumTopic`
        The forum topic that was locked.
    """

    __gateway_event__ = 'ForumTopicLocked'
    __dispatch_event__ = 'forum_topic_lock'


class ForumTopicUnlockEvent(_ForumTopicEvent):
    """Represents a :gdocs:`ForumTopicUnlocked <websockets/ForumTopicUnlocked>` event for dispatching to event handlers.

    Attributes
    -----------
    server_id: :class:`str`
        The ID of the server that the forum topic is in.
    server: :class:`Server`
        The server that the forum topic is in.
    channel: :class:`ForumChannel`
        The channel that the forum topic is in.
    topic: :class:`ForumTopic`
        The forum topic that was unlocked.
    """

    __gateway_event__ = 'ForumTopicUnlocked'
    __dispatch_event__ = 'forum_topic_unlock'


class _ForumTopicReactionEvent(ServerEvent):
    __slots__: Tuple[str, ...] = (
        'channel_id',
        'topic_id',
        'user_id',
        'emote',
        'channel',
        'member',
    )

    def __init__(
        self,
        state,
        data: gw.ForumTopicReactionEvent,
        /,
        channel: ForumChannel,
    ) -> None:
        super().__init__(state, data)

        self.channel_id = data['reaction']['channelId']
        self.topic_id = data['reaction']['forumTopicId']
        self.user_id = data['reaction']['createdBy']
        self.emote = Emote(state=state, data=data['reaction']['emote'])

        self.channel = channel
        self.member = self.server.get_member(self.user_id)


class ForumTopicReactionAddEvent(_ForumTopicReactionEvent):
    """Represents a :gdocs:`ForumTopicReactionCreated <websockets/ForumTopicReactionCreated>` event for dispatching to event handlers.

    .. versionadded:: 1.5

    Attributes
    -----------
    server_id: :class:`str`
        The ID of the server that the reaction is in.
    server: :class:`Server`
        The server that the reaction is in.
    channel: :class:`ForumChannel`
        The channel that the reaction is in.
    member: Optional[:class:`Member`]
        The member that added the reaction, if they are cached.
    channel_id: :class:`str`
        The ID of the channel that the reaction is in.
    topic_id: :class:`int`
        The ID of the forum topic that the reaction is on.
    user_id: :class:`str`
        The ID of the user that added the reaction.
    emote: :class:`Emote`
        The emote that the reaction shows.
    """

    __gateway_event__ = 'ForumTopicReactionCreated'
    __dispatch_event__ = 'forum_topic_reaction_add'


class ForumTopicReactionRemoveEvent(_ForumTopicReactionEvent):
    """Represents a :gdocs:`ForumTopicReactionDeleted <websockets/ForumTopicReactionDeleted>` event for dispatching to event handlers.

    .. versionadded:: 1.5

    Attributes
    -----------
    server_id: :class:`str`
        The ID of the server that the reaction is in.
    server: :class:`Server`
        The server that the reaction is in.
    channel: :class:`ForumChannel`
        The channel that the reaction is in.
    member: Optional[:class:`Member`]
        The member that added the reaction, if they are cached.
    channel_id: :class:`str`
        The ID of the channel that the reaction is in.
    topic_id: :class:`int`
        The ID of the forum topic that the reaction is on.
    user_id: :class:`str`
        The ID of the user that added the reaction.
    emote: :class:`Emote`
        The emote that the reaction shows.
    """

    __gateway_event__ = 'ForumTopicReactionDeleted'
    __dispatch_event__ = 'forum_topic_reaction_remove'


class _ForumTopicCommentEvent(ServerEvent):
    __slots__: Tuple[str, ...] = (
        'channel',
        'topic',
        'reply',
    )

    def __init__(
        self,
        state,
        data: gw.ForumTopicCommentEvent,
        /,
        topic: ForumTopic,
    ) -> None:
        super().__init__(state, data)

        self.channel = topic.channel
        self.topic = topic
        self.reply = ForumTopicReply(state=state, data=data['forumTopicComment'], parent=topic)


class ForumTopicReplyCreateEvent(_ForumTopicCommentEvent):
    """Represents a :gdocs:`ForumTopicCommentCreated <websockets/ForumTopicCommentCreated>` event for dispatching to event handlers.

    .. versionadded:: 1.6

    Attributes
    -----------
    server_id: :class:`str`
        The ID of the server that the reply is in.
    server: :class:`Server`
        The server that the reply is in.
    channel: :class:`ForumChannel`
        The channel that the reply is in.
    topic: :class:`ForumTopic`
        The topic that the reply is under.
    reply: :class:`ForumTopicReply`
        The reply that was created.
    """

    __gateway_event__ = 'ForumTopicCommentCreated'
    __dispatch_event__ = 'forum_topic_reply_create'


class ForumTopicReplyUpdateEvent(_ForumTopicCommentEvent):
    """Represents a :gdocs:`ForumTopicCommentUpdated <websockets/ForumTopicCommentUpdated>` event for dispatching to event handlers.

    .. versionadded:: 1.6

    Attributes
    -----------
    server_id: :class:`str`
        The ID of the server that the reply is in.
    server: :class:`Server`
        The server that the reply is in.
    channel: :class:`ForumChannel`
        The channel that the reply is in.
    topic: :class:`ForumTopic`
        The topic that the reply is under.
    reply: :class:`ForumTopicReply`
        The reply that was updated.
    """

    __gateway_event__ = 'ForumTopicCommentUpdated'
    __dispatch_event__ = 'forum_topic_reply_update'


class ForumTopicReplyDeleteEvent(_ForumTopicCommentEvent):
    """Represents a :gdocs:`ForumTopicCommentDeleted <websockets/ForumTopicCommentDeleted>` event for dispatching to event handlers.

    .. versionadded:: 1.6

    Attributes
    -----------
    server_id: :class:`str`
        The ID of the server that the reply was in.
    server: :class:`Server`
        The server that the reply was in.
    channel: :class:`ForumChannel`
        The channel that the reply was in.
    topic: :class:`ForumTopic`
        The topic that the reply was under.
    reply: :class:`ForumTopicReply`
        The reply that was deleted.
    """

    __gateway_event__ = 'ForumTopicCommentDeleted'
    __dispatch_event__ = 'forum_topic_reply_delete'


class _ForumTopicReplyReactionEvent(ServerEvent):
    __slots__: Tuple[str, ...] = (
        'channel_id',
        'topic_id',
        'reply_id',
        'user_id',
        'emote',
        'channel',
        'member',
    )

    def __init__(
        self,
        state,
        data: gw.ForumTopicCommentReactionEvent,
        /,
        channel: ForumChannel,
    ) -> None:
        super().__init__(state, data)

        self.channel_id = data['reaction']['channelId']
        self.topic_id = data['reaction']['forumTopicId']
        self.reply_id = data['reaction']['forumTopicCommentId']
        self.user_id = data['reaction']['createdBy']
        self.emote = Emote(state=state, data=data['reaction']['emote'])

        self.channel = channel
        self.member = self.server.get_member(self.user_id)


class ForumTopicReplyReactionAddEvent(_ForumTopicReplyReactionEvent):
    """Represents a :gdocs:`ForumTopicCommentReactionCreated <websockets/ForumTopicCommentReactionCreated>` event for dispatching to event handlers.

    .. versionadded:: 1.6

    Attributes
    -----------
    server_id: :class:`str`
        The ID of the server that the reaction is in.
    server: :class:`Server`
        The server that the reaction is in.
    channel: :class:`ForumChannel`
        The channel that the reaction is in.
    member: Optional[:class:`Member`]
        The member that added the reaction, if they are cached.
    channel_id: :class:`str`
        The ID of the channel that the reaction is in.
    topic_id: :class:`int`
        The ID of the forum topic that the reply is under.
    reply_id: :class:`int`
        The ID of the reply that the reaction is on.
    user_id: :class:`str`
        The ID of the user that added the reaction.
    emote: :class:`Emote`
        The emote that the reaction shows.
    """

    __gateway_event__ = 'ForumTopicCommentReactionCreated'
    __dispatch_event__ = 'forum_topic_reply_reaction_add'


class ForumTopicReplyReactionRemoveEvent(_ForumTopicReplyReactionEvent):
    """Represents a :gdocs:`ForumTopicCommentReactionDeleted <websockets/ForumTopicCommentReactionDeleted>` event for dispatching to event handlers.

    .. versionadded:: 1.6

    Attributes
    -----------
    server_id: :class:`str`
        The ID of the server that the reaction is in.
    server: :class:`Server`
        The server that the reaction is in.
    channel: :class:`ForumChannel`
        The channel that the reaction is in.
    member: Optional[:class:`Member`]
        The member that added the reaction, if they are cached.
    channel_id: :class:`str`
        The ID of the channel that the reaction is in.
    topic_id: :class:`int`
        The ID of the forum topic that the reply is under.
    reply_id: :class:`int`
        The ID of the reply that the reaction is on.
    user_id: :class:`str`
        The ID of the user that added the reaction.
    emote: :class:`Emote`
        The emote that the reaction shows.
    """

    __gateway_event__ = 'ForumTopicCommentReactionDeleted'
    __dispatch_event__ = 'forum_topic_reply_reaction_remove'


class _GroupEvent(ServerEvent):
    __slots__: Tuple[str, ...] = (
        'group',
    )

    def __init__(
        self,
        state,
        data: gw.GroupEvent,
        /,
    ) -> None:
        super().__init__(state, data)

        self.group = Group(state=state, data=data['group'], server=self.server)


class GroupCreateEvent(_GroupEvent):
    """Represents a :gdocs:`GroupCreated <websockets/GroupCreated>` event for dispatching to event handlers.

    Attributes
    -----------
    server_id: :class:`str`
        The ID of the server that the group is in.
    server: :class:`Server`
        The server that the group is in.
    group: :class:`Group`
        The group that was created.
    """

    __gateway_event__ = 'GroupCreated'
    __dispatch_event__ = 'group_create'


class GroupUpdateEvent(_GroupEvent):
    """Represents a :gdocs:`GroupUpdated <websockets/GroupUpdated>` event for dispatching to event handlers.

    Attributes
    -----------
    server_id: :class:`str`
        The ID of the server that the group is in.
    server: :class:`Server`
        The server that the group is in.
    group: :class:`Group`
        The group after modification.
    """

    __gateway_event__ = 'GroupUpdated'
    __dispatch_event__ = 'group_update'


class GroupDeleteEvent(_GroupEvent):
    """Represents a :gdocs:`GroupDeleted <websockets/GroupDeleted>` event for dispatching to event handlers.

    Attributes
    -----------
    server_id: :class:`str`
        The ID of the server that the group was in.
    server: :class:`Server`
        The server that the group was in.
    group: :class:`Group`
        The group that was deleted.
    """

    __gateway_event__ = 'GroupDeleted'
    __dispatch_event__ = 'group_delete'


class _ListItemEvent(ServerEvent):
    __slots__: Tuple[str, ...] = (
        'channel',
        'item',
    )

    def __init__(
        self,
        state,
        data: gw.ListItemEvent,
        /,
        channel: ListChannel,
    ) -> None:
        super().__init__(state, data)

        self.channel = channel
        self.item = ListItem(state=state, data=data['listItem'], channel=channel)


class ListItemCreateEvent(_ListItemEvent):
    """Represents a :gdocs:`ListItemCreated <websockets/ListItemCreated>` event for dispatching to event handlers.

    Attributes
    -----------
    server_id: :class:`str`
        The ID of the server that the list item is in.
    server: :class:`Server`
        The server that the list item is in.
    channel: :class:`ListChannel`
        The channel that the list item is in.
    item: :class:`ListItem`
        The list item that was created.
    """

    __gateway_event__ = 'ListItemCreated'
    __dispatch_event__ = 'list_item_create'


class ListItemUpdateEvent(_ListItemEvent):
    """Represents a :gdocs:`ListItemUpdated <websockets/ListItemUpdated>` event for dispatching to event handlers.

    Attributes
    -----------
    server_id: :class:`str`
        The ID of the server that the list item is in.
    server: :class:`Server`
        The server that the list item is in.
    channel: :class:`ListChannel`
        The channel that the list item is in.
    item: :class:`ListItem`
        The list item after modification.
    """

    __gateway_event__ = 'ListItemUpdated'
    __dispatch_event__ = 'list_item_update'


class ListItemDeleteEvent(_ListItemEvent):
    """Represents a :gdocs:`ListItemDeleted <websockets/ListItemDeleted>` event for dispatching to event handlers.

    Attributes
    -----------
    server_id: :class:`str`
        The ID of the server that the list item was in.
    server: :class:`Server`
        The server that the list item was in.
    channel: :class:`ListChannel`
        The channel that the list item was in.
    item: :class:`ListItem`
        The list item that was deleted.
    """

    __gateway_event__ = 'ListItemDeleted'
    __dispatch_event__ = 'list_item_delete'


class ListItemCompleteEvent(_ListItemEvent):
    """Represents a :gdocs:`ListItemCompleted <websockets/ListItemCompleted>` event for dispatching to event handlers.

    Attributes
    -----------
    server_id: :class:`str`
        The ID of the server that the list item is in.
    server: :class:`Server`
        The server that the list item is in.
    channel: :class:`ListChannel`
        The channel that the list item is in.
    item: :class:`ListItem`
        The list item that was completed.
    """

    __gateway_event__ = 'ListItemCompleted'
    __dispatch_event__ = 'list_item_complete'


class ListItemUncompleteEvent(_ListItemEvent):
    """Represents a :gdocs:`ListItemUncompleted <websockets/ListItemUncompleted>` event for dispatching to event handlers.

    Attributes
    -----------
    server_id: :class:`str`
        The ID of the server that the list item is in.
    server: :class:`Server`
        The server that the list item is in.
    channel: :class:`ListChannel`
        The channel that the list item is in.
    item: :class:`ListItem`
        The list item that was uncompleted.
    """

    __gateway_event__ = 'ListItemUncompleted'
    __dispatch_event__ = 'list_item_uncomplete'


class MessageReactionAddEvent(ServerEvent):
    """Represents a :gdocs:`ChannelMessageReactionCreated <websockets/ChannelMessageReactionCreated>` event for dispatching to event handlers.

    Attributes
    -----------
    server_id: :class:`str`
        The ID of the server that the reaction is in.
    server: :class:`Server`
        The server that the reaction is in.
    channel: Union[:class:`ChatChannel`, :class:`VoiceChannel`, :class:`Thread`, :class:`DMChannel`]
        The channel that the reaction is in.
    message: Optional[:class:`ChatMessage`]
        The message that the reaction is on, if it is cached.
    member: Optional[:class:`Member`]
        The member that added the reaction, if they are cached.
    channel_id: :class:`str`
        The ID of the channel that the reaction is in.
    message_id: :class:`str`
        The ID of the message that the reaction is on.
    user_id: :class:`str`
        The ID of the user that added the reaction.
    emote: :class:`Emote`
        The emote that the reaction shows.
    """

    __gateway_event__ = 'ChannelMessageReactionCreated'
    __dispatch_event__ = 'message_reaction_add'
    __slots__: Tuple[str, ...] = (
        'channel_id',
        'message_id',
        'user_id',
        'emote',
        'channel',
        'message',
        'member',
    )

    def __init__(
        self,
        state,
        data: gw.ChannelMessageReactionCreatedEvent,
        /,
        channel: Union[ChatChannel, VoiceChannel, Thread, DMChannel],
    ) -> None:
        super().__init__(state, data)

        self.channel_id = data['reaction']['channelId']
        self.message_id = data['reaction']['messageId']
        self.user_id = data['reaction']['createdBy']
        self.emote = Emote(state=state, data=data['reaction']['emote'])

        self.channel = channel
        self.message: Optional[ChatMessage] = state._get_message(self.message_id)
        self.member = self.server.get_member(self.user_id)


class MessageReactionRemoveEvent(ServerEvent):
    """Represents a :gdocs:`ChannelMessageReactionDeleted <websockets/ChannelMessageReactionDeleted>` event for dispatching to event handlers.

    Attributes
    -----------
    server_id: :class:`str`
        The ID of the server that the reaction was in.
    server: :class:`Server`
        The server that the reaction was in.
    channel: Union[:class:`ChatChannel`, :class:`VoiceChannel`, :class:`Thread`, :class:`DMChannel`]
        The channel that the reaction was in.
    message: Optional[:class:`ChatMessage`]
        The message that the reaction was on, if it is cached.
    member: Optional[:class:`Member`]
        The member that added the reaction, if they are cached.
    deleted_by: Optional[:class:`Member`]
        The member that removed the reaction, if they are cached.
    channel_id: :class:`str`
        The ID of the channel that the reaction was in.
    message_id: :class:`str`
        The ID of the message that the reaction was on.
    user_id: :class:`str`
        The ID of the user that added the reaction.
    deleted_by_id: :class:`str`
        The ID of the user that removed the reaction.
    emote: :class:`Emote`
        The emote that the reaction showed.
    """

    __gateway_event__ = 'ChannelMessageReactionDeleted'
    __dispatch_event__ = 'message_reaction_remove'
    __slots__: Tuple[str, ...] = (
        'channel_id',
        'message_id',
        'user_id',
        'deleted_by_id',
        'emote',
        'channel',
        'message',
        'member',
        'deleted_by',
    )

    def __init__(
        self,
        state,
        data: gw.ChannelMessageReactionDeletedEvent,
        /,
        channel: Union[ChatChannel, VoiceChannel, Thread, DMChannel],
    ) -> None:
        super().__init__(state, data)

        self.channel_id = data['reaction']['channelId']
        self.message_id = data['reaction']['messageId']
        self.user_id = data['reaction']['createdBy']
        self.deleted_by_id = data['deletedBy']
        self.emote = Emote(state=state, data=data['reaction']['emote'])

        self.channel = channel
        self.message: Optional[ChatMessage] = state._get_message(self.message_id)
        self.member = self.server.get_member(self.user_id)
        self.deleted_by = self.server.get_member(self.deleted_by_id)


class BulkMessageReactionRemoveEvent(ServerEvent):
    """Represents a :gdocs:`ChannelMessageReactionManyDeleted <websockets/ChannelMessageReactionManyDeleted>` event for dispatching to event handlers.

    .. versionadded: 1.9

    Attributes
    -----------
    server_id: :class:`str`
        The ID of the server that the reactions were in.
    server: :class:`Server`
        The server that the reactions were in.
    channel: Union[:class:`ChatChannel`, :class:`VoiceChannel`, :class:`Thread`, :class:`DMChannel`]
        The channel that the reactions were in.
    message: Optional[:class:`ChatMessage`]
        The message that the reactions were on, if it is cached.
    channel_id: :class:`str`
        The ID of the channel that the reactions were in.
    message_id: :class:`str`
        The ID of the message that the reactions were on.
    user_id: :class:`str`
        The ID of the user that added the reaction.
    deleted_by_id: :class:`str`
        The ID of the user that removed the reactions.
    deleted_by: Optional[:class:`Member`]
        The member that removed the reactions, if they are cached.
    count: :class:`int`
        The number of reactions that were removed.
    emote: :class:`Emote`
        The emote that the reactions showed.
    """

    __gateway_event__ = 'ChannelMessageReactionManyDeleted'
    __dispatch_event__ = 'bulk_message_reaction_remove'

    __slots__: Tuple[str, ...] = (
        'channel_id',
        'message_id',
        'user_id',
        'deleted_by_id',
        'count',
        'emote',
        'channel',
        'message',
        'deleted_by',
    )

    def __init__(
        self,
        state,
        data: gw.ChannelMessageReactionManyDeletedEvent,
        /,
        channel: Union[ChatChannel, VoiceChannel, Thread, DMChannel],
    ) -> None:
        super().__init__(state, data)

        self.channel_id = data['channelId']
        self.message_id = data['messageId']
        self.deleted_by_id = data['deletedBy']
        self.count = data['count']
        self.emote = Emote(state=state, data=data['emote'])

        self.channel = channel
        self.message: Optional[ChatMessage] = state._get_message(self.message_id)
        self.deleted_by = self.server.get_member(self.deleted_by_id)
