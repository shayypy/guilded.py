.. currentmodule:: guilded

.. _ext_commands_commands:

Commands
=========

At its simplest, the commands extension can be used to easily define commands
which can be called by users with a pre-defined prefix.

.. code-block:: python3

    @bot.command()
    async def hello(ctx, arg):
        await ctx.send(f'Hello {arg}!')

Then, with the prefix ``!``, this could be called with ``hello world``:

.. image:: /images/commands/hello.png

A command must always have at least one parameter, ``ctx``, which is the :class:`.Context`, as the first one.

There are two ways of registering a command. The first one is by using :meth:`.Bot.command` decorator,
as seen in the example above. The second is using the :func:`~ext.commands.command` decorator followed by
:meth:`.Bot.add_command` on the instance.

Essentially, these two are equivalent:

.. code-block:: python3

    from guilded.ext import commands

    bot = commands.Bot(user_id='Ann6LewA', command_prefix='$')

    @bot.command()
    async def test(ctx):
        pass

    # or:

    @commands.command()
    async def test(ctx):
        pass

    bot.add_command(test)

Since the :meth:`.Bot.command` decorator is shorter and easier to comprehend, it will be the one used throughout the
documentation here.

Any parameter that is accepted by the :class:`.Command` constructor can be passed into the decorator. For example, to change
the name to something other than the function would be as simple as doing this:

.. code-block:: python3

    @bot.command(name='list')
    async def _list(ctx, arg):
        pass

Parameters
------------

Since we define commands by making Python functions, we also define the argument passing behaviour by the function
parameters.

Certain parameter types do different things in the user side and most forms of parameter types are supported.

Positional
++++++++++++

The most basic form of parameter passing is the positional parameter. This is where we pass a parameter as-is:

.. code-block:: python3

    @bot.command()
    async def test(ctx, arg):
        await ctx.send(arg)


On the bot using side, you can provide positional arguments by just passing a regular string:

.. image:: /images/commands/positional1.png

To make use of an argument with spaces in between, you should quote it:

.. image:: /images/commands/positional2.png

As a note of warning, if you omit the quotes, you will only get the first word:

.. image:: /images/commands/positional3.png

Since positional arguments are just regular Python arguments, you can have as many as you want:

.. code-block:: python3

    @bot.command()
    async def test(ctx, arg1, arg2):
        await ctx.send(f'You passed {arg1} and {arg2}')

Variable
++++++++++

Sometimes you want users to pass in an undetermined number of parameters. The library supports this
similar to how variable list parameters are done in Python:

.. code-block:: python3

    @bot.command()
    async def test(ctx, *args):
        arguments = ', '.join(args)
        await ctx.send(f'{len(args)} arguments: {arguments}')

This allows our user to accept either one or many arguments as they please. This works similar to positional arguments,
so multi-word parameters should be quoted.

For example, on the bot side:

.. image:: /images/commands/variable1.png

If the user wants to input a multi-word argument, they have to quote it like earlier:

.. image:: /images/commands/variable2.png

Do note that similar to the Python function behaviour, a user can technically pass no arguments
at all:

.. image:: /images/commands/variable3.png

Since the ``args`` variable is a :class:`py:tuple`,
you can do anything you would usually do with one.

Keyword-Only Arguments
++++++++++++++++++++++++

When you want to handle parsing of the argument yourself or do not feel like you want to wrap multi-word user input into
quotes, you can ask the library to give you the rest as a single argument. We do this by using a **keyword-only argument**,
seen below:

.. code-block:: python3

    @bot.command()
    async def test(ctx, *, arg):
        await ctx.send(arg)

.. warning::

    You can only have one keyword-only argument due to parsing ambiguities.

On the bot side, we do not need to quote input with spaces:

.. image:: /images/commands/keyword1.png

Do keep in mind that wrapping it in quotes leaves it as-is:

.. image:: /images/commands/keyword2.png

By default, the keyword-only arguments are stripped of white space to make it easier to work with. This behaviour can be
toggled by the :attr:`.Command.rest_is_raw` argument in the decorator.

.. _ext_commands_context:

Invocation Context
-------------------

As seen earlier, every command must take at least a single parameter, called the :class:`~ext.commands.Context`.

This parameter gives you access to something called the "invocation context". Essentially all the information you need to
know how the command was executed. It contains a lot of useful information:

