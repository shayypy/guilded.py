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

import re
import inspect
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Iterable,
    List,
    Literal,
    Optional,
    Protocol,
    TypeVar,
    Union,
    Tuple,
    Type,
    runtime_checkable,
)

import guilded

from .context import Context
from .errors import *

if TYPE_CHECKING:
    from .bot import Bot


__all__ = (
    'Converter',
    'ObjectConverter',
    'MemberConverter',
    'UserConverter',
    'IntIDConverter',
    'GenericIDConverter',
    'UUIDConverter',
    'ServerChannelConverter',
    'GuildChannelConverter',
    'ServerChannelConverter',
    'AnnouncementChannelConverter',
    'ChatChannelConverter',
    'TextChannelConverter',
    'DocsChannelConverter',
    'ForumChannelConverter',
    'MediaChannelConverter',
    'ListChannelConverter',
    'SchedulingChannelConverter',
    'ThreadConverter',
    'VoiceChannelConverter',
    'ServerConverter',
    'GuildConverter',
    'ServerConverter',
    'ChatMessageConverter',
    'MessageConverter',
    'ColourConverter',
    'ColorConverter',
    'EmoteConverter',
    'EmojiConverter',
    'GameConverter',
    'RoleConverter',
    'Greedy',
    'clean_content',
    'run_converters',
)


_utils_get = guilded.utils.get
_utils_find = guilded.utils.find
T = TypeVar('T')
T_co = TypeVar('T_co', covariant=True)
CT = TypeVar('CT', bound=guilded.abc.ServerChannel)
TT = TypeVar('TT', bound=guilded.Thread)


def _get_from_servers(bot, getter, argument):
    result = None
    for server in bot.servers:
        result = getattr(server, getter)(argument)
        if result:
            return result
    return result


@runtime_checkable
class Converter(Protocol[T_co]):
    """The base class of custom converters that require the :class:`.Context`
    to be passed to be useful.

    This allows you to implement converters that function similar to the
    special cased ``guilded`` classes.

    Classes that derive from this should override the :meth:`~.Converter.convert`
    method to do its conversion logic. This method must be a :ref:`coroutine <coroutine>`.
    """

    async def convert(self, ctx: Context, argument: str):
        """|coro|

        The method to override to do conversion logic.
        If an error is found while converting, it is recommended to
        raise a :exc:`.CommandError` derived exception as it will
        properly propagate to the error handlers.

        Parameters
        -----------
        ctx: :class:`.Context`
            The invocation context that the argument is being used in.
        argument: :class:`str`
            The argument that is being converted.

        Raises
        -------
        :exc:`.CommandError`
            A generic exception occurred when converting the argument.
        :exc:`.BadArgument`
            The converter failed to convert the argument.
        """
        raise NotImplementedError('Derived classes need to implement this.')


# There are multiple different types of IDs in Guilded:

# - 6-10 digit ints:
#   roles, emotes, games, media posts, profile posts,
#   content replies (sometimes incremental), docs

# - 8-char alphanumeric strings ("generic IDs"):
#   servers, groups, users, invites, announcements

# - UUIDs:
#   channels, messages, flowbots, webhooks, list items

# The maximum lengths of the former two types should not be hard-coded,
# but we estimate a likely range for the purpose of string matching.

_INT_ID_REGEX = re.compile(r'(\d{6,10})$')
_GENERIC_ID_REGEX = re.compile(r'([a-zA-Z0-9]{8,10})$')
_UUID_REGEX = re.compile(r'(\b[0-9a-f]{8}\b-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-\b[0-9a-f]{12}\b)$')

class IntIDConverter(Converter[T_co]):
    @staticmethod
    def _get_id_match(argument: str):
        return _INT_ID_REGEX.match(argument)


class GenericIDConverter(Converter[T_co]):
    @staticmethod
    def _get_id_match(argument: str):
        return _GENERIC_ID_REGEX.match(argument)


class UUIDConverter(Converter[T_co]):
    @staticmethod
    def _get_id_match(argument: str):
        return _UUID_REGEX.match(argument)


