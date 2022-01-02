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

import re
import inspect
from typing import (
    Optional,
    List,
    TypeVar,
)

import guilded

from .errors import *


__all__ = (
    'Converter',
    'ObjectConverter',
    'MemberConverter',
    'GenericIDConverter',
    'UUIDConverter',
)


def _get_from_teams(bot, getter, argument):
    result = None
    for team in bot.teams:
        result = getattr(team, getter)(argument)
        if result:
            return result
    return result


class Converter:
    """The base class of custom converters that require the :class:`.Context`
    to be passed to be useful.

    This allows you to implement converters that function similar to the
    special cased ``guilded`` classes.

    Classes that derive from this should override the :meth:`~.Converter.convert`
    method to do its conversion logic. This method must be a :ref:`coroutine <coroutine>`.
    """

    async def convert(self, ctx, argument):
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


class GenericIDConverter(Converter):
    def __init__(self):
        self._id_regex = r'([a-zA-Z0-9]{8})'
        super().__init__()

    def _get_id_match(self, argument):
        return re.search(self._id_regex, argument)


class UUIDConverter(Converter):
    def __init__(self):
        self._id_regex = r'(\b[0-9a-f]{8}\b-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-\b[0-9a-f]{12}\b)'
        super().__init__()

    def _get_id_match(self, argument):
        return re.search(self._id_regex, argument)


class ObjectConverter(Converter):
    """Converts to a :class:`~guilded.Object`.

    This is generally not useful unless you simply want to make sure something
    is a possibly-valid Guilded object, even if you don't care what it is.

    The lookup strategy is as follows (in order):

    1. Lookup by member, role, or channel mention.
    2. Lookup by ID.
    """

    async def convert(self, ctx, argument: str):
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


class MemberConverter(GenericIDConverter):
    """Converts to a :class:`~guilded.Member`.

    All lookups are via the current team. If in a DM context, then the lookup
    is done by the global cache.

    The lookup strategy is as follows (in order):

    1. Lookup by ID.
    2. Lookup by mention.
    3. Lookup by name
    4. Lookup by nickname
    """

    def find_member_named(self, team, argument: str):
        # Guilded doesn't really have a query-members-through-gateway ability,
        # so instead we just search the internal cache.
        return guilded.utils.find(lambda m: m.name == argument or m.nick == argument, team.members)

    async def convert(self, ctx, argument: str):
        bot = ctx.bot
        match = self._get_id_match(argument)
        team = ctx.team
        result = None
        user_id = None
        if match is None:
            # not a mention
            #if team:
            #    result = team.get_member_named(argument)
            #else:
            #    result = _get_from_teams(bot, 'get_member_named', argument)

            # i'm too tired to implement get_member_named right now

            result = self.find_member_named(team, argument)
        else:
            user_id = match.group(1)
            if team:
                result = team.get_member(user_id) or guilded.utils.get(ctx.message.mentions, id=user_id)
            else:
                result = _get_from_teams(bot, 'get_member', user_id)

        if result is None:
            if team is None:
                raise MemberNotFound(argument)

            if user_id is not None:
                result = await team.getch_member(user_id)
            else:
                result = self.find_member_named(team, argument)

            if not result:
                raise MemberNotFound(argument)

        return result
