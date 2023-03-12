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

import datetime
import re
from typing import TYPE_CHECKING, Any, AsyncIterator, Dict, Optional, List, Tuple, Union

import guilded.abc

from .asset import Asset
from .colour import Colour
from .enums import ChannelType, CustomRepeatInterval, DeleteSeriesType, FileType, RSVPStatus, RepeatInterval, Weekday, try_enum
from .group import Group
from .message import HasContentMixin
from .mixins import Hashable
from .reply import CalendarEventReply, DocReply, ForumTopicReply
from .user import Member
from .utils import GUILDED_EPOCH_DATETIME, MISSING, ISO8601, Object
from .status import Game

if TYPE_CHECKING:
    from .types.calendar_event import (
        CalendarEvent as CalendarEventPayload,
        CalendarEventRsvp as CalendarEventRsvpPayload,
        RepeatInfo as RepeatInfoPayload,
    )
    from .types.doc import Doc as DocPayload
    from .types.list_item import (
        ListItem as ListItemPayload,
        ListItemNote as ListItemNotePayload,
    )
    from .types.forum_topic import ForumTopic as ForumTopicPayload

    from .emote import Emote
    from .server import Server
    from .user import User
    from .webhook import Webhook


__all__ = (
    'Announcement',
    'AnnouncementChannel',
    'Availability',
    'CalendarChannel',
    'CalendarEvent',
    'CalendarEventRSVP',
    'ChatChannel',
    'DMChannel',
    'Doc',
    'DocsChannel',
    'ForumChannel',
    'ForumTopic',
    'Media',
    'MediaChannel',
    'ListChannel',
    'ListItem',
    'ListItemNote',
    'PartialMessageable',
    'RepeatInfo',
    'SchedulingChannel',
    'TextChannel',
    'Thread',
    'VoiceChannel',
)


class CalendarChannel(guilded.abc.ServerChannel):
    """Represents a calendar channel in a :class:`.Server`."""
    def __init__(self, **fields):
        super().__init__(**fields)
        self.type = ChannelType.calendar

    async def create_event(
        self,
        *,
        name: str,
        starts_at: Optional[datetime.datetime],
        duration: Optional[Union[datetime.timedelta, int]],
        description: Optional[str] = MISSING,
        location: Optional[str] = MISSING,
        url: Optional[str] = MISSING,
        colour: Optional[Union[Colour, int]] = MISSING,
        color: Optional[Union[Colour, int]] = MISSING,
        rsvp_limit: Optional[int] = MISSING,
        private: bool = MISSING,
        repeat: Optional[Union[RepeatInterval, RepeatInfo]] = MISSING,
    ) -> CalendarEvent:
        """|coro|

        Create an event in this channel.

        Parameters
        -----------
        name: :class:`str`
            The name of the event.
        starts_at: :class:`datetime.datetime`
            When the event starts.
        duration: Union[:class:`datetime.timedelta`, :class:`int`]
            The duration of the event.
            If this is an :class:`int`, the value must be in minutes.
        description: Optional[:class:`str`]
            The description of the event.
        location: Optional[:class:`str`]
            The location of the event.
        url: Optional[:class:`str`]
            A URL to associate with the event.
        colour: Optional[Union[:class:`.Colour`, :class:`int`]]
            The colour of the event when viewing in the channel.
            This parameter is also aliased to ``color``.
        rsvp_limit: Optional[:class:`int`]
            The number of RSVPs to allow before waitlisting.

            .. versionadded:: 1.7
        private: Optional[:class:`bool`]
            Whether the event should be private.
        repeat: Optional[Union[:class:`RepeatInterval`, :class:`RepeatInfo`]]
            A basic interval for repeating the event or a :class:`RepeatInfo`
            for more detailed repeat options.

            .. versionadded:: 1.7

        Returns
        --------
        :class:`.CalendarEvent`
            The created event.

        Raises
        -------
        Forbidden
            You do not have permissions to create events.
        HTTPException
            Failed to create the event.
        """

        payload = {
            'name': name,
        }

        if description is not MISSING:
            payload['description'] = description

        if location is not MISSING:
            payload['location'] = location

        if starts_at is not MISSING:
            if starts_at is not None:
                starts_at = self._state.valid_ISO8601(starts_at)

            payload['startsAt'] = starts_at

        if url is not MISSING:
            payload['url'] = url

        if colour is not MISSING or color is not MISSING:
            if colour is MISSING:
                colour = color
            if isinstance(colour, Colour):
                colour = colour.value

            payload['color'] = colour

        if duration is not MISSING:
            if isinstance(duration, datetime.timedelta):
                duration = duration.seconds / 60

            payload['duration'] = duration

        if private is not MISSING:
            payload['isPrivate'] = private

        if rsvp_limit is not MISSING:
            payload['rsvpLimit'] = rsvp_limit

        if repeat is not MISSING:
            if isinstance(repeat, RepeatInterval):
                payload['repeatInfo'] = RepeatInfo(repeat).to_dict()
            elif isinstance(repeat, RepeatInfo):
                payload['repeatInfo'] = repeat.to_dict()

        data = await self._state.create_calendar_event(self.id, payload=payload)
        event = CalendarEvent(state=self._state, data=data['calendarEvent'], channel=self)
        return event

    async def fetch_event(self, event_id: int, /) -> CalendarEvent:
        """|coro|

        Fetch an event in this channel from the API.

        Returns
        --------
        :class:`.CalendarEvent`
            The event from the ID.

        Raises
        -------
        NotFound
            There is no event with the ID.
        Forbidden
            You do not have permissions to get events in this channel.
        HTTPException
            Failed to get the event.
        """

        data = await self._state.get_calendar_event(self.id, event_id)
        event = CalendarEvent(state=self._state, data=data['calendarEvent'], channel=self)
        return event

    async def events(
        self,
        limit: Optional[int] = 25,
        after: Optional[Union[datetime.datetime, CalendarEvent]] = None,
        before: Optional[Union[datetime.datetime, CalendarEvent]] = None,
    ) -> AsyncIterator[CalendarEvent]:
        """An :term:`asynchronous iterator` for the events in this channel.

        Results are ordered ascending by :attr:`.CalendarEvent.starts_at`.

        Examples
        ---------

        Usage ::

            async for event in channel.events():
                print(f'{event} starts at {event.starts_at}')

        Flattening into a list ::

            events = [event async for event in channel.events()]
            # events is now a list of CalendarEvent

        Parameters
        -----------
        limit: Optional[:class:`int`]
            The maximum number of events to return.
            Defaults to 25 if not specified.
        before: Optional[Union[:class:`.CalendarEvent`, :class:`datetime.datetime`]]
            The event to stop pagination at.
        after: Optional[Union[:class:`.CalendarEvent`, :class:`datetime.datetime`]]
            The event to begin pagination at.

        Yields
        -------
        :class:`.CalendarEvent`
            An event in this channel.

        Raises
        -------
        Forbidden
            You do not have permissions to get events in this channel.
        HTTPException
            Failed to get the events.
        """

        if isinstance(before, CalendarEvent):
            before = before.starts_at
        if isinstance(after, CalendarEvent):
            after = after.starts_at

        while True:
            sublimit = min(500 if limit is None else limit, 500)
            if sublimit < 1:
                return

            data = await self._state.get_calendar_events(
                self.id,
                limit=sublimit,
                before=before,
                after=after,
            )
            data = data['calendarEvents']

            # Adjust sublimit according to how much data is left
            if len(data) < 500:
                limit = 0
            else:
                limit -= len(data)

            for event_data in data:
                yield CalendarEvent(state=self._state, data=event_data, channel=self)


