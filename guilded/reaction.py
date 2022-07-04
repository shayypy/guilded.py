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

from typing import TYPE_CHECKING, AsyncIterator, Optional, Set, Union

from .emote import Emote
from .enums import ChannelType, try_enum

if TYPE_CHECKING:
    from guilded.abc import ServerChannel, User as abc_User
    from .types.reaction import ChannelMessageReaction as ChannelMessageReactionPayload

    from .message import ChatMessage
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
    parent: :class:`.ChatMessage`
        The content that the reaction is on.
    message: :class:`.ChatMessage`
        |dpyattr|

        This is an alias of :attr:`.parent`

        The content that the reaction is on.
    user: Optional[:class:`.Member`]
        The user that added the reaction.
    emote: :class:`.Emote`
        The emote that the reaction shows.
    """

    __slots__ = (
        '_state',
        '_user_ids',
        'parent',
        'message',
        '_channel_id',
        '_message_id',
        'emote',
    )

    def __init__(self, *, data: ChannelMessageReactionPayload, parent: ChatMessage):
        self._state = parent._state
        self.parent = parent
        self.message = parent

        self._channel_id = data.get('channelId')
        self._message_id = data.get('messageId')

        self.emote = Emote(state=self._state, data=data['emote'])

        self._user_ids: Set[str] = set()
        if data.get('createdBy'):
            self._user_ids.add(data.get('createdBy'))

    @property
    def emoji(self) -> Emote:
        """:class:`.Emote`: |dpyattr|

        This is an alias of :attr:`.emote`

        The emote that the reaction shows.
        """
        return self.emote

    @property
    def me(self) -> bool:
        """:class:`bool`: Whether the client added the reaction."""
        return self._state.my_id in self._user_ids

    @property
    def count(self) -> int:
        """:class:`int`: How many users have added this reaction."""
        return len(self._user_ids)

    @property
    def channel(self) -> ServerChannel:
        """:class:`~.abc.ServerChannel`: The channel that the reaction is in."""
        return self._state._get_server_channel_or_thread(self._channel_id) if self._channel_id is not None else self.parent.channel

    def is_custom_emote(self) -> bool:
        """:class:`bool`: Whether this reaction uses a custom emote."""
        return not self.emote.stock

    @property
    def is_custom_emoji(self) -> bool:
        """:class:`bool`: |dpyattr|

        This is an alias of :meth:`.is_custom_emote`\.

        Whether this reaction uses a custom emote.
        """
        return self.is_custom_emote

    async def remove_self(self) -> None:
        """|coro|

        Remove this reaction for yourself.

        You cannot remove other users' reactions.
        """
        await self.parent.remove_self_reaction(self.emote)

    async def users(
        self,
        *,
        limit: Optional[int] = None,
        after: Optional[abc_User] = None
    ) -> AsyncIterator[Union[User, Member]]:
        """An :term:`asynchronous iterator` for the users that have reacted with this emote to this content.

        Results may not be in any expected order.

        Examples
        ---------

        Usage ::

            async for user in reaction.users():
                print(f'{user} reacted with {reaction.emote}')

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
            This will be a :class:`.User` if there is no server or if the member is otherwise unavailable.

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
            server = self.parent.server

            cached_users = []
            new_user_ids = []

            if server is not None:
                for uid in user_ids:
                    user = server.get_member(uid) or self._state._get_user(uid)
                    if user is None:
                        new_user_ids.append(uid)
                    else:
                        cached_users.append(user)

                if new_user_ids:
                    data = await self._state.get_detailed_team_members(
                        server.id,
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
                # server will never be None here
                limit -= len(data)
                after = data[-1]['id']

                for raw_member in data:
                    member = self._state.create_member(data=raw_member, server=server)
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
    server_id: Optional[:class:`str`]
        The server ID that the reaction is in, if applicable.
    emote: :class:`.Emote`
        The emote that the reaction shows.
    member: Optional[Union[:class:`.Member`, :class:`.User`]]
        The member that added or removed their reaction.
        This is only available if the member was cached prior to this event being received.
        This will only be a :class:`.User` if the reaction is in a DM.
    event_type: :class:`str`
        The event type that this action was created from.
        For messages, this will be one of ``ChatMessageReactionCreated`` or ``ChatMessageReactionDeleted``.
    """

    __slots__ = (
        '_from_message',
        'parent_id',
        'message_id',
        'user_id',
        'channel_id',
        'channel_type',
        'server_id',
        'emote',
        'member',
        'event_type',
    )

    def __init__(self, *, state, data: ChannelMessageReactionPayload):
        self._from_message: bool = 'message' in data
        self.parent_id: Union[str, int]
        self.user_id: str
        self.channel_id: str = data.get('channelId')
        self.channel_type: ChannelType
        self.server_id: Optional[str] = data.get('serverId')
        self.emote: Emote
        self.event_type: str = data['type']

        # The message reaction events and else-content reaction events are
        # structured differently enough that I felt this distinction was necessary
        if self._from_message:
            self.parent_id = data['message']['id']
            self.channel_type = ChannelType.chat
            self.user_id = data['reaction'].get('createdBy')
            if 'customReaction' not in data['reaction']:
                emote_id: int = data['reaction']['customReactionId']
                self.emote = (
                    state._get_emote(emote_id)
                    or Emote(state=state, data={'id': emote_id, 'url': ''})
                )
            else:
                self.emote = Emote(
                    state=state,
                    data=data['reaction']['customReaction'],
                )

        else:
            self.parent_id = int(data['contentId']) if data['contentId'].isdigit() else data['contentId']
            self.channel_type = try_enum(ChannelType, data.get('contentType'))
            self.user_id = data.get('userId')
            self.emote = Emote(
                state=state,
                data=data['customReaction'],
            )

        self.message_id = self.parent_id  # discord.py
        self.member: Optional[Union[Member, User]]
        if self.server_id and self.user_id:
            self.member = state._get_server_member(self.server_id, self.user_id)
        elif self.user_id:
            self.member = state._get_user(self.user_id)
        else:
            self.member = None

    def is_message_event(self) -> bool:
        """:class:`bool`: Whether this event pertains to a message reaction."""
        return self._from_message
