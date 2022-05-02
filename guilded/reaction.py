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

from typing import TYPE_CHECKING, Any, AsyncIterator, Dict, List, Optional, Union

from .emoji import Emoji
from .enums import ChannelType, try_enum
from .utils import ISO8601

if TYPE_CHECKING:
    import datetime

    from guilded.abc import User as abc_User

    from .message import ChatMessage
    from .channel import (
        Announcement,
        AnnouncementReply,
        Doc,
        DocReply,
        ForumTopic,
        ForumReply,
        Media,
        MediaReply,
    )
    from .user import User, Member

__all__ = (
    'ContentReaction',
    'RawReactionActionEvent',
    'Reaction',
)


class ContentReaction:
    """Represents an emoji reaction on an instance of content (represented by :attr:`.parent`).

    Attributes
    -----------
    parent: Union[:class:`.Announcement`, :class:`.AnnouncementReply`, :class:`.ChatMessage`, :class:`.Doc`, :class:`.DocReply`, :class:`.ForumTopic`, :class:`.ForumReply`, :class:`.Media`, :class:`.MediaReply`]
        The content that this reaction is on.
    created_at: :class:`datetime.datetime`
        When the reaction was added to its content.
    emoji: :class:`.Emoji`
        The emoji that the reaction shows.
    """

    __slots__ = (
        '_state',
        '_user_ids',
        '_emoji_id',
        'parent',
        'id',
        'created_at',
        'emoji',
    )

    def __init__(self, *, data, parent):
        self._state = parent._state
        self.parent: Union[
            Announcement,
            AnnouncementReply,
            ChatMessage,
            Doc,
            DocReply,
            ForumTopic,
            ForumReply,
            Media,
            MediaReply,
        ]
        self.parent = parent

        self.id: int = data.get('reactionId')  # This seems to always be 0
        self.created_at: datetime.datetime = ISO8601(data.get('createdAt'))
        self._user_ids: List[str] = data.get('reactedUsers') or []

        # Messgae reaction events
        if data.get('createdBy') and data.get('createdBy') not in self._user_ids:
            self._user_ids.append(data.get('createdBy'))
        # Content reaction events
        if data.get('userId') and data.get('userId') not in self._user_ids:
            self._user_ids.append(data.get('userId'))

        self._emoji_id: int = data.get('customReactionId')
        if 'customReaction' not in data:
            self.emoji = (
                self._state._get_emoji(self._emoji_id)
                or Emoji(state=self._state, data={'id': self._emoji_id, 'webp': ''})
            )
        else:
            self.emoji: Emoji = Emoji(
                state=self._state,
                data=data['customReaction'],
                stock=data['customReaction'].get('webp') is None,
            )

    @property
    def message(self) -> Optional[ChatMessage]:
        """Optional[:class:`.ChatMessage`]: |dpyattr|

        The message that this reaction is on.

        This is the same as :attr:`.parent` except that it is only present if the parent is a :class:`.ChatMessage`.
        """
        from .message import ChatMessage

        return self.parent if isinstance(self.parent, ChatMessage) else None

    @property
    def me(self) -> bool:
        """:class:`bool`: Whether the client added the reaction."""
        return self._state.my_id in self._user_ids

    @property
    def count(self) -> int:
        """:class:`int`: How many users have added this reaction."""
        return len(self._user_ids)

    def is_custom_emoji(self) -> bool:
        """:class:`bool`: Whether the reaction uses a custom emoji."""
        return self.emoji.stock

    async def remove_self(self) -> None:
        """|coro|

        Remove this reaction for yourself.

        You cannot remove other users' reactions.
        """
        await self.parent.remove_self_reaction(self.emoji)

    async def users(
        self,
        *,
        limit: Optional[int] = None,
        after: Optional[abc_User] = None
    ) -> AsyncIterator[Union[User, Member]]:
        """An :term:`asynchronous iterator` for the users that have reacted with this emoji to this content.

        Results may not be in any expected order.

        Examples
        ---------

        Usage ::

            async for user in reaction.users():
                print(f'{user} reacted with {reaction.emoji}')

        Flattening into a list ::

            users = [user async for user in reaction.users()]
            # users is now a list of User
            winner = random.choice(users)
            await channel.send(f'Out of all {reaction.count} entrants, {winner} has won our completely unbiased contest.')

        Parameters
        -----------
        limit: Optional[:class:`int`]
            The maximum number of users to return.
        after: Optional[:class:`~.abc.User`]
            The user to begin pagination at.
            This may be an :class:`.Object`\.

        Yields
        -------
        Union[:class:`.User`, :class:`.Member`]
            The user that created the reaction.
            This will be a :class:`.User` if there is no team or if the member is otherwise unavailable.

        Raises
        -------
        HTTPException
            Failed to get one or multiple users.
        ValueError
            ``after`` is not a valid option.
        """

        if limit is None:
            limit = self.count

        after_index = -1
        user_ids = self._user_ids

        while limit > 0:
            if after is not None:
                after_index = user_ids.index(after.id)

            user_ids = self._user_ids[(after_index + 1):]
            team = self.parent.team

            cached_users = []
            new_user_ids = []

            if team is not None:
                for uid in user_ids:
                    user = team.get_member(uid) or self._state._get_user(uid)
                    if user is None:
                        new_user_ids.append(uid)
                    else:
                        cached_users.append(user)

                if new_user_ids:
                    data = await self._state.get_detailed_team_members(
                        team.id,
                        user_ids=new_user_ids,
                        ids_for_basic_info=new_user_ids,
                    )
                    for uid in data:
                        new_user_ids.remove(uid)

                    data = list(data.values())

            else:
                data = []
                for uid in user_ids:
                    user = self._state._get_user(uid)
                    if user is None:
                        new_user_ids.append(uid)
                    else:
                        cached_users.append(user)

            if cached_users:
                limit -= len(cached_users)
                after = cached_users[-1]

                for cached_user in cached_users:
                    yield cached_user

                continue

            if data:
                # team will never be None here
                limit -= len(data)
                after = data[-1]['id']

                for raw_member in data:
                    member = self._state.create_member(data=raw_member, team=team)
                    yield member

                continue

            for uid in new_user_ids:
                raw_user = await self._state.get_user(uid)
                yield User(state=self._state, data=raw_user)

