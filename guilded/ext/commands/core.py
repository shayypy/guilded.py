import asyncio
import inspect


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

def command(**kwargs):
    def decorator(coro):
        if isinstance(coro, Command):
            raise TypeError('Function is already a command.')
        return Command(coro, **kwargs)

    return decorator