class CalendarEvent(Hashable, HasContentMixin):
    """Represents an event in a :class:`CalendarChannel`.

    .. container:: operations

        .. describe:: x == y

            Checks if two events are equal.

        .. describe:: x != y

            Checks if two events are not equal.

        .. describe:: hash(x)

            Returns the hash of the event.

        .. describe:: str(x)

            Returns the name of the event.

        .. describe:: x < y

            Checks if an event starts before another event.

        .. describe:: x > y

            Checks if an event starts after another event.

        .. describe:: x <= y

            Checks if an event starts before or at the same time as another event.

        .. describe:: x >= y

            Checks if an event starts after or at the same time as another event.

    .. versionadded:: 1.2

    Attributes
    -----------
    id: :class:`int`
        The event's ID.
    name: :class:`str`
        The event's name.
    description: Optional[:class:`str`]
        The event's description.
    channel: :class:`.CalendarChannel`
        The channel that the event is in.
    created_at: :class:`datetime.datetime`
        When the event was created.
    starts_at: Optional[:class:`datetime.datetime`]
        When the event starts.
    location: Optional[:class:`str`]
        The location of the event.
    url: Optional[:class:`str`]
        A URL to associate with the event.
        This is not an in-app share link, but rather something that is set by
        users while creating the event.
    private: :class:`bool`
        Whether the event is private.
    repeats: :class:`bool`
        Whether the event is set to repeat.

        .. versionadded:: 1.7
    series_id: Optional[:class:`str`]
        The ID of the event series, if applicable.

        .. versionadded:: 1.8
        .. versionadded:: 1.8
    rsvp_limit: Optional[:class:`int`]
        The number of RSVPs to allow before waitlisting RSVPs.

        .. versionadded:: 1.7
    duration: Optional[:class:`datetime.timedelta`]
        The duration of the event. Minimum 60 seconds.
    cancellation_description: Optional[:class:`str`]
        The description of the event cancellation, if any.

        There is an alias for this attribute called :attr:`.cancelation_description`.
    """

    __slots__: Tuple[str, ...] = (
        '_state',
        'channel',
        'id',
        'server_id',
        'channel_id',
        'author_id',
        'name',
        'description',
        '_mentions',
        'location',
        'url',
        'starts_at',
        'created_at',
        'private',
        'repeats',
        'series_id',
        'rsvp_limit',
        '_colour',
        'duration',
        'cancellation_description',
        'cancelled_by_id',
    )

    def __init__(self, *, state, data: CalendarEventPayload, channel: CalendarChannel):
        super().__init__()
        self._state = state
        self.channel = channel

        self.id = data['id']
        self.server_id = data.get('serverId')
        self.channel_id = data.get('channelId')
        self.author_id = data.get('createdBy')

        self.name = data.get('name')
        self.description = data.get('description')
        self._mentions = self._create_mentions(data.get('mentions'))
        self._extract_attachments(self.description)

        self.location = data.get('location')
        self.url = data.get('url')
        self.starts_at: datetime.datetime = ISO8601(data.get('startsAt'))
        self.created_at: datetime.datetime = ISO8601(data.get('createdAt'))
        self.private = data.get('isPrivate') or False
        self.repeats = data.get('repeats') or False
        self.rsvp_limit = data.get('rsvpLimit')
        self._colour = data.get('color')

        self.duration: Optional[datetime.timedelta]
        _duration = data.get('duration')  # minutes
        if _duration is not None:
            self.duration = datetime.timedelta(minutes=_duration)
        else:
            self.duration = None

        _cancellation = data.get('cancellation') or {}
        self.cancellation_description = _cancellation.get('description')
        self.cancelled_by_id = _cancellation.get('createdBy')

    def __repr__(self) -> str:
        return f'<CalendarEvent id={self.id!r} name={self.name!r} channel={self.channel!r}>'

    def __str__(self) -> str:
        return self.name

    def __lt__(self, other) -> bool:
        return isinstance(other, CalendarEvent) and self.starts_at < other.starts_at

    def __le__(self, other) -> bool:
        return isinstance(other, CalendarEvent) and self.starts_at <= other.starts_at

    def __gt__(self, other) -> bool:
        return isinstance(other, CalendarEvent) and self.starts_at > other.starts_at

    def __ge__(self, other) -> bool:
        return isinstance(other, CalendarEvent) and self.starts_at >= other.starts_at

    @property
    def server(self) -> Server:
        """:class:`.Server`: The server that the event is in."""
        return self._state._get_server(self.server_id) or self.channel.server

    @property
    def guild(self) -> Server:
        """:class:`.Server`: |dpyattr|

        This is an alias of :attr:`.server`.

        The server that the event is in.
        """
        return self.server

    @property
    def group(self) -> Optional[Group]:
        """:class:`.Group`: The group that the event is in."""
        return self.channel.group

    @property
    def author(self) -> Optional[Member]:
        """Optional[:class:`.Member`]: The member that created the event."""
        return self.server.get_member(self.author_id)

    @property
    def colour(self) -> Optional[Colour]:
        """Optional[:class:`.Colour`]: The colour of the event when viewing in the channel."""
        return Colour(self._colour) if self._colour is not None else None

    color = colour

    @property
    def cancelation_description(self) -> Optional[str]:
        """Optional[:class:`str`]: The description of the event cancelation, if any.

        There is an alias for this attribute called :attr:`.cancellation_description`.
        """
        return self.cancellation_description

    @property
    def cancelled_by(self) -> Optional[Member]:
        """Optional[:class:`.Member`]: The member that cancelled the event, if applicable.

        There is an alias for this attribute called :attr:`.canceled_by`.
        """
        return self.server.get_member(self.cancelled_by_id)

    @property
    def canceled_by(self) -> Optional[Member]:
        """Optional[:class:`.Member`]: The member that canceled the event, if applicable.

        There is an alias for this attribute called :attr:`.cancelled_by`.
        """
        return self.server.get_member(self.cancelled_by_id)

    @property
    def share_url(self) -> str:
        return f'{self.channel.share_url}/{self.id}'

    async def edit(
        self,
        *,
        name: str = MISSING,
        description: Optional[str] = MISSING,
        location: Optional[str] = MISSING,
        starts_at: Optional[datetime.datetime] = MISSING,
        url: Optional[str] = MISSING,
        colour: Optional[Union[Colour, int]] = MISSING,
        color: Optional[Union[Colour, int]] = MISSING,
        duration: Optional[Union[datetime.timedelta, int]] = MISSING,
        rsvp_limit: Optional[int] = MISSING,
        private: bool = MISSING,
        repeat: Optional[Union[RepeatInterval, RepeatInfo]] = MISSING,
        edit_series: bool = MISSING,
    ) -> CalendarEvent:
        """|coro|

        Edit this event.

        All parameters are optional.

        Parameters
        -----------
        name: :class:`str`
            The name of the event.
        description: :class:`str`
            The description of the event.
        location: :class:`str`
            The location of the event.
        starts_at: :class:`datetime.datetime`
            When the event starts.
        url: :class:`str`
            A URL to associate with the event.
        colour: Union[:class:`.Colour`, :class:`int`]
            The colour of the event when viewing in the channel.
            This parameter is also aliased to ``color``.
        duration: Union[:class:`datetime.timedelta`, :class:`int`]
            The duration of the event.
            If this is an :class:`int`, the value must be in minutes.
        rsvp_limit: Optional[:class:`int`]
            The number of RSVPs to allow before waitlisting.

            .. versionadded:: 1.7
        private: :class:`bool`
            Whether the event should be private.
        repeat: Optional[Union[:class:`RepeatInterval`, :class:`RepeatInfo`]]
            A basic interval for repeating the event or a :class:`RepeatInfo`
            for more detailed repeat options.

            .. versionadded:: 1.7
        edit_series: :class:`bool`
            Whether to also edit all future events in the series, if
            applicable.

            .. versionadded:: 1.7

        Returns
        --------
        :class:`.CalendarEvent`
            The newly edited event.

        Raises
        -------
        NotFound
            The event has been deleted.
        Forbidden
            You do not have permissions to edit the event.
        HTTPException
            Failed to edit the event.
        """

        payload = {}

        if name is not MISSING:
            payload['name'] = name

        if description is not MISSING:
            payload['description'] = description

        if location is not MISSING:
            payload['location'] = location

        if starts_at is not MISSING:
            if starts_at is not None:
                starts_at = self._state.valid_ISO8601(starts_at)

            payload['startsAt'] = starts_at

        if url is not MISSING:
            payload['url'] = url

        if colour is not MISSING or color is not MISSING:
            if colour is MISSING:
                colour = color
            if isinstance(colour, Colour):
                colour = colour.value

            payload['color'] = colour

        if duration is not MISSING:
            if isinstance(duration, datetime.timedelta):
                duration = duration.seconds / 60

            payload['duration'] = duration

        if private is not MISSING:
            payload['isPrivate'] = private

        if rsvp_limit is not MISSING:
            payload['rsvpLimit'] = rsvp_limit

        if repeat is not MISSING:
            if isinstance(repeat, RepeatInterval):
                payload['repeatInfo'] = RepeatInfo(repeat).to_dict()
            elif isinstance(repeat, RepeatInfo):
                payload['repeatInfo'] = repeat.to_dict()
            else:
                payload['repeatInfo'] = None

        if edit_series is not MISSING:
            payload['editSeries'] = edit_series

        data = await self._state.update_calendar_event(self.channel.id, self.id, payload=payload)
        event = CalendarEvent(state=self._state, data=data['calendarEvent'], channel=self.channel)
        return event

    async def delete(self, *, series: Optional[DeleteSeriesType] = None) -> None:
        """|coro|

        Delete this event.

        Parameters
        -----------
        series: Optional[:class:`DeleteSeriesType`]
            If the event is part of a series (i.e. :attr:`.repeats` is
            ``True``), sets whether to delete all events in the series or only
            this one and its subsequent events.
            If ``None`` or not provided, only this event will be deleted.

            .. versionadded:: 1.7

        Raises
        -------
        NotFound
            The event has already been deleted.
        Forbidden
            You do not have permissions to delete the event.
        HTTPException
            Failed to delete the event.
        """

        await self._state.delete_calendar_event(
            self.channel.id,
            self.id,
            delete_series=series.value if series else None,
        )

    async def create_rsvp(
        self,
        user: guilded.abc.User,
        /,
        *,
        status: RSVPStatus,
    ) -> CalendarEventRSVP:
        """|coro|

        Create an RSVP for a user.

        This method can also be used for editing an existing RSVP, which may
        be preferable if all you need to do is edit it.

        Parameters
        -----------
        user: :class:`~.abc.User`
            The user to create an RSVP for.
        status: :class:`.RSVPStatus`
            The status of the RSVP.

        Returns
        --------
        :class:`.CalendarEventRSVP`
            The newly created RSVP.

        Raises
        -------
        Forbidden
            You do not have permissions to create an RSVP for another user.
        HTTPException
            Failed to create an RSVP.
        """

        payload = {
            'status': status.value,
        }

        data = await self._state.put_calendar_event_rsvp(
            self.channel_id,
            self.id,
            user.id,
            payload=payload,
        )
        rsvp = CalendarEventRSVP(data=data['calendarEventRsvp'], event=self)
        return rsvp

    async def fetch_rsvp(self, user: guilded.abc.User, /) -> CalendarEventRSVP:
        """|coro|

        Fetch a user's RSVP to this event.

        Returns
        --------
        :class:`.CalendarEventRSVP`
            The user's RSVP.

        Raises
        -------
        NotFound
            This user does not have an RSVP for this event.
        HTTPException
            Failed to fetch this user's RSVP.
        """

        data = await self._state.get_calendar_event_rsvp(self.channel_id, self.id, user.id)
        rsvp = CalendarEventRSVP(data=data['calendarEventRsvp'], event=self)
        return rsvp

    async def fetch_rsvps(self) -> List[CalendarEventRSVP]:
        """|coro|

        Fetch all RSVPs to this event.

        Returns
        --------
        :class:`.CalendarEventRSVP`
            A user's RSVP.

        Raises
        -------
        HTTPException
            Failed to fetch the RSVPs.
        """

        rsvps = []
        data = await self._state.get_calendar_event_rsvps(self.channel_id, self.id)
        for rsvp_data in data['calendarEventRsvps']:
            rsvp = CalendarEventRSVP(data=rsvp_data, event=self)
            rsvps.append(rsvp)

        return rsvps

    async def add_reaction(self, emote: Emote, /) -> None:
        """|coro|

        Add a reaction to this event.

        .. versionadded:: 1.7

        Parameters
        -----------
        emote: :class:`.Emote`
            The emote to add.
        """
        emote_id: int = getattr(emote, 'id', emote)
        await self._state.add_calendar_event_reaction_emote(self.channel_id, self.id, emote_id)

    async def remove_self_reaction(self, emote: Emote, /) -> None:
        """|coro|

        Remove one of your reactions from this event.

        .. versionadded:: 1.7

        Parameters
        -----------
        emote: :class:`.Emote`
            The emote to remove.
        """
        emote_id: int = getattr(emote, 'id', emote)
        await self._state.remove_calendar_event_reaction_emote(self.channel_id, self.id, emote_id)

    async def reply(self, content: str) -> CalendarEventReply:
        """|coro|

        Reply to this event.

        .. versionadded:: 1.7

        Parameters
        -----------
        content: :class:`str`
            The content of the reply.

        Returns
        --------
        :class:`CalendarEventReply`
            The created reply.

        Raises
        -------
        NotFound
            This event does not exist.
        Forbidden
            You do not have permission to reply to this event.
        HTTPException
            Failed to reply to this event.
        """

        data = await self._state.create_calendar_event_comment(self.channel_id, self.id, content=content)
        return CalendarEventReply(state=self._state, data=data['calendarEventComment'], parent=self)

    async def fetch_reply(self, reply_id: int, /) -> CalendarEventReply:
        """|coro|

        Fetch a reply to this event.

        .. versionadded:: 1.7

        Returns
        --------
        :class:`CalendarEventReply`
            The reply from the ID.

        Raises
        -------
        NotFound
            This reply or topic does not exist.
        Forbidden
            You do not have permission to read this event's replies.
        HTTPException
            Failed to fetch the reply.
        """

        data = await self._state.get_calendar_event_comment(self.channel_id, self.id, reply_id)
        return CalendarEventReply(state=self._state, data=data['calendarEventComment'], parent=self)

    async def fetch_replies(self) -> List[CalendarEventReply]:
        """|coro|

        Fetch all replies to this event.

        .. versionadded:: 1.7

        Returns
        --------
        List[:class:`CalendarEventReply`]
            The replies under the event.

        Raises
        -------
        NotFound
            This event does not exist.
        Forbidden
            You do not have permission to read this event's replies.
        HTTPException
            Failed to fetch the replies to this event.
        """

        data = await self._state.get_calendar_event_comments(self.channel_id, self.id)
        return [
            CalendarEventReply(state=self._state, data=reply_data, parent=self)
            for reply_data in data['calendarEventComments']
        ]


class RepeatInfo:
    """Represents simplified repeat info for a calendar event.

    .. versionadded:: 1.7

    Attributes
    -----------
    type: Union[:class:`RepeatInterval`, :class:`CustomRepeatInterval`]
        The type of interval for the repeating event.
        Custom intervals are able to specify additional details.
        Otherwise, the event will repeat for 180 days.
    interval_count: Optional[:class:`int`]
        How often the event should repeat between the interval.
        E.g., A value of ``1`` with a ``type`` of :attr:`CustomRepeatInterval.daily` would be once per day,
        and a value of ``2`` with a ``type`` of :attr:`CustomRepeatInterval.daily` would be once per two days.
        Defaults to ``1`` if applicable and not specified.
    end_after_count: Optional[:class:`int`]
        The maximum number of repeats for the event.
        If used with :attr:`.end_at`, the earliest end date of the two is used.
    end_at: Optional[:class:`datetime.datetime`]
        The timestamp at which the event should stop repeating.
        If used with :attr:`.end_after_count`, the earliest end date of the two is used.
    weekdays: Optional[List[:class:`Weekday`]]
        The days of the week that the event should repeat on.
        Only applicable for type :attr:`CustomRepeatInterval.weekly`.
    """

    __slots__: Tuple[str, ...] = (
        'type',
        'interval_count',
        'end_after_count',
        'end_at',
        'weekdays',
    )

    def __init__(
        self,
        type: Union[RepeatInterval, CustomRepeatInterval],
        *,
        interval_count: Optional[int] = None,
        end_after_count: Optional[int] = None,
        end_at: Optional[datetime.datetime] = None,
        weekdays: Optional[List[Weekday]] = None,
    ):
        self.type: Union[RepeatInterval, CustomRepeatInterval] = type
        self.interval_count: Optional[int] = interval_count
        if isinstance(self.type, CustomRepeatInterval) and self.interval_count is None:
            # Default to once per interval for custom repeats if not specified
            self.interval_count = 1

        self.end_after_count: Optional[int] = end_after_count
        self.end_at: Optional[datetime.datetime] = end_at
        self.weekdays: Optional[List[Weekday]] = weekdays

    @classmethod
    def from_dict(cls, data: RepeatInfoPayload):
        custom = data['type'] == 'custom'
        return cls(
            try_enum(
                CustomRepeatInterval if custom else RepeatInterval,
                data['every']['interval'] if custom else data['type']
            ),
            interval_count=data.get('every', {}).get('count'),
            end_after_count=data.get('endsAfterOccurrences'),
            end_at=ISO8601(data.get('endDate')),
            weekdays=[try_enum(Weekday, weekday) for weekday in data['on']] if data.get('on') else None,
        )

    def to_dict(self) -> RepeatInfoPayload:
        type: RepeatInterval = RepeatInterval.custom if isinstance(self.type, CustomRepeatInterval) else self.type
        custom_type: Optional[CustomRepeatInterval] = self.type if isinstance(self.type, CustomRepeatInterval) else None

        data = {
            'type': type.value,
        }

        if custom_type and self.interval_count is not None:
            data['every'] = {
                'interval': custom_type.value,
                'count': self.interval_count,
            }

        if self.end_after_count is not None:
            data['endsAfterOccurrences'] = self.end_after_count

        if self.end_at is not None:
            data['endDate'] = self.end_at.isoformat()

        if self.weekdays:
            data['on'] = [weekday.value for weekday in self.weekdays]

        return data


