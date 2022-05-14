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

from typing import TYPE_CHECKING, Any, List, Tuple
from guilded.errors import ClientException, GuildedException

if TYPE_CHECKING:
    from inspect import Parameter


__all__ = (
    'CommandError',
    'MissingRequiredArgument',
    'BadArgument',
    'PrivateMessageOnly',
    'NoPrivateMessage',
    'CheckFailure',
    'CheckAnyFailure',
    'CommandNotFound',
    'DisabledCommand',
    'CommandInvokeError',
    'MissingRequiredAttachment',
    'TooManyArguments',
    'UserInputError',
    'CommandOnCooldown',
    'MaxConcurrencyReached',
    'NotOwner',
    'MessageNotFound',
    'ObjectNotFound',
    'MemberNotFound',
    'TeamNotFound',
    'UserNotFound',
    'ChannelNotFound',
    'ChannelNotReadable',
    'ThreadNotFound',
    'BadColourArgument',
    'RoleNotFound',
    'BadInviteArgument',
    'BadGameArgument',
    'GameNotFound',
    'EmojiNotFound',
    'BadBoolArgument',
    'MissingRole',
    'BotMissingRole',
    'MissingAnyRole',
    'BotMissingAnyRole',
    'MissingPermissions',
    'BotMissingPermissions',
    'ConversionError',
    'BadUnionArgument',
    'BadLiteralArgument',
    'ArgumentParsingError',
    'UnexpectedQuoteError',
    'InvalidEndOfQuotedStringError',
    'ExpectedClosingQuoteError',
    'ExtensionError',
    'ExtensionAlreadyLoaded',
    'ExtensionNotLoaded',
    'NoEntryPointError',
    'ExtensionFailed',
    'ExtensionNotFound',
    'CommandRegistrationError',
)

class CommandError(GuildedException):
    r"""The base exception type for all command related errors.

    This inherits from :exc:`guilded.GuildedException`.

    This exception and exceptions inherited from it are handled
    in a special way as they are caught and passed into a special event
    from :class:`.Bot`\, :func:`on_command_error`.
    """
    def __init__(self, message=None, *args):
        if message is not None:
            # clean-up @everyone and @here mentions
            m = message.replace('@everyone', '@\u200beveryone').replace('@here', '@\u200bhere')
            super().__init__(m, *args)
        else:
            super().__init__(*args)

class ConversionError(CommandError):
    """Exception raised when a Converter class raises non-CommandError.

    This inherits from :exc:`CommandError`.

    Attributes
    ----------
    converter: :class:`guilded.ext.commands.Converter`
        The converter that failed.
    original: :exc:`Exception`
        The original exception that was raised. You can also get this via
        the ``__cause__`` attribute.
    """
    def __init__(self, converter, original):
        self.converter = converter
        self.original = original

class UserInputError(CommandError):
    """The base exception type for errors that involve errors
    regarding user input.

    This inherits from :exc:`CommandError`.
    """
    pass

class CommandNotFound(CommandError):
    """Exception raised when a command is attempted to be invoked
    but no command under that name is found.

    This is not raised for invalid subcommands, rather just the
    initial main command that is attempted to be invoked.

    This inherits from :exc:`CommandError`.
    """
    pass

class MissingRequiredArgument(UserInputError):
    """Exception raised when parsing a command and a parameter
    that is required is not encountered.

    This inherits from :exc:`UserInputError`

    Attributes
    -----------
    param: :class:`inspect.Parameter`
        The argument that is missing.
    """
    def __init__(self, param):
        self.param = param
        super().__init__(f'{param.name} is a required argument that is missing.')

class MissingRequiredAttachment(UserInputError):
    """Exception raised when parsing a command and a parameter that requires
    an attachment is not given.

    This inherits from :exc:`UserInputError`

    Attributes
    -----------
    param: :class:`Parameter`
        The argument that is missing an attachment.
    """
    def __init__(self, param: Parameter) -> None:
        self.param: Parameter = param
        super().__init__(f'{param.name} is a required argument that is missing an attachment.')