- :attr:`.Context.server` to fetch the :class:`Server` of the command, if any.
- :attr:`.Context.message` to fetch the :class:`ChatMessage` of the command.
- :attr:`.Context.author` to fetch the :class:`Member` or :class:`~guilded.User` that called the command.
- :meth:`.Context.send` to send a message to the channel the command was used in.

The context implements the :class:`abc.Messageable` interface, so anything you can do on a :class:`abc.Messageable` you
can do on the :class:`~ext.commands.Context`.

Converters
------------

Adding bot arguments with function parameters is only the first step in defining your bot's command interface. To actually
make use of the arguments, we usually want to convert the data into a target type. We call these
:ref:`ext_commands_api_converters`.

Converters come in a few flavours:

- A regular callable object that takes an argument as a sole parameter and returns a different type.

    - These range from your own function, to something like :class:`bool` or :class:`int`.

- A custom class that inherits from :class:`~ext.commands.Converter`.

.. _ext_commands_basic_converters:

Basic Converters
+++++++++++++++++

At its core, a basic converter is a callable that takes in an argument and turns it into something else.

For example, if we wanted to add two numbers together, we could request that they are turned into integers
for us by specifying the converter:

.. code-block:: python3

    @bot.command()
    async def add(ctx, a: int, b: int):
        await ctx.send(a + b)

We specify converters by using something called a **function annotation**. This is a Python 3 exclusive feature that was
introduced in :pep:`3107`.

This works with any callable, such as a function that would convert a string to all upper-case:

.. code-block:: python3

    def to_upper(argument):
        return argument.upper()

    @bot.command()
    async def up(ctx, *, content: to_upper):
        await ctx.send(content)

bool
^^^^^

Unlike the other basic converters, the :class:`bool` converter is treated slightly different. Instead of casting directly to the :class:`bool` type, which would result in any non-empty argument returning ``True``, it instead evaluates the argument as ``True`` or ``False`` based on its given content:

.. code-block:: python3

    if lowered in ('yes', 'y', 'true', 't', '1', 'enable', 'on'):
        return True
    elif lowered in ('no', 'n', 'false', 'f', '0', 'disable', 'off'):
        return False

.. _ext_commands_adv_converters:

Advanced Converters
++++++++++++++++++++

Sometimes a basic converter doesn't have enough information that we need. For example, sometimes we want to get some
information from the :class:`ChatMessage` that called the command or we want to do some asynchronous processing.

For this, the library provides the :class:`~ext.commands.Converter` interface. This allows you to have access to the
:class:`.Context` and have the callable be asynchronous. Defining a custom converter using this interface requires
overriding a single method, :meth:`.Converter.convert`.

An example converter:

.. code-block:: python3

    import random

    class Slapper(commands.Converter):
        async def convert(self, ctx, argument):
            to_slap = random.choice(ctx.server.members)
            return f'{ctx.author} slapped {to_slap} because *{argument}*'

    @bot.command()
    async def slap(ctx, *, reason: Slapper):
        await ctx.send(reason)

The converter provided can either be constructed or not. Essentially these two are equivalent:

.. code-block:: python3

    @bot.command()
    async def slap(ctx, *, reason: Slapper):
        await ctx.send(reason)

    # is the same as...

    @bot.command()
    async def slap(ctx, *, reason: Slapper()):
        await ctx.send(reason)

Having the possibility of the converter be constructed allows you to set up some state in the converter's ``__init__`` for
fine tuning the converter. An example of this is actually in the library, :class:`~ext.commands.clean_content`.

.. code-block:: python3

    @bot.command()
    async def clean(ctx, *, content: commands.clean_content):
        await ctx.send(content)

    # or for fine-tuning

    @bot.command()
    async def clean(ctx, *, content: commands.clean_content(use_nicknames=False)):
        await ctx.send(content)


If a converter fails to convert an argument to its designated target type, the :exc:`.BadArgument` exception must be
raised.

Inline Advanced Converters
+++++++++++++++++++++++++++

If we don't want to inherit from :class:`~ext.commands.Converter`, we can still provide a converter that has the
advanced functionalities of an advanced converter and save us from specifying two types.

For example, a common idiom would be to have a class and a converter for that class:

.. code-block:: python3

    class JoinDistance:
        def __init__(self, joined, created):
            self.joined = joined
            self.created = created

        @property
        def delta(self):
            return self.joined - self.created

    class JoinDistanceConverter(commands.MemberConverter):
        async def convert(self, ctx, argument):
            member = await super().convert(ctx, argument)
            return JoinDistance(member.joined_at, member.created_at)

    @bot.command()
    async def delta(ctx, *, member: JoinDistanceConverter):
        is_new = member.delta.days < 100
        if is_new:
            await ctx.send("Hey, you're pretty new!")
        else:
            await ctx.send("Hm, you're not so new.")