class CalendarEventRSVP:
    """Represents an RSVP to a :class:`CalendarEvent`.

    .. container:: operations

        .. describe:: x == y

            Checks if two RSVPs are equal.

        .. describe:: x != y

            Checks if two RSVPs are not equal.

    .. versionadded:: 1.2

    Attributes
    -----------
    event: :class:`.CalendarEvent`
        The event that the RSVP is for.
    channel_id: Optional[:class:`str`]
        The ID of the channel that the RSVP's event is in.
    server_id: :class:`str`
        The ID of the server that the RSVP's event is in.
    user_id: :class:`str`
        The ID of the user that the RSVP is for.
    status: :class:`.RSVPStatus`
        The status of the RSVP.
    created_at: :class:`datetime.datetime`
        When the RSVP was created.
    updated_at: :class:`datetime.datetime`
        When the RSVP was last updated.
    """

    __slots__: Tuple[str, ...] = (
        'event',
        'server_id',
        'channel_id',
        'user_id',
        'author_id',
        'updated_by_id',
        'status',
        'created_at',
        'updated_at',
    )

    def __init__(self, *, data: CalendarEventRsvpPayload, event: CalendarEvent):
        super().__init__()
        self.event = event

        self.server_id = data.get('serverId')
        self.channel_id = data.get('channelId')
        self.user_id = data.get('userId')
        self.author_id = data.get('createdBy')
        self.updated_by_id = data.get('updatedBy')

        self.status: RSVPStatus = try_enum(RSVPStatus, data.get('status'))
        self.created_at: datetime.datetime = ISO8601(data.get('createdAt'))
        self.updated_at: Optional[datetime.datetime] = ISO8601(data.get('updatedAt'))

    def __repr__(self) -> str:
        return f'<CalendarEventRSVP user_id={self.user_id!r} status={self.status!r} event={self.event!r}>'

    def __eq__(self, other) -> bool:
        return isinstance(other, CalendarEventRSVP) and self.event == other.event and self.user_id == other.user_id

    @property
    def channel(self) -> CalendarChannel:
        """:class:`.CalendarChannel`: The channel that the RSVP's event is in."""
        return self.event._state._get_server_channel(self.server_id, self.channel_id) or self.event.channel

    @property
    def server(self) -> Server:
        """:class:`.Server`: The server that the RSVP's event is in."""
        return self.event._state._get_server(self.server_id) or self.event.server

    @property
    def guild(self) -> Server:
        """:class:`.Server`: |dpyattr|

        This is an alias of :attr:`.server`.

        The server that the RSVP's event is in.
        """
        return self.server

    @property
    def group(self) -> Optional[Group]:
        """:class:`.Group`: The group that the event is in."""
        return self.channel.group

    @property
    def author(self) -> Optional[Member]:
        """Optional[:class:`.Member`]: The member that created the RSVP."""
        return self.server.get_member(self.author_id)

    @property
    def updated_by(self) -> Optional[Member]:
        """Optional[:class:`.Member`]: The member that last updated the RSVP."""
        return self.server.get_member(self.updated_by_id)

    @property
    def member(self) -> Member:
        """:class:`.Member`: The member that the RSVP is for."""
        return self.server.get_member(self.user_id)

    async def edit(
        self,
        *,
        status: RSVPStatus,
    ) -> CalendarEventRSVP:
        """|coro|

        Edit this RSVP.

        Parameters
        -----------
        status: :class:`.RSVPStatus`
            The status of the RSVP.

        Returns
        --------
        :class:`.CalendarEventRSVP`
            The newly edited RSVP.

        Raises
        -------
        Forbidden
            You do not have permissions to edit this RSVP.
        NotFound
            This RSVP was deleted.
        HTTPException
            Failed to edit this RSVP.
        """
        return await self.event.create_rsvp(
            Object(self.user_id),
            status=status,
        )

    async def delete(self) -> None:
        """|coro|

        Delete this RSVP.

        Raises
        -------
        Forbidden
            You do not have permissions to delete this RSVP.
        NotFound
            This RSVP was already deleted.
        HTTPException
            Failed to delete this RSVP.
        """
        await self.event._state.delete_calendar_event_rsvp(self.channel_id, self.event.id, self.user_id)


class ChatChannel(guilded.abc.ServerChannel, guilded.abc.Messageable):
    """Represents a chat channel in a :class:`.Server`."""
    def __init__(self, **fields):
        super().__init__(**fields)
        self.type = ChannelType.chat
        self._channel_id = self.id

    async def create_webhook(self, *, name: str) -> Webhook:
        """|coro|

        Create a webhook in this channel.

        Parameters
        -----------
        name: :class:`str`
            The webhook's name.

        Returns
        --------
        :class:`Webhook`
            The created webhook.

        Raises
        -------
        HTTPException
            Creating the webhook failed.
        Forbidden
            You do not have permissions to create a webhook.
        """

        webhook = await self.server.create_webhook(
            channel=self,
            name=name,
        )
        return webhook

    async def webhooks(self) -> List[Webhook]:
        """|coro|

        Fetch the list of webhooks in this channel.

        .. warning::

            This endpoint cannot be paginated.

        Returns
        --------
        List[:class:`Webhook`]
            The webhooks in this channel.

        Raises
        -------
        Forbidden
            You do not have permissions to get the webhooks.
        """

        webhooks = await self.server.webhooks(channel=self)
        return webhooks

TextChannel = ChatChannel  # discord.py


class Doc(Hashable, HasContentMixin):
    """Represents a doc in a :class:`DocsChannel`.

    .. container:: operations

        .. describe:: x == y

            Checks if two docs are equal.

        .. describe:: x != y

            Checks if two docs are not equal.

        .. describe:: hash(x)

            Returns the hash of the doc.

        .. describe:: str(x)

            Returns the title of the doc.

    Attributes
    -----------
    id: :class:`int`
        The doc's ID.
    title: :class:`str`
        The doc's title.
    content: :class:`str`
        The doc's text content.
    channel: :class:`.DocsChannel`
        The channel that the doc is in.
    created_at: :class:`datetime.datetime`
        When the doc was created.
    updated_at: Optional[:class:`datetime.datetime`]
        When the doc was last modified.
    """

    __slots__: Tuple[str, ...] = (
        '_state',
        'channel',
        'server_id',
        'channel_id',
        'id',
        'title',
        'content',
        '_mentions',
        'author_id',
        'created_at',
        'updated_by_id',
        'updated_at',
    )

    def __init__(self, *, state, data: DocPayload, channel: DocsChannel):
        super().__init__()
        self._state = state

        self.channel = channel
        self.server_id: str = data.get('serverId')
        self.channel_id: str = data.get('channelId')

        self.id: int = data['id']
        self.title: str = data['title']
        self.content: str = data['content']
        self._mentions = self._create_mentions(data.get('mentions'))
        self._extract_attachments(self.content)

        self.author_id: str = data.get('createdBy')
        self.created_at: datetime.datetime = ISO8601(data.get('createdAt'))

        self.updated_by_id: Optional[str] = data.get('updatedBy')
        self.updated_at: Optional[datetime.datetime] = ISO8601(data.get('updatedAt'))

    def __repr__(self) -> str:
        return f'<Doc id={self.id!r} title={self.title!r} channel={self.channel!r}>'

    def __str__(self) -> str:
        return self.title

    @property
    def server(self) -> Server:
        """:class:`.Server`: The server that the doc is in."""
        return self._state._get_server(self.server_id)

    @property
    def guild(self) -> Server:
        """:class:`.Server`: |dpyattr|

        This is an alias of :attr:`.server`.

        The server that the doc is in.
        """
        return self.server

    @property
    def group(self) -> Group:
        """Optional[:class:`.Group`]: The group that the doc is in."""
        return self.channel.group

    @property
    def author(self) -> Optional[Member]:
        """Optional[:class:`.Member`]: The :class:`.Member` that created the doc."""
        return self.server.get_member(self.author_id)

    @property
    def updated_by(self) -> Optional[Member]:
        """Optional[:class:`.Member`]: The :class:`.Member` that last updated the doc."""
        return self.server.get_member(self.updated_by_id)

    async def add_reaction(self, emote: Emote, /) -> None:
        """|coro|

        Add a reaction to this doc.

        Parameters
        -----------
        emote: :class:`.Emote`
            The emote to add.
        """
        emote_id: int = getattr(emote, 'id', emote)
        await self._state.add_doc_reaction_emote(self.channel.id, self.id, emote_id)

    async def remove_self_reaction(self, emote: Emote, /) -> None:
        """|coro|

        Remove one of your reactions from this doc.

        Parameters
        -----------
        emote: :class:`.Emote`
            The emote to remove.
        """
        emote_id: int = getattr(emote, 'id', emote)
        await self._state.remove_doc_reaction_emote(self.channel.id, self.id, emote_id)

    async def delete(self) -> None:
        """|coro|

        Delete this doc.
        """
        await self._state.delete_doc(self.channel.id, self.id)

    async def edit(
        self,
        *,
        title: str = MISSING,
        content: str = MISSING,
    ) -> Doc:
        """|coro|

        Edit this doc.

        Parameters
        -----------
        title: :class:`str`
            The title of the doc.
        content: :class:`str`
            The content of the doc.

        Returns
        --------
        :class:`.Doc`
            The updated doc.
        """

        payload = {
            'title': title if title is not MISSING else self.title,
            'content': content if content is not MISSING else self.content,
        }

        data = await self._state.update_doc(self.channel.id, self.id, payload=payload)
        doc = Doc(data=data, channel=self.channel, state=self._state)
        return doc

    async def reply(self, content: str) -> DocReply:
        """|coro|

        Reply to this doc.

        .. versionadded:: 1.7

        Parameters
        -----------
        content: :class:`str`
            The content of the reply.

        Returns
        --------
        :class:`DocReply`
            The created reply.

        Raises
        -------
        NotFound
            This doc does not exist.
        Forbidden
            You do not have permission to reply to this doc.
        HTTPException
            Failed to reply to this doc.
        """

        data = await self._state.create_doc_comment(self.channel_id, self.id, content=content)
        return DocReply(state=self._state, data=data['docComment'], parent=self)

    async def fetch_reply(self, reply_id: int, /) -> DocReply:
        """|coro|

        Fetch a reply to this doc.

        .. versionadded:: 1.7

        Returns
        --------
        :class:`DocReply`
            The reply from the ID.

        Raises
        -------
        NotFound
            This reply or topic does not exist.
        Forbidden
            You do not have permission to read this doc's replies.
        HTTPException
            Failed to fetch the reply.
        """

        data = await self._state.get_doc_comment(self.channel_id, self.id, reply_id)
        return DocReply(state=self._state, data=data['docComment'], parent=self)

    async def fetch_replies(self) -> List[DocReply]:
        """|coro|

        Fetch all replies to this doc.

        .. versionadded:: 1.7

        Returns
        --------
        List[:class:`DocReply`]
            The replies under the doc.

        Raises
        -------
        NotFound
            This doc does not exist.
        Forbidden
            You do not have permission to read this doc's replies.
        HTTPException
            Failed to fetch the replies to this doc.
        """

        data = await self._state.get_doc_comments(self.channel_id, self.id)
        return [
            DocReply(state=self._state, data=reply_data, parent=self)
            for reply_data in data['docComments']
        ]