class ObjectConverter(Converter[guilded.Object]):
    """Converts to a :class:`~guilded.Object`.

    This is generally not useful unless you simply want to make sure something
    is a possibly-valid Guilded object, even if you don't care what it is.

    The lookup strategy is as follows (in order):

    1. Lookup by member, role, or channel mention
    2. Lookup by ID
    """

    async def convert(self, ctx: Context, argument: str):
        match = re.match(r'<(?:@|#)([a-zA-Z0-9]{8}|\b[0-9a-f]{8}\b-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-\b[0-9a-f]{12}\b)>$', argument)
        if match:
            argument = match.group(1)

        if argument.isdigit():
            argument = int(argument)
        try:
            # Any validation we need is done inside of Object's __init__
            result = guilded.Object(argument)
        except:
            raise ObjectNotFound(argument)

        return result


class MemberConverter(GenericIDConverter[guilded.Member]):
    """Converts to a :class:`~guilded.Member`.

    All lookups are via the current server. If in a DM context, then the lookup
    is done by the global cache.

    The lookup strategy is as follows (in order):

    1. Lookup by ID
    2. Lookup by mention
    3. Lookup by name
    4. Lookup by nickname
    """

    def find_member_named(self, server: guilded.Server, argument: str):
        # Guilded doesn't really have a query-members-through-gateway ability,
        # so instead we just search the internal cache.
        return _utils_find(lambda m: m.name == argument or m.nick == argument, server.members)

    async def convert(self, ctx: Context, argument: str) -> guilded.Member:
        bot = ctx.bot
        match = self._get_id_match(argument)
        server = ctx.server
        result = None
        user_id = None
        if match is None:
            # not a mention
            result = self.find_member_named(server, argument)
        else:
            user_id = match.group(1)
            if server:
                result = server.get_member(user_id) or _utils_get(ctx.message.mentions, id=user_id)
            else:
                result = _get_from_servers(bot, 'get_member', user_id)

        if result is None:
            if server is None:
                raise MemberNotFound(argument)

            if user_id is not None:
                result = await server.getch_member(user_id)
            else:
                result = self.find_member_named(server, argument)

            if not result:
                raise MemberNotFound(argument)

        return result


class UserConverter(GenericIDConverter[guilded.User]):
    """Converts to a :class:`~guilded.User`.

    The lookup strategy is as follows (in order):

    1. Lookup by ID
    2. Lookup by mention
    3. Lookup by name
    """

    def find_user_named(self, bot: Bot, argument: str):
        return _utils_find(lambda m: m.name == argument, bot.users)

    async def convert(self, ctx: Context, argument: str) -> guilded.User:
        bot = ctx.bot
        match = self._get_id_match(argument)
        result = None
        user_id = None
        if match is None:
            # not a mention
            result = self.find_user_named(bot, argument)
        else:
            user_id = match.group(1)
            result = bot.get_user(user_id) or _utils_get(ctx.message.mentions, id=user_id)

        if result is None:
            if user_id is not None:
                result = await bot.getch_user(user_id)
            else:
                result = self.find_user_named(bot, argument)

            if not result:
                raise UserNotFound(argument)

        return result


class ChatMessageConverter(UUIDConverter[guilded.ChatMessage]):
    """Converts to a :class:`~guilded.ChatMessage`.

    The lookup strategy is as follows (in order):

    1. Lookup by ID (the message **must** be in the context channel)
    2. Lookup by message share URL
    """

    async def convert(self, ctx: Context, argument: str) -> guilded.ChatMessage:
        bot = ctx.bot
        match = self._get_id_match(argument)
        result = None
        if match is None:
            match = re.match(
                r'https:\/\/(?:www\.)?guilded\.gg\/[\w_-]+\/groups\/\w{8,10}\/channels\/(\b[0-9a-f]{8}\b-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-\b[0-9a-f]{12}\b)\/[a-z]{4,13}\?messageId=(\b[0-9a-f]{8}\b-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-\b[0-9a-f]{12}\b)',
                argument,
            )
            if match is not None:
                channel_id = match.group(1)
                message_id = match.group(2)
                channel = await bot.getch_channel(channel_id)
                result = await channel.fetch_message(message_id)
        else:
            message_id = match.group(1)
            result = await ctx.fetch_message(message_id)

        if result is None:
            raise MessageNotFound(argument)

        return result

MessageConverter = ChatMessageConverter  # discord.py