class TooManyArguments(UserInputError):
    """Exception raised when the command was passed too many arguments and its
    :attr:`.Command.ignore_extra` attribute was not set to ``True``.

    This inherits from :exc:`UserInputError`
    """
    pass

class BadArgument(UserInputError):
    """Exception raised when a parsing or conversion failure is encountered
    on an argument to pass into a command.

    This inherits from :exc:`UserInputError`
    """
    pass

class CheckFailure(CommandError):
    """Exception raised when the predicates in :attr:`.Command.checks` have failed.

    This inherits from :exc:`CommandError`
    """
    pass

class CheckAnyFailure(CheckFailure):
    """Exception raised when all predicates in :func:`check_any` fail.

    This inherits from :exc:`CheckFailure`.

    Attributes
    ------------
    errors: List[:class:`CheckFailure`]
        A list of errors that were caught during execution.
    checks: List[Callable[[:class:`Context`], :class:`bool`]]
        A list of check predicates that failed.
    """

    def __init__(self, checks, errors):
        self.checks = checks
        self.errors = errors
        super().__init__('You do not have permission to run this command.')

class PrivateMessageOnly(CheckFailure):
    """Exception raised when an operation does not work outside of private
    message contexts.

    This inherits from :exc:`CheckFailure`
    """
    def __init__(self, message=None):
        super().__init__(message or 'This command can only be used in private messages.')

class NoPrivateMessage(CheckFailure):
    """Exception raised when an operation does not work in private message
    contexts.

    This inherits from :exc:`CheckFailure`
    """

    def __init__(self, message=None):
        super().__init__(message or 'This command cannot be used in private messages.')

class NotOwner(CheckFailure):
    """Exception raised when the message author is not the owner of the bot.

    This inherits from :exc:`CheckFailure`
    """
    pass

class ObjectNotFound(BadArgument):
    """Exception raised when the argument provided did not match the format
    of an ID or a mention.

    This inherits from :exc:`BadArgument`

    Attributes
    -----------
    argument: :class:`str`
        The argument supplied by the caller that was not matched
    """
    def __init__(self, argument: str) -> None:
        self.argument: str = argument
        super().__init__(f'{argument!r} does not follow a valid ID or mention format.')

class MemberNotFound(BadArgument):
    """Exception raised when the member provided was not found in the bot's
    cache.

    This inherits from :exc:`BadArgument`

    Attributes
    -----------
    argument: :class:`str`
        The member supplied by the caller that was not found
    """
    def __init__(self, argument):
        self.argument = argument
        super().__init__(f'Member "{argument}" not found.')

class TeamNotFound(BadArgument):
    """Exception raised when the team provided was not found in the bot's cache.

    This inherits from :exc:`BadArgument`

    Attributes
    -----------
    argument: :class:`str`
        The team supplied by the caller that was not found
    """
    def __init__(self, argument):
        self.argument = argument
        super().__init__(f'Team "{argument}" not found.')

class UserNotFound(BadArgument):
    """Exception raised when the user provided was not found in the bot's
    cache.

    This inherits from :exc:`BadArgument`

    Attributes
    -----------
    argument: :class:`str`
        The user supplied by the caller that was not found
    """
    def __init__(self, argument):
        self.argument = argument
        super().__init__(f'User "{argument}" not found.')

class MessageNotFound(BadArgument):
    """Exception raised when the message provided was not found in the channel.

    This inherits from :exc:`BadArgument`

    Attributes
    -----------
    argument: :class:`str`
        The message supplied by the caller that was not found
    """
    def __init__(self, argument):
        self.argument = argument
        super().__init__(f'Message "{argument}" not found.')

