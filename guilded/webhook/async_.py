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
import io

import logging
import asyncio
import json
import re

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Sequence, Tuple, Union
from contextvars import ContextVar

import aiohttp

from .. import utils
from ..channel import ChatChannel, ListChannel
from ..enums import FileType, MediaType
from ..errors import HTTPException, Forbidden, NotFound, GuildedServerError
from ..message import ChatMessage
from ..user import Member, User
from ..utils import ISO8601, find
from ..asset import Asset
from ..http import Route, UserbotRoute, handle_message_parameters
from ..file import File

__all__ = (
    'Webhook',
    'WebhookMessage',
)

log = logging.getLogger(__name__)

if TYPE_CHECKING:
    from ..abc import TeamChannel
    from ..http import HTTPClient
    from ..embed import Embed
    from ..team import Team
    import datetime

    from ..types.webhook import Webhook as WebhookPayload

MISSING = utils.MISSING


class AsyncWebhookAdapter:
    async def request(
        self,
        route: Union[UserbotRoute, Route],
        session: aiohttp.ClientSession,
        webhook_id: str,
        *,
        payload: Optional[Dict[str, Any]] = None,
        multipart: Optional[List[Dict[str, Any]]] = None,
        files: Optional[List[File]] = None,
        auth_token: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        userbot: bool = None,
    ) -> Any:
        headers: Dict[str, str] = {}
        files = files or []
        to_send: Optional[Union[str, aiohttp.FormData]] = None

        if auth_token is not None:
            if userbot is None:
                raise ValueError('userbot must be provided if auth_token is also provided.')

            if userbot:
                headers['guilded-client-id'] = auth_token
                headers['cookie'] = f'guilded_mid={auth_token}'
            else:
                headers['Authorization'] = f'Bearer {auth_token}'

        if payload is not None:
            headers['Content-Type'] = 'application/json'
            to_send = json.dumps(payload)

        response: Optional[aiohttp.ClientResponse] = None
        data: Optional[Union[Dict[str, Any], str]] = None
        method = route.method
        url = route.url

        for attempt in range(5):
            for file in files:
                file.reset(seek=attempt)

            if multipart:
                form_data = aiohttp.FormData(quote_fields=False)
                for p in multipart:
                    form_data.add_field(**p)
                to_send = form_data

            try:
                async with session.request(method, url, data=to_send, headers=headers, params=params) as response:
                    log.debug(
                        'Webhook ID %s with %s %s has returned status code %s',
                        webhook_id,
                        method,
                        url,
                        response.status,
                    )
                    data = (await response.text(encoding='utf-8')) or None
                    if data and response.headers['Content-Type'] == 'application/json':
                        data = json.loads(data)

                    if 300 > response.status >= 200:
                        return data

                    if response.status == 429:
                        if not response.headers.get('Via'):
                            raise HTTPException(response, data)

                        retry_after: float
                        try:
                            retry_after = float(data['retry_after'])
                        except (KeyError, TypeError):
                            retry_after = 3.0

                        log.warning('Webhook ID %s is rate limited. Retrying in %.2f seconds', webhook_id, retry_after)
                        await asyncio.sleep(retry_after)
                        continue

                    if response.status >= 500:
                        await asyncio.sleep(1 + attempt * 2)
                        continue

                    if response.status == 403:
                        raise Forbidden(response, data)
                    elif response.status == 404:
                        raise NotFound(response, data)
                    else:
                        raise HTTPException(response, data)

            except OSError as e:
                if attempt < 4 and e.errno in (54, 10054):
                    await asyncio.sleep(1 + attempt * 2)
                    continue
                raise

        if response:
            if response.status >= 500:
                raise GuildedServerError(response, data)
            raise HTTPException(response, data)

        raise RuntimeError('Unreachable code in HTTP handling.')

    def get_webhook(
        self,
        server_id: str,
        webhook_id: str,
        *,
        auth_token: str,
        userbot: bool,
        session: aiohttp.ClientSession,
    ):
        if userbot:
            route = UserbotRoute('GET', f'/teams/{server_id}/members')
        else:
            route = Route('GET', f'/servers/{server_id}/webhooks/{webhook_id}')

        return self.request(route, session, webhook_id, auth_token=auth_token, userbot=userbot)

    def get_webhook_details(
        self,
        server_id: str,
        webhook_id: str,
        *,
        auth_token: str,
        session: aiohttp.ClientSession,
    ):
        # This method is intentionally limited so that it fits the "model" of single-entity operations here.

        route = UserbotRoute('POST', f'/teams/{server_id}/webhooks/detail')
        payload = {
            'webhookIds': [webhook_id],
        }
        return self.request(route, session, webhook_id, payload=payload, auth_token=auth_token, userbot=True)

    def delete_webhook(
        self,
        server_id: str,
        webhook_id: str,
        *,
        auth_token: str,
        userbot: bool,
        session: aiohttp.ClientSession,
    ):
        if userbot:
            route = UserbotRoute('DELETE', f'/webhooks/{webhook_id}')
        else:
            route = Route('DELETE', f'/servers/{server_id}/webhooks/{webhook_id}')

        return self.request(route, session, webhook_id, auth_token=auth_token, userbot=userbot)

    def update_webhook(
        self,
        server_id: str,
        webhook_id: str,
        payload: Dict[str, Any],
        *,
        auth_token: str,
        userbot: bool,
        session: aiohttp.ClientSession,
    ):
        if userbot:
            route = UserbotRoute('PUT', f'/webhooks/{webhook_id}')
        else:
            route = Route('PUT', f'/servers/{server_id}/webhooks/{webhook_id}')

        return self.request(route, session, webhook_id, payload=payload, auth_token=auth_token, userbot=userbot)

    def execute_webhook(
        self,
        webhook_id: str,
        token: str,
        *,
        session: aiohttp.ClientSession,
        payload: Optional[Dict[str, Any]] = None,
        multipart: Optional[List[Dict[str, Any]]] = None,
        files: Optional[List[File]] = None,
    ):
        route = UserbotRoute('POST', f'/webhooks/{webhook_id}/{token}', override_base=UserbotRoute.MEDIA_BASE)
        return self.request(route, session, webhook_id, payload=payload, multipart=multipart, files=files)

    def delete_channel_message(
        self,
        webhook_id: str,
        channel_id: str,
        message_id: str,
        *,
        auth_token: str,
        userbot: bool,
        session: aiohttp.ClientSession,
    ):
        cls = UserbotRoute if userbot else Route
        route = cls('DELETE', f'/channels/{channel_id}/messages/{message_id}')
        return self.request(route, session, webhook_id, auth_token=auth_token, userbot=userbot)

    def get_channel_message(
        self,
        webhook_id: str,
        channel_id: str,
        message_id: str,
        *,
        auth_token: str,
        userbot: bool,
        session: aiohttp.ClientSession,
    ):
        if userbot:
            route = UserbotRoute('GET', f'/content/route/metadata?route=//channels/{channel_id}/chat?messageId={message_id}')
        else:
            route = Route('GET', f'/channels/{channel_id}/messages/{message_id}')
        return self.request(route, session, webhook_id, auth_token=auth_token, userbot=userbot)