class ServerChannelConverter(UUIDConverter[guilded.abc.ServerChannel]):
    """Converts to a :class:`~guilded.abc.ServerChannel`.

    All lookups are via the local server. If in a DM context, then the lookup
    is done by the global cache.

    The lookup strategy is as follows (in order):

    1. Lookup by ID
    2. Lookup by mention
    3. Lookup by name.
    """

    async def convert(self, ctx: Context, argument: str) -> guilded.abc.GuildChannel:
        return self._resolve_channel(ctx, argument, 'channels', guilded.abc.GuildChannel)

    @staticmethod
    def _resolve_channel(ctx: Context, argument: str, attribute: str, type: Type[CT]) -> CT:
        bot = ctx.bot

        match = UUIDConverter._get_id_match(argument) or re.match(r'<#(\b[0-9a-f]{8}\b-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-\b[0-9a-f]{12}\b)>$', argument)
        result = None
        server = ctx.server

        if match is None:
            # not a mention
            if server:
                iterable: Iterable[CT] = getattr(server, attribute)
                result: Optional[CT] = _utils_get(iterable, name=argument)
            else:

                def check(c):
                    return isinstance(c, type) and c.name == argument

                result = _utils_find(check, bot.get_all_channels())  # type: ignore
        else:
            channel_id = match.group(1)
            if server:
                # server.get_channel returns an explicit union instead of the base class
                result = server.get_channel(channel_id)  # type: ignore
            else:
                result = _get_from_servers(bot, 'get_channel', channel_id)

        if not isinstance(result, type):
            raise ChannelNotFound(argument)

        return result

    @staticmethod
    def _resolve_thread(ctx: Context, argument: str, attribute: str, type: Type[TT]) -> TT:
        match = UUIDConverter._get_id_match(argument) or re.match(r'<#(\b[0-9a-f]{8}\b-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-\b[0-9a-f]{12}\b)>$', argument)
        result = None
        server = ctx.server

        if match is None:
            # not a mention
            if server:
                iterable: Iterable[TT] = getattr(server, attribute)
                result: Optional[TT] = _utils_get(iterable, name=argument)
        else:
            thread_id = match.group(1)
            if server:
                result = server.get_thread(thread_id)  # type: ignore

        if not result or not isinstance(result, type):
            raise ThreadNotFound(argument)

        return result

GuildChannelConverter = ServerChannelConverter  # discord.py


class AnnouncementChannelConverter(UUIDConverter[guilded.AnnouncementChannel]):
    """Converts to a :class:`~guilded.AnnouncementChannel`.

    All lookups are via the local server. If in a DM context, then the lookup
    is done by the global cache.

    The lookup strategy is as follows (in order):

    1. Lookup by ID
    2. Lookup by mention
    3. Lookup by name
    """

    async def convert(self, ctx: Context, argument: str) -> guilded.AnnouncementChannel:
        return ServerChannelConverter._resolve_channel(ctx, argument, 'announcement_channels', guilded.AnnouncementChannel)


class ChatChannelConverter(UUIDConverter[guilded.ChatChannel]):
    """Converts to a :class:`~guilded.ChatChannel`.

    All lookups are via the local server. If in a DM context, then the lookup
    is done by the global cache.

    The lookup strategy is as follows (in order):

    1. Lookup by ID
    2. Lookup by mention
    3. Lookup by name
    """

    async def convert(self, ctx: Context, argument: str) -> guilded.ChatChannel:
        return ServerChannelConverter._resolve_channel(ctx, argument, 'chat_channels', guilded.ChatChannel)

TextChannelConverter = ChatChannelConverter  # discord.py


class DocsChannelConverter(UUIDConverter[guilded.DocsChannel]):
    """Converts to a :class:`~guilded.DocsChannel`.

    All lookups are via the local server. If in a DM context, then the lookup
    is done by the global cache.

    The lookup strategy is as follows (in order):

    1. Lookup by ID
    2. Lookup by mention
    3. Lookup by name
    """

    async def convert(self, ctx: Context, argument: str) -> guilded.DocsChannel:
        return ServerChannelConverter._resolve_channel(ctx, argument, 'docs_channels', guilded.DocsChannel)


