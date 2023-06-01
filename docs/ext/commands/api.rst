.. currentmodule:: guilded

API Reference
==============

The following section outlines the API of guilded.py's command extension.

.. _ext_commands_api_bot:

Bots
-----

Bot
~~~~

.. autoclass:: guilded.ext.commands.Bot
    :members:
    :inherited-members:

Event Reference
----------------

Events detailed here are exclusive to the commands extension.

.. function:: guilded.ext.commands.on_command_error(ctx, error)

    An error was raised while executing a command - be it user input error or
    an error in the command function itself.

    :param ctx: The invocation context.
    :type ctx: :class:`Context`

    :param error: The error that was raised.
    :type error: Inherited from :class:`CommandError`

.. function:: guilded.ext.commands.on_command(ctx)

    A command was executed in chat. This event is called before the command
    function, and is thus agnostic to whether or not the command completed
    successfully.

    :param ctx: The invocation context.
    :type ctx: :class:`Context`

.. function:: guilded.ext.commands.on_command_completion(ctx)

    A command finished execution with no errors.

    :param ctx: The invocation context.
    :type ctx: :class:`Context`

Commands
---------

Decorators
~~~~~~~~~~~

.. autofunction:: guilded.ext.commands.command

.. autofunction:: guilded.ext.commands.group

Command
~~~~~~~~

.. autoclass:: guilded.ext.commands.Command
    :members:

Group
~~~~~~

.. autoclass:: guilded.ext.commands.Group
    :members:

Cogs
-----

Cog
~~~~

.. autoclass:: guilded.ext.commands.Cog
    :members:

CogMeta
~~~~~~~~

.. autoclass:: guilded.ext.commands.CogMeta
    :members:

Help Commands
--------------

HelpCommand
~~~~~~~~~~~~

.. autoclass:: guilded.ext.commands.HelpCommand
    :members:

DefaultHelpCommand
~~~~~~~~~~~~~~~~~~~

.. autoclass:: guilded.ext.commands.DefaultHelpCommand
    :members:
    :inherited-members:

MinimalHelpCommand
~~~~~~~~~~~~~~~~~~~

.. autoclass:: guilded.ext.commands.MinimalHelpCommand
    :members:
    :inherited-members:

Paginator
~~~~~~~~~~

.. autoclass:: guilded.ext.commands.Paginator
    :members:

.. _ext_commands_api_checks:

Checks
-------

.. autofunction:: guilded.ext.commands.check(predicate)
    :decorator:

.. autofunction:: guilded.ext.commands.before_invoke(coro)
    :decorator:

.. autofunction:: guilded.ext.commands.after_invoke(coro)
    :decorator:

.. autofunction:: guilded.ext.commands.server_only(,)
    :decorator:

.. autofunction:: guilded.ext.commands.guild_only(,)
    :decorator:

.. autofunction:: guilded.ext.commands.is_owner(,)
    :decorator:

.. autofunction:: guilded.ext.commands.is_nsfw(,)
    :decorator:

.. autofunction:: guilded.ext.commands.cooldown(,)
    :decorator:

.. autofunction:: guilded.ext.commands.dynamic_cooldown(,)
    :decorator:

.. autofunction:: guilded.ext.commands.max_concurrency(,)
    :decorator:

.. autofunction:: guilded.ext.commands.has_role(,)
    :decorator:

.. autofunction:: guilded.ext.commands.has_any_role(,)
    :decorator:

.. autofunction:: guilded.ext.commands.bot_has_role(,)
    :decorator:

.. autofunction:: guilded.ext.commands.bot_has_any_role(,)
    :decorator:

.. autofunction:: guilded.ext.commands.has_server_permissions(,)
    :decorator:

.. autofunction:: guilded.ext.commands.has_guild_permissions(,)
    :decorator:

.. autofunction:: guilded.ext.commands.bot_has_server_permissions(,)
    :decorator:

.. autofunction:: guilded.ext.commands.bot_has_guild_permissions(,)
    :decorator:

.. _ext_commands_api_context:

Context
--------

.. autoclass:: guilded.ext.commands.Context
    :members:
    :inherited-members:

.. _ext_commands_api_converters:

Converters
-----------

.. autoclass:: guilded.ext.commands.Converter
    :members:

.. autoclass:: guilded.ext.commands.ObjectConverter
    :members:

.. autoclass:: guilded.ext.commands.MemberConverter
    :members:

.. autoclass:: guilded.ext.commands.UserConverter
    :members:

.. autoclass:: guilded.ext.commands.ServerChannelConverter
    :members:

.. autoclass:: guilded.ext.commands.AnnouncementChannelConverter
    :members:

.. autoclass:: guilded.ext.commands.ChatChannelConverter
    :members:

.. autoclass:: guilded.ext.commands.TextChannelConverter

.. autoclass:: guilded.ext.commands.DocsChannelConverter
    :members:

.. autoclass:: guilded.ext.commands.ForumChannelConverter
    :members:

.. autoclass:: guilded.ext.commands.MediaChannelConverter
    :members:

.. autoclass:: guilded.ext.commands.ListChannelConverter
    :members:

.. autoclass:: guilded.ext.commands.SchedulingChannelConverter
    :members:

.. autoclass:: guilded.ext.commands.ThreadConverter
    :members:

.. autoclass:: guilded.ext.commands.VoiceChannelConverter
    :members:

.. autoclass:: guilded.ext.commands.ServerConverter
    :members:

.. autoclass:: guilded.ext.commands.GuildConverter

