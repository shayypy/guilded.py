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
from typing import Any, Dict, List, Literal, Optional, TypedDict
from typing_extensions import NotRequired

from .announcement import Announcement, AnnouncementComment
from .calendar_event import CalendarEvent, CalendarEventComment, CalendarEventRsvp
from .channel import ServerChannel
from .doc import Doc, DocComment
from .emote import Emote
from .forum_topic import ForumTopic, ForumTopicComment
from .group import Group
from .list_item import ListItem
from .message import ChatMessage, DeletedChatMessage
from .reaction import AnnouncementCommentReaction, AnnouncementReaction, CalendarEventCommentReaction, ChannelMessageReaction, CalendarEventReaction, DocCommentReaction, DocReaction, ForumTopicCommentReaction, ForumTopicReaction
from .server import Server
from .social_link import SocialLink
from .user import ServerMember, ServerMemberBan, User
from .webhook import Webhook


class EventSkeleton(TypedDict):
    op: Literal[0, 1, 2, 8, 9]
    d: NotRequired[Dict[str, Any]]
    s: NotRequired[str]
    t: NotRequired[str]


class WelcomeEvent(TypedDict):
    lastMessageId: str
    heartbeatIntervalMs: float
    user: User


class InvalidCursorEvent(TypedDict):
    message: str


class InternalErrorEvent(TypedDict):
    message: str


class _ServerEvent(TypedDict):
    serverId: str


class ChatMessageCreatedEvent(_ServerEvent):
    message: ChatMessage


class ChatMessageUpdatedEvent(_ServerEvent):
    message: ChatMessage


class ChatMessageDeletedEvent(_ServerEvent):
    message: DeletedChatMessage


class BotServerMembershipCreatedEvent(TypedDict):
    server: Server
    createdBy: str


class BotServerMembershipDeletedEvent(TypedDict):
    server: Server
    deletedBy: str


class ServerMemberJoinedEvent(_ServerEvent):
    member: ServerMember


class ServerMemberRemovedEvent(_ServerEvent):
    userId: str
    isKick: NotRequired[bool]
    isBan: NotRequired[bool]


class ServerMemberBanEvent(_ServerEvent):
    serverMemberBan: ServerMemberBan


class UserInfo(TypedDict):
    id: str
    nickname: NotRequired[Optional[str]]


class ServerMemberUpdatedEvent(_ServerEvent):
    userInfo: UserInfo


class MemberRoleUpdate(TypedDict):
    userId: str
    roleIds: List[int]


class ServerMemberSocialLinkEvent(_ServerEvent):
    socialLink: SocialLink


class ServerRolesUpdatedEvent(_ServerEvent):
    memberRoleIds: NotRequired[List[MemberRoleUpdate]]


class ServerXpAddedEvent(_ServerEvent):
    userIds: List[str]
    amount: int


class ServerChannelEvent(_ServerEvent):
    channel: ServerChannel


class ServerWebhookEvent(_ServerEvent):
    webhook: Webhook


class AnnouncementEvent(_ServerEvent):
    announcement: Announcement


class AnnouncementReactionEvent(_ServerEvent):
    reaction: AnnouncementReaction


class AnnouncementCommentEvent(_ServerEvent):
    announcementComment: AnnouncementComment


class AnnouncementCommentReactionEvent(_ServerEvent):
    reaction: AnnouncementCommentReaction


class DocEvent(_ServerEvent):
    doc: Doc


class DocReactionEvent(_ServerEvent):
    reaction: DocReaction


class DocCommentEvent(_ServerEvent):
    docComment: DocComment


class DocCommentReactionEvent(_ServerEvent):
    reaction: DocCommentReaction


class CalendarEventEvent(_ServerEvent):
    calendarEvent: CalendarEvent


class CalendarEventReactionEvent(_ServerEvent):
    reaction: CalendarEventReaction


class CalendarEventCommentEvent(_ServerEvent):
    calendarEventComment: CalendarEventComment


class CalendarEventCommentReactionEvent(_ServerEvent):
    reaction: CalendarEventCommentReaction


class ForumTopicEvent(_ServerEvent):
    forumTopic: ForumTopic


class ForumTopicReactionEvent(_ServerEvent):
    reaction: ForumTopicReaction


class ForumTopicCommentEvent(_ServerEvent):
    forumTopicComment: ForumTopicComment


class ForumTopicCommentReactionEvent(_ServerEvent):
    reaction: ForumTopicCommentReaction


class GroupEvent(_ServerEvent):
    group: Group


class CalendarEventRsvpEvent(_ServerEvent):
    calendarEventRsvp: CalendarEventRsvp


class CalendarEventRsvpManyUpdatedEvent(_ServerEvent):
    calendarEventRsvps: List[CalendarEventRsvp]


class ListItemEvent(_ServerEvent):
    listItem: ListItem


class ChannelMessageReactionCreatedEvent(_ServerEvent):
    reaction: ChannelMessageReaction


class ChannelMessageReactionDeletedEvent(_ServerEvent):
    deletedBy: str
    reaction: ChannelMessageReaction


class ChannelMessageReactionManyDeletedEvent(_ServerEvent):
    channelId: str
    messageId: str
    deletedBy: str
    count: int
    emote: Emote
