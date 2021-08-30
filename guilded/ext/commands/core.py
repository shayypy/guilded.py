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

import asyncio
import inspect
import functools
import typing

import guilded

from . import converters
from .context import Context
from .errors import *


def _convert_to_bool(argument):
    lowered = argument.lower()
    if lowered in ('yes', 'y', 'true', 't', '1', 'enable', 'on'):
        return True
    elif lowered in ('no', 'n', 'false', 'f', '0', 'disable', 'off'):
        return False
    else:
        raise BadBoolArgument(lowered)


def hooked_wrapped_callback(command, ctx, coro):
    @functools.wraps(coro)
    async def wrapped(*args, **kwargs):
        try:
            ret = await coro(*args, **kwargs)
        except CommandError:
            ctx.command_failed = True
            raise
        except asyncio.CancelledError:
            ctx.command_failed = True
            return
        except Exception as exc:
            ctx.command_failed = True
            raise CommandInvokeError(exc) from exc
        # finally:
        #    if command._max_concurrency is not None:
        #        await command._max_concurrency.release(ctx)

        #    await command.call_after_hooks(ctx)
        return ret

    return wrapped


class _CaseInsensitiveDict(dict):
    def __contains__(self, k):
        return super().__contains__(k.casefold())

    def __delitem__(self, k):
        return super().__delitem__(k.casefold())

    def __getitem__(self, k):
        return super().__getitem__(k.casefold())

    def get(self, k, default=None):
        return super().get(k.casefold(), default)

    def pop(self, k, default=None):
        return super().pop(k.casefold(), default)

    def __setitem__(self, k, v):
        super().__setitem__(k.casefold(), v)