class ForumChannelConverter(UUIDConverter[guilded.ForumChannel]):
    """Converts to a :class:`~guilded.ForumChannel`.

    All lookups are via the local server. If in a DM context, then the lookup
    is done by the global cache.

    The lookup strategy is as follows (in order):

    1. Lookup by ID
    2. Lookup by mention
    3. Lookup by name
    """

    async def convert(self, ctx: Context, argument: str) -> guilded.ForumChannel:
        return ServerChannelConverter._resolve_channel(ctx, argument, 'forum_channels', guilded.ForumChannel)


class ListChannelConverter(UUIDConverter[guilded.ListChannel]):
    """Converts to a :class:`~guilded.ListChannel`.

    All lookups are via the local server. If in a DM context, then the lookup
    is done by the global cache.

    The lookup strategy is as follows (in order):

    1. Lookup by ID
    2. Lookup by mention
    3. Lookup by name
    """

    async def convert(self, ctx: Context, argument: str) -> guilded.ListChannel:
        return ServerChannelConverter._resolve_channel(ctx, argument, 'list_channels', guilded.ListChannel)


class MediaChannelConverter(UUIDConverter[guilded.MediaChannel]):
    """Converts to a :class:`~guilded.MediaChannel`.

    All lookups are via the local server. If in a DM context, then the lookup
    is done by the global cache.

    The lookup strategy is as follows (in order):

    1. Lookup by ID
    2. Lookup by mention
    3. Lookup by name
    """

    async def convert(self, ctx: Context, argument: str) -> guilded.MediaChannel:
        return ServerChannelConverter._resolve_channel(ctx, argument, 'media_channels', guilded.MediaChannel)


class SchedulingChannelConverter(UUIDConverter[guilded.SchedulingChannel]):
    """Converts to a :class:`~guilded.SchedulingChannel`.

    All lookups are via the local server. If in a DM context, then the lookup
    is done by the global cache.

    The lookup strategy is as follows (in order):

    1. Lookup by ID
    2. Lookup by mention
    3. Lookup by name
    """

    async def convert(self, ctx: Context, argument: str) -> guilded.SchedulingChannel:
        return ServerChannelConverter._resolve_channel(ctx, argument, 'scheduling_channels', guilded.SchedulingChannel)


class ThreadConverter(UUIDConverter[guilded.Thread]):
    """Converts to a :class:`~guilded.Thread`.

    All lookups are via the local server. If in a DM context, then the lookup
    is done by the global cache.

    The lookup strategy is as follows (in order):

    1. Lookup by ID
    2. Lookup by mention
    3. Lookup by name
    """

    async def convert(self, ctx: Context, argument: str) -> guilded.Thread:
        return ServerChannelConverter._resolve_thread(ctx, argument, 'threads', guilded.Thread)


class VoiceChannelConverter(UUIDConverter[guilded.VoiceChannel]):
    """Converts to a :class:`~guilded.VoiceChannel`.

    All lookups are via the local server. If in a DM context, then the lookup
    is done by the global cache.

    The lookup strategy is as follows (in order):

    1. Lookup by ID
    2. Lookup by mention
    3. Lookup by name
    """

    async def convert(self, ctx: Context, argument: str) -> guilded.VoiceChannel:
        return ServerChannelConverter._resolve_channel(ctx, argument, 'voice_channels', guilded.VoiceChannel)


class ServerConverter(GenericIDConverter[guilded.Server]):
    """Converts to a :class:`~guilded.Server`.

    The lookup strategy is as follows (in order):

    1. Lookup by ID
    2. Lookup by name
    """

    async def convert(self, ctx: Context, argument: str) -> guilded.Server:
        bot = ctx.bot
        match = self._get_id_match(argument)
        result = None

        if match is not None:
            server_id = match.group(1)
            result = bot.get_server(server_id)

        if result is None:
            result = _utils_get(bot.servers, name=argument)

            if result is None:
                raise ServerNotFound(argument)

        return result

GuildConverter = ServerConverter  # discord.py


class EmoteConverter(IntIDConverter[guilded.Emote]):
    """Converts to a :class:`~guilded.Emote`.

    All lookups are done for the local server first, if available.
    If that lookup fails, then it checks the client's global cache.

    The lookup strategy is as follows (in order):

    1. Lookup by ID
    2. Lookup by extracting ID from the emote
    3. Lookup by name
    """

    async def convert(self, ctx: Context, argument: str) -> guilded.Emote:
        match = self._get_id_match(argument)
        result = None
        bot = ctx.bot
        server = ctx.server

        if match is None:
            # Try to get the emote by name.
            if server:
                result = _utils_get(server.emotes, name=argument)

            if result is None:
                result = _utils_get(bot.emotes, name=argument)
        else:
            emote_id = int(match.group(1))

            # Try to look up emote by id.
            result = bot.get_emote(emote_id)

        if result is None:
            raise EmoteNotFound(argument)

        return result

