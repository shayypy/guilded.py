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

from .calendar_event import CalendarEvent, CalendarEventRsvp
from .channel import ServerChannel
from .doc import Doc
from .forum_topic import ForumTopic
from .list_item import ListItem
from .message import ChatMessage, DeletedChatMessage
from .reaction import ChannelMessageReaction
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


class TeamMemberJoinedEvent(_ServerEvent):
    member: ServerMember


class TeamMemberRemovedEvent(_ServerEvent):
    userId: str
    isKick: NotRequired[bool]
    isBan: NotRequired[bool]


class TeamMemberBanEvent(_ServerEvent):
    serverMemberBan: ServerMemberBan


class UserInfo(TypedDict):
    id: str
    nickname: NotRequired[Optional[str]]


class TeamMemberUpdatedEvent(_ServerEvent):
    userInfo: UserInfo


class MemberRoleUpdate(TypedDict):
    userId: str
    roleIds: List[int]


class TeamRolesUpdatedEvent(_ServerEvent):
    memberRoleIds: NotRequired[List[MemberRoleUpdate]]


class TeamChannelEvent(_ServerEvent):
    channel: ServerChannel


class TeamWebhookEvent(_ServerEvent):
    webhook: Webhook


class DocEvent(_ServerEvent):
    doc: Doc


class CalendarEventEvent(_ServerEvent):
    calendarEvent: CalendarEvent


class ForumTopicEvent(_ServerEvent):
    forumTopic: ForumTopic


class CalendarEventRsvpEvent(_ServerEvent):
    calendarEventRsvp: CalendarEventRsvp


class CalendarEventRsvpManyUpdatedEvent(_ServerEvent):
    calendarEventRsvps: List[CalendarEventRsvp]


class ListItemEvent(_ServerEvent):
    listItem: ListItem


class ChannelMessageReactionEvent(_ServerEvent):
    reaction: ChannelMessageReaction
