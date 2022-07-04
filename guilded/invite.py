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
"""

from __future__ import annotations

from typing import Any, Dict, Tuple

from .server import Server
from .user import User


class Invite:
    """Represents an invite that can be used to add members to a :class:`.Server`.

    Attributes
    -----------
    id: :class:`str`
        The invite's ID.
    code: :class:`str`
        The URL fragment used for the invite.
        This could be the same as :attr:`.id` or the server's :attr:`~.Server.slug`.
    server: :class:`.Server`
        The server that the invite is for.
    inviter: :class:`~guilded.User`
        The user that created the invite.
    """

    __slots__: Tuple[str, ...] = (
        '_state',
        'id',
        'author_id',
        '_code_is_vanity',
        'code',
        'server',
        'inviter',
    )

    def __init__(self, *, state, data: Dict[str, Any], canonical: str = None):
        self._state = state

        self.id: str = data['inviteId']
        self.author_id: str = data['createdBy']

        self._code_is_vanity: bool = False
        if canonical is not None and not canonical.startswith('/i/'):
            # Guilded generally forces vanities onto servers so `canonical` *should* never be None
            # and *should* never start with /i/, but we have this check just in case.

            # It should be noted that server vanity URLs are not actually invites that can be fetched.
            self._code_is_vanity = True
            self.code = canonical.replace('/', '', 1)
        else:
            self.code = self.id

        self.server = Server(data=data['team'], state=state)
        self.inviter = User(data=data['createdByInfo'], state=state)

    def __repr__(self) -> str:
        return f'<Invite id={self.id!r} code={self.code!r} server={self.server!r}>'

    @property
    def url(self) -> str:
        """:class:`str`: The full URL of the invite."""
        return f'https://guilded.gg/{"" if self._code_is_vanity else "i/"}{self.code}'

    @property
    def guild(self) -> Server:
        """:class:`.Server`: |dpyattr|

        This is an alias of :attr:`.server`.

        The server that the invite is for.
        """
        return self.server
