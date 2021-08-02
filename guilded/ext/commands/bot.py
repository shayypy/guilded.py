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

import collections.abc
import inspect
import sys
import traceback

import guilded

from . import errors
from .core import Command
from .context import Context
from .view import StringView


class Bot(guilded.Client):
    """A Guilded bot with commands.

    This is a subclass of :class:`guilded.Client`, and thus it implements all
    the functionality of :class:`guilded.Client` but comes with
    commands-related features.

    Parameters
    ------------
    command_prefix: Union[:class:`list`, :class:`str`]
        The command prefix or list of command prefixes to listen for.
    description: Optional[:class:`str`]
        A description of this bot. Will show up in the default help command,
        when it is created.
    owner_id: Optional[:class:`str`]
        The user's ID who owns this bot. Used for the
        :meth:`guilded.ext.commands.is_owner` decorator. Must not be specified
        with ``owner_ids``.
    owner_ids: Optional[List[:class:`str`]]
        The users' IDs who own this bot. Used for the
        :meth:`guilded.ext.commands.is_owner` decorator. Must not be specified
        with ``owner_id``.

    Attributes
    ------------
    command_prefix: Union[:class:`list`, :class:`str`]
        The command prefix or list of command prefixes to listen for.
    commands: :class:`list`
        A list of all the :class:`Command` s registered to this bot.
    description: Optional[:class:`str`]
        A description of this bot.
    owner_id: Optional[:class:`str`]
        The user's ID who owns this bot.
    owner_ids: Optional[List[:class:`str`]]
        The users' IDs who own this bot.
    """
    def __init__(self, *, command_prefix, description=None, **options):
        super().__init__(**options)
        self.command_prefix = command_prefix
        self.description = inspect.cleandoc(description) if description else ''
        self.__extensions = {}
        self.__cogs = {}
        self._commands = {}
        self.strip_after_prefix = options.pop('strip_after_prefix', False)
        self.owner_id = options.get('owner_id')
        self.owner_ids = options.get('owner_ids', set())

        if self.owner_id and self.owner_ids:
            raise TypeError('Both owner_id and owner_ids are set.')
        if self.owner_ids and not isinstance(self.owner_ids, collections.abc.Collection):
            raise TypeError(f'owner_ids must be a collection not {self.owner_ids.__class__!r}')

        self._listeners = {'on_message': self.on_message, 'on_command_error': self.on_command_error}
        self.extra_events = {}

        if options.pop('self_bot', False):
            self._skip_check = lambda x, y: x != y
        else:
            self._skip_check = lambda x, y: x == y

    @property
    def commands(self):
        return list(self._commands.values())

    @property
    def _commands_by_alias(self):
        aliases = {}
        for command in self.commands:
            aliases = {**{alias: command for alias in command.aliases}, **aliases}
        return aliases

    @property
    def all_commands(self):
        return {**self._commands, **self._commands_by_alias}

    def dispatch(self, event_name, *args, **kwargs):
        super().dispatch(event_name, *args, **kwargs)
        ev = 'on_' + event_name
        for event in self.extra_events.get(ev, []):
            self._schedule_event(event, ev, *args, **kwargs)

    def add_command(self, command):
        if command.name in self._commands.keys():
            raise errors.CommandRegistrationError(f'A command with the name {command.name} is already registered.')
        elif command.name in self._commands_by_alias.keys():
            raise errors.CommandRegistrationError(f'A command with the alias {command.name} is already registered.')
        self._commands[command.name] = command

    def command(self, **kwargs):
        def decorator(coro):
            if isinstance(coro, Command):
                raise TypeError('Function is already a command.')
            command = Command(coro, **kwargs)
            self.add_command(command)
            return command

        return decorator

    async def close(self):
        for extension in tuple(self.__extensions):
            try:
                self.unload_extension(extension)
            except Exception:
                pass

        for cog in tuple(self.__cogs):
            try:
                self.remove_cog(cog)
            except Exception:
                pass

        await super().close()

    async def on_command_error(self, context, exception):
        """|coro|

        The default command error handler provided by the bot.

        By default this prints to :data:`sys.stderr` however it could be
        overridden to have a different implementation.

        This only fires if you do not specify any listeners for command error.
        """
        if self.extra_events.get('on_command_error', None):
            return

        command = context.command
        #if command and command.has_error_handler():
        #    return

        cog = context.cog
        if cog and cog.has_error_handler():
            return

        print(f'Ignoring exception in command {context.command}:', file=sys.stderr)
        traceback.print_exception(type(exception), exception, exception.__traceback__, file=sys.stderr)

    # listeners

    def add_listener(self, func, name=None):
        name = func.__name__ if name is None else name

        if not asyncio.iscoroutinefunction(func):
            raise TypeError('Listeners must be coroutines')

        if name in self.extra_events:
            self.extra_events[name].append(func)
        else:
            self.extra_events[name] = [func]

    def remove_listener(self, func, name=None):
        name = func.__name__ if name is None else name

        if name in self.extra_events:
            try:
                self.extra_events[name].remove(func)
            except ValueError:
                pass

    def listen(self, name=None):
        def decorator(func):
            self.add_listener(func, name)
            return func

        return decorator

    async def is_owner(self, user: guilded.User):
        """|coro|

        Checks if a :class:`guilded.User` or :class:`guilded.Member` is the
        owner of this bot. If an :attr:`.owner_id` or :attr:`.owner_ids` are
        not set, this function will always return False, unless the user
        provided is the bot itself.

        Parameters
        -----------
        user: :class:`.abc.User`
            The user to check for.

        Returns
        --------
        :class:`bool`
            Whether the user is the owner.
        """
        if self.owner_id:
            return user.id == self.owner_id
        elif self.owner_ids:
            return user.id in self.owner_ids
        else:
            return user.id == self.user.id

    #async def get_prefix(self, message):
    #    prefix = ret = self.command_prefix
    #    if callable(prefix):
    #        ret = await guilded.utils.maybe_coroutine(prefix, self, message)
    #    if not isinstance(ret, str):
    #        try:
    #            ret = list(ret)
    #        except TypeError:
    #            # It's possible that a generator raised this exception. Don't
    #            # replace it with our own error if that's the case.
    #            if isinstance(ret, collections.abc.Iterable):
    #                raise

    #            raise TypeError('command_prefix must be plain string or iterable of strings, not {ret.__class__.__name__}')

    #        if not ret:
    #            raise ValueError('Iterable command_prefix must contain at least one prefix')

    #    return ret

    async def get_context(self, message: guilded.Message):
        view = StringView(str(message.content))
        ctx = Context(prefix=None, view=view, bot=self, message=message)

        if self._skip_check(message.author.id, self.user.id):
            return ctx

        prefix = self.command_prefix#await self.get_prefix(message)
        invoked_prefix = prefix

        if isinstance(prefix, str):
            if not view.skip_string(prefix):
                return ctx
        else:
            try:
                # if the context class' __init__ consumes something from the view this
                # will be wrong. That seems unreasonable though.
                if message.content.startswith(tuple(prefix)):
                    invoked_prefix = guilded.utils.find(view.skip_string, prefix)
                else:
                    return ctx

            except TypeError:
                if not isinstance(prefix, list):
                    raise TypeError('get_prefix must return either a string or a list of string, '
                                    f'not {prefix.__class__.__name__}')

                # It's possible a bad command_prefix got us here.
                for value in prefix:
                    if not isinstance(value, str):
                        raise TypeError('Iterable command_prefix or list returned from get_prefix must '
                                        f'contain only strings, not {value.__class__.__name__}')

                # Getting here shouldn't happen
                raise

        if self.strip_after_prefix:
            view.skip_ws()

        invoker = view.get_word()
        ctx.invoked_with = invoker
        ctx.prefix = invoked_prefix
        ctx.command = self.all_commands.get(invoker)
        return ctx

    async def invoke(self, ctx):
        if ctx.command is not None:
            self.dispatch('command', ctx)
            try:
                #if await self.can_run(ctx, call_once=True):
                await ctx.command.invoke(ctx)
                #else:
                #    raise errors.CheckFailure('The global check once functions failed.')
            except errors.CommandError as exc:
                self.dispatch('command_error', ctx, exc)
                #await ctx.command.dispatch_error(ctx, exc)
            else:
                self.dispatch('command_completion', ctx)
        elif ctx.invoked_with:
            exc = errors.CommandNotFound(f'Command "{ctx.invoked_with}" is not found')
            self.dispatch('command_error', ctx, exc)

    async def process_commands(self, message):
        if message.author.bot:
            # this is a bit of a hacky attr. obviously, it's impractical to tell if a user
            # account is a bot, so this returns true if the message had either a webhookId
            # or botId (for flow-bots) attribute.
            return

        ctx = await self.get_context(message)
        await self.invoke(ctx)

    async def on_message(self, message):
        """|coro|

        The default handler for :func:`guilded.on_message` provided by the bot.

        If you are overriding this, remember to call :meth:`.process_commands`
        or all commands will be ignored.
        """
        await self.process_commands(message)
