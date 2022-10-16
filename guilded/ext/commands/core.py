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

import asyncio
import contextlib
import datetime
import functools
import inspect
import typing
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Union, TypeVar

import guilded

from .cog import Cog
from .context import Context
from .converters import Greedy, get_converter, run_converters
from .cooldowns import BucketType, Cooldown, CooldownMapping, DynamicCooldownMapping, MaxConcurrency
from .errors import *
from ._types import Check, CoroFunc, _BaseCommand

if TYPE_CHECKING:
    from typing_extensions import Self


__all__ = (
    'Command',
    'Group',
    'command',
    'group',
    # 'has_role',
    # 'has_permissions',
    # 'has_any_role',
    'check',
    'check_any',
    'before_invoke',
    'after_invoke',
    # 'bot_has_role',
    # 'bot_has_permissions',
    # 'bot_has_any_role',
    'cooldown',
    'dynamic_cooldown',
    'max_concurrency',
    'dm_only',
    'server_only',
    'guild_only',
    'is_owner',
    # 'has_server_permissions',
    # 'bot_has_server_permissions',
)


T = TypeVar('T')


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
        finally:
            if command._max_concurrency is not None:
                await command._max_concurrency.release(ctx)

            await command.call_after_hooks(ctx)
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


class _AttachmentIterator:
    def __init__(self, data: List[guilded.Attachment]):
        self.data: List[guilded.Attachment] = data
        self.index: int = 0

    def __iter__(self) -> Self:
        return self

    def __next__(self) -> guilded.Attachment:
        try:
            value = self.data[self.index]
        except IndexError:
            raise StopIteration
        else:
            self.index += 1
            return value

    def is_empty(self) -> bool:
        return self.index >= len(self.data)