class Command:
    def __init__(self, coro, **kwargs):
        if not asyncio.iscoroutinefunction(coro):
            raise TypeError('Function must be a coroutine.')

        name = kwargs.get('name') or coro.__name__
        if not isinstance(name, str):
            raise TypeError('Command name must be a string.')
        self.name = name
        self.callback = coro

        help_doc = kwargs.get('help')
        if help_doc is not None:
            help_doc = inspect.cleandoc(help_doc)
        else:
            help_doc = inspect.getdoc(coro)
            if isinstance(help_doc, bytes):
                help_doc = help_doc.decode('utf-8')

        self.help = help_doc
        self.enabled = kwargs.get('enabled', True)
        self.brief = kwargs.get('brief')
        self.usage = kwargs.get('usage')
        self.rest_is_raw = kwargs.get('rest_is_raw', False)
        self.require_var_positional = kwargs.get(
            'require_var_positional', False
        )
        self.ignore_extra = kwargs.get('ignore_extra', True)
        self.cooldown_after_parsing = kwargs.get(
            'cooldown_after_parsing', False
        )
        self.cog = None
        self.aliases = kwargs.get('aliases', [])

        if not isinstance(self.aliases, (list, tuple)):
            if isinstance(self.aliases, str):
                # accept one alias even if not passed as a list of one
                # this may be reverted later if people attempt to pass multiple aliases in one string
                self.aliases = [self.aliases]
            else:
                raise TypeError(
                    'Command aliases must be a list or a tuple of strings.'
                )

        self.description = inspect.cleandoc(kwargs.get('description', ''))
        self.hidden = kwargs.get('hidden', False)

        # try:
        #    checks = func.__commands_checks__
        #    checks.reverse()
        # except AttributeError:
        #    checks = kwargs.get('checks', [])
        # finally:
        #    self.checks = checks

    @property
    def callback(self):
        return self._callback

    @callback.setter
    def callback(self, function):
        self._callback = function
        self.module = function.__module__

        signature = inspect.signature(function)
        self.params = signature.parameters.copy()

        # PEP-563 allows postponing evaluation of annotations with a __future__
        # import. When postponed, Parameter.annotation will be a string and must
        # be replaced with the real value for the converters to work later on
        for key, value in self.params.items():
            if isinstance(value.annotation, str):
                self.params[key] = value = value.replace(
                    annotation=eval(value.annotation, function.__globals__)
                )

            # fail early for when someone passes an unparameterized Greedy type
            # if value.annotation is converters.Greedy:
            #    raise TypeError('Unparameterized Greedy[...] is disallowed in signature.')

    def __str__(self):
        return self.name

    async def __call__(self, *args, **kwargs):
        """|coro|

        Calls the internal callback that the command holds.
        """
        if self.cog is not None:
            # manually pass the cog class to the coro instead of calling it as a method
            return await self.callback(self.cog, *args, **kwargs)
        else:
            return await self.callback(*args, **kwargs)

    def _get_converter(self, param):
        converter = param.annotation
        if converter is param.empty:
            if param.default is not param.empty:
                converter = (
                    str if param.default is None else type(param.default)
                )
            else:
                converter = str
        return converter

    async def transform(self, ctx, param):
        required = param.default is param.empty
        converter = self._get_converter(param)
        consume_rest_is_special = (
            param.kind == param.KEYWORD_ONLY and not self.rest_is_raw
        )
        view = ctx.view
        view.skip_ws()

        # The greedy converter is simple -- it keeps going until it fails in which case,
        # it undos the view ready for the next parameter to use instead
        # if type(converter) is converters._Greedy:
        #    if param.kind == param.POSITIONAL_OR_KEYWORD or param.kind == param.POSITIONAL_ONLY:
        #        return await self._transform_greedy_pos(ctx, param, required, converter.converter)
        #    elif param.kind == param.VAR_POSITIONAL:
        #        return await self._transform_greedy_var_pos(ctx, param, converter.converter)
        #    else:
        #        # if we're here, then it's a KEYWORD_ONLY param type
        #        # since this is mostly useless, we'll helpfully transform Greedy[X]
        #        # into just X and do the parsing that way.
        #        converter = converter.converter

        if view.eof:
            if param.kind == param.VAR_POSITIONAL:
                raise RuntimeError()  # break the loop
            if required:
                # if self._is_typing_optional(param.annotation):
                #    return None
                raise MissingRequiredArgument(param)
            return param.default

        previous = view.index
        if consume_rest_is_special:
            argument = view.read_rest().strip()
        else:
            argument = view.get_quoted_word()
        view.previous = previous

        return await self.do_conversion(ctx, converter, argument, param)

    async def do_conversion(self, ctx, converter, argument, param):
        try:
            origin = converter.__origin__
        except AttributeError:
            pass
        else:
            if origin is typing.Union:
                errors = []
                _NoneType = type(None)
                for conv in converter.__args__:
                    # if we got to this part in the code, then the previous conversions have failed
                    # so we should just undo the view, return the default, and allow parsing to continue
                    # with the other parameters
                    if (
                        conv is _NoneType
                        and param.kind != param.VAR_POSITIONAL
                    ):
                        ctx.view.undo()
                        return (
                            None
                            if param.default is param.empty
                            else param.default
                        )

                    try:
                        value = await self._actual_conversion(
                            ctx, conv, argument, param
                        )
                    except CommandError as exc:
                        errors.append(exc)
                    else:
                        return value

                # if we're  here, then we failed all the converters
                raise BadUnionArgument(param, converter.__args__, errors)

        return await self._actual_conversion(ctx, converter, argument, param)

    async def _actual_conversion(self, ctx, converter, argument, param):
        if converter is bool:
            return _convert_to_bool(argument)

        try:
            module = converter.__module__
        except AttributeError:
            pass
        else:
            if module is not None and (
                module.startswith('guilded.')
                and not module.endswith('converter')
            ):
                converter = getattr(
                    converters, converter.__name__ + 'Converter', converter
                )

        try:
            if inspect.isclass(converter):
                if issubclass(converter, converters.Converter):
                    instance = converter()
                    ret = await instance.convert(ctx, argument)
                    return ret
                else:
                    method = getattr(converter, "convert", None)
                    if method is not None and inspect.ismethod(method):
                        ret = await method(ctx, argument)
                        return ret
            elif isinstance(converter, converters.Converter):
                ret = await converter.convert(ctx, argument)
                return ret
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

            raise BadArgument(
                f'Converting to {name!r} failed for parameter {param.name!r}.'
            ) from exc

    async def _parse_arguments(self, ctx):
        ctx.args = [ctx] if self.cog is None else [self.cog, ctx]
        ctx.kwargs = {}
        args = ctx.args
        kwargs = ctx.kwargs

        view = ctx.view
        iterator = iter(self.params.items())

        if self.cog is not None:
            # we have 'self' as the first parameter so just advance
            # the iterator and resume parsing
            try:
                next(iterator)
            except StopIteration:
                fmt = 'Callback for {0.name} command is missing "self" parameter.'
                raise guilded.ClientException(fmt.format(self))

        # next we have the 'ctx' as the next parameter
        try:
            next(iterator)
        except StopIteration:
            fmt = 'Callback for {0.name} command is missing "ctx" parameter.'
            raise guilded.ClientException(fmt.format(self))

        for name, param in iterator:
            if (
                param.kind == param.POSITIONAL_OR_KEYWORD
                or param.kind == param.POSITIONAL_ONLY
            ):
                transformed = await self.transform(ctx, param)
                args.append(transformed)
            elif param.kind == param.KEYWORD_ONLY:
                # kwarg only param denotes "consume rest" semantics
                if self.rest_is_raw:
                    converter = self._get_converter(param)
                    argument = view.read_rest()
                    kwargs[name] = await self.do_conversion(
                        ctx, converter, argument, param
                    )
                else:
                    kwargs[name] = await self.transform(ctx, param)
                break
            elif param.kind == param.VAR_POSITIONAL:
                if view.eof and self.require_var_positional:
                    raise MissingRequiredArgument(param)
                while not view.eof:
                    try:
                        transformed = await self.transform(ctx, param)
                        args.append(transformed)
                    except RuntimeError:
                        break

        if not self.ignore_extra:
            if not view.eof:
                raise TooManyArguments(f'Too many arguments passed to {self.qualified_name}')

    async def invoke(self, ctx):
        ctx.command = self
        await self.prepare(ctx)

        # terminate the invoked_subcommand chain.
        # since we're in a regular command (and not a group) then
        # the invoked subcommand is None.
        ctx.invoked_subcommand = None
        ctx.subcommand_passed = None
        injected = hooked_wrapped_callback(self, ctx, self.callback)
        await injected(*ctx.args, **ctx.kwargs)

    async def prepare(self, ctx):
        ctx.command = self

        # if not await self.can_run(ctx):
        #    raise CheckFailure('The check functions for command {0.qualified_name} failed.'.format(self))

        # if self._max_concurrency is not None:
        #    await self._max_concurrency.acquire(ctx)

        try:
            if self.cooldown_after_parsing:
                await self._parse_arguments(ctx)
                # self._prepare_cooldowns(ctx)
            else:
                # self._prepare_cooldowns(ctx)
                await self._parse_arguments(ctx)

            # await self.call_before_hooks(ctx)
        except:
            # if self._max_concurrency is not None:
            #    await self._max_concurrency.release(ctx)
            raise