class DocsChannel(guilded.abc.ServerChannel):
    """Represents a docs channel in a :class:`.Server`."""
    def __init__(self, **fields):
        super().__init__(**fields)
        self.type = ChannelType.docs
        self._docs = {}

    @property
    def docs(self) -> List[Doc]:
        """List[:class:`.Doc`]: The list of docs in this channel."""
        return list(self._docs.values())

    def get_doc(self, doc_id: int, /) -> Optional[Doc]:
        """Optional[:class:`.Doc`]: Get a doc in this channel."""
        return self._docs.get(doc_id)

    async def getch_doc(self, doc_id: int, /) -> Doc:
        return self.get_doc(doc_id) or await self.fetch_doc(doc_id)

    async def create_doc(
        self,
        *,
        title: str,
        content: str,
    ) -> Doc:
        """|coro|

        Create a new doc in this channel.

        Parameters
        -----------
        title: :class:`str`
            The doc's title.
        content: :class:`str`
            The content to create the doc with.

        Returns
        --------
        :class:`.Doc`
            The created doc.
        """

        data = await self._state.create_doc(self.id, title=title, content=content)
        doc = Doc(data=data['doc'], channel=self, state=self._state)
        return doc

    async def fetch_doc(self, doc_id: int, /) -> Doc:
        """|coro|

        Fetch an doc in this channel.

        Returns
        --------
        :class:`.Doc`
            The doc by the ID.
        """

        data = await self._state.get_doc(self.id, doc_id)
        doc = Doc(data=data['doc'], channel=self, state=self._state)
        return doc

    # TODO: async iterator
    async def fetch_docs(self, *, limit: int = None, before: datetime.datetime = None) -> List[Doc]:
        """|coro|

        Fetch multiple docs in this channel.

        All parameters are optional.

        Parameters
        -----------
        limit: :class:`int`
            The maximum number of docs to return.
            Defaults to 25, can be at most 100.
        before: :class:`datetime.datetime`
            The latest date that an doc can be from. Defaults to the
            current time.

        Returns
        --------
        List[:class:`.Doc`]
            The docs in the channel.
        """

        data = await self._state.get_docs(self.id, limit=limit, before=before)
        docs = []
        for doc_data in data['docs']:
            docs.append(Doc(data=doc_data, channel=self, state=self._state))

        return docs


class ForumTopic(Hashable, HasContentMixin):
    """Represents a forum topic.

    .. container:: operations

        .. describe:: x == y

            Checks if two topics are equal.

        .. describe:: x != y

            Checks if two topics are not equal.

        .. describe:: hash(x)

            Returns the hash of the topic.

        .. describe:: str(x)

            Returns the title of the topic.

    Attributes
    -----------
    id: :class:`int`
        The topic's ID.
    title: :class:`str`
        The topic's title.
    content: Optional[:class:`str`]
        The topic's content.
    channel: :class:`.ForumChannel`
        The forum channel that the topic is in.
    created_at: :class:`datetime.datetime`
        When the topic was created.
    updated_at: Optional[:class:`datetime.datetime`]
        When the topic was last updated.
    bumped_at: Optional[:class:`datetime.datetime`]
        When the topic was last bumped.
    pinned: :class:`bool`
        Whether the topic is pinned.
    locked: :class:`bool`
        Whether the topic is locked.
    """

    __slots__: Tuple[str, ...] = (
        '_state',
        'channel',
        'channel_id',
        'id',
        'title',
        'content',
        '_mentions',
        'author_id',
        'created_at',
        'updated_at',
        'bumped_at',
        'pinned',
        'locked',
    )

    def __init__(self, *, state, data: ForumTopicPayload, channel: ForumChannel):
        super().__init__()
        self._state = state
        self.channel = channel
        self.channel_id: str = data.get('channelId')
        self.server_id: str = data.get('serverId')

        self.id: int = data['id']
        self.title: Optional[str] = data.get('title')
        self.content: Optional[str] = data.get('content')
        self._mentions = self._create_mentions(data.get('mentions'))
        self._extract_attachments(self.content)

        self.author_id: str = data.get('createdBy')
        self.created_at: datetime.datetime = ISO8601(data.get('createdAt'))
        self.updated_at: Optional[datetime.datetime] = ISO8601(data.get('updatedAt'))
        self.bumped_at: Optional[datetime.datetime] = ISO8601(data.get('bumpedAt'))

        self.pinned: bool = data.get('isPinned', False)
        self.locked: bool = data.get('isLocked', False)

    def __str__(self) -> str:
        return self.title

    def __repr__(self) -> str:
        return f'<ForumTopic id={self.id!r} title={self.title!r} channel={self.channel!r}>'

    @property
    def server(self) -> Server:
        """:class:`.Server`: The server that the topic is in."""
        return self._state._get_server(self.server_id)

    @property
    def guild(self) -> Server:
        """:class:`.Server`: |dpyattr|

        This is an alias of :attr:`.server`.

        The server that the topic is in.
        """
        return self.server

    @property
    def group(self) -> Group:
        """Optional[:class:`.Group`]: The group that the topic is in."""
        return self.channel.group

    @property
    def author(self) -> Optional[Member]:
        """Optional[:class:`.Member`]: The :class:`.Member` that created the topic."""
        return self.server.get_member(self.author_id)

    @property
    def share_url(self) -> str:
        """:class:`str`: The share URL of the topic."""
        return f'{self.channel.share_url}/{self.id}'

    async def add_reaction(self, emote: Emote, /) -> None:
        """|coro|

        Add a reaction to this topic.

        Parameters
        -----------
        emote: :class:`.Emote`
            The emote to add.
        """
        emote_id: int = getattr(emote, 'id', emote)
        await self._state.add_forum_topic_reaction_emote(self.channel.id, self.id, emote_id)

    async def remove_self_reaction(self, emote: Emote, /) -> None:
        """|coro|

        Remove one of your reactions from this topic.

        Parameters
        -----------
        emote: :class:`.Emote`
            The emote to remove.
        """
        emote_id: int = getattr(emote, 'id', emote)
        await self._state.remove_forum_topic_reaction_emote(self.channel.id, self.id, emote_id)

    async def edit(
        self,
        *,
        title: str = MISSING,
        content: str = MISSING,
    ) -> ForumTopic:
        """|coro|

        Edit this topic.

        All parameters are optional.

        Parameters
        -----------
        title: :class:`str`
            The title of the topic.
        content: :class:`str`
            The content of the topic.

        Returns
        --------
        :class:`.ForumTopic`
            The newly edited topic.
        """

        payload = {}

        if title is not MISSING:
            payload['title'] = title

        if content is not MISSING:
            payload['content'] = content

        data = await self._state.update_forum_topic(
            self.channel.id,
            self.id,
            payload=payload,
        )
        topic = ForumTopic(state=self._state, data=data['forumTopic'], channel=self.channel)
        return topic

    async def delete(self) -> None:
        """|coro|

        Delete this topic.

        Raises
        -------
        NotFound
            This topic does not exist.
        Forbidden
            You do not have permission to delete this topic.
        HTTPException
            Failed to delete this topic.
        """
        await self._state.delete_forum_topic(self.channel.id, self.id)

    async def pin(self) -> None:
        """|coro|

        Pin (sticky) this topic.

        .. versionadded:: 1.4

        Raises
        -------
        NotFound
            This topic does not exist.
        Forbidden
            You do not have permission to pin this topic.
        HTTPException
            Failed to pin this topic.
        """
        await self._state.pin_forum_topic(self.channel.id, self.id)

    sticky = pin

    async def unpin(self) -> None:
        """|coro|

        Unpin (unsticky) this topic.

        .. versionadded:: 1.4

        Raises
        -------
        NotFound
            This topic does not exist.
        Forbidden
            You do not have permission to unpin this topic.
        HTTPException
            Failed to unpin this topic.
        """
        await self._state.unpin_forum_topic(self.channel.id, self.id)

    unsticky = unpin

    async def lock(self) -> None:
        """|coro|

        Lock this topic.

        .. versionadded:: 1.4

        Raises
        -------
        NotFound
            This topic does not exist.
        Forbidden
            You do not have permission to lock this topic.
        HTTPException
            Failed to lock this topic.
        """
        await self._state.lock_forum_topic(self.channel.id, self.id)

    async def unlock(self) -> None:
        """|coro|

        Unlock this topic.

        .. versionadded:: 1.4

        Raises
        -------
        NotFound
            This topic does not exist.
        Forbidden
            You do not have permission to unlock this topic.
        HTTPException
            Failed to unlock this topic.
        """
        await self._state.unlock_forum_topic(self.channel.id, self.id)

    async def reply(self, content: str) -> ForumTopicReply:
        """|coro|

        Reply to this topic.

        .. versionadded:: 1.5

        Parameters
        -----------
        content: :class:`str`
            The content of the reply.

        Returns
        --------
        :class:`ForumTopicReply`
            The created reply.

        Raises
        -------
        NotFound
            This topic does not exist.
        Forbidden
            You do not have permission to reply to this topic.
        HTTPException
            Failed to reply to this topic.
        """

        data = await self._state.create_forum_topic_comment(self.channel_id, self.id, content=content)
        return ForumTopicReply(state=self._state, data=data['forumTopicComment'], parent=self)

    async def fetch_reply(self, reply_id: int, /) -> ForumTopicReply:
        """|coro|

        Fetch a reply to this topic.

        .. versionadded:: 1.5

        Returns
        --------
        :class:`ForumTopicReply`
            The reply from the ID.

        Raises
        -------
        NotFound
            This reply or topic does not exist.
        Forbidden
            You do not have permission to read this topic's replies.
        HTTPException
            Failed to fetch the reply.
        """

        data = await self._state.get_forum_topic_comment(self.channel_id, self.id, reply_id)
        return ForumTopicReply(state=self._state, data=data['forumTopicComment'], parent=self)

    async def fetch_replies(self) -> List[ForumTopicReply]:
        """|coro|

        Fetch all replies to this topic.

        .. versionadded:: 1.5

        Returns
        --------
        List[:class:`ForumTopicReply`]
            The replies under the topic.

        Raises
        -------
        NotFound
            This topic does not exist.
        Forbidden
            You do not have permission to read this topic's replies.
        HTTPException
            Failed to fetch the replies to this topic.
        """

        data = await self._state.get_forum_topic_comments(self.channel_id, self.id)
        return [
            ForumTopicReply(state=self._state, data=reply_data, parent=self)
            for reply_data in data['forumTopicComments']
        ]


class ForumChannel(guilded.abc.ServerChannel):
    """Represents a forum channel in a :class:`.Server`."""
    def __init__(self, **fields):
        super().__init__(**fields)

        self.type = ChannelType.forums

    async def create_topic(
        self,
        *,
        title: str,
        content: str,
    ) -> ForumTopic:
        """|coro|

        Create a new topic in this forum.

        Parameters
        -----------
        title: :class:`str`
            The title to create the topic with.
        content: :class:`str`
            The text content to include in the body of the topic.

        Returns
        --------
        :class:`.ForumTopic`
            The topic that was created.
        """

        data = await self._state.create_forum_topic(
            self.id,
            title=title,
            content=content,
        )

        topic = ForumTopic(data=data['forumTopic'], channel=self, state=self._state)
        return topic

    async def create_thread(self, *, name: str, content: Optional[str] = None, **kwargs) -> ForumTopic:
        """|coro|

        |dpyattr|

        Create a new topic in this forum.

        Parameters
        -----------
        name: :class:`str`
            The title to create the topic with.
        content: Optional[:class:`str`]
            The content to create the topic with.

        Returns
        --------
        :class:`.ForumTopic`
            The topic that was created.
        """
        return await self.create_topic(title=name, content=str(content))

    async def fetch_topic(self, topic_id: int, /) -> ForumTopic:
        """|coro|

        Fetch a topic from this forum.

        Returns
        --------
        :class:`.ForumTopic`
            The topic by its ID.
        """

        data = await self._state.get_forum_topic(self.id, topic_id)
        topic = ForumTopic(data=data['forumTopic'], channel=self, state=self._state)
        return topic

    async def topics(
        self,
        limit: Optional[int] = 25,
        before: Optional[Union[datetime.datetime, ForumTopic]] = None,
    ) -> AsyncIterator[ForumTopic]:
        """An :term:`asynchronous iterator` for the events in this channel.

        Examples
        ---------

        Usage ::

            async for topic in channel.topics():
                print(f"{topic}'s last activity was at {topic.bumped_at or topic.created_at}")

        Flattening into a list ::

            topics = [topic async for topic in channel.topics()]
            # topics is now a list of ForumTopic

        Parameters
        -----------
        limit: Optional[:class:`int`]
            The maximum number of topics to return.
            Defaults to 25 if not specified.
        before: Optional[Union[:class:`.ForumTopic`, :class:`datetime.datetime`]]
            The topic to stop pagination at.

        Yields
        -------
        :class:`.ForumTopic`
            An topic in this channel.

        Raises
        -------
        Forbidden
            You do not have permissions to get topics in this channel.
        HTTPException
            Failed to get the topics.
        """

        if isinstance(before, ForumTopic):
            before = before.starts_at

        while True:
            sublimit = min(100 if limit is None else limit, 100)
            if sublimit < 1:
                return

            data = await self._state.get_forum_topics(
                self.id,
                limit=sublimit,
                before=before,
            )
            data = data['forumTopics']

            # Adjust sublimit according to how much data is left
            if len(data) < 100:
                limit = 0
            else:
                limit -= len(data)

            for event_data in data:
                yield ForumTopic(state=self._state, data=event_data, channel=self)


