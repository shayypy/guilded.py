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
from typing import List, Literal, TypedDict
from typing_extensions import NotRequired

from .comment import ContentComment
from .channel import Mentions


class CalendarEventCancellation(TypedDict):
    description: NotRequired[str]
    createdBy: str


class CalendarEvent(TypedDict):
    id: int
    serverId: str
    channelId: str
    name: str
    description: NotRequired[str]
    location: NotRequired[str]
    url: NotRequired[str]
    color: NotRequired[int]
    repeats: NotRequired[bool]
    rsvpLimit: NotRequired[int]
    startsAt: str
    duration: NotRequired[int]
    isPrivate: NotRequired[bool]
    mentions: NotRequired[Mentions]
    createdAt: str
    createdBy: str
    cancellation: NotRequired[CalendarEventCancellation]


class CalendarEventRsvp(TypedDict):
    calendarEventId: int
    channelId: NotRequired[str]
    serverId: str
    userId: str
    status: Literal['going', 'maybe', 'declined', 'invited', 'waitlisted', 'not responded']
    createdBy: str
    createdAt: str
    updatedBy: NotRequired[str]
    updatedAt: NotRequired[str]


class CalendarEventComment(ContentComment):
    calendarEventId: int


class RepeatInfoEvery(TypedDict):
    count: int
    interval: Literal['day', 'week', 'month', 'year']


class RepeatInfo(TypedDict):
    type: Literal['once', 'everyDay', 'everyWeek', 'everyMonth', 'custom']
    every: NotRequired[RepeatInfoEvery]
    endsAfterOccurrences: NotRequired[int]
    endDate: NotRequired[str]
    # Weekdays for type == custom and every.interval == week
    on: List[Literal['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']]