async_context: ContextVar[AsyncWebhookAdapter] = ContextVar('async_webhook_context', default=AsyncWebhookAdapter())


class _WebhookState:
    __slots__ = (
        '_parent',
        '_webhook',
        'userbot',
    )

    def __init__(self, webhook: Any, parent: Optional[Union[HTTPClient, _WebhookState]], userbot: bool = None):
        self._webhook: Any = webhook
        self.userbot: bool = userbot

        self._parent: Optional[HTTPClient]
        if isinstance(parent, _WebhookState):
            self._parent = None
        else:
            self._parent = parent

        if self._parent is not None:
            self.userbot = parent.userbot

    def _get_team(self, team_id: str):
        if self._parent is not None:
            return self._parent._get_team(team_id)
        return None

    def _get_team_channel(self, team_id: str, channel_id: str):
        if self._parent is not None:
            return self._parent._get_team_channel(team_id, channel_id)
        return None

    def _get_emoji(self, emoji_id: str):
        if self._parent is not None:
            return self._parent._get_emoji(emoji_id)
        return None

    def _get_team_member(self, team_id: str, user_id: str):
        if self._parent is not None:
            return self._parent._get_team_member(team_id, user_id)
        return None

    def _get_user(self, user_id: str):
        if self._parent is not None:
            return self._parent._get_user(user_id)
        return None

    def store_user(self, data):
        if self._parent is not None:
            return self._parent.store_user(data)
        # state parameter is artificial
        return User(state=self, data=data)  # type: ignore

    def create_user(self, **data):
        # state parameter is artificial
        return User(state=self, **data)  # type: ignore

    def create_member(self, **data):
        return Member(state=self, **data)

    def __getattr__(self, attr):
        if self._parent is not None:
            return getattr(self._parent, attr)

        raise AttributeError(f'PartialWebhookState does not support {attr!r}.')