This can get tedious, so an inline advanced converter is possible through a :func:`classmethod` inside the type:

.. code-block:: python3

    class JoinDistance:
        def __init__(self, joined, created):
            self.joined = joined
            self.created = created

        @classmethod
        async def convert(cls, ctx, argument):
            member = await commands.MemberConverter().convert(ctx, argument)
            return cls(member.joined_at, member.created_at)

        @property
        def delta(self):
            return self.joined - self.created

    @bot.command()
    async def delta(ctx, *, member: JoinDistance):
        is_new = member.delta.days < 100
        if is_new:
            await ctx.send("Hey, you're pretty new!")
        else:
            await ctx.send("Hm, you're not so new.")

Guilded Converters
+++++++++++++++++++

Working with :ref:`guilded_api_models` is a fairly common thing when defining commands, as a result the library makes
working with them easy.

For example, to receive a :class:`Member` you can just pass it as a converter:

.. code-block:: python3

    @bot.command()
    async def joined(ctx, *, member: guilded.Member):
        await ctx.send(f'{member} joined on {member.joined_at}')

When this command is executed, it attempts to convert the string given into a :class:`Member` and then passes it as a
parameter for the function. This works by checking if the string is a mention, an ID, a nickname, a username + discriminator,
or just a regular username. The default set of converters have been written to be as easy to use as possible.

A lot of guilded models work out of the gate as a parameter. Having any of
these set as the converter will intelligently convert the argument to the
appropriate target type you specify.

Under the hood, these are implemented by the :ref:`ext_commands_adv_converters`
interface. A table of the equivalent converter is given below:

+------------------------------+-----------------------------------------------------+
|         Guilded Class        |                      Converter                      |
+------------------------------+-----------------------------------------------------+
| :class:`Object`              | :class:`~ext.commands.ObjectConverter`              |
+------------------------------+-----------------------------------------------------+
| :class:`Member`              | :class:`~ext.commands.MemberConverter`              |
+------------------------------+-----------------------------------------------------+
| :class:`User`                | :class:`~ext.commands.UserConverter`                |
+------------------------------+-----------------------------------------------------+
| :class:`ChatMessage`         | :class:`~ext.commands.ChatMessageConverter`         |
+------------------------------+-----------------------------------------------------+
| :class:`.ServerChannel`      | :class:`~ext.commands.ServerChannelConverter`       |
+------------------------------+-----------------------------------------------------+
| :class:`AnnouncementChannel` | :class:`~ext.commands.AnnouncementChannelConverter` |
+------------------------------+-----------------------------------------------------+
| :class:`ChatChannel`         | :class:`~ext.commands.ChatChannelConverter`         |
+------------------------------+-----------------------------------------------------+
| :class:`DocsChannel`         | :class:`~ext.commands.DocsChannelConverter`         |
+------------------------------+-----------------------------------------------------+
| :class:`ForumChannel`        | :class:`~ext.commands.ForumChannelConverter`        |
+------------------------------+-----------------------------------------------------+
| :class:`MediaChannel`        | :class:`~ext.commands.MediaChannelConverter`        |
+------------------------------+-----------------------------------------------------+
| :class:`ListChannel`         | :class:`~ext.commands.ListChannelConverter`         |
+------------------------------+-----------------------------------------------------+
| :class:`SchedulingChannel`   | :class:`~ext.commands.SchedulingChannelConverter`   |
+------------------------------+-----------------------------------------------------+
| :class:`Thread`              | :class:`~ext.commands.ThreadConverter`              |
+------------------------------+-----------------------------------------------------+
| :class:`VoiceChannel`        | :class:`~ext.commands.VoiceChannelConverter`        |
+------------------------------+-----------------------------------------------------+
| :class:`Server`              | :class:`~ext.commands.ServerConverter`              |
+------------------------------+-----------------------------------------------------+
| :class:`Role`                | :class:`~ext.commands.RoleConverter`                |
+------------------------------+-----------------------------------------------------+
| :class:`Colour`              | :class:`~ext.commands.ColourConverter`              |
+------------------------------+-----------------------------------------------------+
| :class:`Emote`               | :class:`~ext.commands.EmoteConverter`               |
+------------------------------+-----------------------------------------------------+