def command(name, cls=Command, **kwargs):
    def decorator(coro):
        if isinstance(coro, Command):
            raise TypeError('Function is already a command.')
        return cls(coro, **kwargs)

    return decorator


class Group(Command):
    invoke_without_command: bool = False
    case_insensitive: bool = False
    all_commands: typing.Dict[str, Command]

    def __init__(self, *args: typing.Any, **attrs: typing.Any):
        super().__init__(*args, **attrs)
        self.invoke_without_command = attrs.pop(
            'invoke_without_command', False
        )
        case_i = self.case_insensitive = attrs.pop('case_insensitive', False)
        self.all_commands = _CaseInsensitiveDict() if case_i else {}

    @property
    def commands(self) -> set:
        """Set[:class:`.Command`]: A unique set of commands without aliases that are registered."""
        return set(self.all_commands.values())

    def copy(self):
        ret = super().copy()
        for cmd in self.commands:
            ret.add_command(cmd.copy())
        return ret

    async def invoke(self, ctx: Context) -> None:
        ctx.invoked_subcommand = ctx.subcommand_passed = None
        early_invoke = not self.invoke_without_command
        if early_invoke:
            await self.prepare(ctx)

        view = ctx.view
        previous = view.index
        view.skip_ws()
        trigger = view.get_word()

        if trigger:
            ctx.subcommand_passed = trigger
            ctx.invoked_subcommand = self.all_commands.get(trigger, None)

        if early_invoke:
            injected = hooked_wrapped_callback(self, ctx, self.callback)
            await injected(*ctx.args, **ctx.kwargs)

        ctx.invoked_parents.append(ctx.invoked_with)

        if trigger and ctx.invoked_subcommand:
            ctx.invoked_with = trigger
            await ctx.invoked_subcommand.invoke(ctx)
        elif not early_invoke:
            # undo the trigger parsing
            view.index = previous
            view.previous = previous
            await super().invoke(ctx)

    async def reinvoke(
        self, ctx: Context, *, call_hooks: bool = False
    ) -> None:
        ctx.invoked_subcommand = None
        early_invoke = not self.invoke_without_command
        if early_invoke:
            ctx.command = self
            await self._parse_arguments(ctx)

            if call_hooks:
                await self.call_before_hooks(ctx)

        view = ctx.view
        previous = view.index
        view.skip_ws()
        trigger = view.get_word()

        if trigger:
            ctx.subcommand_passed = trigger
            ctx.invoked_subcommand = self.all_commands.get(trigger, None)

        if early_invoke:
            try:
                await self.callback(*ctx.args, **ctx.kwargs)  # type: ignore
            except:
                ctx.command_failed = True
                raise
            finally:
                if call_hooks:
                    await self.call_after_hooks(ctx)

        ctx.invoked_parents.append(ctx.invoked_with)  # type: ignore

        if trigger and ctx.invoked_subcommand:
            ctx.invoked_with = trigger
            await ctx.invoked_subcommand.reinvoke(ctx, call_hooks=call_hooks)
        elif not early_invoke:
            # undo the trigger parsing
            view.index = previous
            view.previous = previous
            await super().reinvoke(ctx, call_hooks=call_hooks)

    def add_command(self, command: Command) -> None:
        """Adds a :class:`.Command` into the internal list of commands.

        This is usually not called, instead the :meth:`~.GroupMixin.command` or
        :meth:`~.GroupMixin.group` shortcut decorators are used instead.

        Parameters
        -----------
        command: :class:`Command`
            The command to add.

        Raises
        -------
        :exc:`.CommandRegistrationError`
            If the command or its alias is already registered by different command.
        TypeError
            If the command passed is not a subclass of :class:`.Command`.
        """

        if not isinstance(command, Command):
            raise TypeError('The command passed must be a subclass of Command')

        if isinstance(self, Command):
            command.parent = self

        if command.name in self.all_commands:
            raise CommandRegistrationError(command.name)

        self.all_commands[command.name] = command
        for alias in command.aliases:
            if alias in self.all_commands:
                self.remove_command(command.name)
                raise CommandRegistrationError(alias, alias_conflict=True)
            self.all_commands[alias] = command

    def remove_command(self, name: str) -> typing.Optional[Command]:
        """Remove a :class:`.Command` from the internal list
        of commands.

        This could also be used as a way to remove aliases.

        Parameters
        -----------
        name: :class:`str`
            The name of the command to remove.

        Returns
        --------
        Optional[:class:`.Command`]
            The command that was removed. If the name is not valid then
            ``None`` is returned instead.
        """
        command = self.all_commands.pop(name, None)

        # does not exist
        if command is None:
            return None

        if name in command.aliases:
            # we're removing an alias so we don't want to remove the rest
            return command

        # we're not removing the alias so let's delete the rest of them.
        for alias in command.aliases:
            cmd = self.all_commands.pop(alias, None)
            # in the case of a CommandRegistrationError, an alias might conflict
            # with an already existing command. If this is the case, we want to
            # make sure the pre-existing command is not removed.
            if cmd is not None and cmd != command:
                self.all_commands[alias] = cmd
        return command

    def walk_commands(self) -> typing.Generator[Command, None, None]:
        """An iterator that recursively walks through all commands and subcommands.

        Yields
        -------
        Union[:class:`.Command`, :class:`.Group`]
            A command or group from the internal list of commands.
        """
        for command in self.commands:
            yield command
            if isinstance(command, Group):
                yield from command.walk_commands()

    def get_command(self, name: str) -> typing.Optional[Command]:
        """Get a :class:`.Command` from the internal list
        of commands.

        This could also be used as a way to get aliases.

        The name could be fully qualified (e.g. ``'foo bar'``) will get
        the subcommand ``bar`` of the group command ``foo``. If a
        subcommand is not found then ``None`` is returned just as usual.

        Parameters
        -----------
        name: :class:`str`
            The name of the command to get.

        Returns
        --------
        Optional[:class:`Command`]
            The command that was requested. If not found, returns ``None``.
        """

        # fast path, no space in name.
        if ' ' not in name:
            return self.all_commands.get(name)

        names = name.split()
        if not names:
            return None
        obj = self.all_commands.get(names[0])
        if not isinstance(obj, Group):
            return obj

        for name in names[1:]:
            try:
                obj = obj.all_commands[name]
            except (AttributeError, KeyError):
                return None

        return obj

    def command(
        self,
        name: str = None,
        cls: typing.Type[Command] = Command,
        *args,
        **kwargs,
    ):
        """A shortcut decorator that invokes :func:`.command` and adds it to
        the internal command list via :meth:`~.GroupMixin.add_command`.

        Returns
        --------
        Callable[..., :class:`Command`]
            A decorator that converts the provided method into a Command, adds it to the bot, then returns it.
        """

        def deco(coro):
            kwargs.setdefault('parent', self)
            res = command(name, cls, *args, **kwargs)(coro)
            self.add_command(res)
            return res

        return deco

    def group(
        self,
        name: str = None,
        cls=None,
        *args,
        **kwargs,
    ):
        """A shortcut decorator that invokes :func:`.group` and adds it to
        the internal command list via :meth:`~.GroupMixin.add_command`.

        Returns
        --------
        Callable[..., :class:`Group`]
            A decorator that converts the provided method into a Group, adds it to the bot, then returns it.
        """

        def decorator(func: typing.Callable):
            kwargs.setdefault('parent', self)
            result = group(
                name=name or func.__name__, cls=cls or Group, *args, **kwargs
            )(func)
            self.add_command(result)
            return result

        return decorator


def group(name, cls=Group, **attrs):
    def deco(coro):
        if isinstance(coro, Group):
            raise TypeError('Function is already a group.')
        return cls(coro, **attrs)

    return deco