class VoiceChannel(guilded.abc.ServerChannel, guilded.abc.Messageable):
    """Represents a voice channel in a :class:`.Server`."""
    def __init__(self, **fields):
        super().__init__(**fields)
        self.type = ChannelType.voice
        self._channel_id = self.id
        self._ws = None

    #async def connect(self):
    #    state = self._state

    #    connection_info = await state.get_voice_connection_info(self.id)
    #    endpoint = connection_info['endpoint']
    #    token = connection_info['token']

    #    ws_build = GuildedVoiceWebSocket.build( loop=self.loop)
    #    gws = await asyncio.wait_for(ws_build, timeout=60)
    #    if type(gws) != GuildedVoiceWebSocket:
    #        self.dispatch('error', gws)
    #        return

    #    self._ws = gws
    #    self.dispatch('connect')

    #    lobby = await state.get_voice_lobby(endpoint, self.id)
    #    lobby_connection_data = await state.connect_to_voice_lobby(
    #        endpoint,
    #        self.id,
    #        rtp_capabilities=lobby['routerRtpCapabilities']
    #    )

    #    dtls_parameters = lobby_connection_data['sendTransportOptions']['dtlsParameters']
    #    # The client transforms the default "auto" to "server" and sends only
    #    # the fingerprint where algorithm is "sha-256"
    #    dtls_parameters['role'] = 'server'

    #    transport = await state.connect_to_voice_transport(
    #        endpoint,
    #        self.id,
    #        transport_id=lobby_connection_data['sendTransportOptions']['id'],
    #        dtls_parameters=dtls_parameters
    #    )


class Thread(guilded.abc.ServerChannel, guilded.abc.Messageable):
    """Represents a thread in a :class:`.Server`.
    """
    def __init__(self, **fields):
        super().__init__(**fields)
        self.type = ChannelType.thread
    #    data = fields.get('data') or fields.get('channel', {})

    #    self._message_count = data.get('messageCount') or 0
    #    self.initial_message_id = data.get('threadMessageId')
    #    self._initial_message = self._state._get_message(self.initial_message_id)
    #    # This is unlikely to not be None given the temporal nature of message cache

    #    self._participant_ids = []

    #    for user_id in data.get('userIds') or []:
    #        self._participant_ids.append(user_id)

    #    for member_data in data.get('participants') or []:
    #        if member_data.get('id'):
    #            self._participant_ids.append(member_data['id'])

    #@property
    #def message_count(self) -> int:
    #    """:class:`int`: The number of messages in the thread.

    #    This may be inaccurate if this object has existed for an extended
    #    period of time since it does not get updated by the library when new
    #    messages are sent within the thread.
    #    """
    #    return int(self._message_count)

    #@property
    #def initial_message(self) -> Optional[ChatMessage]:
    #    """Optional[:class:`.ChatMessage`]: The initial message in this thread.

    #    This may be ``None`` if the message was not cached when this object was
    #    created. In this case, you may fetch the message with :meth:`.fetch_initial_message`.
    #    """
    #    return self._initial_message

    #@property
    #def participants(self) -> List[Member]:
    #    """List[:class:`.Member`]: The cached list of participants in this thread."""
    #    return [self.server.get_member(member_id) for member_id in self._participant_ids]

    #async def archive(self) -> None:
    #    """|coro|

    #    Archive this thread.
    #    """
    #    request = self._state.archive_thread(self.server_id, self.group_id, self.id)
    #    await request

    #async def restore(self) -> None:
    #    """|coro|

    #    Restore this thread.
    #    """
    #    request = self._state.restore_thread(self.server_id, self.group_id, self.id)
    #    await request

    #async def leave(self) -> None:
    #    """|coro|

    #    Leave this thread.
    #    """
    #    request = self._state.leave_thread(self.id)
    #    await request

    #async def fetch_initial_message(self) -> ChatMessage:
    #    """|coro|

    #    Fetch the initial message in this thread. Sometimes this may be
    #    available via :attr:`.initial_message`, but it is unlikely when
    #    dealing with existing threads because it relies on message cache.

    #    This is equivalent to:

    #    .. code-block:: python3

    #        initial_message = await thread.fetch_message(thread.initial_message_id)

    #    Returns
    #    --------
    #    :class:`.ChatMessage`
    #        The initial message in the thread.
    #    """
    #    message = await self.fetch_message(self.initial_message_id)
    #    return message


class DMChannel(Hashable, guilded.abc.Messageable):
    """Represents a private channel between users.

    .. container:: operations

        .. describe:: x == y

            Checks if two DM channels are equal.

        .. describe:: x != y

            Checks if two DM channels are not equal.

        .. describe:: hash(x)

            Returns the hash of the DM channel.

    Attributes
    -----------
    created_at: :class:`datetime.datetime`
        When the channel was created.
    updated_at: Optional[:class:`datetime.datetime`]
        When the channel was last updated.
    """

    def __init__(self, *, state, data: Dict[str, Any]):
        super().__init__(state=state, data=data)
        self.type = ChannelType.dm
        self.server = None
        self.group = None

        self._user_ids = set()
        self.recipient = None

        self.created_at: datetime.datetime = ISO8601(data.get('createdAt'))
        self.updated_at: Optional[datetime.datetime] = ISO8601(data.get('updatedAt'))

    @property
    def share_url(self) -> str:
        """:class:`str`: The URL which can be used to navigate to this channel."""
        return f'https://guilded.gg/chat/{self.id}'

    @property
    def users(self) -> List[User]:
        """List[:class:`~guilded.User`]: The list of participants in this DM, including yourself."""
        return [self._state._get_user(user_id) for user_id in self._user_ids]

    def __repr__(self) -> str:
        return f'<DMChannel id={self.id!r} recipient={self.recipient!r}>'


class Announcement(Hashable, HasContentMixin):
    """Represents an announcement in an :class:`.AnnouncementChannel`.

    .. container:: operations

        .. describe:: x == y

            Checks if two announcements are equal.

        .. describe:: x != y

            Checks if two announcements are not equal.

        .. describe:: hash(x)

            Returns the hash of the announcement.

        .. describe:: str(x)

            Returns the title of the announcement.

    Attributes
    -----------
    id: :class:`str`
        The announcement's ID.
    title: :class:`str`
        The announcement's title.
    content: :class:`str`
        The announcement's text content.
    channel: :class:`.AnnouncementChannel`
        The channel that the announcement is in.
    public: :class:`bool`
        Whether the announcement is public.
    pinned: :class:`bool`
        Whether the announcement is pinned.
    created_at: :class:`datetime.datetime`
        When the announcement was created.
    updated_at: Optional[:class:`datetime.datetime`]
        When the announcement was last updated.
    slug: Optional[:class:`str`]
        The announcement's blog URL slug.
    """

    def __init__(self, *, state, data, channel: AnnouncementChannel):
        super().__init__()
        self._state = state
        self.channel = channel
        self.tags: str = data.get('tags')
        self._replies = {}

        self.public: bool = data.get('isPublic', False)
        self.pinned: bool = data.get('isPinned', False)
        self.slug: Optional[str] = data.get('slug')

        self.author_id: str = data.get('createdBy')
        self.created_at: datetime.datetime = ISO8601(data.get('createdAt'))
        self.updated_at: Optional[datetime.datetime] = ISO8601(data.get('editedAt'))

        self.id: str = data['id']
        self.title: str = data['title']
        self.content: str = self._get_full_content(data['content'])

    def __repr__(self) -> str:
        return f'<Announcement id={self.id!r} title={self.title!r} channel={self.channel!r}>'

    def __str__(self) -> str:
        return self.title

    @property
    def server(self) -> Server:
        """:class:`.Server`: The server that the announcement is in."""
        return self.channel.server

    @property
    def guild(self) -> Server:
        """:class:`.Server`: |dpyattr|

        This is an alias of :attr:`.server`.

        The server that the announcement is in.
        """
        return self.server

    @property
    def group(self) -> Group:
        """:class:`.Group`: The group that the announcement is in."""
        return self.channel.group

    @property
    def author(self) -> Optional[Member]:
        """Optional[:class:`.Member`]: The :class:`.Member` that created the announcement."""
        return self.server.get_member(self.author_id)

    @property
    def blog_url(self) -> Optional[str]:
        """Optional[:class:`str`]: The blog URL of the announcement."""
        if self.channel.blog_url and self.slug:
            return f'{self.channel.blog_url}/{self.slug}'
        return None

    @property
    def share_url(self) -> str:
        return f'{self.channel.share_url}/{self.id}'

    async def sticky(self) -> None:
        """|coro|

        Sticky (pin) this announcement.
        """
        await self._state.toggle_announcement_pin(self.channel.id, self.id, pinned=True)
        self.pinned = True

    async def unsticky(self) -> None:
        """|coro|

        Unsticky (unpin) this announcement.
        """
        await self._state.toggle_announcement_pin(self.channel.id, self.id, pinned=False)
        self.pinned = False

    async def pin(self) -> None:
        """|coro|

        Pin (sticky) this announcement. This is an alias of :meth:`.sticky`.
        """
        await self.sticky()

    async def unpin(self) -> None:
        """|coro|

        Unpin (unsticky) this announcement. This is an alias of :meth:`.unsticky`.
        """
        await self.unsticky()

    async def delete(self) -> None:
        """|coro|

        Delete this announcement.
        """
        await self._state.delete_announcement(self.channel.id, self.id)

    async def edit(self, *content, **kwargs) -> None:
        """|coro|

        Edit this announcement.

        Parameters
        -----------
        \*content: Any
            The content of the announcement.
        title: :class:`str`
            The title of the announcement.
        """

        payload = {
            'title': kwargs.pop('title', self.title),
            'content': content,
        }

        await self._state.update_announcement(self.channel.id, self.id, payload=payload)

    async def add_reaction(self, emote: Emote, /) -> None:
        """|coro|

        Add a reaction to this announcement.

        Parameters
        -----------
        emote: :class:`.Emote`
            The emote to add.
        """
        await self._state.add_content_reaction(self.channel.type.value, self.id, emote.id)

    async def remove_self_reaction(self, emote: Emote, /) -> None:
        """|coro|

        Remove one of your reactions from this announcement.

        Parameters
        -----------
        emote: :class:`.Emote`
            The emote to remove.
        """
        emote_id: int = getattr(emote, 'id', emote)
        await self._state.remove_reaction_emote(self.channel.id, self.id, emote_id)