class Command(_BaseCommand):
    _before_invoke = None
    _after_invoke = None

    def __new__(cls, *args: Any, **kwargs: Any):
        # ensure we have a complete original copy of **kwargs even for classes
        # that mess with it by popping before delegating to the subclass
        # __init__. control instance creation and inject original kwargs
        self = super().__new__(cls)

        self.__original_kwargs__ = kwargs.copy()
        return self

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
        self.require_var_positional = kwargs.get('require_var_positional', False)
        self.ignore_extra = kwargs.get('ignore_extra', True)
        self.cooldown_after_parsing = kwargs.get('cooldown_after_parsing', False)
        self.cog = None
        self.aliases = kwargs.get('aliases', [])

        if not isinstance(self.aliases, (list, tuple)):
            if isinstance(self.aliases, str):
                # accept one alias even if not passed as a list of one
                # this may be reverted later if people attempt to pass multiple aliases in one string
                self.aliases = [self.aliases]
            else:
                raise TypeError('Command aliases must be a list or a tuple of strings.')

        self.description = inspect.cleandoc(kwargs.get('description', ''))
        self.hidden = kwargs.get('hidden', False)

        try:
            checks = coro.__commands_checks__
            checks.reverse()
        except AttributeError:
            checks = kwargs.get('checks', [])

        self.checks = checks

        try:
            cooldown = coro.__commands_cooldown__
        except AttributeError:
            cooldown = kwargs.get('cooldown')

        if cooldown is None:
            buckets = CooldownMapping(cooldown, BucketType.default)
        elif isinstance(cooldown, CooldownMapping):
            buckets: CooldownMapping[Context[Any]] = cooldown
        else:
            raise TypeError("Cooldown must be an instance of CooldownMapping or None.")
        self._buckets: CooldownMapping[Context[Any]] = buckets

        try:
            max_concurrency = coro.__commands_max_concurrency__
        except AttributeError:
            max_concurrency = kwargs.get('max_concurrency')

        self._max_concurrency: Optional[MaxConcurrency] = max_concurrency

        self.cooldown_after_parsing: bool = kwargs.get('cooldown_after_parsing', False)

        with contextlib.suppress(AttributeError):
            before_invoke = coro.__before_invoke__
            self.before_invoke(before_invoke)

        with contextlib.suppress(AttributeError):
            after_invoke = coro.__after_invoke__
            self.after_invoke(after_invoke)

        parent = kwargs.get('parent')
        self.parent = parent if isinstance(parent, Command) else None

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

    @property
    def full_parent_name(self) -> str:
        """:class:`str`: Retrieves the fully qualified parent command name.

        This the base command name required to execute it. For example,
        in ``?one two three`` the parent name would be ``one two``.
        """
        entries = []
        command = self
        # command.parent is type-hinted as Group some attributes are resolved via MRO
        while command.parent is not None: # type: ignore
            command = command.parent # type: ignore
            entries.append(command.name) # type: ignore

        return ' '.join(reversed(entries))

    @property
    def parents(self):
        """List[:class:`Group`]: Retrieves the parents of this command.

        If the command has no parents then it returns an empty :class:`list`.

        For example in commands ``?a b c test``, the parents are ``[c, b, a]``.
        """
        entries = []
        command = self
        while command.parent is not None: # type: ignore
            command = command.parent # type: ignore
            entries.append(command)

        return entries

    @property
    def root_parent(self):
        """Optional[:class:`Group`]: Retrieves the root parent of this command.

        If the command has no parents then it returns ``None``.

        For example in commands ``?a b c test``, the root parent is ``a``.
        """
        if not self.parent:
            return None
        return self.parents[-1]

    @property
    def qualified_name(self) -> str:
        """:class:`str`: Retrieves the fully qualified command name.

        This is the full parent name with the command name as well.
        For example, in ``?one two three`` the qualified name would be
        ``one two three``.
        """

        parent = self.full_parent_name
        if parent:
            return parent + ' ' + self.name
        else:
            return self.name

    @property
    def short_doc(self) -> str:
        """:class:`str`: Gets the "short" documentation of a command.

        By default, this is the :attr:`.brief` attribute.
        If that lookup leads to an empty string then the first line of the
        :attr:`.help` attribute is used instead.
        """
        if self.brief is not None:
            return self.brief
        if self.help is not None:
            return self.help.split('\n', 1)[0]
        return ''

    @property
    def signature(self) -> str:
        """:class:`str`: Returns a POSIX-like signature useful for help command output."""
        if self.usage is not None:
            return self.usage

        params = self.clean_params
        if not params:
            return ''

        result = []
        for name, param in params.items():
            greedy = False
            # isinstance(param.annotation, Greedy)
            optional = False  # postpone evaluation of if it's an optional argument

            # for typing.Literal[...], typing.Optional[typing.Literal[...]], and Greedy[typing.Literal[...]], the
            # parameter signature is a literal list of it's values
            annotation = param.annotation.converter if greedy else param.annotation
            origin = getattr(annotation, '__origin__', None)
            if not greedy and origin is Union:
                none_cls = type(None)
                union_args = annotation.__args__
                optional = union_args[-1] is none_cls
                if len(union_args) == 2 and optional:
                    annotation = union_args[0]
                    origin = getattr(annotation, '__origin__', None)

            # typing.Literal is >=3.8 and this library supports 3.7
            #if origin is Literal:
            #    name = '|'.join(f'"{v}"' if isinstance(v, str) else str(v) for v in annotation.__args__)
            if param.default is not param.empty:
                # We don't want None or '' to trigger the [name=value] case and instead it should
                # do [name] since [name=None] or [name=] are not exactly useful for the user.
                should_print = param.default if isinstance(param.default, str) else param.default is not None
                if should_print:
                    result.append(f'[{name}={param.default}]' if not greedy else
                                  f'[{name}={param.default}]...')
                    continue
                else:
                    result.append(f'[{name}]')

            elif param.kind == param.VAR_POSITIONAL:
                if self.require_var_positional:
                    result.append(f'<{name}...>')
                else:
                    result.append(f'[{name}...]')
            elif greedy:
                result.append(f'[{name}]...')
            elif optional:
                result.append(f'[{name}]')
            else:
                result.append(f'<{name}>')

        return ' '.join(result)

    @property
    def clean_params(self) -> Dict[str, inspect.Parameter]:
        """Dict[:class:`str`, :class:`inspect.Parameter`]:
        Retrieves the parameter dictionary without the context or self parameters.

        Useful for inspecting signature.
        """
        result = self.params.copy()
        if self.cog is not None:
            # first parameter is self
            try:
                del result[next(iter(result))]
            except StopIteration:
                raise ValueError("missing 'self' parameter") from None

        try:
            # first/second parameter is context
            del result[next(iter(result))]
        except StopIteration:
            raise ValueError("missing 'context' parameter") from None

        return result

    @property
    def cooldown(self) -> Optional[Cooldown]:
        """Optional[:class:`.Cooldown`]: The cooldown of a command when invoked
        or ``None`` if the command doesn't have a registered cooldown.

        .. versionadded:: 1.5
        """
        return self._buckets._cooldown

    def __str__(self):
        return self.name

    async def __call__(self, *args, **kwargs):
        """|coro|

        Calls the internal callback that the command holds.

        .. note::

            This bypasses all mechanisms -- including checks, converters,
            invoke hooks, cooldowns, etc. You must take care to pass
            the proper arguments and types to this function.
        """
        if self.cog is not None:
            # manually pass the cog class to the coro instead of calling it as a method
            return await self.callback(self.cog, *args, **kwargs)
        else:
            return await self.callback(*args, **kwargs)

    def _is_typing_optional(self, annotation: Union[T, Optional[T]]) -> bool:
        return getattr(annotation, '__origin__', None) is Union and type(None) in annotation.__args__  # type: ignore

    async def _transform_greedy_pos(self, ctx: Context, param: inspect.Parameter, required: bool, converter: Any) -> Any:
        view = ctx.view
        result = []
        while not view.eof:
            # for use with a manual undo
            previous = view.index

            view.skip_ws()
            try:
                argument = view.get_quoted_word()
                value = await run_converters(ctx, converter, argument, param)  # type: ignore
            except (CommandError, ArgumentParsingError):
                view.index = previous
                break
            else:
                result.append(value)

        if not result and not required:
            return param.default
        return result

    async def _transform_greedy_var_pos(self, ctx: Context, param: inspect.Parameter, converter: Any) -> Any:
        view = ctx.view
        previous = view.index
        try:
            argument = view.get_quoted_word()
            value = await run_converters(ctx, converter, argument, param)  # type: ignore
        except (CommandError, ArgumentParsingError):
            view.index = previous
            raise RuntimeError() from None  # break loop
        else:
            return value

    async def transform(self, ctx: Context, param: inspect.Parameter, attachments: _AttachmentIterator):
        required = param.default is param.empty
        converter = get_converter(param)
        consume_rest_is_special = (
            param.kind == param.KEYWORD_ONLY and not self.rest_is_raw
        )
        view = ctx.view
        view.skip_ws()

        # The greedy converter is simple -- it keeps going until it fails in which case,
        # it undos the view ready for the next parameter to use instead
        if isinstance(converter, Greedy):
            # Special case to consume the entire attachments list in the case of Greedy[Attachment]
            if converter.converter is guilded.Attachment:
                return list(attachments)

            if param.kind in (param.POSITIONAL_OR_KEYWORD, param.POSITIONAL_ONLY):
                return await self._transform_greedy_pos(ctx, param, required, converter.converter)
            elif param.kind == param.VAR_POSITIONAL:
                return await self._transform_greedy_var_pos(ctx, param, converter.converter)
            else:
                # if we're here, then it's a KEYWORD_ONLY param type
                # since this is mostly useless, we'll helpfully transform Greedy[X]
                # into just X and do the parsing that way.
                converter = converter.converter

        if converter is guilded.Attachment:
            try:
                return next(attachments)
            except StopIteration:
                raise MissingRequiredAttachment(param)

        if self._is_typing_optional(param.annotation) and param.annotation.__args__[0] is guilded.Attachment:
            if attachments.is_empty():
                # I have no idea who would be doing Optional[Attachment] = 1
                # but for those cases then 1 should be returned instead of None
                return None if param.default is param.empty else param.default
            return next(attachments)

        if view.eof:
            if param.kind == param.VAR_POSITIONAL:
                raise RuntimeError()  # break the loop
            if required:
                if self._is_typing_optional(param.annotation):
                    return None
                raise MissingRequiredArgument(param)
            return param.default

        previous = view.index
        if consume_rest_is_special:
            argument = view.read_rest().strip()
        else:
            argument = view.get_quoted_word()
        view.previous = previous

        return await run_converters(ctx, converter, argument, param)

    async def _parse_arguments(self, ctx: Context):
        ctx.args = [ctx] if self.cog is None else [self.cog, ctx]
        ctx.kwargs = {}
        args = ctx.args
        kwargs = ctx.kwargs
        attachments = _AttachmentIterator(ctx.message.attachments)

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

        # 'ctx' is the next parameter
        try:
            next(iterator)
        except StopIteration:
            fmt = 'Callback for {0.name} command is missing "ctx" parameter.'
            raise guilded.ClientException(fmt.format(self))

        for name, param in iterator:
            if param.kind in (param.POSITIONAL_OR_KEYWORD, param.POSITIONAL_ONLY):
                transformed = await self.transform(ctx, param, attachments)
                args.append(transformed)

            elif param.kind == param.KEYWORD_ONLY:
                # kwarg only param denotes "consume rest" semantics
                if self.rest_is_raw:
                    converter = get_converter(param)
                    argument = view.read_rest()
                    kwargs[name] = await run_converters(ctx, converter, argument, param)
                else:
                    kwargs[name] = await self.transform(ctx, param, attachments)
                break

            elif param.kind == param.VAR_POSITIONAL:
                if view.eof and self.require_var_positional:
                    raise MissingRequiredArgument(param)
                while not view.eof:
                    try:
                        transformed = await self.transform(ctx, param, attachments)
                        args.append(transformed)
                    except RuntimeError:
                        break

        if not self.ignore_extra and not view.eof:
            raise TooManyArguments(f'Too many arguments passed to {self.qualified_name}')

    def _ensure_assignment_on_copy(self, other):
        other._before_invoke = self._before_invoke
        other._after_invoke = self._after_invoke
        if self.checks != other.checks:
            other.checks = self.checks.copy()
        if self._buckets.valid and not other._buckets.valid:
            other._buckets = self._buckets.copy()
        if self._max_concurrency and self._max_concurrency != other._max_concurrency:
            other._max_concurrency = self._max_concurrency.copy()

        try:
            other.on_error = self.on_error
        except AttributeError:
            pass
        return other

    def copy(self):
        """Creates a copy of this command.

        Returns
        --------
        :class:`Command`
            A new instance of this command.
        """
        ret = self.__class__(self.callback, **self.__original_kwargs__)
        return self._ensure_assignment_on_copy(ret)

    def _update_copy(self, kwargs: Dict[str, Any]):
        if kwargs:
            kw = kwargs.copy()
            kw.update(self.__original_kwargs__)
            copy = self.__class__(self.callback, **kw)
            return self._ensure_assignment_on_copy(copy)
        else:
            return self.copy()

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

    async def call_before_hooks(self, ctx: Context, /) -> None:
        # now that we're done preparing we can call the pre-command hooks
        # first, call the command local hook:
        cog = self.cog
        if self._before_invoke is not None:
            # should be cog if @commands.before_invoke is used
            instance = getattr(self._before_invoke, '__self__', cog)
            # __self__ only exists for methods, not functions
            # however, if @command.before_invoke is used, it will be a function
            if instance:
                await self._before_invoke(instance, ctx)  # type: ignore
            else:
                await self._before_invoke(ctx)  # type: ignore

        # call the cog local hook if applicable:
        if cog is not None:
            hook = Cog._get_overridden_method(cog.cog_before_invoke)
            if hook is not None:
                await hook(ctx)

        # call the bot global hook if necessary
        hook = ctx.bot._before_invoke
        if hook is not None:
            await hook(ctx)

    async def call_after_hooks(self, ctx: Context, /) -> None:
        cog = self.cog
        if self._after_invoke is not None:
            instance = getattr(self._after_invoke, '__self__', cog)
            if instance:
                await self._after_invoke(instance, ctx)  # type: ignore
            else:
                await self._after_invoke(ctx)  # type: ignore

        # call the cog local hook if applicable:
        if cog is not None:
            hook = Cog._get_overridden_method(cog.cog_after_invoke)
            if hook is not None:
                await hook(ctx)

        hook = ctx.bot._after_invoke
        if hook is not None:
            await hook(ctx)

    def _prepare_cooldowns(self, ctx: Context) -> None:
        if self._buckets.valid:
            dt = ctx.message.updated_at or ctx.message.created_at
            current = dt.replace(tzinfo=datetime.timezone.utc).timestamp()
            bucket = self._buckets.get_bucket(ctx, current)
            if bucket is not None:
                retry_after = bucket.update_rate_limit(current)
                if retry_after:
                    raise CommandOnCooldown(bucket, retry_after, self._buckets.type)  # type: ignore

    async def prepare(self, ctx: Context):
        ctx.command = self

        if not await self.can_run(ctx):
           raise CheckFailure(f'The check functions for command {self.qualified_name} failed.')

        if self._max_concurrency is not None:
            await self._max_concurrency.acquire(ctx)

        try:
            if self.cooldown_after_parsing:
                await self._parse_arguments(ctx)
                self._prepare_cooldowns(ctx)
            else:
                self._prepare_cooldowns(ctx)
                await self._parse_arguments(ctx)

            await self.call_before_hooks(ctx)
        except:
            if self._max_concurrency is not None:
                await self._max_concurrency.release(ctx)
            raise

    def is_on_cooldown(self, ctx: Context, /) -> bool:
        """Checks whether the command is currently on cooldown.

        .. versionadded:: 1.5

        Parameters
        -----------
        ctx: :class:`.Context`
            The invocation context to use when checking the command's cooldown status.

        Returns
        --------
        :class:`bool`
            A boolean indicating if the command is on cooldown.
        """

        if not self._buckets.valid:
            return False

        bucket = self._buckets.get_bucket(ctx)
        if bucket is None:
            return False

        dt = ctx.message.updated_at or ctx.message.created_at
        current = dt.replace(tzinfo=datetime.timezone.utc).timestamp()
        return bucket.get_tokens(current) == 0

    def reset_cooldown(self, ctx: Context, /) -> None:
        """Resets the cooldown on this command.

        .. versionadded:: 1.5

        Parameters
        -----------
        ctx: :class:`.Context`
            The invocation context to reset the cooldown under.
        """

        if self._buckets.valid:
            bucket = self._buckets.get_bucket(ctx)
            if bucket is not None:
                bucket.reset()

    def get_cooldown_retry_after(self, ctx: Context, /) -> float:
        """Retrieves the amount of seconds before this command can be tried again.

        .. versionadded:: 1.5

        Parameters
        -----------
        ctx: :class:`.Context`
            The invocation context to retrieve the cooldown from.

        Returns
        --------
        :class:`float`
            The amount of time left on this command's cooldown in seconds.
            If this is ``0.0`` then the command isn't on cooldown.
        """

        if self._buckets.valid:
            bucket = self._buckets.get_bucket(ctx)
            if bucket is None:
                return 0.0

            dt = ctx.message.updated_at or ctx.message.created_at
            current = dt.replace(tzinfo=datetime.timezone.utc).timestamp()
            return bucket.get_retry_after(current)

        return 0.0

    def before_invoke(self, coro):
        """A decorator that registers a coroutine as a pre-invoke hook.

        A pre-invoke hook is called directly before the command is
        called. This makes it a useful function to set up database
        connections or any type of set up required.

        This pre-invoke hook takes a sole parameter, a :class:`.Context`.

        See :meth:`.Bot.before_invoke` for more info.

        Parameters
        -----------
        coro: :ref:`coroutine <coroutine>`
            The coroutine to register as the pre-invoke hook.

        Raises
        -------
        TypeError
            The coroutine passed is not actually a coroutine.
        """
        if not asyncio.iscoroutinefunction(coro):
            raise TypeError('The pre-invoke hook must be a coroutine.')

        self._before_invoke = coro
        return coro

    def after_invoke(self, coro):
        """A decorator that registers a coroutine as a post-invoke hook.

        A post-invoke hook is called directly after the command is
        called. This makes it a useful function to clean-up database
        connections or any type of clean up required.

        This post-invoke hook takes a sole parameter, a :class:`.Context`.

        See :meth:`.Bot.after_invoke` for more info.

        Parameters
        -----------
        coro: :ref:`coroutine <coroutine>`
            The coroutine to register as the post-invoke hook.

        Raises
        -------
        TypeError
            The coroutine passed is not actually a coroutine.
        """
        if not asyncio.iscoroutinefunction(coro):
            raise TypeError('The post-invoke hook must be a coroutine.')

        self._after_invoke = coro
        return coro

    async def can_run(self, ctx: Context) -> bool:
        """|coro|

        Checks if the command can be executed by checking all the predicates
        inside the :attr:`~Command.checks` attribute. This also checks whether the
        command is disabled.

        Parameters
        -----------
        ctx: :class:`.Context`
            The ctx of the command currently being invoked.

        Raises
        -------
        :class:`CommandError`
            Any command error that was raised during a check call will be propagated
            by this function.

        Returns
        --------
        :class:`bool`
            A boolean indicating if the command can be invoked.
        """

        if not self.enabled:
            raise DisabledCommand(f'{self.name} command is disabled')

        original = ctx.command
        ctx.command = self

        try:
            if not await ctx.bot.can_run(ctx):
                raise CheckFailure(f'The global check functions for command {self.qualified_name} failed.')

            cog = self.cog
            if cog is not None:
                local_check = Cog._get_overridden_method(cog.cog_check)
                if local_check is not None:
                    ret = await guilded.utils.maybe_coroutine(local_check, ctx)
                    if not ret:
                        return False

            predicates = self.checks
            if not predicates:
                # since we have no checks, then we just return True.
                return True

            return await guilded.utils.async_all(predicate(ctx) for predicate in predicates)  # type: ignore
        finally:
            ctx.command = original


