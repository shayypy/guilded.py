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

import datetime
from typing import TYPE_CHECKING, List, Optional

from .asset import AssetMixin, Asset
from .errors import InvalidArgument
from .user import Member
from .utils import ISO8601

if TYPE_CHECKING:
    from .types.emote import Emote as EmotePayload


__all__ = (
    'Emoji',
    'Emote',
)


class Emote(AssetMixin):
    """Represents a server or stock emote in Guilded.

    .. container:: operations

        .. describe:: x == y

            Checks if two emotes are equal.

        .. describe:: x != y

            Checks if two emotes are not equal.

        .. describe:: str(x)

            Returns the name of the emote.

    Attributes
    -----------
    id: :class:`int`
        The emote's ID.
    name: :class:`str`
        The emote's name.
    stock: :class:`bool`
        Whether the emote is a stock emote (Unicode or by Guilded).
    """

    def __init__(self, *, state, data: EmotePayload, **extra):
        self._state = state
        self._server = extra.get('server')

        self.id: int = data.get('id')
        self.name: str = data.get('name') or ''
        self.server_id: Optional[str] = data.get('serverId') or data.get('teamId')
        self.author_id: Optional[str] = data.get('createdBy')
        self.created_at: Optional[datetime.datetime] = ISO8601(data.get('createdAt'))
        _url: Optional[str] = data.get('url')

        self._animated: bool = data.get('isAnimated', False)
        self.aliases: List[str] = data.get('aliases', [])
        self.stock: bool = self.id in range(90000000, 90003376) or (_url and '/asset/Emojis' in _url)
        # Stock emoji IDs increment up from 90,000,000.
        # The ceiling is currently 90,003,375 (grinning..heavy_equals_sign).

        # At time of writing (May 2022), custom emoji IDs are >1,200,000 and
        # are also incremental.
        # Presumably, there are checks in place to prevent the 90 millionth
        # emoji from overwriting :grinning:.

        # This handles data from Guilded (_url is not None) as well as custom data from StockReactions:
        # https://github.com/GuildedAPI/datatables/blob/main/reactions-stripped.json
        self._stock_guilded: bool = self.stock and (data.get('category') == 'Guilded' or (_url and '/asset/Emojis/Custom' in _url))
        self._stock_unicode: bool = self.stock and (data.get('category') != 'Guilded' or (_url and '/asset/Emojis/Custom' not in _url))

        if self._stock_guilded:
            asset: Asset = Asset._from_guilded_stock_reaction(state, self.name, animated=self._animated)
        elif self._stock_unicode:
            asset: Asset = Asset._from_unicode_stock_reaction(state, self.name, animated=self._animated)
        else:
            url = _url or data.get('webp') or data.get('png')
            asset: Asset = Asset._from_custom_reaction(state, url, animated=self._animated or 'ia=1' in url)

        self._underlying: Asset = asset

    def __eq__(self, other):
        return isinstance(other, Emote) and other.id == self.id

    def __str__(self):
        return self.name

    def __repr__(self):
        return f'<Emote id={self.id!r} name={self.name!r} server={self.server!r}>'

    @property
    def author(self) -> Optional[Member]:
        """Optional[:class:`.Member`]: The :class:`.Member` who created the custom emote, if any."""
        return self.server.get_member(self.author_id)

    @property
    def server(self):
        """Optional[:class:`.Server`]: The server that the emote is from, if any."""
        return self._server or self._state._get_server(self.server_id)

    @property
    def guild(self):
        """Optional[:class:`.Server`]: |dpyattr|

        This is an alias of :attr:`.server`.

        The server that the emote is from, if any.
        """
        return self.server

    @property
    def animated(self) -> bool:
        """:class:`bool`: Whether the emote is animated."""
        return self._underlying.is_animated()

    @property
    def url(self) -> str:
        """:class:`str`: The emote's CDN URL."""
        return self._underlying.url

    def url_with_format(self, format: str) -> str:
        """Returns a new URL with a different format. By default, the format
        will be ``apng`` if provided, else ``webp``.

        This is functionally a more restricted version of :meth:`Asset.with_format`;
        that is, only formats that are available to emotes can be used in an
        attempt to avoid generating nonfunctional URLs.

        Parameters
        -----------
        format: :class:`str`
            The new format to change it to. Must be
            'png' or 'webp' if stock unicode or custom, and
            'png', 'webp', or 'apng' if stock Guilded.

        Returns
        --------
        :class:`str`
            The emote's newly updated CDN URL.

        Raises
        -------
        InvalidArgument
            Invalid format provided.
        """

        valid_formats = ['png', 'webp']
        if self._stock_guilded:
            if self.animated:
                valid_formats.append('apng')

        if format not in valid_formats:
            raise InvalidArgument(f'format must be one of {valid_formats}')

        return self._underlying.with_format(format).url

    def url_with_static_format(self, format: str) -> str:
        """Returns a new URL with a different format if the emote is static,
        else the current (animated) URL is returned.

        This is functionally a more restricted version of :meth:`Asset.with_static_format`;
        that is, only formats that are available to emotes can be used in an
        attempt to avoid generating nonfunctional URLs.

        Parameters
        -----------
        format: :class:`str`
            The new format to change it to. Must be one of 'png' or 'webp'.

        Returns
        --------
        :class:`str`
            The emote's newly updated CDN URL.

        Raises
        -------
        InvalidArgument
            Invalid format provided.
        """

        valid_formats = ['png', 'webp']

        if format not in valid_formats:
            raise InvalidArgument(f'format must be one of {valid_formats}')

        return self._underlying.with_static_format(format).url

Emoji = Emote