class ChannelNotReadable(BadArgument):
    """Exception raised when the bot does not have permission to read messages
    in the channel.

    This inherits from :exc:`BadArgument`

    Attributes
    -----------
    argument: :class:`.abc.TeamChannel`
        The channel supplied by the caller that was not readable
    """
    def __init__(self, argument):
        self.argument = argument
        super().__init__(f"Can't read messages in {argument.mention}.")

class ChannelNotFound(BadArgument):
    """Exception raised when the bot can not find the channel.

    This inherits from :exc:`BadArgument`

    Attributes
    -----------
    argument: :class:`str`
        The channel supplied by the caller that was not found
    """
    def __init__(self, argument):
        self.argument = argument
        super().__init__(f'Channel "{argument}" not found.')

class ThreadNotFound(BadArgument):
    """Exception raised when the bot can not find the thread.

    This inherits from :exc:`BadArgument`

    Attributes
    -----------
    argument: :class:`str`
        The thread supplied by the caller that was not found
    """

    def __init__(self, argument: str) -> None:
        self.argument: str = argument
        super().__init__(f'Thread "{argument}" not found.')

class BadColourArgument(BadArgument):
    """Exception raised when the colour is not valid.

    This inherits from :exc:`BadArgument`

    Attributes
    -----------
    argument: :class:`str`
        The colour supplied by the caller that was not valid
    """
    def __init__(self, argument):
        self.argument = argument
        super().__init__(f'Colour "{argument}" is invalid.')

BadColorArgument = BadColourArgument

class RoleNotFound(BadArgument):
    """Exception raised when the bot can not find the role.

    This inherits from :exc:`BadArgument`

    Attributes
    -----------
    argument: :class:`str`
        The role supplied by the caller that was not found
    """
    def __init__(self, argument):
        self.argument = argument
        super().__init__(f'Role "{argument}" not found.')

class BadInviteArgument(BadArgument):
    """Exception raised when the invite is invalid or expired.

    This inherits from :exc:`BadArgument`
    """
    def __init__(self):
        super().__init__('Invite is invalid or expired.')

class BadGameArgument(BadArgument):
    """Exception raised when the game mapping is not filled.

    This inherits from :exc:`BadArgument`

    Attributes
    -----------
    argument: :class:`str`
        The game supplied by the caller
    """

    def __init__(self, argument: str) -> None:
        self.argument: str = argument
        super().__init__(f'Game "{argument}" was not found because the internal game mapping is not present.')

class GameNotFound(BadArgument):
    """Exception raised when the game mapping is filled but the provided
    argument was not in it.

    This inherits from :exc:`BadArgument`

    Attributes
    -----------
    argument: :class:`str`
        The game supplied by the caller that was not found
    """

    def __init__(self, argument: str) -> None:
        self.argument: str = argument
        super().__init__(f'Game "{argument}" is invalid.')

class EmojiNotFound(BadArgument):
    """Exception raised when the bot can not find the emoji.

    This inherits from :exc:`BadArgument`

    Attributes
    -----------
    argument: :class:`str`
        The emoji supplied by the caller that was not found
    """
    def __init__(self, argument):
        self.argument = argument
        super().__init__(f'Emoji "{argument}" not found.')

class BadBoolArgument(BadArgument):
    """Exception raised when a boolean argument was not convertable.

    This inherits from :exc:`BadArgument`

    Attributes
    -----------
    argument: :class:`str`
        The boolean argument supplied by the caller that is not in the predefined list
    """
    def __init__(self, argument):
        self.argument = argument
        super().__init__(f'{argument} is not a recognised boolean option')

class DisabledCommand(CommandError):
    """Exception raised when the command being invoked is disabled.

    This inherits from :exc:`CommandError`
    """
    pass

class CommandInvokeError(CommandError):
    """Exception raised when the command being invoked raised an exception.

    This inherits from :exc:`CommandError`

    Attributes
    -----------
    original: :exc:`Exception`
        The original exception that was raised. You can also get this via
        the ``__cause__`` attribute.
    """
    def __init__(self, e):
        self.original = e
        super().__init__(f'Command raised an exception: {e.__class__.__name__}: {e}')