class AnnouncementChannel(guilded.abc.ServerChannel):
    """Represents an announcement channel in a :class:`.Server`."""
    def __init__(self, **fields):
        super().__init__(**fields)

        self.type = ChannelType.announcements
        self._announcements = {}

    @property
    def blog_url(self) -> Optional[str]:
        """Optional[:class:`str`]: The blog URL of the announcement channel.

        .. note::

            Due to an API limitation, this property cannot check if the
            channel is set as a blog, and it assumes the slug based on the
            channel's :attr:`~AnnouncementChannel.name`.
        """

        if not self.public:
            # Blog channels must be public
            return None

        channel_slug = re.sub(r'(?![\w-]).', '', self.server.name.replace(' ', '-'))
        if not channel_slug:
            # Guilded does not let you save an empty-when-stripped blog name
            return None

        server_portion = self.server.slug if self.server.slug is not None else f'teams/{self.server.id}'
        return f'https://guilded.gg/{server_portion}/blog/{channel_slug}'

    @property
    def announcements(self) -> List[Announcement]:
        """List[:class:`.Announcement`]: The list of announcements in this channel."""
        return list(self._announcements.values())

    def get_announcement(self, id) -> Optional[Announcement]:
        """Optional[:class:`.Announcement`]: Get an announcement from this channel."""
        return self._announcements.get(id)

    #async def getch_announcement(self, id: str) -> Announcement:
    #    return self.get_announcement(id) or await self.fetch_announcement(id)

    #async def fetch_announcement(self, id: str) -> Announcement:
    #    """|coro|

    #    Fetch an announcement in this channel.

    #    Parameters
    #    -----------
    #    id: :class:`str`
    #        The announcement's ID.

    #    Returns
    #    --------
    #    :class:`.Announcement`
    #    """
    #    data = await self._state.get_announcement(self.id, id)
    #    announcement = Announcement(data=data['announcement'], channel=self, state=self._state)
    #    return announcement

    #async def fetch_announcements(self, *, limit: int = 50, before: datetime.datetime = None) -> List[Announcement]:
    #    """|coro|

    #    Fetch multiple announcements in this channel.

    #    All parameters are optional.

    #    Parameters
    #    -----------
    #    limit: :class:`int`
    #        The maximum number of announcements to return. Defaults to 50.
    #    before: :class:`datetime.datetime`
    #        The latest date that an announcement can be from. Defaults to the
    #        current time.

    #    Returns
    #    --------
    #    List[:class:`.Announcement`]
    #    """

    #    before = before or datetime.datetime.now(datetime.timezone.utc)
    #    data = await self._state.get_announcements(self.id, limit=limit, before=before)
    #    announcements = []
    #    for announcement_data in data['announcements']:
    #        announcements.append(Announcement(data=announcement_data, channel=self, state=self._state))

    #    return announcements

    #async def fetch_pinned_announcements(self) -> List[Announcement]:
    #    """|coro|

    #    Fetch all pinned announcements in this channel.

    #    Returns
    #    --------
    #    List[:class:`.Announcement`]
    #    """
    #    data = await self._state.get_pinned_announcements(self.id)
    #    announcements = []
    #    for announcement_data in data['announcements']:
    #        announcements.append(Announcement(data=announcement_data, channel=self, state=self._state))

    #    return announcements

    #async def create_announcement(self, *content, **kwargs) -> Announcement:
    #    """|coro|

    #    Create an announcement in this channel.

    #    Parameters
    #    -----------
    #    content: Any
    #        The content of the announcement.
    #    title: :class:`str`
    #        The title of the announcement.
    #    game: Optional[:class:`.Game`]
    #        The game to be associated with this announcement.
    #    send_notifications: Optional[:class:`bool`]
    #        Whether to send notifications to all members ("Notify all
    #        members" in the client). Defaults to ``True`` if not specified.

    #    Returns
    #    --------
    #    :class:`.Announcement`
    #        The created announcement.
    #    """
    #    title = kwargs.pop('title')
    #    game = kwargs.pop('game', None)
    #    dont_send_notifications = not kwargs.pop('send_notifications', True)

    #    data = await self._state.create_announcement(
    #        self.id,
    #        title=title,
    #        content=content,
    #        game_id=(game.id if game else None),
    #        dont_send_notifications=dont_send_notifications
    #    )
    #    announcement = Announcement(data=data['announcement'], channel=self, game=game, state=self._state)
    #    return announcement


class Media(Hashable, HasContentMixin):
    """Represents a media post in a :class:`.MediaChannel`.

    .. container:: operations

        .. describe:: x == y

            Checks if two medias are equal.

        .. describe:: x != y

            Checks if two medias are not equal.

        .. describe:: hash(x)

            Returns the hash of the media.

        .. describe:: str(x)

            Returns the URL of the media.

        .. describe:: len(x)

            Returns the length of the media's URL.

    Attributes
    -----------
    id: :class:`int`
        The media's ID.
    title: :class:`str`
        The media's title.
    description: :class:`str`
        The media's description.
    url: :class:`str`
        The media's URL on Guilded's CDN.
    thumbnail: Optional[:class:`.Asset`]
        An asset for the media's thumbnail.
    channel: :class:`.MediaChannel`
        The channel that the media is in.
    public: :class:`bool`
        Whether the media is public.
    created_at: :class:`datetime.datetime`
        When the media was created.
    reply_count: :class:`int`
        How many replies the media has.
    """

    def __init__(self, *, state, data, channel: MediaChannel):
        super().__init__()
        self._state = state
        self.type = getattr(FileType, (data.get('type', 'image')), None)
        self.channel = channel
        self.tags: List[str] = list(data.get('tags') or [])  # sometimes an empty string is present instead of a list
        self._replies = {}

        self.public: bool = data.get('isPublic', False)
        self.url: str = data.get('src')

        thumbnail = None
        if data.get('srcThumbnail'):
            thumbnail = Asset._from_media_thumbnail(state, data['srcThumbnail'])
        self.thumbnail: Optional[Asset] = thumbnail

        self.author_id: str = data.get('createdBy')
        self.created_at: datetime.datetime = ISO8601(data.get('createdAt'))

        self.id: int = int(data['id'])
        self.title: str = data['title']
        self.description: str = data.get('description', '')

        self.reply_count: int = int(data.get('replyCount', 0))

        if data.get('additionalInfo', {}).get('externalVideoSrc'):
            self.youtube_embed_url = data['additionalInfo']['externalVideoSrc']
            self.youtube_video_id = re.sub(r'^https?:\/\/(www\.)youtube\.com\/embed\/', '', self.youtube_embed_url)

    def __repr__(self) -> str:
        return f'<Media id={self.id!r} title={self.title!r} author={self.author!r}>'

    def __str__(self) -> str:
        return self.url

    def __len__(self) -> int:
        return len(str(self))

    def _update(self, data) -> None:
        try:
            self.title = data['title']
        except KeyError:
            pass
        try:
            self.description = data['description']
        except KeyError:
            pass
        try:
            self.tags = data['tags']
        except KeyError:
            pass
        try:
            self.url = data['src']
        except KeyError:
            pass
        try:
            self.type = getattr(FileType, data['type'])
        except (KeyError, AttributeError):
            pass
        try:
            self.game = Game(game_id=data['gameId'])
        except KeyError:
            pass

    @property
    def server(self) -> Server:
        """:class:`.Server`: The server that the media is in."""
        return self.channel.server

    @property
    def guild(self) -> Server:
        """:class:`.Server`: |dpyattr|

        This is an alias of :attr:`.server`.

        The server that the media is in.
        """
        return self.server

    @property
    def group(self) -> Group:
        """:class:`.Group`: The group that the media is in."""
        return self.channel.group

    @property
    def author(self) -> Optional[Member]:
        """Optional[:class:`.Member`]: The member that created this media."""
        return self.server.get_member(self.author_id)

    async def add_reaction(self, emote: Emote, /) -> None:
        """|coro|

        Add a reaction to this media post.

        Parameters
        -----------
        emote: :class:`.Emote`
            The emote to add.
        """
        emote_id: int = getattr(emote, 'id', emote)
        await self._state.add_reaction_emote(self.channel.id, self.id, emote_id)

    async def remove_self_reaction(self, emote: Emote, /) -> None:
        """|coro|

        Remove one of your reactions from this media post.

        Parameters
        -----------
        emote: :class:`.Emote`
            The emote to remove.
        """
        emote_id: int = getattr(emote, 'id', emote)
        await self._state.remove_reaction_emote(self.channel.id, self.id, emote_id)

    #async def reply(self, *content, **kwargs) -> MediaReply:
    #    """|coro|

    #    Reply to this media.

    #    Parameters
    #    -----------
    #    content: Any
    #        The content to create the reply with.
    #    reply_to: Optional[:class:`.MediaReply`]
    #        An existing reply to reply to.

    #    Returns
    #    --------
    #    :class:`.MediaReply`
    #        The created reply.
    #    """
    #    data = await self._state.create_content_reply(self.channel.content_type, self.server.id, self.id, content=content, reply_to=kwargs.get('reply_to'))
    #    reply = MediaReply(data=data['reply'], parent=self, state=self._state)
    #    return reply

    #async def fetch_replies(self) -> List[MediaReply]:
    #    """|coro|

    #    Fetch the replies to this media post.

    #    Returns
    #    --------
    #    List[:class:`.MediaReply`]
    #    """
    #    replies = []
    #    data = await self._state.get_content_replies(self.channel.content_type, self.id)
    #    for reply_data in data:
    #        reply = MediaReply(data=reply_data, parent=self, state=self._state)
    #        replies.append(reply)

    #    return replies

    #async def fetch_reply(self, id: int) -> MediaReply:
    #    """|coro|

    #    Fetch a reply to this media.

    #    Parameters
    #    -----------
    #    id: :class:`int`
    #        The ID of the reply.

    #    Returns
    #    --------
    #    :class:`.MediaReply`
    #    """
    #    data = await self._state.get_content_reply(self.channel.type.value, self.channel.id, self.id, id)
    #    # metadata uses 'media' and not 'team_media'
    #    reply = MediaReply(data=data['metadata']['reply'], parent=self, state=self._state)
    #    return reply

    #async def move(self, to: MediaChannel) -> None:
    #    """|coro|

    #    Move this media post to another :class:`.MediaChannel`.

    #    Parameters
    #    -----------
    #    to: :class:`.MediaChannel`
    #        The media channel to move this media post to.
    #    """
    #    await self._state.move_media(self.channel.id, self.id, to.id)

    #async def delete(self) -> None:
    #    """|coro|

    #    Delete this media post.
    #    """
    #    await self._state.delete_media(self.channel.id, self.id)

    #async def edit(self, *,
    #    title: str = None,
    #    description: str = None,
    #    file: Optional[File] = None,
    #    youtube_url: Optional[str] = None,
    #    tags: List[str] = None,
    #    game: Optional[Game] = None,
    #) -> Media:
    #    """|coro|

    #    Edit this media post.

    #    All parameters are optional.

    #    Parameters
    #    -----------
    #    title: :class:`str`
    #        The title of the media.
    #    description: :class:`str`
    #        The description of the media. Does not accept markdown or any
    #        inline content.
    #    file: :class:`.File`
    #        The file to upload.
    #    youtube_url: :class:`str`
    #        The YouTube embed URL to use (``https://www.youtube.com/embed/...``).
    #    game: :class:`.Game`
    #        The game associated with the media.
    #    tags: List[:class:`str`]
    #        The tags on the media.

    #    Returns
    #    --------
    #    :class:`.Media`
    #        The newly updated media.
    #    """

    #    if file and youtube_url:
    #        raise ValueError('Must not specify both file and youtube_url')

    #    payload = {
    #        'id': self.id,
    #        'title': title or self.title,
    #        'description': description or self.description,
    #    }

    #    if tags is not None:
    #        payload['tags'] = tags
    #    else:
    #        payload['tags'] = self.tags

    #    if file:
    #        file.set_media_type(MediaType.media_channel_upload)
    #        await file._upload(self._state)
    #        payload['src'] = file.url
    #        payload['type'] = file.file_type.value
    #    elif youtube_url:
    #        data = await self._state.upload_third_party_media(youtube_url)
    #        payload['src'] = data['url']
    #        payload['additionalInfo'] = {'externalVideoSrc': youtube_url}
    #        payload['type'] = FileType.video.value
    #    else:
    #        payload['src'] = self.url
    #        payload['type'] = self.type.value

    #    if game is not None:
    #        payload['gameId'] = game.id
    #    elif self.game:
    #        payload['gameId'] = self.game.id

    #    await self._state.create_media(self.channel.id, payload=payload)

    #    self._update(payload)
    #    return self

    async def read(self) -> bytes:
        """|coro|

        Fetches the raw data of this media as a :class:`bytes`.

        Returns
        --------
        :class:`bytes`
            The raw data of this media.
        """
        return await self._state.read_filelike_data(self)


class ListItemNote(HasContentMixin):
    """Represents the note on a :class:`.ListItem`.

    Attributes
    -----------
    parent: :class:`.ListItem`
        The note's parent item.
    content: Optional[:class:`str`]
        The note's content.
    created_at: :class:`datetime.datetime`
        When the note was created.
    updated_at: Optional[:class:`datetime.datetime`]
        When the note was last updated.
    """
    def __init__(self, *, data: ListItemNotePayload, parent: ListItem):
        super().__init__()
        self._state = parent._state

        self.parent = parent

        self.author_id: str = data.get('createdBy')
        self.created_at: datetime.datetime = ISO8601(data.get('createdAt'))
        self.updated_by_id: Optional[str] = data.get('updatedBy')
        self.updated_at: Optional[datetime.datetime] = ISO8601(data.get('updatedAt'))

        self.content: Optional[str]
        if isinstance(data.get('content'), dict):
            # Webhook execution responses
            self.content = self._get_full_content(data['content'])
            # Realistically we never have to worry about absent note content because the
            # note of a webhook-created item is always populated with its execution payload
        else:
            self.content = data.get('content')
            self._mentions = self._create_mentions(data.get('mentions'))
            self._extract_attachments(self.content)

    def __repr__(self) -> str:
        return f'<ListItemNote parent={self.parent!r} author={self.author!r}>'

    @property
    def server(self) -> Server:
        """:class:`.Server`: The server that the note's parent item is in."""
        return self.parent.server

    @property
    def guild(self) -> Server:
        """:class:`.Server`: |dpyattr|

        This is an alias of :attr:`.server`.

        The server that the note's parent item is in.
        """
        return self.server

    @property
    def group(self) -> Group:
        """:class:`.Group`: The group that the note's parent item is in."""
        return self.parent.group

    @property
    def channel(self) -> ListChannel:
        """:class:`.ListChannel`: The channel that the note's parent item is in."""
        return self.parent.channel

    @property
    def author(self) -> Optional[Member]:
        """Optional[:class:`.Member`]: The :class:`.Member` that created the note."""
        if self.parent.server:
            return self.parent.server.get_member(self.author_id)

    @property
    def updated_by(self) -> Optional[Member]:
        """Optional[:class:`.Member`]: The :class:`.Member` that last updated the note."""
        if self.parent.server:
            return self.parent.server.get_member(self.updated_by_id)

    async def delete(self) -> None:
        """|coro|

        Delete this note.
        """
        await self.edit(content=None)

    async def edit(
        self,
        *,
        content: Optional[str] = MISSING,
    ) -> ListItemNote:
        """|coro|

        Edit this note.

        Parameters
        -----------
        content: :class:`str`
            The text content of the note.

        Returns
        --------
        :class:`.ListItemNote`
            The newly edited note.
        """

        payload = {
            'message': self.parent.message,
        }
        if content is not MISSING and content is not None:
            payload['note'] = {
                'content': content,
            }

        data = await self._state.update_list_item(
            self.channel.id,
            self.parent.id,
            payload=payload,
        )
        item = ListItem(data=data['listItem'], channel=self.parent.channel, state=self._state)
        return item.note


