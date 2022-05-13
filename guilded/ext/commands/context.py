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

import re
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Sequence, Union

import guilded.abc
from guilded.utils import MISSING

if TYPE_CHECKING:
    from guilded.channel import DMChannel
    from guilded.embed import Embed
    from guilded.emoji import Emoji
    from guilded.file import File
    from guilded.message import ChatMessage
    from guilded.team import Team
    from guilded.user import ClientUser, Member, User

    from .core import Cog, Command
    from .bot import Bot
    from .view import StringView


class Context(guilded.abc.Messageable):
    def __init__(self, **attrs):
        self.message: ChatMessage = attrs.pop('message', None)
        self._state = attrs.pop('state', self.message._state)
        self.bot: Bot = attrs.pop('bot', None)
        self.args: List[Any] = attrs.pop('args', [])
        self.kwargs: Dict[str, Any] = attrs.pop('kwargs', {})
        self.prefix: str = attrs.pop('prefix')
        self.command: Optional[Command] = attrs.pop('command', None)
        self.view: Optional[StringView] = attrs.pop('view', None)
        self.invoked_with: Optional[str] = attrs.pop('invoked_with', None)
        self.invoked_parents: List[str] = attrs.pop('invoked_parents', [])
        self.invoked_subcommand: Optional[Command] = attrs.pop('invoked_subcommand', None)
        self.subcommand_passed: Optional[str] = attrs.pop('subcommand_passed', None)
        self.command_failed: bool = attrs.pop('command_failed', False)

    def __repr__(self) -> str:
        return f'<Context prefix={self.prefix} message={repr(self.message)}>'

    @property
    def valid(self) -> bool:
        return self.prefix is not None and self.command is not None

    @property
    def cog(self) -> Optional[Cog]:
        if self.command is None:
            return None
        return self.command.cog

    @property
    def channel(self) -> Union[guilded.abc.TeamChannel, DMChannel]:
        return self.message.channel

    @property
    def _channel_id(self) -> str:
        return self.message.channel_id

    @property
    def team(self) -> Optional[Team]:
        return self.message.team

    @property
    def guild(self) -> Optional[Team]:
        return self.team

    @property
    def server(self) -> Optional[Team]:
        return self.team

    @property
    def author(self) -> Union[Member, User]:
        return self.message.author

    @property
    def me(self) -> Union[Member, ClientUser]:
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

    async def reply(
        self,
        *pos_content: Optional[Union[str, Embed, File, Emoji, Member]],
        content: Optional[str] = MISSING,
        file: Optional[File] = MISSING,
        files: Optional[Sequence[File]] = MISSING,
        embed: Optional[Embed] = MISSING,
        embeds: Optional[Sequence[Embed]] = MISSING,
        reference: Optional[ChatMessage] = MISSING,
        reply_to: Optional[Sequence[ChatMessage]] = MISSING,
        mention_author: Optional[bool] = None,
        silent: Optional[bool] = None,
        private: bool = False,
        share: Optional[ChatMessage] = MISSING,
        delete_after: Optional[float] = None,
    ) -> ChatMessage:
        """|coro|

        Reply to the invoking message.
        This is identical to :meth:`abc.Messageable.send`, but the
        ``reply_to`` parameter already includes the context message.
        """

        return await self.message.reply(
            *pos_content,
            content=content,
            file=file,
            files=files,
            embed=embed,
            embeds=embeds,
            reference=reference,
            reply_to=reply_to,
            mention_author=mention_author,
            silent=silent,
            private=private,
            share=share,
            delete_after=delete_after,
        )