EmojiConverter = EmoteConverter  # discord.py


class ColourConverter(Converter[guilded.Colour]):
    """Converts to a :class:`~guilded.Colour`.

    The following formats are accepted:

    - ``0x<hex>``
    - ``#<hex>``
    - ``0x#<hex>``
    - ``rgb(<number>, <number>, <number>)``
    - Any of the ``classmethod``\s in :class:`~guilded.Colour`

        - The ``_`` in the name can be optionally replaced with spaces.

    Like CSS, ``<number>`` can be either 0-255 or 0-100% and ``<hex>`` can be
    either a 6 digit hex number or a 3 digit hex shortcut (e.g. #fff).
    """

    async def convert(self, ctx: Context, argument: str) -> guilded.Colour:
        try:
            return guilded.Colour.from_str(argument)
        except ValueError:
            arg = argument.lower().replace(' ', '_')
            method = getattr(guilded.Colour, arg, None)
            if arg.startswith('from_') or method is None or not inspect.ismethod(method):
                raise BadColourArgument(arg)
            return method()

ColorConverter = ColourConverter


class GameConverter(Converter[guilded.Game]):
    """Converts to a :class:`~guilded.Game`.

    :attr:`~guilded.Game.MAPPING` must be populated for this converter to work
    as expected. Call :meth:`~guilded.Client.fill_game_list` at least
    once in your process's lifetime to ensure this.

    The lookup strategy is as follows (in order):

    1. Lookup by ID
    2. Lookup by name
    """

    async def convert(self, ctx: Context, argument: str):
        if not guilded.Game.MAPPING:
            raise BadGameArgument(argument)

        result = None
        if argument in guilded.Game.MAPPING.keys():
            result = guilded.Game(game_id=argument)
        elif argument in guilded.Game.MAPPING.values():
            result = guilded.Game(name=argument)
        else:
            raise GameNotFound(argument)

        return result


class RoleConverter(IntIDConverter[guilded.Role]):
    """Converts to a :class:`~guilded.Role`.

    All lookups are via the local server. If in a DM context, the converter raises
    the :exc:`.NoPrivateMessage` exception.

    The lookup strategy is as follows (in order):

    1. Lookup by ID
    2. Lookup by mention
    3. Lookup by name
    """

    async def convert(self, ctx: Context, argument: str):
        server = ctx.server
        if not server:
            raise NoPrivateMessage()

        result = None
        match = self._get_id_match(argument)

        if match is not None:
            role_id = int(match.group(1))
            result = server.get_role(role_id)
        else:
            result = _utils_get(server.roles, name=argument)

        if not result:
            raise RoleNotFound(argument)

        return result