class ListItem(Hashable, HasContentMixin):
    """Represents an item in a :class:`.ListChannel`.

    .. container:: operations

        .. describe:: x == y

            Checks if two items are equal.

        .. describe:: x != y

            Checks if two items are not equal.

        .. describe:: hash(x)

            Returns the hash of the item.

    Attributes
    -----------
    id: :class:`str`
        The item's ID.
    created_at: :class:`datetime.datetime`
        When the item was created.
    message: :class:`str`
        The main message of the item.
    position: :class:`int`
        Where the item is in its :attr:`.channel`. A value of ``0`` is
        at the bottom of the list visually.
    note: :class:`.ListItemNote`
        The item's note.
    updated_at: Optional[:class:`datetime.datetime`]
        When the item was last updated.
    completed_at: Optional[:class:`datetime.datetime`]
        When the item was marked as completed.
    deleted_at: Optional[:class:`datetime.datetime`]
        When the item was deleted.
    parent_id: Optional[:class:`str`]
        The ID of the item's parent, if the item is nested.
    webhook_id: Optional[:class:`str`]
        The ID of the webhook that created the item, if applicable.
    """

    def __init__(self, *, state, data: ListItemPayload, channel: ListChannel):
        super().__init__()
        self._state = state
        self._channel = channel

        self.id: str = data['id']
        self.parent_id: Optional[str] = data.get('parentListItemId') or data.get('parentId')
        self.channel_id: str = data.get('channelId')
        self.server_id: str = data.get('serverId') or data.get('teamId')

        self.webhook_id: Optional[str] = data.get('createdByWebhookId') or data.get('webhookId')
        self.author_id: str = data.get('createdBy')
        self.created_at: datetime.datetime = ISO8601(data.get('createdAt'))
        self.updated_by_id: Optional[str] = data.get('updatedBy')
        self.updated_at: Optional[datetime.datetime] = ISO8601(data.get('updatedAt'))
        self.completed_by_id: Optional[str] = data.get('completedBy')
        self.completed_at: Optional[datetime.datetime] = ISO8601(data.get('completedAt'))

        if isinstance(data.get('message'), dict):
            # Webhook execution response
            self.message = self._get_full_content(data['message'])

            _note = {
                'content': data.get('note'),
                'createdAt': data.get('noteCreatedAt'),
                'createdBy': data.get('noteCreatedBy'),
                'updatedAt': data.get('noteUpdatedAt'),
                'updatedBy': data.get('noteUpdatedBy'),
            }
            self.note = ListItemNote(data=_note, parent=self)

        else:
            self.message: str = data['message']
            self._mentions = self._create_mentions(data.get('mentions'))
            self._extract_attachments(self.message)

            self.note = ListItemNote(data=data.get('note') or {}, parent=self)

    def __repr__(self) -> str:
        return f'<ListItem id={self.id!r} author={self.author!r} channel={self.channel!r}>'

    @property
    def server(self) -> Optional[Server]:
        """Optional[:class:`.Server`]: The server that the item is in.

        Chances are that this will only be ``None`` for partial webhook responses.
        """
        return self.channel.server

    @property
    def guild(self) -> Optional[Server]:
        """Optional[:class:`.Server`]: |dpyattr|

        This is an alias of :attr:`.server`.

        The server that the item is in.
        """
        return self.server

    @property
    def channel(self) -> ListChannel:
        """:class:`.ListChannel`: The channel that the item is in."""
        return self._channel or self._state._get_server_channel(self.server_id, self.channel_id)

    @property
    def group(self) -> Group:
        """:class:`.Group`: The group that the item is in."""
        if self.server:
            return self.channel.group

    @property
    def author(self) -> Optional[Member]:
        """Optional[:class:`.Member`]: The :class:`.Member` that created the item."""
        if self.server:
            return self.server.get_member(self.author_id)

    @property
    def updated_by(self) -> Optional[Member]:
        """Optional[:class:`.Member`]: The :class:`.Member` that last updated the item."""
        if self.server:
            return self.server.get_member(self.updated_by_id)

    @property
    def completed_by(self) -> Optional[Member]:
        """Optional[:class:`.Member`]: The :class:`.Member` that marked the the item as completed."""
        if self.server:
            return self.server.get_member(self.completed_by_id)

    @property
    def share_url(self) -> Optional[str]:
        """:class:`str`: The share URL of the item."""
        return f'{self.channel.share_url}?listItemId={self.id}'

    @property
    def assigned_to(self) -> List[Member]:
        """List[:class:`.Member`]: The members that the item is assigned to,
        designated by the user & role mentions in :attr:`.message`."""

        members = set(self.user_mentions)
        for role in self.role_mentions:
            for member in role.members:
                members.add(member)

        return list(members)

    @property
    def parent(self) -> Optional[ListItem]:
        """Optional[:class:`.ListItem`]: The item that this item is a child of."""
        return self.channel.get_item(self.parent_id)

    def has_note(self) -> bool:
        """:class:`bool`: Whether the item has a note."""
        return self.note.content is not None

    async def fetch_parent(self) -> ListItem:
        """|coro|
        
        Fetch the item that this item is a child of, if it exists.

        Returns
        --------
        :class:`.ListItem`
            The item's parent.

        Raises
        -------
        ValueError
            This item has no parent.
        """
        if self.parent_id is None:
            raise ValueError('This item has no parent.')

        return await self.channel.fetch_item(self.parent_id)

    async def fetch_note(self) -> ListItemNote:
        """|coro|

        Fetch this item's note. This should only be necessary if you obtained
        this object through :meth:`.ListChannel.fetch_items`.

        Returns
        --------
        :class:`.ListItemNote`
            This item's note.
        """

        item = await self.channel.fetch_item(self.id)
        self.note = item.note
        return self.note

    async def delete(self) -> None:
        """|coro|

        Delete this item.
        """
        await self._state.delete_list_item(self.channel.id, self.id)

    async def edit(
        self,
        *,
        message: Optional[str] = MISSING,
        note_content: Optional[str] = MISSING,
    ) -> ListItem:
        """|coro|

        Edit this item.

        All parameters are optional.

        Parameters
        -----------
        message: :class:`str`
            The text content to set as the main message of the item.
        note_content: :class:`str`
            The item's note content.

        Returns
        --------
        :class:`.ListItem`
            The newly edited item.
        """

        # The parameter is named ``message`` for API compliance but we use ``content`` internally for consistency.
        content = message

        payload = {}
        if content is not MISSING:
            payload['message'] = content
        else:
            payload['message'] = self.message

        if note_content is not MISSING and note_content is not None:
            payload['note'] = {
                'content': note_content
            }

        data = await self._state.update_list_item(
            self.channel.id,
            self.id,
            payload=payload,
        )
        item = ListItem(data=data['listItem'], channel=self.channel, state=self._state)
        return item

    #async def create_item(
    #    self,
    #    message: str = MISSING,
    #    *,
    #    note_content: Optional[str] = MISSING,
    #) -> ListItem:
    #    """|coro|

    #    Create an item with this item as its parent.

    #    This method is identical to :meth:`ListChannel.create_item`.
    #    """
    #    return await self.channel.create_item(
    #        message=message,
    #        note_content=note_content,
    #        parent=self,
    #    )

    #async def move(self, to: ListChannel) -> None:
    #    """|coro|

    #    Move this item to another channel.

    #    Parameters
    #    -----------
    #    to: :class:`.ListChannel`
    #        The list channel to move this item to.
    #    """
    #    await self._state.move_list_item(self.channel.id, self.id, to.id)

    async def complete(self) -> None:
        """|coro|

        Mark this list item as complete.

        If this item has any children, they will also be marked as complete.
        """
        await self._state.complete_list_item(self.channel.id, self.id)

    async def uncomplete(self) -> None:
        """|coro|

        Mark this list item as incomplete.
        """
        await self._state.uncomplete_list_item(self.channel.id, self.id)


class MediaChannel(guilded.abc.ServerChannel):
    """Represents a media channel in a :class:`.Server`."""
    def __init__(self, **fields):
        super().__init__(**fields)
        self.type = ChannelType.media
        self.content_type = 'team_media'
        self._medias = {}

    @property
    def medias(self) -> List[Media]:
        """List[:class:`.Media`]: The list of cached medias in this channel."""
        return list(self._medias.values())

    def get_media(self, id) -> Optional[Media]:
        """Optional[:class:`.Media`]: Get a cached media post in this channel."""
        return self._medias.get(id)

    #async def getch_media(self, id: int) -> Media:
    #    return self.get_media(id) or await self.fetch_media(id)

    #async def fetch_media(self, id: int) -> Media:
    #    """|coro|

    #    Fetch a media post in this channel.

    #    Parameters
    #    -----------
    #    id: :class:`int`
    #        The media's ID.

    #    Returns
    #    --------
    #    :class:`.Media`
    #    """
    #    data = await self._state.get_media(self.id, id)
    #    media = Media(data=data, channel=self, state=self._state)
    #    return media

    #async def fetch_medias(self, *, limit: int = 50) -> List[Media]:
    #    """|coro|

    #    Fetch multiple media posts in this channel.

    #    All parameters are optional.

    #    Parameters
    #    -----------
    #    limit: :class:`int`
    #        The maximum number of media posts to return. Defaults to 50.

    #    Returns
    #    --------
    #    List[:class:`.Media`]
    #    """
    #    data = await self._state.get_medias(self.id, limit=limit)
    #    medias = []
    #    for media_data in data:
    #        medias.append(Media(data=media_data, channel=self, state=self._state))

    #    return medias

    #async def create_media(
    #    self,
    #    *,
    #    title: str,
    #    description: str = None,
    #    file: Optional[File] = None,
    #    youtube_url: Optional[str] = None,
    #    tags: List[str] = None,
    #    game: Optional[Game] = None,
    #) -> Media:
    #    """|coro|

    #    Create a media post in this channel.

    #    Parameters
    #    -----------
    #    title: :class:`str`
    #        The title of the media.
    #    description: Optional[:class:`str`]
    #        The description of the media. Does not accept markdown or any
    #        inline content.
    #    file: :class:`.File`
    #        The file to upload. Either this or ``youtube_url`` is required.
    #    youtube_url: :class:`str`
    #        The YouTube embed URL to use (``https://www.youtube.com/embed/...``).
    #        Either this or ``file`` is required.
    #    game: Optional[:class:`.Game`]
    #        The game associated with the media.
    #    tags: List[:class:`str`]
    #        The tags on the media.

    #    Returns
    #    --------
    #    :class:`.Media`
    #        The created media.
    #    """
    #    if file and youtube_url:
    #        raise ValueError('Must not specify both file and youtube_url')
    #    if not file and not youtube_url:
    #        raise ValueError('Must specify either file or youtube_url')

    #    payload = {
    #        'title': title,
    #        'description': description or '',
    #        'tags': tags or [],
    #    }

    #    if file:
    #        file.set_media_type(MediaType.media_channel_upload)
    #        await file._upload(self._state)
    #        payload['src'] = file.url
    #        payload['type'] = file.file_type.value
    #    elif youtube_url:
    #        data = await self._state.upload_third_party_media(youtube_url)
    #        payload['src'] = data['url']
    #        payload['additionalInfo'] = {'externalVideoSrc': youtube_url}
    #        payload['type'] = FileType.video.value

    #    if game is not None:
    #        payload['gameId'] = game.id

    #    data = await self._state.create_media(self.id, payload=payload)
    #    media = Media(data=data, channel=self, game=game, state=self._state)
    #    return media