def command(name: str = None, cls=Command, **kwargs):
    """A decorator that transforms a function into a :class:`.Command`
    or if called with :func:`group`, :class:`.Group`.

    By default the help attribute is received automatically from the docstring
    of the function and is cleaned up with the use of inspect.cleandoc.
    If the docstring is bytes, then it is decoded into str using utf-8 encoding.

    All checks added using the :func:`check` & co. decorators are added into the function.
    There is no way to supply your own checks through this decorator.

    Parameters
    -----------
    name: :class:`str`
        The name to create the command with. By default this uses the function name unchanged.
    cls
        The class to construct with. By default this is :class:`.Command`. You usually do not change this.
    attrs
        Keyword arguments to pass into the construction of the class denoted by ``cls``.

    Raises
    -------
    TypeError
        If the function is not a coroutine or is already a command.
    """
    def decorator(coro):
        if isinstance(coro, Command):
            raise TypeError('Function is already a command.')
        kwargs['name'] = kwargs.get('name', name)
        return cls(coro, **kwargs)

    return decorator


class Group(Command):
    invoke_without_command: bool = False
    case_insensitive: bool = False
    all_commands: typing.Dict[str, Command]

    """A class that implements a grouping protocol for commands to be executed
    as subcommands.

    This class is a subclass of :class:`.Command` and thus all options valid
    for :class:`.Command` are valid for this as well.

    Attributes
    -----------
    invoke_without_command: :class:`bool`
        Indicates if the group callback should begin parsing and invocation
        only if no subcommand was found. Useful for making it an error handling
        function to tell the user that no subcommand was found or to have
        different functionality in case no subcommand was found.
        If this is ``False``, then the group callback will always be invoked
        first. This means that the checks and the parsing dictated by its
        parameters will be executed. Defaults to ``False``.
    case_insensitive: :class:`bool`
        Indicates if the group's commands should be case insensitive.
        Defaults to ``False``.
    """

    def __init__(self, *args: typing.Any, **attrs: typing.Any):
        super().__init__(*args, **attrs)
        self.invoke_without_command = attrs.pop('invoke_without_command', False)
        case_i = self.case_insensitive = attrs.pop('case_insensitive', False)
        self.all_commands = _CaseInsensitiveDict() if case_i else {}

    @property
    def commands(self) -> set:
        """Set[:class:`.Command`]: A unique set of commands without aliases that are registered."""
        return set(self.all_commands.values())

    def copy(self):
        """Creates a copy of this :class:`.Group`.

        Returns
        --------
        :class:`.Group`
            The copied instance of this group.
        """
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

    async def reinvoke(self, ctx: Context, *, call_hooks: bool = False) -> None:
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
                await self.callback(*ctx.args, **ctx.kwargs)
            except:
                ctx.command_failed = True
                raise
            finally:
                if call_hooks:
                    await self.call_after_hooks(ctx)

        ctx.invoked_parents.append(ctx.invoked_with)

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

        This is usually not called, instead the :meth:`~.Group.command` or
        :meth:`~.Group.group` shortcut decorators are used instead.

        Parameters
        -----------
        command: :class:`.Command`
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
        """Remove a :class:`.Command` from the internal list of commands.

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
        the internal command list via :meth:`~.Group.add_command`.

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
        the internal command list via :meth:`.add_command`.

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


def group(name: str = None, cls=Group, **kwargs):
    """A decorator that transforms a function into a :class:`.Group`.

    This is similar to the :func:`.command` decorator but the ``cls``
    parameter is set to :class:`Group` by default.
    """
    def deco(coro):
        if isinstance(coro, Group):
            raise TypeError('Function is already a group.')
        kwargs['name'] = kwargs.get('name', name)
        return cls(coro, **kwargs)

    return deco


def check(predicate: Check) -> Callable[[T], T]:
    r"""A decorator that adds a check to the :class:`.Command` or its
    subclasses. These checks could be accessed via :attr:`.Command.checks`.

    These checks should be predicates that take in a single parameter taking
    a :class:`.Context`. If the check returns a ``False``\-like value then
    during invocation a :exc:`.CheckFailure` exception is raised and sent to
    the :func:`.on_command_error` event.

    If an exception should be thrown in the predicate then it should be a
    subclass of :exc:`.CommandError`. Any exception not subclassed from it
    will be propagated while those subclassed will be sent to
    :func:`.on_command_error`.

    A special attribute named ``predicate`` is bound to the value
    returned by this decorator to retrieve the predicate passed to the
    decorator. This allows the following introspection and chaining to be done:

    .. code-block:: python3

        def owner_or_permissions(**perms):
            original = commands.has_permissions(**perms).predicate
            async def extended_check(ctx):
                if ctx.server is None:
                    return False
                return ctx.server.owner_id == ctx.author.id or await original(ctx)
            return commands.check(extended_check)

    .. note::
        The function returned by ``predicate`` is **always** a coroutine,
        even if the original function was not a coroutine.

    Examples
    ---------
    Creating a basic check to see if the command invoker is you.

    .. code-block:: python3

        def check_if_it_is_me(ctx):
            return ctx.message.author.id == 'EdVMVKR4'

        @bot.command()
        @commands.check(check_if_it_is_me)
        async def only_for_me(ctx):
            await ctx.send('I know you!')

    Transforming common checks into its own decorator:

    .. code-block:: python3

        def is_me():
            def predicate(ctx):
                return ctx.message.author.id == 'EdVMVKR4'
            return commands.check(predicate)

        @bot.command()
        @is_me()
        async def only_me(ctx):
            await ctx.send('Only you!')

    Parameters
    -----------
    predicate: Callable[[:class:`Context`], :class:`bool`]
        The predicate to check if the command should be invoked.
    """

    def decorator(func: Union[Command, CoroFunc]) -> Union[Command, CoroFunc]:
        if isinstance(func, Command):
            func.checks.append(predicate)
        else:
            if not hasattr(func, '__commands_checks__'):
                func.__commands_checks__ = []

            func.__commands_checks__.append(predicate)

        return func

    if inspect.iscoroutinefunction(predicate):
        decorator.predicate = predicate
    else:
        @functools.wraps(predicate)
        async def wrapper(ctx):
            return predicate(ctx)  # type: ignore
        decorator.predicate = wrapper

    return decorator  # type: ignore


def check_any(*checks: Check[Context]) -> Check[Context]:
    r"""A :func:`check` that is added that checks if any of the checks passed
    will pass, i.e. using logical OR.

    If all checks fail then :exc:`.CheckAnyFailure` is raised to signal the failure.
    It inherits from :exc:`.CheckFailure`.

    .. note::

        The ``predicate`` attribute for this function **is** a coroutine.

    .. versionadded:: 1.5

    Parameters
    ------------
    \*checks: Callable[[:class:`Context`], :class:`bool`]
        An argument list of checks that have been decorated with
        the :func:`check` decorator.

    Raises
    -------
    TypeError
        A check passed has not been decorated with the :func:`check`
        decorator.

    Examples
    ---------
    Creating a basic check to see if it's the bot owner or
    the server owner:

    .. code-block:: python3

        def is_server_owner():
            def predicate(ctx):
                return ctx.server is not None and ctx.author.is_owner()
            return commands.check(predicate)

        @bot.command()
        @commands.check_any(commands.is_owner(), is_server_owner())
        async def only_for_owners(ctx):
            await ctx.send('Hello mister owner!')
    """

    unwrapped = []
    for wrapped in checks:
        try:
            pred = wrapped.predicate
        except AttributeError:
            raise TypeError(f'{wrapped!r} must be wrapped by commands.check decorator') from None
        else:
            unwrapped.append(pred)

    async def predicate(ctx: Context) -> bool:
        errors = []
        for func in unwrapped:
            try:
                value = await func(ctx)
            except CheckFailure as e:
                errors.append(e)
            else:
                if value:
                    return True

        # if we're here, all checks failed
        raise CheckAnyFailure(unwrapped, errors)

    return check(predicate)  # type: ignore


def dm_only():
    """A :func:`.check` that indicates this command must only be used in a
    DM context. Only private messages are allowed when
    using the command.

    This check raises a special exception, :exc:`.PrivateMessageOnly`
    that is inherited from :exc:`.CheckFailure`.
    """

    def predicate(ctx: Context) -> bool:
        if ctx.server is not None:
            raise PrivateMessageOnly()
        return True

    return check(predicate)


def server_only():
    """A :func:`.check` that indicates this command must only be used in a
    server context only. Basically, no private messages are allowed when
    using the command.

    This check raises a special exception, :exc:`.NoPrivateMessage`
    that is inherited from :exc:`.CheckFailure`.
    """

    def predicate(ctx: Context) -> bool:
        if ctx.server is None:
            raise NoPrivateMessage()
        return True

    return check(predicate)

guild_only = server_only  # discord.py


def is_owner():
    """A :func:`.check` that checks if the person invoking this command is the
    owner of the bot.

    This is powered by :meth:`.Bot.is_owner`.

    This check raises a special exception, :exc:`.NotOwner` that is derived
    from :exc:`.CheckFailure`.
    """

    async def predicate(ctx: Context) -> bool:
        if not await ctx.bot.is_owner(ctx.author):
            raise NotOwner('You do not own this bot.')
        return True

    return check(predicate)


def before_invoke(coro) -> Callable[[T], T]:
    """A decorator that registers a coroutine as a pre-invoke hook.

    This allows you to refer to one before invoke hook for several commands that
    do not have to be within the same cog.

    Example
    ---------

    .. code-block:: python3

        async def record_usage(ctx):
            print(ctx.author, 'used', ctx.command, 'at', ctx.message.created_at)

        @bot.command()
        @commands.before_invoke(record_usage)
        async def who(ctx): # Output: <User> used who at <Time>
            await ctx.send('i am a bot')

        class What(commands.Cog):

            @commands.before_invoke(record_usage)
            @commands.command()
            async def when(self, ctx): # Output: <User> used when at <Time>
                await ctx.send(f'and i have existed since {ctx.bot.user.created_at}')

            @commands.command()
            async def where(self, ctx): # Output: <Nothing>
                await ctx.send('on Guilded')

            @commands.command()
            async def why(self, ctx): # Output: <Nothing>
                await ctx.send('because someone made me')

        bot.add_cog(What())
    """
    def decorator(func: Union[Command, CoroFunc]) -> Union[Command, CoroFunc]:
        if isinstance(func, Command):
            func.before_invoke(coro)
        else:
            func.__before_invoke__ = coro
        return func
    return decorator  # type: ignore


def after_invoke(coro) -> Callable[[T], T]:
    """A decorator that registers a coroutine as a post-invoke hook.

    This allows you to refer to one after invoke hook for several commands that
    do not have to be within the same cog.
    """
    def decorator(func: Union[Command, CoroFunc]) -> Union[Command, CoroFunc]:
        if isinstance(func, Command):
            func.after_invoke(coro)
        else:
            func.__after_invoke__ = coro
        return func
    return decorator  # type: ignore


def cooldown(
    rate: int,
    per: float,
    type: Union[BucketType, Callable[[Context[Any]], Any]] = BucketType.default,
) -> Callable[[T], T]:
    """A decorator that adds a cooldown to a :class:`.Command`

    A cooldown allows a command to only be used a specific amount
    of times in a specific time frame. These cooldowns can be based
    either on a per-guild, per-channel, per-user, per-role, per-group, or global basis.
    Denoted by the third argument of ``type`` which must be of enum
    type :class:`.BucketType`.

    If a cooldown is triggered, then :exc:`.CommandOnCooldown` is triggered in
    :func:`.on_command_error` and the local error handler.

    A command can only have a single cooldown.

    Parameters
    ------------
    rate: :class:`int`
        The number of times a command can be used before triggering a cooldown.
    per: :class:`float`
        The amount of seconds to wait for a cooldown when it's been triggered.
    type: Union[:class:`.BucketType`, Callable[[:class:`.Context`], Any]]
        The type of cooldown to have. If callable, should return a key for the mapping.
    """

    def decorator(func: Union[Command, CoroFunc]) -> Union[Command, CoroFunc]:
        if isinstance(func, Command):
            func._buckets = CooldownMapping(Cooldown(rate, per), type)
        else:
            func.__commands_cooldown__ = CooldownMapping(Cooldown(rate, per), type)
        return func

    return decorator  # type: ignore


def dynamic_cooldown(
    cooldown: Callable[[Context[Any]], Optional[Cooldown]],
    type: Union[BucketType, Callable[[Context[Any]], Any]],
) -> Callable[[T], T]:
    """A decorator that adds a dynamic cooldown to a :class:`.Command`

    This differs from :func:`.cooldown` in that it takes a function that
    accepts a single parameter of type :class:`.Context` and must
    return a :class:`.Cooldown` or ``None``.
    If ``None`` is returned then that cooldown is effectively bypassed.

    A cooldown allows a command to only be used a specific amount
    of times in a specific time frame. These cooldowns can be based
    either on a per-guild, per-channel, per-user, per-role or global basis.
    Denoted by the third argument of ``type`` which must be of enum
    type :class:`.BucketType`.

    If a cooldown is triggered, then :exc:`.CommandOnCooldown` is triggered in
    :func:`.on_command_error` and the local error handler.

    A command can only have a single cooldown.

    .. versionadded:: 1.5

    Parameters
    ------------
    cooldown: Callable[[:class:`.Context`], Optional[:class:`.Cooldown`]]
        A function that takes a message and returns a cooldown that will
        apply to this invocation or ``None`` if the cooldown should be bypassed.
    type: :class:`.BucketType`
        The type of cooldown to have.
    """

    if not callable(cooldown):
        raise TypeError("A callable must be provided")

    if type is BucketType.default:
        raise ValueError('BucketType.default cannot be used in dynamic cooldowns')

    def decorator(func: Union[Command, CoroFunc]) -> Union[Command, CoroFunc]:
        if isinstance(func, Command):
            func._buckets = DynamicCooldownMapping(cooldown, type)
        else:
            func.__commands_cooldown__ = DynamicCooldownMapping(cooldown, type)
        return func

    return decorator  # type: ignore


def max_concurrency(number: int, per: BucketType = BucketType.default, *, wait: bool = False) -> Callable[[T], T]:
    """A decorator that adds a maximum concurrency to a :class:`.Command` or its subclasses.

    This enables you to only allow a certain number of command invocations at the same time,
    for example if a command takes too long or if only one user can use it at a time. This
    differs from a cooldown in that there is no set waiting period or token bucket -- only
    a set number of people can run the command.

    .. versionadded:: 1.5

    Parameters
    -------------
    number: :class:`int`
        The maximum number of invocations of this command that can be running at the same time.
    per: :class:`.BucketType`
        The bucket that this concurrency is based on, e.g. ``BucketType.server`` would allow
        it to be used up to ``number`` times per server.
    wait: :class:`bool`
        Whether the command should wait for the queue to be over. If this is set to ``False``
        then instead of waiting until the command can run again, the command raises
        :exc:`.MaxConcurrencyReached` to its error handler. If this is set to ``True``
        then the command waits until it can be executed.
    """

    def decorator(func: Union[Command, CoroFunc]) -> Union[Command, CoroFunc]:
        value = MaxConcurrency(number, per=per, wait=wait)
        if isinstance(func, Command):
            func._max_concurrency = value
        else:
            func.__commands_max_concurrency__ = value
        return func

    return decorator  # type: ignore