class CommandOnCooldown(CommandError):
    """Exception raised when the command being invoked is on cooldown.

    This inherits from :exc:`CommandError`

    Attributes
    -----------
    cooldown: Cooldown
        A class with attributes ``rate``, ``per``, and ``type`` similar to
        the :func:`.cooldown` decorator.
    retry_after: :class:`float`
        The amount of seconds to wait before you can retry again.
    """
    def __init__(self, cooldown, retry_after):
        self.cooldown = cooldown
        self.retry_after = retry_after
        super().__init__(f'You are on cooldown. Try again in {retry_after:.2f}s')

class MaxConcurrencyReached(CommandError):
    """Exception raised when the command being invoked has reached its maximum concurrency.

    This inherits from :exc:`CommandError`.

    Attributes
    ------------
    number: :class:`int`
        The maximum number of concurrent invokers allowed.
    per: :class:`.BucketType`
        The bucket type passed to the :func:`.max_concurrency` decorator.
    """

    def __init__(self, number, per):
        self.number = number
        self.per = per
        name = per.name
        suffix = 'per %s' % name if per.name != 'default' else 'globally'
        plural = '%s times %s' if number > 1 else '%s time %s'
        fmt = plural % (number, suffix)
        super().__init__(f'Too many people using this command. It can only be used {fmt} concurrently.')

class MissingRole(CheckFailure):
    """Exception raised when the command invoker lacks a role to run a command.

    This inherits from :exc:`CheckFailure`

    Attributes
    -----------
    missing_role: Union[:class:`str`, :class:`int`]
        The required role that is missing.
        This is the parameter passed to :func:`~.commands.has_role`.
    """
    def __init__(self, missing_role):
        self.missing_role = missing_role
        message = f'Role {missing_role!r} is required to run this command.'
        super().__init__(message)

class BotMissingRole(CheckFailure):
    """Exception raised when the bot's member lacks a role to run a command.

    This inherits from :exc:`CheckFailure`

    Attributes
    -----------
    missing_role: Union[:class:`str`, :class:`int`]
        The required role that is missing.
        This is the parameter passed to :func:`~.commands.has_role`.
    """
    def __init__(self, missing_role):
        self.missing_role = missing_role
        message = f'Bot requires the role {missing_role!r} to run this command'
        super().__init__(message)

class MissingAnyRole(CheckFailure):
    """Exception raised when the command invoker lacks any of
    the roles specified to run a command.

    This inherits from :exc:`CheckFailure`

    Attributes
    -----------
    missing_roles: List[Union[:class:`str`, :class:`int`]]
        The roles that the invoker is missing.
        These are the parameters passed to :func:`~.commands.has_any_role`.
    """
    def __init__(self, missing_roles):
        self.missing_roles = missing_roles

        missing = [f"'{role}'" for role in missing_roles]

        if len(missing) > 2:
            fmt = '{}, or {}'.format(", ".join(missing[:-1]), missing[-1])
        else:
            fmt = ' or '.join(missing)

        message = f"You are missing at least one of the required roles: {fmt}"
        super().__init__(message)

class BotMissingAnyRole(CheckFailure):
    """Exception raised when the bot's member lacks any of
    the roles specified to run a command.

    This inherits from :exc:`CheckFailure`

    Attributes
    -----------
    missing_roles: List[Union[:class:`str`, :class:`int`]]
        The roles that the bot's member is missing.
        These are the parameters passed to :func:`~.commands.has_any_role`.

    """
    def __init__(self, missing_roles):
        self.missing_roles = missing_roles

        missing = [f"'{role}'" for role in missing_roles]

        if len(missing) > 2:
            fmt = '{}, or {}'.format(", ".join(missing[:-1]), missing[-1])
        else:
            fmt = ' or '.join(missing)

        message = f"Bot is missing at least one of the required roles: {fmt}"
        super().__init__(message)

