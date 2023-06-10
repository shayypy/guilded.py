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

import logging
import asyncio
import json
import re

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Sequence, Tuple, Union
from contextvars import ContextVar

import aiohttp

from .. import utils
from ..channel import ChatChannel, ListChannel, ListItem
from ..errors import HTTPException, Forbidden, NotFound, GuildedServerError
from ..message import ChatMessage
from ..user import Member, User
from ..utils import ISO8601
from ..asset import Asset
from ..http import Route, handle_message_parameters
from ..file import File

__all__ = (
    'Webhook',
    'WebhookMessage',
)

log = logging.getLogger(__name__)

if TYPE_CHECKING:
    from ..abc import ServerChannel
    from ..http import HTTPClient
    from ..embed import Embed
    from ..emote import Emote
    from ..server import Server

    from ..types.webhook import Webhook as WebhookPayload

    import datetime

MISSING = utils.MISSING


class AsyncWebhookAdapter:
    async def request(
        self,
        route: Route,
        session: aiohttp.ClientSession,
        webhook_id: str,
        *,
        payload: Optional[Dict[str, Any]] = None,
        multipart: Optional[List[Dict[str, Any]]] = None,
        files: Optional[List[File]] = None,
        auth_token: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Any:
        headers: Dict[str, str] = {}
        files = files or []
        to_send: Optional[Union[str, aiohttp.FormData]] = None

        if auth_token is not None:
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

    def get_server_webhook(
        self,
        server_id: str,
        webhook_id: str,
        *,
        auth_token: str,
        session: aiohttp.ClientSession,
    ):
        route = Route('GET', f'/servers/{server_id}/webhooks/{webhook_id}')
        return self.request(route, session, webhook_id, auth_token=auth_token)

    def delete_webhook(
        self,
        server_id: str,
        webhook_id: str,
        *,
        auth_token: str,
        session: aiohttp.ClientSession,
    ):
        route = Route('DELETE', f'/servers/{server_id}/webhooks/{webhook_id}')
        return self.request(route, session, webhook_id, auth_token=auth_token)

    def update_webhook(
        self,
        server_id: str,
        webhook_id: str,
        payload: Dict[str, Any],
        *,
        auth_token: str,
        session: aiohttp.ClientSession,
    ):
        route = Route('PUT', f'/servers/{server_id}/webhooks/{webhook_id}')
        return self.request(route, session, webhook_id, payload=payload, auth_token=auth_token)

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
        route = Route('POST', f'/webhooks/{webhook_id}/{token}', override_base=Route.MEDIA_BASE)
        return self.request(route, session, webhook_id, payload=payload, multipart=multipart, files=files)

    def delete_channel_message(
        self,
        webhook_id: str,
        channel_id: str,
        message_id: str,
        *,
        auth_token: str,
        session: aiohttp.ClientSession,
    ):
        route = Route('DELETE', f'/channels/{channel_id}/messages/{message_id}')
        return self.request(route, session, webhook_id, auth_token=auth_token)

    def get_channel_message(
        self,
        webhook_id: str,
        channel_id: str,
        message_id: str,
        *,
        auth_token: str,
        session: aiohttp.ClientSession,
    ):
        route = Route('GET', f'/channels/{channel_id}/messages/{message_id}')
        return self.request(route, session, webhook_id, auth_token=auth_token)


async_context: ContextVar[AsyncWebhookAdapter] = ContextVar('async_webhook_context', default=AsyncWebhookAdapter())


class _WebhookState:
    __slots__ = (
        '_parent',
        '_webhook',
    )

    def __init__(self, webhook: Webhook, parent: Optional[Union[HTTPClient, _WebhookState]]):
        self._webhook: Webhook = webhook

        self._parent: Optional[HTTPClient]
        if isinstance(parent, _WebhookState):
            self._parent = None
        else:
            self._parent = parent

    def _get_server(self, server_id: str) -> Optional[Server]:
        if self._parent is not None:
            return self._parent._get_server(server_id)
        return None

    def _get_server_channel(self, server_id: str, channel_id: str) -> Optional[ServerChannel]:
        if self._parent is not None:
            return self._parent._get_server_channel(server_id, channel_id)
        return None

    def _get_emote(self, emote_id: str) -> Optional[Emote]:
        if self._parent is not None:
            return self._parent._get_emote(emote_id)
        return None

    def _get_server_member(self, server_id: str, user_id: str) -> Optional[Member]:
        if self._parent is not None:
            return self._parent._get_server_member(server_id, user_id)
        return None

    def _get_user(self, user_id: str) -> Optional[User]:
        if self._parent is not None:
            return self._parent._get_user(user_id)
        return None

    def _get_message(self, message_id: str) -> Optional[ChatMessage]:
        if self._parent is not None:
            return self._parent._get_message(message_id)
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
        raise AttributeError('Webhook messages cannot be edited.')

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
            await self._state._webhook.delete_message(self.channel_id, self.id)


class BaseWebhook:
    __slots__: Tuple[str, ...] = (
        'auth_token',
        '_state',
        'id',
        'channel_id',
        'server_id',
        'name',
        '_avatar_url',
        'token',
        'created_by_id',
        'created_at',
        'deleted_at',
    )

    def __init__(
        self,
        data: WebhookPayload,
        auth_token: Optional[str] = None,
        state: Optional[HTTPClient] = None,
    ):
        self.auth_token: Optional[str] = auth_token

        self._state: Union[HTTPClient, _WebhookState] = state or _WebhookState(self, parent=state)
        self._update(data.get('webhook', data))

    def __repr__(self):
        return f'<{self.__class__.__name__} id={self.id!r} server={self.server!r}>'

    def _update(self, data: WebhookPayload):
        self.id: str = data['id']
        self.channel_id: Optional[str] = data.get('channelId')
        self.server_id: Optional[str] = data.get('serverId')
        self.name: Optional[str] = data.get('name')
        self._avatar_url: Optional[str] = data.get('avatar')
        self.token: Optional[str] = data.get('token')
        self.created_by_id: Optional[str] = data.get('createdBy')
        self.created_at: Optional[datetime.datetime] = ISO8601(data.get('createdAt'))
        self.deleted_at: Optional[datetime.datetime] = ISO8601(data.get('deletedAt'))

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
    def server(self) -> Optional[Server]:
        """Optional[:class:`.Server`]: The server this webhook belongs to.

        If this is a partial webhook, then this will always return ``None``.
        """
        return self._state and self._state._get_server(self.server_id)

    @property
    def guild(self) -> Optional[Server]:
        """Optional[:class:`.Server`]: |dpyattr|

        This is an alias of :attr:`.server`.
        """
        return self.server

    @property
    def channel(self) -> Optional[Union[ChatChannel, ListChannel]]:
        """Optional[Union[:class:`.ChatChannel`, :class:`.ListChannel`]]: The channel this webhook belongs to.

        If this is a partial webhook, then this will always return ``None``.
        """
        server = self.server
        return server and server.get_channel(self.channel_id)  # type: ignore

    @property
    def avatar(self) -> Optional[Asset]:
        """Optional[:class:`Asset`]: Returns an :class:`Asset` for the avatar the webhook has.

        If the webhook does not have an uploaded avatar, ``None`` is returned.
        If you want the avatar that the webhook displays, consider :attr:`display_avatar` instead.
        """
        if self._avatar_url is not None:
            return Asset._from_user_avatar(self._state, self._avatar_url)
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
    received by the library such as :meth:`.Server.webhooks` and
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
    server_id: Optional[:class:`str`]
        The server ID this webhook is for.
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

    def __init__(
        self,
        data: WebhookPayload,
        session: aiohttp.ClientSession,
        auth_token: Optional[str] = None,
        state: Optional[HTTPClient] = None,
    ):
        super().__init__(data, auth_token, state)
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

        return cls(data, session, auth_token=auth_token)

    @classmethod
    def from_url(
        cls,
        url: str,
        *,
        session: aiohttp.ClientSession,
        auth_token: Optional[str] = None,
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
            The bot authentication token for authenticated requests involving the webhook.
            This is required to fetch and delete messages and the webhook itself.

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
        # but only the former will be generated by the client, and it is the only one that supports files.
        # [A-Za-z0-9\.\-\_] may be needlessly broad for tokens.
        m = re.search(r'(?:media\.guilded\.gg|guilded\.gg\/api)\/webhooks/(?P<id>[0-9a-fA-F]{8}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{12})/(?P<token>[A-Za-z0-9\.\-\_]{80,90})', url)
        if m is None:
            raise ValueError('Invalid webhook URL given.')

        data: Dict[str, Any] = m.groupdict()
        return cls(data, session, auth_token=auth_token)  # type: ignore

    @classmethod
    def from_state(cls, data: WebhookPayload, state: HTTPClient) -> Webhook:
        return cls(data, session=state.session, state=state, auth_token=state.token)

    async def fetch(self, *, server: Optional[Server] = None) -> Webhook:
        """|coro|

        Fetches the current webhook.

        This could be used to get a full webhook from a partial webhook.

        This requires an authenticated webhook.

        Parameters
        -----------
        server: Optional[:class:`.Server`]
            The server that the webhook exists in.
            This is only required if :attr:`.server_id` is ``None``.

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
            This instance of a webhook does not have authentication info associated with it
            or no server was provided but it is required.
        """

        if not self.auth_token:
            raise ValueError('This instance of a webhook does not have authentication info associated with it.')
        if not server and not self.server_id:
            raise ValueError('server must be provided if this instance of a webhook\'s server_id is None.')

        adapter = async_context.get()
        data = await adapter.get_server_webhook(
            self.server_id or server.id,
            self.id,
            auth_token=self.auth_token,
            session=self.session,
        )

        return Webhook(data, self.session, auth_token=self.auth_token, state=self._state)

    async def delete(self, *, server: Optional[Server] = None) -> None:
        """|coro|

        Deletes this webhook.

        This requires an authenticated webhook.

        Parameters
        -----------
        server: Optional[:class:`.Server`]
            The server that the webhook exists in.
            This is only required if :attr:`.server_id` is ``None``.

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
            or no server was provided but it is required.
        """

        if self.auth_token is None:
            raise ValueError('This instance of a webhook does not have authentication info associated with it.')
        if not server and not self.server_id:
            raise ValueError('server must be provided if this instance of a webhook\'s server_id is None.')

        adapter = async_context.get()
        await adapter.delete_webhook(
            self.server_id or server.id,
            self.id,
            auth_token=self.auth_token,
            session=self.session,
        )

    async def edit(
        self,
        *,
        name: Optional[str] = MISSING,
        channel: Optional[Union[ChatChannel, ListChannel]] = None,
        server: Optional[Server] = None,
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
        server: Optional[:class:`.Server`]
            The server that the webhook exists in.
            This is only required if :attr:`.server_id` is ``None``.

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
            or no server was provided but it is required.
        """

        if self.auth_token is None:
            raise ValueError('This instance of a webhook does not have authentication info associated with it.')
        if not server and not self.server_id:
            raise ValueError('server must be provided if this instance of a webhook\'s server_id is None.')

        payload = {}
        if name is not MISSING:
            payload['name'] = str(name) if name is not None else None

        if channel is not None:
            payload['channelId'] = channel.id

        adapter = async_context.get()
        data = await adapter.update_webhook(
            self.server_id or server.id,
            self.id,
            auth_token=self.auth_token,
            payload=payload,
            session=self.session
        )

        return Webhook(data=data, session=self.session, auth_token=self.auth_token, state=self._state)

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
        return await self.edit(channel=to, server=to.server)

    def _create_message(self, data: Dict[str, Any]):
        state = _WebhookState(self, parent=self._state)
        # state may be artificial (unlikely at this point...)
        channel = self.channel or ChatChannel(state=self._state, data={'id': data['channelId']}, group=None)  # type: ignore
        # state is artificial
        return WebhookMessage(data=data, state=state, channel=channel, webhook=self)  # type: ignore

    async def send(
        self,
        content: str = MISSING,
        *,
        username: str = MISSING,
        avatar_url: Any = MISSING,
        embed: Embed = MISSING,
        embeds: Sequence[Embed] = MISSING,
        file: File = MISSING,
        files: Sequence[File] = MISSING,
    ) -> Union[WebhookMessage, ListItem]:
        """|coro|

        Sends a message or create a list item using this webhook.

        .. warning::

            If this webhook is in a :class:`ListChannel`, this method will
            return a :class:`ListItem` instead of a :class:`WebhookMessage`.

        The content must be a type that can convert to a string through ``str(content)``.

        To upload a single file, the ``file`` parameter should be used with a
        single :class:`File` object.

        If the ``embed`` parameter is provided, it must be of type :class:`Embed` and
        it must be a rich embed type. You cannot mix the ``embed`` parameter with the
        ``embeds`` parameter, which must be a :class:`list` of :class:`Embed` objects to send.

        Parameters
        ------------
        content: :class:`str`
            The :attr:`~WebhookMessage.content` of the message to send,
            or the :attr:`~ListItem.message` of the list item to create.
        username: :class:`str`
            A custom username to use with this message instead of the
            webhook's own username.

            .. versionadded:: 1.4
        avatar_url: :class:`str`
            A custom avatar URL to use with this message instead of the
            webhook's own avatar.
            This is explicitly cast to ``str`` if it is not already.

            .. versionadded:: 1.4
        file: :class:`File`
            The file to upload. This cannot be mixed with ``files`` parameter.
        files: List[:class:`File`]
            A list of files to send. This cannot be mixed with the
            ``file`` parameter.
        embed: :class:`Embed`
            The rich embed for the content to send. This cannot be mixed with
            ``embeds`` parameter.
        embeds: List[:class:`Embed`]
            A list of embeds to send. Maximum of 10. This cannot
            be mixed with the ``embed`` parameter.

        Returns
        ---------
        Union[:class:`WebhookMessage`, :class:`ListItem`]
            If this webhook is in a :class:`ChatChannel`, the :class:`WebhookMessage` that was sent.
            Otherwise, the :class:`ListItem` that was created.

        Raises
        --------
        HTTPException
            Executing the webhook failed.
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
            username=username,
            avatar_url=avatar_url,
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

        # We don't rely on the type of self.channel here because it could easily be None
        if 'note' in data:
            # The webhook is in a ListChannel
            channel = self.channel
            if channel is None:
                channel = ListChannel(
                    data={
                        'id': data.get('channelId'),
                        'type': 'list',
                        'serverId': data.get('teamId'),
                    },
                    state=self._state,
                    group=None,
                )
            created = ListItem(state=self._state, data=data, channel=channel)
        else:
            # The webhook is in a ChatChannel
            created = self._create_message(data)

        # In case the webhook moved or this was not previously set
        self.channel_id = created.channel_id
        if self.server_id is None and created.server_id is not None:
            self.server_id = created.server_id

        return created

    async def fetch_message(self, message_id: str, /, *, channel: Optional[ChatChannel] = None) -> WebhookMessage:
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

        cached_message = self._state._get_message(message_id)
        channel_id: str
        if cached_message is not None:
            channel_id = cached_message.channel_id
        elif channel is not None:
            channel_id = channel.id
        elif self.channel_id is not None:
            channel_id = self.channel_id
        else:
            raise ValueError('channel must be provided if this instance of a webhook\'s channel_id is None and the message to delete is not cached.')

        adapter = async_context.get()
        data = await adapter.get_channel_message(
            self.id,
            channel_id,
            message_id,
            auth_token=self.auth_token,
            session=self.session,
        )
        return self._create_message(data)

    async def delete_message(self, message_id: str, /, *, channel: Optional[ChatChannel] = None) -> None:
        """|coro|

        Deletes a message sent by this webhook.

        This is a lower level interface to :meth:`.WebhookMessage.delete` in case
        you only have an ID.

        This requires an authenticated webhook.

        Parameters
        ------------
        message_id: :class:`str`
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

        cached_message = self._state._get_message(message_id)
        channel_id: str
        if cached_message is not None:
            channel_id = cached_message.channel_id
        elif channel is not None:
            channel_id = channel.id
        elif self.channel_id is not None:
            channel_id = self.channel_id
        else:
            raise ValueError('channel must be provided if this instance of a webhook\'s channel_id is None and the message to delete is not cached.')

        adapter = async_context.get()
        await adapter.delete_channel_message(
            self.id,
            channel_id,
            message_id,
            auth_token=self.auth_token,
            session=self.session,
        )