.. autoclass:: guilded.ext.commands.ChatMessageConverter
    :members:

.. autoclass:: guilded.ext.commands.MessageConverter

.. autoclass:: guilded.ext.commands.ColourConverter
    :members:

.. autoclass:: guilded.ext.commands.ColorConverter

.. autoclass:: guilded.ext.commands.EmoteConverter
    :members:

.. autoclass:: guilded.ext.commands.EmojiConverter

.. autoclass:: guilded.ext.commands.GameConverter
    :members:

.. autoclass:: guilded.ext.commands.RoleConverter
    :members:

.. autoclass:: guilded.ext.commands.Greedy()

.. autoclass:: guilded.ext.commands.clean_content
    :members:

.. autofunction:: guilded.ext.commands.run_converters

.. _ext_commands_api_errors:

Exceptions
-----------

.. autoexception:: guilded.ext.commands.CommandRegistrationError
    :members:

.. autoexception:: guilded.ext.commands.CommandError
    :members:

.. autoexception:: guilded.ext.commands.ConversionError
    :members:

.. autoexception:: guilded.ext.commands.UserInputError
    :members:

.. autoexception:: guilded.ext.commands.MissingRequiredArgument
    :members:

.. autoexception:: guilded.ext.commands.TooManyArguments
    :members:

.. autoexception:: guilded.ext.commands.BadArgument
    :members:

.. autoexception:: guilded.ext.commands.BadUnionArgument
    :members:

.. autoexception:: guilded.ext.commands.BadLiteralArgument
    :members:

.. autoexception:: guilded.ext.commands.ArgumentParsingError
    :members:

.. autoexception:: guilded.ext.commands.UnexpectedQuoteError
    :members:

.. autoexception:: guilded.ext.commands.InvalidEndOfQuotedStringError
    :members:

.. autoexception:: guilded.ext.commands.ExpectedClosingQuoteError
    :members:

.. autoexception:: guilded.ext.commands.CommandNotFound
    :members:

.. autoexception:: guilded.ext.commands.CheckFailure
    :members:

.. autoexception:: guilded.ext.commands.CheckAnyFailure
    :members:

.. autoexception:: guilded.ext.commands.PrivateMessageOnly
    :members:

.. autoexception:: guilded.ext.commands.NoPrivateMessage
    :members:

.. autoexception:: guilded.ext.commands.NotOwner
    :members:

.. autoexception:: guilded.ext.commands.MissingRole
    :members:

.. autoexception:: guilded.ext.commands.BotMissingRole
    :members:

.. autoexception:: guilded.ext.commands.MissingAnyRole
    :members:

.. autoexception:: guilded.ext.commands.BotMissingAnyRole
    :members:

.. autoexception:: guilded.ext.commands.NSFWChannelRequired
    :members:

.. autoexception:: guilded.ext.commands.MissingPermissions
    :members:

.. autoexception:: guilded.ext.commands.BotMissingPermissions
    :members:

.. autoexception:: guilded.ext.commands.DisabledCommand
    :members:

.. autoexception:: guilded.ext.commands.CommandInvokeError
    :members:

.. autoexception:: guilded.ext.commands.CommandOnCooldown
    :members:

.. autoexception:: guilded.ext.commands.MaxConcurrencyReached
    :members:

.. autoexception:: guilded.ext.commands.ExtensionError
    :members:

.. autoexception:: guilded.ext.commands.ExtensionAlreadyLoaded
    :members:

.. autoexception:: guilded.ext.commands.ExtensionNotLoaded
    :members:

.. autoexception:: guilded.ext.commands.NoEntryPointError
    :members:

.. autoexception:: guilded.ext.commands.ExtensionFailed
    :members:

.. autoexception:: guilded.ext.commands.ExtensionNotFound
    :members:

.. _ext_commands_api_exception_hierarchy:

Hierarchy
~~~~~~~~~~

* :exc:`Exception`

    * :exc:`GuildedException`

        * :exc:`ClientException`

            * :exc:`CommandRegistrationError`

        * :exc:`CommandError`

            * :exc:`ConversionError`
            * :exc:`UserInputError`

                * :exc:`MissingRequiredArgument`
                * :exc:`TooManyArguments`
                * :exc:`BadArgument`
                * :exc:`BadUnionArgument`
                * :exc:`BadLiteralArgument`
                * :exc:`ArgumentParsingError`

                    * :exc:`UnexpectedQuoteError`
                    * :exc:`InvalidEndOfQuotedStringError`
                    * :exc:`ExpectedClosingQuoteError`

            * :exc:`CommandNotFound`
            * :exc:`CheckFailure`

                * :exc:`CheckAnyFailure`
                * :exc:`PrivateMessageOnly`
                * :exc:`NoPrivateMessage`
                * :exc:`NotOwner`
                * :exc:`MissingRole`
                * :exc:`BotMissingRole`
                * :exc:`MissingAnyRole`
                * :exc:`BotMissingAnyRole`
                * :exc:`NSFWChannelRequired`
                * :exc:`MissingPermissions`
                * :exc:`BotMissingPermissions`

            * :exc:`DisabledCommand`
            * :exc:`CommandInvokeError`
            * :exc:`CommandOnCooldown`
            * :exc:`MaxConcurrencyReached`

        * :exc:`ExtensionError`

            * :exc:`ExtensionAlreadyLoaded`
            * :exc:`ExtensionNotLoaded`
            * :exc:`NoEntryPointError`
            * :exc:`ExtensionFailed`
            * :exc:`ExtensionNotFound`
