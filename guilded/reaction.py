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

from typing import TYPE_CHECKING, AsyncIterator, Literal, Optional, Set, Union

from .emote import Emote

if TYPE_CHECKING:
    from guilded.abc import ServerChannel, User as abc_User
    from .types.reaction import ChannelMessageReaction as ChannelMessageReactionPayload

    from .message import ChatMessage
    from .server import Server
    from .user import User, Member

__all__ = (
    'RawReactionActionEvent',
    'Reaction',
)


class Reaction:
    """Represents an emoji reaction on an instance of content (represented by :attr:`.parent`).

    Attributes
    -----------
    parent: :class:`.ChatMessage`
        The content that the reaction is on.
    message: :class:`.ChatMessage`
        |dpyattr|

        This is an alias of :attr:`.parent`

        The content that the reaction is on.
    emote: :class:`.Emote`
        The emote that the reaction shows.
    user: Optional[Union[:class:`.Member`, :class:`~guilded.User`]]
        If in the context of a reaction event, this is the user who added or
        removed the reaction.
        For most cases, :meth:`.users` should be used instead.
    """

    __slots__ = (
        '_state',
        '_user_ids',
        'parent',
        'message',
        'channel_id',
        'message_id',
        '_user_id',
        'user',
        'emote',
    )

    def __init__(self, *, data: ChannelMessageReactionPayload, parent: ChatMessage):
        self._state = parent._state
        self.parent = parent
        self.message = parent

        self.channel_id = data.get('channelId')
        self.message_id = data.get('messageId')
        self._user_id = data.get('createdBy')
        user = None
        if parent.server and self._user_id:
            user = parent.server.get_member(self._user_id)
        if not user and self._user_id:
            user = self._state._get_user(self._user_id)
        self.user: Optional[Union[Member, User]] = user

        self.emote = Emote(state=self._state, data=data['emote'])

        self._user_ids: Set[str] = set()
        if self._user_id:
            self._user_ids.add(self._user_id)

    @property
    def emoji(self) -> Emote:
        """:class:`.Emote`: This is an alias of :attr:`.emote`.

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
        return self._state._get_server_channel_or_thread(self.channel_id) or self.parent.channel

    def is_custom_emote(self) -> bool:
        """:class:`bool`: Whether this reaction uses a custom emote."""
        return not self.emote.stock

    is_custom_emoji = is_custom_emote

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
            This will be a :class:`.User` if there is no server or if the
            :class:`.Member` is otherwise unavailable.

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
        user_ids = list(self._user_ids)

        while limit > 0:
            if after is not None:
                after_index = user_ids.index(after.id)

            user_ids = list(self._user_ids)[(after_index + 1):]
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
    server: Optional[:class:`Server`]
        The server that the reaction is in, if applicable.
    emote: :class:`.Emote`
        The emote that the reaction shows.
    emoji: :class:`.Emote`
        This is an alias of :attr:`.emote`.

        The emote that the reaction shows.
    member: Optional[Union[:class:`.Member`, :class:`.User`]]
        The member that added or removed their reaction.
        This is only available if the member was cached prior to this event being received.
        This will be a :class:`.User` if the reaction is in a DM.
    event_type: :class:`str`
        The event type that this action was created from.
        For messages, this will be one of ``ChatMessageReactionCreated`` or ``ChatMessageReactionDeleted``.
    """

    __slots__ = (
        'parent_id',
        'message_id',
        'user_id',
        'channel_id',
        'server',
        'emote',
        'member',
        'event_type',
    )

    def __init__(self, *, state, data: ChannelMessageReactionPayload, server: Optional[Server] = None):
        self.parent_id: str = data.get('messageId')
        self.message_id = self.parent_id
        self.user_id: str = data.get('createdBy')
        self.channel_id: str = data.get('channelId')
        self.event_type: Literal['ChatMessageReactionCreated', 'ChatMessageReactionDeleted'] = data['type']
        self.server = server
        self.emote: Emote

        self.emote = Emote(
            state=state,
            data=data['emote'],
        )

        self.member: Optional[Union[Member, User]]
        if self.server and self.user_id:
            self.member = state._get_server_member(self.server.id, self.user_id)
        elif self.user_id:
            self.member = state._get_user(self.user_id)
        else:
            self.member = None