class ListChannel(guilded.abc.ServerChannel):
    """Represents a list channel in a :class:`.Server`."""
    def __init__(self, **fields):
        super().__init__(**fields)
        self.type = ChannelType.list
        self._items = {}

    @property
    def items(self) -> List[ListItem]:
        """List[:class:`.ListItem`]: The list of items in this channel."""
        return list(self._items.values())

    def get_item(self, id) -> Optional[ListItem]:
        """Optional[:class:`.ListItem`]: Get an item in this channel."""
        return self._items.get(id)

    async def getch_item(self, item_id: str, /) -> ListItem:
        return self.get_item(item_id) or await self.fetch_item(item_id)

    async def fetch_item(self, item_id: str, /) -> ListItem:
        """|coro|

        Fetch an item in this channel.

        Returns
        --------
        :class:`.ListItem`
            The item by the ID.
        """

        data = await self._state.get_list_item(self.id, item_id)
        item = ListItem(data=data['listItem'], channel=self, state=self._state)
        return item

    async def fetch_items(self) -> List[ListItem]:
        """|coro|

        Fetch all items in this channel.

        Returns
        --------
        List[:class:`.ListItem`]
            The items in this channel.
        """

        data = await self._state.get_list_items(self.id)

        items = []
        for item_data in data['listItems']:
            items.append(ListItem(data=item_data, channel=self, state=self._state))

        return items

    async def create_item(
        self,
        message: str,
        *,
        note_content: Optional[str] = None,
    ) -> ListItem:
        """|coro|

        Create an item in this channel.

        Parameters
        -----------
        message: :class:`str`
            The text content to include as the main message of the item.
        note_content: Optional[:class:`str`]
            The item's note content.

        Returns
        --------
        :class:`.ListItem`
            The created item.
        """

        data = await self._state.create_list_item(
            self.id,
            message=message,
            note_content=note_content,
        )
        item = ListItem(data=data['listItem'], channel=self, state=self._state)
        return item

    async def create_webhook(self, *, name: str) -> Webhook:
        """|coro|

        Create a webhook in this channel.

        Parameters
        -----------
        name: :class:`str`
            The webhook's name.

        Returns
        --------
        :class:`Webhook`
            The created webhook.

        Raises
        -------
        HTTPException
            Creating the webhook failed.
        Forbidden
            You do not have permissions to create a webhook.
        """

        webhook = await self.server.create_webhook(
            channel=self,
            name=name,
        )
        return webhook

    async def webhooks(self) -> List[Webhook]:
        """|coro|

        Fetch the list of webhooks in this channel.

        .. warning::

            This endpoint cannot be paginated.

        Returns
        --------
        List[:class:`Webhook`]
            The webhooks in this channel.

        Raises
        -------
        Forbidden
            You do not have permissions to get the webhooks.
        """

        webhooks = await self.server.webhooks(channel=self)
        return webhooks


class Availability(Hashable):
    """Represents an availability in a :class:`.SchedulingChannel`.

    .. container:: operations

        .. describe:: x == y

            Checks if two availabilities are equal.

        .. describe:: x != y

            Checks if two availabilities are not equal.

        .. describe:: hash(x)

            Returns the hash of the availability.

    Attributes
    -----------
    id: :class:`int`
        The availability's ID.
    start: :class:`datetime.datetime`
        When the availability starts.
    end: :class:`datetime.datetime`
        When the availability ends.
    created_at: :class:`datetime.datetime`
        When the availabilty was created.
    updated_at: Optional[:class:`datetime.datetime`]
        When the availabilty was updated.
    channel: :class:`.SchedulingChannel`
        The channel that the availability is in.
    """
    def __init__(self, *, state, data, channel: SchedulingChannel):
        self._state = state

        self.channel = channel
        self.channel_id: str = data.get('channelId')
        self.server_id: str = data.get('serverId')

        self.id: int = data['id']
        self.start: datetime.datetime = ISO8601(data.get('startDate'))
        self.end: datetime.datetime = ISO8601(data.get('endDate'))

        self.user_id: str = data.get('userId')
        self.created_at: datetime.datetime = ISO8601(data.get('createdAt'))

        self.updated_by_id: Optional[str] = data.get('updatedBy')
        self.updated_at: Optional[datetime.datetime] = ISO8601(data.get('updatedAt'))

    def __repr__(self) -> str:
        return f'<Availability id={self.id!r} start={self.start!r} end={self.end!r} channel={self.channel!r}>'

    @property
    def server(self) -> Server:
        """:class:`.Server`: The server that the availability is in."""
        return self._state._get_server(self.server_id)

    @property
    def group(self) -> Optional[Group]:
        """Optional[:class:`.Group`]: The group that the availability is in."""
        return self.channel.group

    @property
    def guild(self) -> Server:
        """:class:`.Server`: |dpyattr|

        This is an alias of :attr:`.server`

        The server that the availability is in.
        """
        return self.server

    @property
    def user(self) -> Optional[Member]:
        """Optional[:class:`.Member`]: The member that the availability is for."""
        return self.server.get_member(self.user_id)

    @property
    def updated_by(self) -> Optional[Member]:
        """Optional[:class:`.Member`]: The member that last updated the availability."""
        return self.server.get_member(self.updated_by_id)

    #async def edit(
    #    self,
    #    *,
    #    start: Optional[datetime.datetime] = None,
    #    end: Optional[datetime.datetime] = None,
    #) -> Availability:
    #    """|coro|

    #    Edit this availability.

    #    All parameters are optional.

    #    Parameters
    #    -----------
    #    start: :class:`datetime.datetime`
    #        When the availability starts.
    #        Time must be in a 30-minute interval (``minute`` must be 0 or 30).
    #    end: :class:`datetime.datetime`
    #        When the availability ends.
    #        Time must be in a 30-minute interval (``minute`` must be 0 or 30).

    #    Returns
    #    --------
    #    :class:`.Availability`
    #        The newly edited availability.
    #    """
    #    payload = {
    #        'startDate': start or self.start,
    #        'endDate': end or self.end,
    #    }
    #    data = await self._state.update_availability(self.channel.id, self.id, payload=payload)
    #    self.start = payload['startDate']
    #    self.end = payload['endDate']
    #    return self

    #async def delete(self) -> None:
    #    """|coro|

    #    Delete this availability.
    #    """
    #    await self._state.delete_availability(self.channel.id, self.id)


class SchedulingChannel(guilded.abc.ServerChannel):
    """Represents a scheduling channel in a :class:`.Server`."""
    def __init__(self, **fields):
        super().__init__(**fields)
        self.type = ChannelType.scheduling
        self._availabilities = {}

    @property
    def availabilities(self) -> List[Availability]:
        """List[:class:`.Availability`]: The list of availabilities in this channel."""
        return list(self._availabilities.values())

    def get_availability(self, id) -> Optional[Availability]:
        """Optional[:class:`.Availability`]: Get an availability in this channel."""
        return self._availabilities.get(id)

    #async def getch_availability(self, id: str) -> Availability:
    #    return self.get_availability(id) or await self.fetch_availability(id)

    #async def fetch_availability(self, id: int) -> Availability:
    #    """|coro|

    #    Fetch an availability in this channel.

    #    .. note::

    #        There is no endpoint to fetch a specific availability, so instead
    #        this method filters :meth:`.fetch_availabilities` and raises
    #        :exc:`InvalidArgument` if no availability was found.

    #    Parameters
    #    -----------
    #    id: :class:`int`
    #        The availability's ID.

    #    Returns
    #    --------
    #    :class:`.Availability`

    #    Raises
    #    -------
    #    InvalidArgument
    #        No availability exists in this channel with the ID specified.
    #    """
    #    availabilities = await self.fetch_availabilities()
    #    availability = get(availabilities, id=id)
    #    if not availability:
    #        raise InvalidArgument(f'No availability exists in this channel with the ID {id}.')
    #    return availability

    #async def fetch_availabilities(self) -> List[Availability]:
    #    """|coro|

    #    Fetch all availabilities in this channel.

    #    Returns
    #    --------
    #    List[:class:`.Availability`]
    #    """
    #    data = await self._state.get_availabilities(self.id)
    #    availabilities = []
    #    for availability_data in data:
    #        availabilities.append(Availability(data=availability_data, channel=self, state=self._state))

    #    return availabilities

    #async def create_availability(self, start: datetime.datetime, end: datetime.datetime) -> Availability:
    #    """|coro|

    #    Create an availability in this channel.

    #    Parameters
    #    -----------
    #    start: :class:`datetime.datetime`
    #        When the availability starts.
    #        Time must be in a 30-minute interval (``minute`` must be 0 or 30).
    #    end: :class:`datetime.datetime`
    #        When the availability ends.
    #        Time must be in a 30-minute interval (``minute`` must be 0 or 30).

    #    Returns
    #    --------
    #    :class:`.Availability`
    #        The created availability.
    #    """
    #    data = await self._state.create_availability(self.id, start=start, end=end)
    #    for availability_data in data['availabilities']:
    #        availability = Availability(data=availability_data, channel=self, state=self._state)
    #        if availability.id == data['id']:
    #            return availability


class PartialMessageable(guilded.abc.Messageable, Hashable):
    """Represents a partial messageable to aid with working messageable channels when
    only a channel ID is present.

    The only way to construct this class is through :meth:`Client.get_partial_messageable`.

    Note that this class is trimmed down and has no rich attributes.

    .. versionadded:: 1.4

    .. container:: operations

        .. describe:: x == y

            Checks if two partial messageables are equal.

        .. describe:: x != y

            Checks if two partial messageables are not equal.

        .. describe:: hash(x)

            Returns the partial messageable's hash.

    Attributes
    -----------
    id: :class:`str`
        The channel ID associated with this partial messageable.
    server_id: Optional[:class:`str`]
        The server ID associated with this partial messageable.
    type: Optional[:class:`ChannelType`]
        The channel type associated with this partial messageable, if given.
    """

    def __init__(
        self,
        state,
        id: str,
        server_id: Optional[str] = None,
        group_id: Optional[str] = None,
        type: Optional[ChannelType] = None,
    ):
        self._state = state
        self.id: str = id
        self._channel_id: str = id
        self.server_id: Optional[str] = server_id
        self.group_id: Optional[str] = group_id
        self.type: Optional[ChannelType] = type

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} id={self.id} type={self.type!r}>'

    async def _get_channel(self) -> PartialMessageable:
        return self

    @property
    def server(self) -> Optional[Server]:
        """Optional[:class:`Server`]: The server this partial messageable is in."""
        return self._state._get_server(self.server_id)

    @property
    def guild(self) -> Server:
        """Optional[:class:`.Server`]: |dpyattr|

        This is an alias of :attr:`.server`.

        The server this partial messageable is in.
        """
        return self.server

    @property
    def group(self) -> Group:
        """Optional[:class:`~guilded.Group`]: The group that this partial messageable is in."""
        if self.server:
            return self.server.get_group(self.group_id)

    @property
    def share_url(self) -> str:
        """:class:`str`: Returns a URL that allows the client to jump to the channel."""
        if self.server_id is None:
            return f'https://www.guilded.gg/chat/{self.id}'

        # Using "_" for groups will render weirdly in the client, but the channel contents do appear
        return f'https://www.guilded.gg/teams/{self.server_id}/groups/{self.group_id or "_"}/channels/{self.id}/chat'

    jump_url = share_url

    @property
    def created_at(self) -> datetime.datetime:
        """:class:`datetime.datetime`: Returns the channel's creation time in UTC.

        This function exists for compatibility with other channel types.
        Since partial messageables cannot determine their creation date from
        only their UUID, this will always return 1/1/2016.
        """

        return GUILDED_EPOCH_DATETIME

    # def permissions_for(self, obj: Any = None, /) -> Permissions:
    #     """Handles permission resolution for a :class:`User`.

    #     This function exists for compatibility with other channel types.
    #     Since partial messageables cannot reasonably have the concept of
    #     permissions, this will always return :meth:`Permissions.none`.

    #     Parameters
    #     -----------
    #     obj: :class:`User`
    #         The user to check permissions for. This parameter is ignored
    #         but kept for compatibility with other ``permissions_for`` methods.

    #     Returns
    #     --------
    #     :class:`Permissions`
    #         The resolved permissions.
    #     """

    #     return Permissions.none()