Reaction = ContentReaction  # discord.py


class RawReactionActionEvent:
    """Represents the payload for a raw reaction add/remove event.

    Attributes
    -----------
    parent_id: Union[:class:`str`, :class:`int`]
        The ID of the reaction's parent content.
    message_id: Union[:class:`str`, :class:`int`]
        |dpyattr|

        This is an alias of :attr:`.parent_id`.
    user_id: :class:`str`
        The user ID that added or removed their reaction.
    channel_id: :class:`str`
        The channel ID that the reaction's content is in.
    channel_type: :class:`.ChannelType`
        The type of channel that the reaction's content is in.
    team_id: Optional[:class:`str`]
        The team ID that the reaction is in, if applicable.
    emoji: :class:`.Emoji`
        The emoji that was reacted with.
        This may be a partial :class:`.Emoji` with only :attr:`.Emoji.id` for
        events where a reaction was removed from a message.
    member: Optional[Union[:class:`.Member`, :class:`.User`]]
        The member that added or removed their reaction.
        This is only available if the member was cached prior to this event being received.
        This will only be a :class:`.User` if the reaction is in a DM.
    event_type: :class:`str`
        The event type that this action was created from.
        For messages, this will be one of ``ChatMessageReactionAdded`` or ``ChatMessageReactionDeleted``,
        otherwise it will be one of ``teamContentReactionsAdded`` or ``teamContentReactionsRemoved``.
    """

    __slots__ = (
        '_from_message',
        'parent_id',
        'message_id',
        'user_id',
        'channel_id',
        'channel_type',
        'team_id',
        'emoji',
        'member',
        'event_type',
    )

    def __init__(self, *, state, data: Dict[str, Any]):
        self._from_message: bool = 'message' in data
        self.parent_id: Union[str, int]
        self.user_id: str
        self.channel_id: str = data.get('channelId')
        self.channel_type: ChannelType
        self.team_id: Optional[str] = data.get('teamId')
        self.emoji: Emoji
        self.event_type: str = data['type']

        # The message reaction events and else-content reaction events are
        # structured differently enough that I felt this distinction was necessary
        if self._from_message:
            self.parent_id = data['message']['id']
            self.channel_type = ChannelType.chat
            self.user_id = data['reaction'].get('createdBy')
            if 'customReaction' not in data['reaction']:
                emoji_id: int = data['reaction']['customReactionId']
                self.emoji = (
                    state._get_emoji(emoji_id)
                    or Emoji(state=state, data={'id': emoji_id, 'webp': ''})
                )
            else:
                self.emoji = Emoji(
                    state=state,
                    data=data['reaction']['customReaction'],
                    stock=data['reaction']['customReaction'].get('webp') is None,
                )

        else:
            self.parent_id = int(data['contentId']) if data['contentId'].isdigit() else data['contentId']
            self.channel_type = try_enum(ChannelType, data.get('contentType'))
            self.user_id = data.get('userId')
            self.emoji = Emoji(
                state=state,
                data=data['customReaction'],
                stock=data['customReaction'].get('webp') is None,
            )

        self.message_id = self.parent_id  # discord.py
        self.member: Optional[Union[Member, User]]
        if self.team_id and self.user_id:
            self.member = state._get_team_member(self.team_id, self.user_id)
        elif self.user_id:
            self.member = state._get_user(self.user_id)
        else:
            self.member = None

    def is_message_event(self) -> bool:
        """:class:`bool`: Whether this event pertains to a message reaction."""
        return self._from_message