class WebhookMessage(ChatMessage):
    """Represents a message sent from your webhook.

    This allows you to delete a message sent by your webhook, although the
    parent webhook requires authentication information.

    This inherits from :class:`.ChatMessage` with changes to
    :meth:`delete` to work.
    """

    _state: _WebhookState

    async def edit(self, *args, **kwargs):
        raise AttributeError('WebhookMessages cannot be edited.')

    async def delete(self, *, delay: Optional[float] = None) -> None:
        """|coro|

        Deletes the message.

        Parameters
        -----------
        delay: Optional[:class:`float`]
            If provided, the number of seconds to wait before deleting the message.
            The waiting is done in the background and deletion failures are ignored.

        Raises
        ------
        Forbidden
            You do not have proper permissions to delete the message.
        NotFound
            The message was deleted already.
        HTTPException
            Deleting the message failed.
        ValueError
            This instance of a webhook does not have authentication info associated with it.
        """

        if delay is not None:

            async def inner_call(delay: float = delay):
                await asyncio.sleep(delay)
                try:
                    await self._state._webhook.delete_message(self.channel_id, self.id)
                except HTTPException:
                    pass

            asyncio.create_task(inner_call())
        else:
            await self._state.delete_message(self.channel_id, self.id)


class BaseWebhook:
    __slots__: Tuple[str, ...] = (
        'auth_token',
        '_state',
        'id',
        'channel_id',
        'team_id',
        'name',
        '_icon_url',
        'token',
        'created_by_id',
        'created_at',
        'deleted_at',
    )

    def __init__(self, data: WebhookPayload, auth_token: Optional[str] = None, state: Optional[HTTPClient] = None, userbot: bool = None):
        self.auth_token: Optional[str] = auth_token
        if userbot is None and state is not None:
            userbot = state.userbot

        self._state: Union[HTTPClient, _WebhookState] = state or _WebhookState(self, parent=state, userbot=userbot)
        self._update(data.get('webhook', data))

    def __repr__(self):
        return f'<{self.__class__.__name__} id={self.id!r} team={self.team!r}>'

    def _update(self, data: WebhookPayload):
        self.id: str = data['id']
        self.channel_id: Optional[str] = data.get('channelId')
        self.team_id: Optional[str] = data.get('teamId', data.get('serverId'))
        self.name: Optional[str] = data.get('name')
        self._icon_url = data.get('iconUrl')
        self.token: Optional[str] = data.get('token')
        self.created_by_id: Optional[str] = data.get('createdBy')
        self.created_at: Optional[datetime.datetime] = ISO8601(data.get('createdAt'))
        self.deleted_at: Optional[datetime.datetime] = ISO8601(data.get('deletedAt'))

    def _update_details(self, data: WebhookPayload):
        # This is specifically for the data received for Get Webhook Details
        self.created_at = ISO8601(data.get('createdAt'))
        self.created_by_id = data.get('createdBy')
        self.token = data.get('token')

    def is_partial(self) -> bool:
        """:class:`bool`: Whether the webhook is a "partial" webhook."""
        return self.channel_id is None

    def is_authenticated(self) -> bool:
        """:class:`bool`: Whether the webhook has non-webhook authentication information associated with it.

        If this is not ``True``, you will not be able to manage messages sent
        by this webhook, nor delete or edit the webhook itself.
        """
        return self.auth_token is not None

    @property
    def team(self) -> Optional[Team]:
        """Optional[:class:`.Team`]: The team this webhook belongs to.

        If this is a partial webhook, then this will always return ``None``.
        """
        return self._state and self._state._get_team(self.team_id)

    @property
    def server(self) -> Optional[Team]:
        """Optional[:class:`.Team`]: This is an alias of :attr:`.team`."""
        return self.team

    @property
    def guild(self) -> Optional[Team]:
        """|dpyattr|

        This is an alias of :attr:`.team`.
        """
        return self.team

    @property
    def channel(self) -> Optional[Union[ChatChannel, ListChannel]]:
        """Optional[Union[:class:`.ChatChannel`, :class:`.ListChannel`]]: The channel this webhook belongs to.

        If this is a partial webhook, then this will always return ``None``.
        """
        team = self.team
        return team and team.get_channel(self.channel_id)  # type: ignore

    @property
    def avatar(self) -> Optional[Asset]:
        """Optional[:class:`Asset`]: Returns an :class:`Asset` for the avatar the webhook has.

        If the webhook does not have an uploaded avatar, ``None`` is returned.
        If you want the avatar that the webhook displays, consider :attr:`display_avatar` instead.
        """
        if self._icon_url is not None:
            return Asset._from_user_avatar(self._state, self._icon_url)
        return None

    @property
    def default_avatar(self) -> Asset:
        """:class:`Asset`: Returns the default avatar.
        This is always `'Gil' <https://img.guildedcdn.com/asset/Default/Gil-md.png>`_."""
        return Asset._from_default_asset(self._state, 'Gil')

    @property
    def display_avatar(self) -> Asset:
        """:class:`Asset`: Returns the webhook's display avatar.

        This is either webhook's default avatar or uploaded avatar.
        """
        return self.avatar or self.default_avatar