class clean_content(Converter[str]):
    """Converts the argument to a mention-scrubbed version of itself.

    Attributes
    -----------
    fix_channel_mentions: :class:`bool`
        Whether to clean channel mentions.
    use_nicknames: :class:`bool`
        Whether to use nicknames when transforming mentions.
    escape_markdown: :class:`bool`
        Whether to also escape special markdown characters.
    remove_markdown: :class:`bool`
        Whether to also remove special markdown characters. This option is not supported with ``escape_markdown``
    """

    def __init__(
        self,
        *,
        fix_channel_mentions: bool = False,
        use_nicknames: bool = True,
        escape_markdown: bool = False,
        remove_markdown: bool = False,
    ) -> None:
        self.fix_channel_mentions = fix_channel_mentions
        self.use_nicknames = use_nicknames
        self.escape_markdown = escape_markdown
        self.remove_markdown = remove_markdown

    async def convert(self, ctx: Context, argument: str) -> str:
        msg = ctx.message

        if ctx.server:

            def resolve_member_or_role(id: Union[str, int]) -> str:
                resolved = _utils_get(msg.mentions, id=id) or ctx.server.get_member(id)
                if not resolved and id.isdigit():
                    id = int(id)
                    resolved = _utils_get(msg.role_mentions, id=id) or ctx.server.get_role(id)
                    if resolved:
                        return f'@{resolved.name}'
                elif resolved:
                    return f'@{resolved.display_name if self.use_nicknames else resolved.name}'
                return '@deleted-user'

        else:

            def resolve_member_or_role(id: Union[str, int]) -> str:
                m = _utils_get(msg.mentions, id=id) or ctx.bot.get_user(id)
                return f'@{m.name}' if m else '@deleted-user'

        if self.fix_channel_mentions and ctx.server:

            def resolve_channel(id: str) -> str:
                c = ctx.server.get_channel_or_thread(id)
                return f'#{c.name}' if c else '#deleted-channel'

        else:

            def resolve_channel(id: str) -> str:
                return f'<#{id}>'

        transforms = {
            '@': resolve_member_or_role,
            '#': resolve_channel,
        }

        def repl(match: re.Match) -> str:
            type = match.group(1)
            id = match.group(2)
            transformed = transforms[type](id)
            return transformed

        # This pattern will also catch impossible mentions like <@uuid> or <#01234567>.
        # I wrote it this way so that parsing the match later would be simpler.
        result = re.sub(r'<(@|#)([0-9]{8}|[a-zA-Z0-9]{8}|\b[0-9a-f]{8}\b-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-\b[0-9a-f]{12}\b)>', repl, argument)
        if self.escape_markdown:
            result = guilded.utils.escape_markdown(result)
        elif self.remove_markdown:
            result = guilded.utils.remove_markdown(result)

        # Completely ensure no mentions escape:
        return guilded.utils.escape_mentions(result)


class Greedy(List[T]):
    r"""A special converter that greedily consumes arguments until it can't.
    As a consequence of this behaviour, most input errors are silently discarded,
    since it is used as an indicator of when to stop parsing.

    When a parser error is met the greedy converter stops converting, undoes the
    internal string parsing routine, and continues parsing regularly.

    For example, in the following code:

    .. code-block:: python3

        @commands.command()
        async def test(ctx, numbers: Greedy[int], reason: str):
            await ctx.send("numbers: {}, reason: {}".format(numbers, reason))

    An invocation of ``[p]test 1 2 3 4 5 6 hello`` would pass ``numbers`` with
    ``[1, 2, 3, 4, 5, 6]`` and ``reason`` with ``hello``\.

    For more information, check :ref:`ext_commands_special_converters`.
    """

    __slots__ = ('converter',)

    def __init__(self, *, converter: T):
        self.converter = converter

    def __repr__(self):
        converter = getattr(self.converter, '__name__', repr(self.converter))
        return f'Greedy[{converter}]'

    def __class_getitem__(cls, params: Union[Tuple[T], T]):
        if not isinstance(params, tuple):
            params = (params,)
        if len(params) != 1:
            raise TypeError('Greedy[...] only takes a single argument')
        converter = params[0]

        origin = getattr(converter, '__origin__', None)
        args = getattr(converter, '__args__', ())

        if not (callable(converter) or isinstance(converter, Converter) or origin is not None):
            raise TypeError('Greedy[...] expects a type or a Converter instance.')

        if converter in (str, type(None)) or origin is Greedy:
            raise TypeError(f'Greedy[{converter.__name__}] is invalid.')

        if origin is Union and type(None) in args:
            raise TypeError(f'Greedy[{converter!r}] is invalid.')

        return cls(converter=converter)


def _convert_to_bool(argument: str) -> bool:
    lowered = argument.lower()
    if lowered in ('yes', 'y', 'true', 't', '1', 'enable', 'on'):
        return True
    elif lowered in ('no', 'n', 'false', 'f', '0', 'disable', 'off'):
        return False
    else:
        raise BadBoolArgument(lowered)


def get_converter(param: inspect.Parameter) -> Any:
    converter = param.annotation
    if converter is param.empty:
        if param.default is not param.empty:
            converter = str if param.default is None else type(param.default)
        else:
            converter = str
    return converter


_GenericAlias = type(List[T])

def is_generic_type(tp: Any, *, _GenericAlias: Type = _GenericAlias) -> bool:
    return isinstance(tp, type) and issubclass(tp, Generic) or isinstance(tp, _GenericAlias)  # type: ignore


