import guilded
import collections.abc
import logging

from . import errors
from .core import Command
from .context import Context
from .view import StringView

log = logging.getLogger(__name__)

class Bot(guilded.Client):
    def __init__(self, *,
        command_prefix: str, self_bot=False,
        description=None, owner_id=None,
        strip_after_prefix=False, **kwargs
    ):
        super().__init__(**kwargs)
        self.command_prefix = command_prefix
        self.self_bot = self_bot
        self.description = description
        self.owner_id = owner_id
        self._commands = {}
        self.strip_after_prefix = strip_after_prefix
        self._listeners = {'on_message': self.on_message}

        if self_bot:
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

    async def get_context(self, message):
        view = StringView(message.content)
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
        #if message.author.webhook_id:  # not sure if a reliable bot attribute exists in the current api, so we check for webhooks instead
        #    return
        # nevermind, it seems like this attribute isn't always returned either, so i guess we'll just accept commands from anyone for now

        ctx = await self.get_context(message)
        await self.invoke(ctx)

    async def on_message(self, message):
        await self.process_commands(message)
