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

import re

import guilded.abc


class Context(guilded.abc.Messageable):
    def __init__(self, **attrs):
        self.message = attrs.pop('message', None)
        self._state = attrs.pop('state', self.message._state)
        self.bot = attrs.pop('bot', None)
        self.args = attrs.pop('args', [])
        self.kwargs = attrs.pop('kwargs', {})
        self.prefix = attrs.pop('prefix')
        self.command = attrs.pop('command', None)
        self.view = attrs.pop('view', None)
        self.invoked_with = attrs.pop('invoked_with', None)
        self.invoked_parents = attrs.pop('invoked_parents', [])
        self.invoked_subcommand = attrs.pop('invoked_subcommand', None)
        self.subcommand_passed = attrs.pop('subcommand_passed', None)
        self.command_failed = attrs.pop('command_failed', False)

    def __repr__(self):
        return f'<Context prefix={self.prefix} message={repr(self.message)}>'

    @property
    def valid(self):
        return self.prefix is not None and self.command is not None

    @property
    def cog(self):
        if self.command is None:
            return None
        return self.command.cog

    @property
    def channel(self):
        return self.message.channel

    @property
    def _channel_id(self):
        return self.message.channel_id

    @property
    def team(self):
        return self.message.team

    @property
    def guild(self):
        return self.team

    @property
    def author(self):
        return self.message.author

    @property
    def me(self):
        return self.team.me if self.team else self.bot.user

    @property
    def clean_prefix(self) -> str:
        """:class:`str`: The cleaned up invoke prefix. i.e. mentions are ``@name`` instead of ``<@id>``."""
        if self.prefix is None:
            return ''

        user = self.me
        # this breaks if the prefix mention is not the bot itself but I
        # consider this to be an *incredibly* strange use case. I'd rather go
        # for this common use case rather than waste performance for the
        # odd one.
        pattern = re.compile(r"<@!?%s>" % user.id)
        return pattern.sub("@%s" % user.display_name.replace('\\', r'\\'), self.prefix)

    def reply(self, *content, **kwargs):
        """|coro|

        Reply to the invoking message. Functions the same as
        :meth:`abc.Messageable.send`, but with the ``reply_to`` parameter
        already set.
        """
        return self.message.reply(*content, **kwargs)
