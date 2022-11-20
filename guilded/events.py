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
from .message import ChatMessage
from .reply import ForumTopicReply
from .user import Member, MemberBan
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
    'BulkMemberXpAddEvent',
    'ServerChannelCreateEvent',
    'ServerChannelUpdateEvent',
    'ServerChannelDeleteEvent',
    'WebhookCreateEvent',
    'WebhookUpdateEvent',
    'DocCreateEvent',
    'DocUpdateEvent',
    'DocDeleteEvent',
    'CalendarEventCreateEvent',
    'CalendarEventUpdateEvent',
    'CalendarEventDeleteEvent',
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
    'ListItemCreateEvent',
    'ListItemUpdateEvent',
    'ListItemDeleteEvent',
    'ListItemCompleteEvent',
    'ListItemUncompleteEvent',
    'MessageReactionAddEvent',
    'MessageReactionRemoveEvent',
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


class _MessageReactionEvent(ServerEvent):
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
        data: gw.ChannelMessageReactionEvent,
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


class MessageReactionAddEvent(_MessageReactionEvent):
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


class MessageReactionRemoveEvent(_MessageReactionEvent):
    """Represents a :gdocs:`ChannelMessageReactionDeleted <websockets/ChannelMessageReactionDeleted>` event for dispatching to event handlers.

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

    __gateway_event__ = 'ChannelMessageReactionDeleted'
    __dispatch_event__ = 'message_reaction_remove'