Providing the converter allows us to use them as building blocks for another converter:

.. code-block:: python3

    class MemberRoles(commands.MemberConverter):
        async def convert(self, ctx, argument):
            member = await super().convert(ctx, argument)
            return [role.name for role in member.roles]

    @bot.command()
    async def roles(ctx, *, member: MemberRoles):
        """Tells you a member's roles."""
        await ctx.send('I see the following roles: ' + ', '.join(member))

.. _ext_commands_special_converters:

Special Converters
+++++++++++++++++++

The command extension also has support for certain converters to allow for more advanced and intricate use cases that go
beyond the generic linear parsing. These converters allow you to introduce some more relaxed and dynamic grammar to your
commands in an easy to use manner.

typing.Union
^^^^^^^^^^^^^

A :data:`typing.Union` is a special type hint that allows for the command to take in any of the specific types instead of
a singular type. For example, given the following:

.. code-block:: python3

    import typing

    @bot.command()
    async def union(ctx, what: typing.Union[guilded.ChatChannel, guilded.Member]):
        await ctx.send(what)


The ``what`` parameter would either take a :class:`guilded.ChatChannel` converter or a :class:`guilded.Member` converter.
The way this works is through a left-to-right order. It first attempts to convert the input to a
:class:`guilded.ChatChannel`, and if it fails it tries to convert it to a :class:`guilded.Member`. If all converters fail,
then a special error is raised, :exc:`~ext.commands.BadUnionArgument`.

Note that any valid converter discussed above can be passed in to the argument list of a :data:`typing.Union`.

typing.Optional
^^^^^^^^^^^^^^^^

A :data:`typing.Optional` is a special type hint that allows for "back-referencing" behaviour. If the converter fails to
parse into the specified type, the parser will skip the parameter and then either ``None`` or the specified default will be
passed into the parameter instead. The parser will then continue on to the next parameters and converters, if any.

Consider the following example:

.. code-block:: python3

    import typing

    @bot.command()
    async def bottles(ctx, amount: typing.Optional[int] = 99, *, liquid="beer"):
        await ctx.send(f'{amount} bottles of {liquid} on the wall!')


.. image:: /images/commands/optional.png

In this example, where some arguments ("water") could not be converted into an ``int``, the default of ``99`` is passed and the parser
resumes handling, which in this case would be to pass it into the ``liquid`` parameter.

.. note::

    This converter only works in regular positional parameters, not variable parameters or keyword-only parameters.

typing.Literal
^^^^^^^^^^^^^^^

A :data:`typing.Literal` is a special type hint that requires the passed parameter to be equal to one of the listed values
after being converted to the same type. For example, given the following:

.. code-block:: python3

    from typing import Literal

    @bot.command()
    async def shop(ctx, buy_sell: Literal['buy', 'sell'], amount: Literal[1, 2], *, item: str):
        await ctx.send(f'{buy_sell.capitalize()}ing {amount} {item}(s)!')


The ``buy_sell`` parameter must be either the literal string ``"buy"`` or ``"sell"`` and ``amount`` must convert to the
``int`` ``1`` or ``2``. If ``buy_sell`` or ``amount`` don't match any value, then a special error is raised,
:exc:`~.ext.commands.BadLiteralArgument`. Any literal values can be mixed and matched within the same :data:`typing.Literal` converter.

Note that ``typing.Literal[True]`` and ``typing.Literal[False]`` still follow the :class:`bool` converter rules.

typing.Dict
^^^^^^^^^^^^

A :class:`dict` annotation is functionally equivalent to ``List[Tuple[K, V]]`` except with the return type
given as a :class:`dict` rather than a :class:`list`.


.. _ext_commands_error_handler:

Error Handling
---------------

When our commands fail to parse we will, by default, receive a noisy error in ``stderr`` of our console that tells us
that an error has happened and has been silently ignored.

In order to handle our errors, we must use something called an error handler. There is a global error handler, called
:func:`.on_command_error` which works like any other event in the :ref:`guilded-api-events`. This global error handler is
called for every error reached.

Most of the time however, we want to handle an error local to the command itself. Luckily, commands come with local error
handlers that allow us to do just that. First we decorate an error handler function with :meth:`.Command.error`:

.. code-block:: python3

    @bot.command()
    async def info(ctx, *, member: guilded.Member):
        """Tells you some info about the member."""
        msg = f'{member} joined on {member.joined_at} and has {len(member.roles)} roles.'
        await ctx.send(msg)

    @info.error
    async def info_error(ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send('I could not find that member...')

The first parameter of the error handler is the :class:`.Context` while the second one is an exception that is derived from
:exc:`~ext.commands.CommandError`. A list of errors is found in the :ref:`ext_commands_api_errors` page of the documentation.

Checks
-------

There are cases when we don't want a user to use our commands. They don't have permissions to do so or maybe we blocked
them from using our bot earlier. The commands extension comes with full support for these things in a concept called
:ref:`ext_commands_api_checks`.

A check is a basic predicate that can take in a :class:`.Context` as its sole parameter. Within it, you have the following
options:

- Return ``True`` to signal that the person can run the command.
- Return ``False`` to signal that the person cannot run the command.
- Raise a :exc:`~ext.commands.CommandError` derived exception to signal the person cannot run the command.

    - This allows you to have custom error messages for you to handle in the
      :ref:`error handlers <ext_commands_error_handler>`.

To register a check for a command, we would have two ways of doing so. The first is using the :meth:`~ext.commands.check`
decorator. For example:

.. code-block:: python3

    async def is_owner(ctx):
        return ctx.author.id == 'EdVMVKR4'

    @bot.command(name='eval')
    @commands.check(is_owner)
    async def _eval(ctx, *, code):
        """A bad example of an eval command"""
        await ctx.send(eval(code))

This would only evaluate the command if the function ``is_owner`` returns ``True``. Sometimes we re-use a check often and
want to split it into its own decorator. To do that we can just add another level of depth:

.. code-block:: python3

    def is_owner():
        async def predicate(ctx):
            return ctx.author.id == 'EdVMVKR4'
        return commands.check(predicate)

    @bot.command(name='eval')
    @is_owner()
    async def _eval(ctx, *, code):
        """A bad example of an eval command"""
        await ctx.send(eval(code))


Since an owner check is so common, the library provides it for you (:func:`~ext.commands.is_owner`):

.. code-block:: python3

    @bot.command(name='eval')
    @commands.is_owner()
    async def _eval(ctx, *, code):
        """A bad example of an eval command"""
        await ctx.send(eval(code))

When multiple checks are specified, **all** of them must be ``True``:

.. code-block:: python3

    def is_in_server(server_id):
        async def predicate(ctx):
            return ctx.server and ctx.server.id == server_id
        return commands.check(predicate)

    @bot.command()
    @commands.is_owner()
    @is_in_server('QR46qKZE')
    async def secretserverdata(ctx):
        """super secret stuff"""
        await ctx.send('secret stuff')

If any of those checks fail in the example above, then the command will not be run.

When an error happens, the error is propagated to the :ref:`error handlers <ext_commands_error_handler>`. If you do not
raise a custom :exc:`~ext.commands.CommandError` derived exception, then it will get wrapped up into a
:exc:`~ext.commands.CheckFailure` exception as so:

.. code-block:: python3

    @bot.command()
    @commands.is_owner()
    @is_in_server('QR46qKZE')
    async def secretserverdata(ctx):
        """super secret stuff"""
        await ctx.send('secret stuff')

    @secretserverdata.error
    async def secretserverdata_error(ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send('nothing to see here comrade.')

If you want a more robust error system, you can derive from the exception and raise it instead of returning ``False``:

.. code-block:: python3

    class NoPrivateMessages(commands.CheckFailure):
        pass

    def server_only():
        async def predicate(ctx):
            if ctx.server is None:
                raise NoPrivateMessages('Hey no DMs!')
            return True
        return commands.check(predicate)

    @server_only()
    async def test(ctx):
        await ctx.send('Hey this is not a DM! Nice.')

    @test.error
    async def test_error(ctx, error):
        if isinstance(error, NoPrivateMessages):
            await ctx.send(error)

.. note::

    Since having a ``server_only`` decorator is pretty common, it comes built-in via :func:`~ext.commands.server_only`.

Global Checks
++++++++++++++

Sometimes we want to apply a check to **every** command, not just certain
commands. The library supports this as well using global checks.

Global checks work similarly to regular checks except they are registered with
the :meth:`ext.commands.Bot.check` decorator.

For example, to block all DMs we could do the following:

.. code-block:: python3

    @bot.check
    async def globally_block_dms(ctx):
        return ctx.server is not None

.. warning::

    Be careful on how you write your global checks, as it could also lock you out of your own bot.