class Webhook(BaseWebhook):
    """Represents an asynchronous webhook.

    There are two main ways to use Webhooks. The first is through the ones
    received by the library such as :meth:`.Team.webhooks` and
    :meth:`.ChatChannel.webhooks`. The ones received by the library will
    automatically be bound using the library's internal HTTP session.

    The second form involves creating a webhook object manually using the
    :meth:`~.Webhook.from_url` or :meth:`~.Webhook.partial` classmethods.

    For example, creating a webhook from a URL and using :doc:`aiohttp <aio:index>`:

    .. code-block:: python3

        from guilded import Webhook
        import aiohttp

        async def foo():
            async with aiohttp.ClientSession() as session:
                webhook = Webhook.from_url('url-here', session=session)
                await webhook.send('Hello World')

    .. container:: operations

        .. describe:: x == y

            Checks if two webhooks are equal.

        .. describe:: x != y

            Checks if two webhooks are not equal.

    Attributes
    ------------
    id: :class:`str`
        The webhook's ID
    token: Optional[:class:`str`]
        The authentication token of the webhook. If this is ``None``
        then the webhook cannot be used to send messages.
    team_id: Optional[:class:`str`]
        The team ID this webhook is for.
    channel_id: Optional[:class:`str`]
        The channel ID this webhook is for.
    name: Optional[:class:`str`]
        The webhook's name.
    created_at: :class:`datetime.datetime`
        When the webhook was created.
    deleted_at: Optional[:class:`datetime.datetime`]
        When the webhook was deleted.
    """

    __slots__: Tuple[str, ...] = ('session',)

    def __init__(self, data, session: aiohttp.ClientSession, auth_token: Optional[str] = None, state: Optional[HTTPClient] = None, userbot: Optional[bool] = None):
        super().__init__(data, auth_token, state, userbot)
        self.session = session

    @property
    def url(self) -> str:
        """:class:`str`: Returns the webhook's URL."""
        return f'https://media.guilded.gg/webhooks/{self.id}/{self.token}'

    @classmethod
    def partial(
        cls,
        id: str,
        token: str,
        *,
        session: aiohttp.ClientSession,
        auth_token: Optional[str] = None,
        bot: Optional[bool] = True
    ) -> Webhook:
        """Creates a partial :class:`Webhook`.

        Parameters
        -----------
        id: :class:`str`
            The ID of the webhook.
        token: :class:`str`
            The authentication token of the webhook.
        session: :class:`aiohttp.ClientSession`
            The session to use to send requests with.
            Note that the library does not manage the session and will not close it.
        auth_token: Optional[:class:`str`]
            The bot authentication token for authenticated requests
            involving the webhook.
            For user authentication, this should be a ``guilded_mid`` cookie.
        bot: Optional[:class:`bool`]
            Whether ``auth_token`` represents a bot account.

        Returns
        --------
        :class:`Webhook`
            A partial :class:`Webhook`.
            A partial webhook is a webhook object with only an ID and a token.
        """
        data = {
            'id': id,
            'token': token,
        }

        return cls(data, session, auth_token=auth_token, userbot=not bot)

    @classmethod
    def from_url(
        cls,
        url: str,
        *,
        session: aiohttp.ClientSession,
        auth_token: Optional[str] = None,
        bot: Optional[bool] = True
    ) -> Webhook:
        """Creates a partial :class:`Webhook` from a webhook URL.

        Parameters
        ------------
        url: :class:`str`
            The URL of the webhook.
        session: :class:`aiohttp.ClientSession`
            The session to use to send requests with.
            Note that the library does not manage the session and will not close it.
        auth_token: Optional[:class:`str`]
            The bot authentication token for authenticated requests
            involving the webhook.
            For user authentication, this should be a ``guilded_mid`` cookie.
        bot: Optional[:class:`bool`]
            Whether ``auth_token`` represents a bot account.

        Returns
        --------
        :class:`Webhook`
            A partial :class:`Webhook`.
            A partial webhook is a webhook object with only an ID and a token.

        Raises
        -------
        ValueError
            The URL is invalid.
        """
        # media.guilded.gg/webhooks & www.guilded.gg/api/webhooks are both valid,
        # but only the former will be generated by the client.
        # [A-Za-z0-9\.\-\_] may be needlessly broad for tokens.
        m = re.search(r'(?:media\.guilded\.gg|guilded\.gg\/api)\/webhooks/(?P<id>[0-9a-fA-F]{8}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{12})/(?P<token>[A-Za-z0-9\.\-\_]{80,90})', url)
        if m is None:
            raise ValueError('Invalid webhook URL given.')

        data: Dict[str, Any] = m.groupdict()
        return cls(data, session, auth_token=auth_token, userbot=not bot)  # type: ignore

    @classmethod
    def from_state(cls, data: WebhookPayload, state: HTTPClient) -> Webhook:
        session = state.session
        token = state.cookie if state.userbot else state.token
        return cls(data, session=session, state=state, auth_token=token)

    async def fetch(self, *, team: Optional[Team] = None) -> Webhook:
        """|coro|

        Fetches the current webhook.

        This could be used to get a full webhook from a partial webhook.

        This requires an authenticated webhook.

        Parameters
        -----------
        team: Optional[:class:`.Team`]
            The team that this webhook exists in.
            This is only required if :attr:`.team_id` is ``None``.

        Returns
        --------
        :class:`Webhook`
            The fetched webhook.

        Raises
        -------
        HTTPException
            Could not fetch the webhook.
        NotFound
            Could not find the webhook by this ID.
        ValueError
            This instance of a webhook does not have authentication info associated with it,
            could not find the webhook by this ID (the client is a user account),
            or no team was provided but it is required.
        """

        if not self.auth_token:
            raise ValueError('This instance of a webhook does not have authentication info associated with it.')
        if not team and not self.team_id:
            raise ValueError('team must be provided if this instance of a webhook\'s team_id is None.')

        adapter = async_context.get()
        data = await adapter.get_webhook(self.team_id or team.id, self.id, auth_token=self.auth_token, userbot=self._state.userbot, session=self.session)
        if self._state.userbot:
            data = find(lambda d: d['id'] == self.id, data['webhooks'])
            if data is None:
                raise ValueError(f'Could not find the webhook by the ID {self.id}')

        return Webhook(data, self.session, auth_token=self.auth_token, state=self._state)

    async def fill_details(self, *, team: Optional[Team] = None) -> Webhook:
        """|coro|

        |onlyuserbot|

        Fills the details for the current webhook instance.

        This method is mainly useful for filling in :attr:`.token` if it is not already present.
        It is separate from :meth:`.fetch` in that :meth:`.fetch` does not provide :attr:`.token` if the client is a user account.
        Similarly, this method does not provide many of the details that :meth:`.fetch` does.

        This requires an authenticated webhook.

        Parameters
        -----------
        team: Optional[:class:`.Team`]
            The team that this webhook exists in.
            This is only required if :attr:`.team_id` is ``None``.

        Returns
        --------
        :class:`Webhook`
            The current webhook instance with details filled in.

        Raises
        -------
        HTTPException
            Could not fill the webhook's details.
        ValueError
            This instance of a webhook does not have authentication info associated with it,
            could not find the webhook by this ID,
            or no team was provided but it is required.
        """

        if not self.auth_token:
            raise ValueError('This instance of a webhook does not have authentication info associated with it.')
        if not team and not self.team_id:
            raise ValueError('team must be provided if this instance of a webhook\'s team_id is None.')

        adapter = async_context.get()
        data = await adapter.get_webhook_details(self.team_id or team.id, self.id, auth_token=self.auth_token, session=self.session)
        if not data:
            raise ValueError(f'Could not find the webhook by the ID {self.id}')

        self._update_details(data[self.id])
        return self

    async def delete(self, *, team: Optional[Team] = None) -> Optional[datetime.datetime]:
        """|coro|

        Deletes this webhook.

        This requires an authenticated webhook.

        Parameters
        -----------
        team: Optional[:class:`.Team`]
            The team that this webhook exists in.
            This is only required if :attr:`.team_id` is ``None`` and the client is a bot account.

        Returns
        --------
        Optional[:class:`datetime.datetime`]
            If the client is a user account, the :class:`datetime.datetime`
            when this webhook was deleted, else ``None``.

        Raises
        -------
        HTTPException
            Deleting the webhook failed.
        NotFound
            This webhook does not exist.
        Forbidden
            You do not have permissions to delete this webhook.
        ValueError
            This instance of a webhook does not have authentication info associated with it
            or no team was provided but it is required.
        """
        if self.auth_token is None:
            raise ValueError('This instance of a webhook does not have authentication info associated with it.')
        if not team and not self.team_id and not self._state.userbot:
            raise ValueError('team must be provided if this instance of a webhook\'s team_id is None.')

        adapter = async_context.get()
        data = await adapter.delete_webhook(self.team_id or team.id, self.id, auth_token=self.auth_token, userbot=self._state.userbot, session=self.session)
        if self._state.userbot:
            deleted_at = ISO8601(data.get('deletedAt'))
            self.deleted_at = deleted_at
            return deleted_at

    async def edit(
        self,
        *,
        name: Optional[str] = MISSING,
        avatar: Optional[Union[bytes, File]] = MISSING,
        channel: Optional[Union[ChatChannel, ListChannel]] = None,
        team: Optional[Team] = None,
    ) -> Webhook:
        """|coro|

        Edits this webhook.

        This requires an authenticated webhook.

        Parameters
        ------------
        name: Optional[:class:`str`]
            The webhook's new name.
        channel: Union[:class:`ChatChannel`, :class:`ListChannel`]
            The channel to move the webhook to.
        avatar: Optional[Union[:class:`bytes`, :class:`File`]]
            A :term:`py:bytes-like object` or :class:`File` for the webhook's new avatar.
            If the client is a bot user, providing this does nothing.
        team: Optional[:class:`.Team`]
            The team that this webhook exists in.
            This is only required if :attr:`.team_id` is ``None`` and the client is a bot account.

        Returns
        --------
        :class:`.Webhook`
            The updated webhook.

        Raises
        -------
        HTTPException
            Editing the webhook failed.
        NotFound
            This webhook does not exist.
        ValueError
            This instance of a webhook does not have authentication info associated with it
            or no team was provided but it is required.
        """
        if self.auth_token is None:
            raise ValueError('This instance of a webhook does not have authentication info associated with it.')
        if not team and not self.team_id and not self._state.userbot:
            raise ValueError('team must be provided if this instance of a webhook\'s team_id is None.')

        payload = {}
        if name is not MISSING:
            payload['name'] = str(name) if name is not None else None

        if channel is not None:
            payload['channelId'] = channel.id

        if avatar is not MISSING and self._state.userbot:
            if isinstance(avatar, bytes):
                avatar = File(io.BytesIO(avatar), file_type=FileType.image)
            elif not isinstance(avatar, File):
                raise TypeError(f'avatar must be type bytes or File, not {avatar.__class__.__name__}')

            avatar.set_media_type(MediaType.user_avatar)
            await avatar._upload()
            payload['iconUrl'] = avatar.url

        adapter = async_context.get()
        data = await adapter.update_webhook(
            self.team_id or team.id,
            self.id,
            auth_token=self.auth_token,
            userbot=self._state.userbot,
            payload=payload,
            session=self.session
        )

        return Webhook(data=data, session=self.session, auth_token=self.auth_token, userbot=self._state.userbot, state=self._state)

    async def move(self, to: Union[ChatChannel, ListChannel]):
        """|coro|

        Moves this webhook to another channel.

        Parameters
        -----------
        to: Union[:class:`.ChatChannel`, :class:`.ListChannel`]
            The channel to move the webhook to.

        Returns
        --------
        :class:`.Webhook`
            The updated webhook.

        Raises
        -------
        HTTPException
            Editing the webhook failed.
        NotFound
            This webhook does not exist.
        ValueError
            This instance of a webhook does not have authentication info associated with it.
        """
        return await self.edit(channel=to, team=to.team)

    def _create_message(self, data):
        state = _WebhookState(self, parent=self._state)
        # state may be artificial (unlikely at this point...)
        channel = self.channel or ChatChannel(state=self._state, data={'id': data['channelId']}, group=None)  # type: ignore
        # state is artificial
        return WebhookMessage(data=data, state=state, channel=channel, webhook=self)  # type: ignore

    async def send(
        self,
        content: str = MISSING,
        *,
        embed: Embed = MISSING,
        embeds: Sequence[Embed] = MISSING,
        file: File = MISSING,
        files: Sequence[File] = MISSING,
    ) -> WebhookMessage:
        """|coro|

        Sends a message using this webhook.

        The content must be a type that can convert to a string through ``str(content)``.

        To upload a single file, the ``file`` parameter should be used with a
        single :class:`File` object.

        If the ``embed`` parameter is provided, it must be of type :class:`Embed` and
        it must be a rich embed type. You cannot mix the ``embed`` parameter with the
        ``embeds`` parameter, which must be a :class:`list` of :class:`Embed` objects to send.

        Parameters
        ------------
        content: :class:`str`
            The content of the message to send.
        file: :class:`File`
            The file to upload. This cannot be mixed with ``files`` parameter.
        files: List[:class:`File`]
            A list of files to send with the content. This cannot be mixed with the
            ``file`` parameter.
        embed: :class:`Embed`
            The rich embed for the content to send. This cannot be mixed with
            ``embeds`` parameter.
        embeds: List[:class:`Embed`]
            A list of embeds to send with the content. Maximum of 10. This cannot
            be mixed with the ``embed`` parameter.

        Returns
        ---------
        :class:`WebhookMessage`
            The message that was sent.

        Raises
        --------
        HTTPException
            Sending the message failed.
        NotFound
            This webhook was not found.
        Forbidden
            The token for the webhook is incorrect.
        TypeError
            You specified both ``embed`` and ``embeds`` or ``file`` and ``files``.
        ValueError
            The length of ``embeds`` was invalid or there was no token
            associated with this webhook.
        """

        if self.token is None:
            raise ValueError('This instance of a webhook does not a token associated with it.')

        if content is None:
            content = MISSING

        params = handle_message_parameters(
            content=content,
            file=file,
            files=files,
            embed=embed,
            embeds=embeds,
        )
        adapter = async_context.get()

        data = await adapter.execute_webhook(
            self.id,
            self.token,
            session=self.session,
            payload=params.payload,
            multipart=params.multipart,
            files=params.files,
        )

        message = self._create_message(data)
        self.team_id = message.team_id

        return message

    async def fetch_message(self, id: str, *, channel: Optional[ChatChannel] = None) -> WebhookMessage:
        """|coro|

        Retrieves a single :class:`.WebhookMessage` sent by this webhook.

        This requires an authenticated webhook.

        Parameters
        ------------
        id: :class:`str`
            The message ID to look for.
        channel: Optional[:class:`.ChatChannel`]
            The channel that this message exists in.
            This is only required if :attr:`.channel_id` is ``None``.

        Returns
        --------
        :class:`.WebhookMessage`
            The message that was asked for.

        Raises
        --------
        NotFound
            The specified message was not found.
        Forbidden
            You do not have the permissions required to get a message.
        HTTPException
            Retrieving the message failed.
        ValueError
            This instance of a webhook does not have authentication info associated with it
            or no channel was provided but it is required.
        """

        if not self.auth_token:
            raise ValueError('This instance of a webhook does not have authentication info associated with it.')
        if self.channel_id is None or channel is None:
            raise ValueError('channel must be provided if this instance of a webhook\'s channel_id is None.')

        channel_id = channel.id if channel is not None else self.channel_id

        adapter = async_context.get()
        data = await adapter.get_channel_message(
            self.id,
            channel_id,
            id,
            auth_token=self.auth_token,
            userbot=self._state.userbot,
            session=self.session,
        )
        if self._state.userbot:
            data = data['metadata']['message']

        return self._create_message(data)

    async def delete_message(self, id: str, *, channel: Optional[ChatChannel] = None) -> None:
        """|coro|

        Deletes a message sent by this webhook.

        This is a lower level interface to :meth:`.WebhookMessage.delete` in case
        you only have an ID.

        This requires an authenticated webhook.

        Parameters
        ------------
        id: :class:`str`
            The message ID to delete.
        channel: Optional[:class:`.ChatChannel`]
            The channel that this message exists in.
            This is only required if :attr:`.channel_id` is ``None``.

        Raises
        -------
        HTTPException
            Deleting the message failed.
        Forbidden
            Deleted a message that is not yours.
        ValueError
            This instance of a webhook does not have authentication info associated with it
            or no channel was provided but it is required.
        """

        if self.auth_token is None:
            raise ValueError('This instance of a webhook does not have authentication info associated with it.')
        if self.channel_id is None or channel is None:
            raise ValueError('channel must be provided if this instance of a webhook\'s channel_id is None.')

        channel_id = channel.id if channel is not None else self.channel_id

        adapter = async_context.get()
        await adapter.delete_channel_message(
            self.id,
            channel_id,
            id,
            auth_token=self.auth_token,
            userbot=self._state.userbot,
            session=self.session,
        )

    async def edit_message(self, *args, **kwargs):
        raise AttributeError('Webhook messages cannot be edited.')
