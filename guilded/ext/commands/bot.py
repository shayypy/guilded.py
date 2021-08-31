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
import importlib.util
import importlib.machinery
import types
from typing import Mapping, List, Dict, Optional

import guilded

from . import errors
from .core import Command, Group
from .context import Context
from .cog import Cog
from .help import HelpCommand, DefaultHelpCommand
from .view import StringView


def _is_submodule(parent: str, child: str) -> bool:
    return parent == child or child.startswith(parent + ".")

class _DefaultRepr:
    def __repr__(self):
        return '<default-help-command>'

_default = _DefaultRepr()

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
    def __init__(self, *, command_prefix, help_command=_default, description=None, **options):
        super().__init__(**options)
        self.command_prefix = command_prefix
        self.description = inspect.cleandoc(description) if description else ''
        self.__extensions: Dict[str, types.ModuleType] = {}
        self.__cogs: Dict[str, Cog] = {}
        self._commands = {}
        self._checks: List[Check] = []
        self._check_once = []
        self._before_invoke = None
        self._after_invoke = None
        self._help_command = None
        self.strip_after_prefix = options.pop('strip_after_prefix', False)
        self.owner_id = options.get('owner_id')
        self.owner_ids = options.get('owner_ids', set())

        if self.owner_id and self.owner_ids:
            raise TypeError('Both owner_id and owner_ids are set.')
        if self.owner_ids and not isinstance(self.owner_ids, collections.abc.Collection):
            raise TypeError(f'owner_ids must be a collection not {self.owner_ids.__class__!r}')

        self._listeners = {'on_message': self.on_message, 'on_command_error': self.on_command_error}
        self.extra_events = {}

        if help_command is _default:
            self.help_command = DefaultHelpCommand()
        else:
            self.help_command = help_command

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

    def group(self, **kwargs):
        def decorator(coro):
            if isinstance(coro, Group):
                raise TypeError('Function is already a group.')
            command = Group(coro, **kwargs)
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

    async def can_run(self, ctx: Context, *, call_once: bool = False) -> bool:
        data = self._check_once if call_once else self._checks

        if len(data) == 0:
            return True

        # type-checker doesn't distinguish between functions and methods
        return await guilded.utils.async_all(f(ctx) for f in data)  # type: ignore

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

        prefix = self.command_prefix
        # later: await self.get_prefix(message)
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
                if await self.can_run(ctx, call_once=True):
                    await ctx.command.invoke(ctx)
                else:
                    raise errors.CheckFailure('The global check once functions failed.')
            except errors.CommandError as exc:
                self.dispatch('command_error', ctx, exc)
                #await ctx.command.dispatch_error(ctx, exc)
            else:
                self.dispatch('command_completion', ctx)
        elif ctx.invoked_with:
            exc = errors.CommandNotFound(f'Command "{ctx.invoked_with}" is not found')
            self.dispatch('command_error', ctx, exc)

    async def process_commands(self, message):
        if not message.author:
            return

        if message.author.bot:
            # webhook or bot
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

    # cogs

    def add_cog(self, cog: Cog, *, override: bool = False) -> None:
        """Adds a "cog" to the bot.

        A cog is a class that has its own event listeners and commands.

        .. versionchanged:: 2.0

            :exc:`.ClientException` is raised when a cog with the same name
            is already loaded.

        Parameters
        -----------
        cog: :class:`.Cog`
            The cog to register to the bot.
        override: :class:`bool`
            If a previously loaded cog with the same name should be ejected
            instead of raising an error.

        Raises
        -------
        TypeError
            The cog does not inherit from :class:`.Cog`.
        CommandError
            An error happened during loading.
        .ClientException
            A cog with the same name is already loaded.
        """

        if not isinstance(cog, Cog):
            raise TypeError('cogs must derive from Cog')

        cog_name = cog.__cog_name__
        existing = self.__cogs.get(cog_name)

        if existing is not None:
            if not override:
                raise guilded.ClientException(f'Cog named {cog_name!r} already loaded')
            self.remove_cog(cog_name)

        cog = cog._inject(self)
        self.__cogs[cog_name] = cog

    def get_cog(self, name: str) -> Optional[Cog]:
        """Gets the cog instance requested.

        If the cog is not found, ``None`` is returned instead.

        Parameters
        -----------
        name: :class:`str`
            The name of the cog you are requesting.
            This is equivalent to the name passed via keyword
            argument in class creation or the class name if unspecified.

        Returns
        --------
        Optional[:class:`Cog`]
            The cog that was requested. If not found, returns ``None``.
        """
        return self.__cogs.get(name)

    def remove_cog(self, name: str) -> Optional[Cog]:
        """Removes a cog from the bot and returns it.

        All registered commands and event listeners that the
        cog has registered will be removed as well.

        If no cog is found then this method has no effect.

        Parameters
        -----------
        name: :class:`str`
            The name of the cog to remove.

        Returns
        -------
        Optional[:class:`.Cog`]
             The cog that was removed. ``None`` if not found.
        """

        cog = self.__cogs.pop(name, None)
        if cog is None:
            return

        help_command = self._help_command
        if help_command and help_command.cog is cog:
            help_command.cog = None
        cog._eject(self)

        return cog

    @property
    def cogs(self) -> Mapping[str, Cog]:
        """Mapping[:class:`str`, :class:`Cog`]: A read-only mapping of cog name to cog."""
        return types.MappingProxyType(self.__cogs)

    # extensions

    def _remove_module_references(self, name: str) -> None:
        # find all references to the module
        # remove the cogs registered from the module
        for cogname, cog in self.__cogs.copy().items():
            if _is_submodule(name, cog.__module__):
                self.remove_cog(cogname)

        # remove all the commands from the module
        for cmd in self.all_commands.copy().values():
            if cmd.module is not None and _is_submodule(name, cmd.module):
                if isinstance(cmd, Group):
                    cmd.recursively_remove_all_commands()
                self.remove_command(cmd.name)

        # remove all the listeners from the module
        for event_list in self.extra_events.copy().values():
            remove = []
            for index, event in enumerate(event_list):
                if event.__module__ is not None and _is_submodule(name, event.__module__):
                    remove.append(index)

            for index in reversed(remove):
                del event_list[index]

    def _call_module_finalizers(self, lib: types.ModuleType, key: str) -> None:
        try:
            func = getattr(lib, 'teardown')
        except AttributeError:
            pass
        else:
            try:
                func(self)
            except Exception:
                pass
        finally:
            self.__extensions.pop(key, None)
            sys.modules.pop(key, None)
            name = lib.__name__
            for module in list(sys.modules.keys()):
                if _is_submodule(name, module):
                    del sys.modules[module]

    def _load_from_module_spec(self, spec: importlib.machinery.ModuleSpec, key: str) -> None:
        # precondition: key not in self.__extensions
        lib = importlib.util.module_from_spec(spec)
        sys.modules[key] = lib
        try:
            spec.loader.exec_module(lib)
        except Exception as e:
            del sys.modules[key]
            raise errors.ExtensionFailed(key, e) from e

        try:
            setup = getattr(lib, 'setup')
        except AttributeError:
            del sys.modules[key]
            raise errors.NoEntryPointError(key)

        try:
            setup(self)
        except Exception as e:
            del sys.modules[key]
            self._remove_module_references(lib.__name__)
            self._call_module_finalizers(lib, key)
            raise errors.ExtensionFailed(key, e) from e
        else:
            self.__extensions[key] = lib

    def _resolve_name(self, name: str, package: str) -> str:
        try:
            return importlib.util.resolve_name(name, package)
        except ImportError:
            raise errors.ExtensionNotFound(name)

    def load_extension(self, name: str, *, package: str = None) -> None:
        """
        Loads an extension.

        An extension is a python module that contains commands, cogs, or
        listeners.

        An extension must have a global function, ``setup`` defined as
        the entry point on what to do when the extension is loaded. This entry
        point must have a single argument, the ``bot``.

        Parameters
        ------------
        name: :class:`str`
            The extension name to load. It must be dot separated like
            regular Python imports if accessing a sub-module. e.g.
            ``foo.test`` if you want to import ``foo/test.py``.
        package: Optional[:class:`str`]
            The package name to resolve relative imports with.
            This is required when loading an extension using a relative path, e.g ``.foo.test``.
            Defaults to ``None``.

        Raises
        --------
        ExtensionNotFound
            The extension could not be imported.
            This is also raised if the name of the extension could not
            be resolved using the provided ``package`` parameter.
        ExtensionAlreadyLoaded
            The extension is already loaded.
        NoEntryPointError
            The extension does not have a setup function.
        ExtensionFailed
            The extension or its setup function had an execution error.
        """

        name = self._resolve_name(name, package)
        if name in self.__extensions:
            raise errors.ExtensionAlreadyLoaded(name)

        spec = importlib.util.find_spec(name)
        if spec is None:
            raise errors.ExtensionNotFound(name)

        self._load_from_module_spec(spec, name)

    def unload_extension(self, name: str, *, package: Optional[str] = None) -> None:
        """Unloads an extension.

        When the extension is unloaded, all commands, listeners, and cogs are
        removed from the bot and the module is un-imported.

        The extension can provide an optional global function, ``teardown``,
        to do miscellaneous clean-up if necessary. This function takes a single
        parameter, the ``bot``, similar to ``setup`` from
        :meth:`~.Bot.load_extension`.

        Parameters
        ------------
        name: :class:`str`
            The extension name to unload. It must be dot separated like
            regular Python imports if accessing a sub-module. e.g.
            ``foo.test`` if you want to import ``foo/test.py``.
        package: Optional[:class:`str`]
            The package name to resolve relative imports with.
            This is required when unloading an extension using a relative path, e.g ``.foo.test``.
            Defaults to ``None``.

        Raises
        -------
        ExtensionNotFound
            The name of the extension could not
            be resolved using the provided ``package`` parameter.
        ExtensionNotLoaded
            The extension was not loaded.
        """

        name = self._resolve_name(name, package)
        lib = self.__extensions.get(name)
        if lib is None:
            raise errors.ExtensionNotLoaded(name)

        self._remove_module_references(lib.__name__)
        self._call_module_finalizers(lib, name)

    def reload_extension(self, name: str, *, package: Optional[str] = None) -> None:
        """Atomically reloads an extension.

        This replaces the extension with the same extension, only refreshed. This is
        equivalent to a :meth:`unload_extension` followed by a :meth:`load_extension`
        except done in an atomic way. That is, if an operation fails mid-reload then
        the bot will roll-back to the prior working state.

        Parameters
        ------------
        name: :class:`str`
            The extension name to reload. It must be dot separated like
            regular Python imports if accessing a sub-module. e.g.
            ``foo.test`` if you want to import ``foo/test.py``.
        package: Optional[:class:`str`]
            The package name to resolve relative imports with.
            This is required when reloading an extension using a relative path, e.g ``.foo.test``.
            Defaults to ``None``.

        Raises
        -------
        ExtensionNotLoaded
            The extension was not loaded.
        ExtensionNotFound
            The extension could not be imported.
            This is also raised if the name of the extension could not
            be resolved using the provided ``package`` parameter.
        NoEntryPointError
            The extension does not have a setup function.
        ExtensionFailed
            The extension setup function had an execution error.
        """

        name = self._resolve_name(name, package)
        lib = self.__extensions.get(name)
        if lib is None:
            raise errors.ExtensionNotLoaded(name)

        # get the previous module states from sys modules
        modules = {
            name: module
            for name, module in sys.modules.items()
            if _is_submodule(lib.__name__, name)
        }

        try:
            # Unload and then load the module...
            self._remove_module_references(lib.__name__)
            self._call_module_finalizers(lib, name)
            self.load_extension(name)
        except Exception:
            # if the load failed, the remnants should have been
            # cleaned from the load_extension function call
            # so let's load it from our old compiled library.
            lib.setup(self)  # type: ignore
            self.__extensions[name] = lib

            # revert sys.modules back to normal and raise back to caller
            sys.modules.update(modules)
            raise

    @property
    def extensions(self) -> Mapping[str, types.ModuleType]:
        """Mapping[:class:`str`, :class:`py:types.ModuleType`]: A read-only mapping of extension name to extension."""
        return types.MappingProxyType(self.__extensions)

    # help command

    @property
    def help_command(self) -> Optional[HelpCommand]:
        return self._help_command

    @help_command.setter
    def help_command(self, value: Optional[HelpCommand]) -> None:
        if value is not None:
            if not isinstance(value, HelpCommand):
                raise TypeError('help_command must be a subclass of HelpCommand')
            if self._help_command is not None:
                self._help_command._remove_from_bot(self)
            self._help_command = value
            value._add_to_bot(self)
        elif self._help_command is not None:
            self._help_command._remove_from_bot(self)
            self._help_command = None
        else:
            self._help_command = None
