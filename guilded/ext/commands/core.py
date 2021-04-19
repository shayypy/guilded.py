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

from .errors import *


def hooked_wrapped_callback(command, ctx, coro):
    @functools.wraps(coro)
    async def wrapped(*args, **kwargs):
        try:
            ret = await coro(ctx, *args, **kwargs)
        except CommandError:
            ctx.command_failed = True
            raise
        except asyncio.CancelledError:
            ctx.command_failed = True
            return
        except Exception as exc:
            ctx.command_failed = True
            raise CommandInvokeError(exc) from exc
        #finally:
        #    if command._max_concurrency is not None:
        #        await command._max_concurrency.release(ctx)

        #    await command.call_after_hooks(ctx)
        return ret
    return wrapped

class Command:
    def __init__(self, coro, **kwargs):
        if not asyncio.iscoroutinefunction(coro):
            raise TypeError('Function must be a coroutine.')

        name = kwargs.get('name') or coro.__name__
        if not isinstance(name, str):
            raise TypeError('Command name must be a string.')
        self.name = name

        help_doc = kwargs.get('help')
        if help_doc is not None:
            help_doc = inspect.cleandoc(help_doc)
        else:
            help_doc = inspect.getdoc(coro)
            if isinstance(help_doc, bytes):
                help_doc = help_doc.decode('utf-8')

        self.help = help_doc
        self.enabled = kwargs.get('enabled', True)
        self.callback = coro
        self.brief = kwargs.get('brief')
        self.usage = kwargs.get('usage')
        self.rest_is_raw = kwargs.get('rest_is_raw', False)
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

        #try:
        #    checks = func.__commands_checks__
        #    checks.reverse()
        #except AttributeError:
        #    checks = kwargs.get('checks', [])
        #finally:
        #    self.checks = checks

    async def __call__(self, *args, **kwargs):
        '''|coro|
        Calls the internal callback that the command holds.
        '''
        if self.cog is not None:
            # manually pass the cog class to the coro instead of calling it as a method
            return await self.callback(self.cog, *args, **kwargs)
        else:
            return await self.callback(*args, **kwargs)

    async def invoke(self, ctx):
        ctx.command = self

        # terminate the invoked_subcommand chain.
        # since we're in a regular command (and not a group) then
        # the invoked subcommand is None.
        ctx.invoked_subcommand = None
        ctx.subcommand_passed = None
        injected = hooked_wrapped_callback(self, ctx, self.callback)
        await injected(*ctx.args, **ctx.kwargs)

def command(**kwargs):
    def decorator(coro):
        if isinstance(coro, Command):
            raise TypeError('Function is already a command.')
        return Command(coro, **kwargs)

    return decorator