CONVERTER_MAPPING: Dict[Type[Any], Any] = {
    guilded.AnnouncementChannel: AnnouncementChannelConverter,
    guilded.ChatChannel: ChatChannelConverter,
    guilded.ChatMessage: ChatMessageConverter,
    guilded.Colour: ColourConverter,
    guilded.DocsChannel: DocsChannelConverter,
    guilded.Emote: EmoteConverter,
    guilded.ForumChannel: ForumChannelConverter,
    guilded.Game: GameConverter,
    guilded.ListChannel: ListChannelConverter,
    guilded.MediaChannel: MediaChannelConverter,
    guilded.Member: MemberConverter,
    guilded.Object: ObjectConverter,
    guilded.Role: RoleConverter,
    guilded.SchedulingChannel: SchedulingChannelConverter,
    guilded.Server: ServerConverter,
    guilded.abc.ServerChannel: ServerChannelConverter,
    guilded.Thread: ThreadConverter,
    guilded.User: UserConverter,
    guilded.VoiceChannel: VoiceChannelConverter,
}


async def _actual_conversion(ctx: Context, converter, argument: str, param: inspect.Parameter):
    if converter is bool:
        return _convert_to_bool(argument)

    try:
        module = converter.__module__
    except AttributeError:
        pass
    else:
        if module is not None and (module.startswith('guilded.') and not module.endswith('converter')):
            converter = CONVERTER_MAPPING.get(converter, converter)

    try:
        if inspect.isclass(converter) and issubclass(converter, Converter):
            if inspect.ismethod(converter.convert):
                return await converter.convert(ctx, argument)
            else:
                return await converter().convert(ctx, argument)
        elif isinstance(converter, Converter):
            return await converter.convert(ctx, argument)
    except CommandError:
        raise
    except Exception as exc:
        raise ConversionError(converter, exc) from exc

    try:
        return converter(argument)
    except CommandError:
        raise
    except Exception as exc:
        try:
            name = converter.__name__
        except AttributeError:
            name = converter.__class__.__name__

        raise BadArgument(f'Converting to "{name}" failed for parameter "{param.name}".') from exc


async def run_converters(ctx: Context, converter, argument: str, param: inspect.Parameter):
    """|coro|

    Runs converters for a given converter, argument, and parameter.

    This function does the same work that the library does under the hood.

    Parameters
    ------------
    ctx: :class:`.Context`
        The invocation context to run the converters under.
    converter: Any
        The converter to run, this corresponds to the annotation in the function.
    argument: :class:`str`
        The argument to convert to.
    param: :class:`inspect.Parameter`
        The parameter being converted. This is mainly for error reporting.

    Raises
    -------
    CommandError
        The converter failed to convert.

    Returns
    --------
    Any
        The resulting conversion.
    """
    origin = getattr(converter, '__origin__', None)

    if origin is Union:
        errors = []
        _NoneType = type(None)
        union_args = converter.__args__
        for conv in union_args:
            # if we got to this part in the code, then the previous conversions have failed
            # so we should just undo the view, return the default, and allow parsing to continue
            # with the other parameters
            if conv is _NoneType and param.kind != param.VAR_POSITIONAL:
                ctx.view.undo()
                return None if param.default is param.empty else param.default

            try:
                value = await run_converters(ctx, conv, argument, param)
            except CommandError as exc:
                errors.append(exc)
            else:
                return value

        # if we're here, then we failed all the converters
        raise BadUnionArgument(param, union_args, errors)

    if origin is Literal:
        errors = []
        conversions = {}
        literal_args = converter.__args__
        for literal in literal_args:
            literal_type = type(literal)
            try:
                value = conversions[literal_type]
            except KeyError:
                try:
                    value = await _actual_conversion(ctx, literal_type, argument, param)
                except CommandError as exc:
                    errors.append(exc)
                    conversions[literal_type] = object()
                    continue
                else:
                    conversions[literal_type] = value

            if value == literal:
                return value

        # if we're here, then we failed to match all the literals
        raise BadLiteralArgument(param, literal_args, errors)

    # This must be the last if-clause in the chain of origin checking
    # Nearly every type is a generic type within the typing library
    # So care must be taken to make sure a more specialised origin handle
    # isn't overwritten by the widest if clause
    if origin is not None and is_generic_type(converter):
        converter = origin

    return await _actual_conversion(ctx, converter, argument, param)