class MissingPermissions(CheckFailure):
    """Exception raised when the command invoker lacks permissions to run a
    command.

    This inherits from :exc:`CheckFailure`

    Attributes
    -----------
    missing_perms: :class:`list`
        The required permissions that are missing.
    """
    def __init__(self, missing_perms, *args):
        self.missing_perms = missing_perms

        missing = [perm.replace('_', ' ').replace('team', 'server').title() for perm in missing_perms]

        if len(missing) > 2:
            fmt = '{}, and {}'.format(", ".join(missing[:-1]), missing[-1])
        else:
            fmt = ' and '.join(missing)
        message = f'You are missing {fmt} permission(s) to run this command.'
        super().__init__(message, *args)

class BotMissingPermissions(CheckFailure):
    """Exception raised when the bot's member lacks permissions to run a
    command.

    This inherits from :exc:`CheckFailure`

    Attributes
    -----------
    missing_perms: :class:`list`
        The required permissions that are missing.
    """
    def __init__(self, missing_perms, *args):
        self.missing_perms = missing_perms

        missing = [perm.replace('_', ' ').replace('team', 'server').title() for perm in missing_perms]

        if len(missing) > 2:
            fmt = '{}, and {}'.format(", ".join(missing[:-1]), missing[-1])
        else:
            fmt = ' and '.join(missing)
        message = f'Bot requires {fmt} permission(s) to run this command.'
        super().__init__(message, *args)

class BadUnionArgument(UserInputError):
    """Exception raised when a :data:`typing.Union` converter fails for all
    its associated types.

    This inherits from :exc:`UserInputError`

    Attributes
    -----------
    param: :class:`inspect.Parameter`
        The parameter that failed being converted.
    converters: Tuple[Type, ...]
        A tuple of converters attempted in conversion, in order of failure.
    errors: List[:class:`CommandError`]
        A list of errors that were caught from failing the conversion.
    """
    def __init__(self, param, converters, errors):
        self.param = param
        self.converters = converters
        self.errors = errors

        def _get_name(x):
            try:
                return x.__name__
            except AttributeError:
                if hasattr(x, '__origin__'):
                    return repr(x)
                return x.__class__.__name__

        to_string = [_get_name(x) for x in converters]
        if len(to_string) > 2:
            fmt = '{}, or {}'.format(', '.join(to_string[:-1]), to_string[-1])
        else:
            fmt = ' or '.join(to_string)

        super().__init__(f'Could not convert "{param.name}" into {fmt}.')

class BadLiteralArgument(UserInputError):
    """Exception raised when a :data:`typing.Literal` converter fails for all
    its associated values.

    This inherits from :exc:`UserInputError`

    Attributes
    -----------
    param: :class:`inspect.Parameter`
        The parameter that failed being converted.
    literals: Tuple[Any, ``...``]
        A tuple of values compared against in conversion, in order of failure.
    errors: List[:class:`CommandError`]
        A list of errors that were caught from failing the conversion.
    """

    def __init__(self, param: Parameter, literals: Tuple[Any, ...], errors: List[CommandError]) -> None:
        self.param: Parameter = param
        self.literals: Tuple[Any, ...] = literals
        self.errors: List[CommandError] = errors

        to_string = [repr(l) for l in literals]
        if len(to_string) > 2:
            fmt = '{}, or {}'.format(', '.join(to_string[:-1]), to_string[-1])
        else:
            fmt = ' or '.join(to_string)

        super().__init__(f'Could not convert "{param.name}" into the literal {fmt}.')

class ArgumentParsingError(UserInputError):
    """An exception raised when the parser fails to parse a user's input.

    This inherits from :exc:`UserInputError`.

    There are child classes that implement more granular parsing errors for
    i18n purposes.
    """
    pass

class UnexpectedQuoteError(ArgumentParsingError):
    """An exception raised when the parser encounters a quote mark inside a non-quoted string.

    This inherits from :exc:`ArgumentParsingError`.

    Attributes
    ------------
    quote: :class:`str`
        The quote mark that was found inside the non-quoted string.
    """
    def __init__(self, quote):
        self.quote = quote
        super().__init__(f'Unexpected quote mark, {quote!r}, in non-quoted string')

class InvalidEndOfQuotedStringError(ArgumentParsingError):
    """An exception raised when a space is expected after the closing quote in a string
    but a different character is found.

    This inherits from :exc:`ArgumentParsingError`.

    Attributes
    -----------
    char: :class:`str`
        The character found instead of the expected string.
    """
    def __init__(self, char):
        self.char = char
        super().__init__(f'Expected space after closing quotation but received {char!r}')

class ExpectedClosingQuoteError(ArgumentParsingError):
    """An exception raised when a quote character is expected but not found.

    This inherits from :exc:`ArgumentParsingError`.

    Attributes
    -----------
    close_quote: :class:`str`
        The quote character expected.
    """

    def __init__(self, close_quote):
        self.close_quote = close_quote
        super().__init__(f'Expected closing {close_quote}.')

class ExtensionError(GuildedException):
    """Base exception for extension related errors.

    This inherits from :exc:`~guilded.GuildedException`.

    Attributes
    ------------
    name: :class:`str`
        The extension that had an error.
    """
    def __init__(self, message=None, *args, name):
        self.name = name
        message = message or f'Extension {name!r} had an error.'
        # clean-up @everyone and @here mentions
        m = message.replace('@everyone', '@\u200beveryone').replace('@here', '@\u200bhere')
        super().__init__(m, *args)

class ExtensionAlreadyLoaded(ExtensionError):
    """An exception raised when an extension has already been loaded.

    This inherits from :exc:`ExtensionError`
    """
    def __init__(self, name):
        super().__init__(f'Extension {name!r} is already loaded.', name=name)

class ExtensionNotLoaded(ExtensionError):
    """An exception raised when an extension was not loaded.

    This inherits from :exc:`ExtensionError`
    """
    def __init__(self, name):
        super().__init__(f'Extension {name!r} has not been loaded.', name=name)

class NoEntryPointError(ExtensionError):
    """An exception raised when an extension does not have a ``setup`` entry point function.

    This inherits from :exc:`ExtensionError`
    """
    def __init__(self, name):
        super().__init__(f"Extension {name!r} has no 'setup' function.", name=name)

class ExtensionFailed(ExtensionError):
    """An exception raised when an extension failed to load during execution of the module or ``setup`` entry point.

    This inherits from :exc:`ExtensionError`

    Attributes
    -----------
    name: :class:`str`
        The extension that had the error.
    original: :exc:`Exception`
        The original exception that was raised. You can also get this via
        the ``__cause__`` attribute.
    """
    def __init__(self, name, original):
        self.original = original
        msg = f'Extension {name!r} raised an error: {original.__class__.__name__}: {original}'
        super().__init__(msg, name=name)

class ExtensionNotFound(ExtensionError):
    """An exception raised when an extension is not found.

    This inherits from :exc:`ExtensionError`

    Attributes
    -----------
    name: :class:`str`
        The extension that had the error.
    """
    def __init__(self, name):
        msg = f'Extension {name!r} could not be loaded.'
        super().__init__(msg, name=name)

class CommandRegistrationError(ClientException):
    """An exception raised when the command can't be added
    because the name is already taken by a different command.

    This inherits from :exc:`guilded.ClientException`

    Attributes
    ----------
    name: :class:`str`
        The command name that had the error.
    alias_conflict: :class:`bool`
        Whether the name that conflicts is an alias of the command we try to add.
    """
    def __init__(self, name, *, alias_conflict=False):
        self.name = name
        self.alias_conflict = alias_conflict
        type_ = 'alias' if alias_conflict else 'command'
        super().__init__(f'The {type_} {name} is already an existing command or alias.')