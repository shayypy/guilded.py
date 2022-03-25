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

import datetime
import os
from typing import List, Optional
import yarl

from .asset import AssetMixin, Asset
from .errors import InvalidArgument
from .user import Member
from .utils import ISO8601


__all__ = (
    'DiscordEmoji',
    'Emoji',
)


class DiscordEmoji(AssetMixin):
    """Represents a Discord emoji that an emoji on Guilded corresponds to.

    Guilded does not provide the emoji's name, so you would likely use this
    data in conjunction with a Discord bot.

    .. container:: operations

        .. describe:: x == y

            Checks if two emojis are equal.

        .. describe:: x != y

            Checks if two emojis are not equal.

    Attributes
    -----------
    id: :class:`int`
        The emoji's ID.
    synced_at: :class:`datetime.datetime`
        When the emoji was last synced with Guilded.
    """
    def __init__(self, *, state, id, synced_at):
        self._state = state
        self.id: int = int(id)
        self.synced_at: datetime.datetime = ISO8601(synced_at)

    @property
    def url(self) -> str:
        """:class:`str`: The Discord CDN URL of the emoji.

        The file extension will be ``png`` by default regardless of whether or
        not the emoji is animated. You may generate a different URL using
        :meth:`.url_with_format`.
        """
        return f'https://cdn.discordapp.com/emojis/{self.id}.png'

    def __eq__(self, other):
        return isinstance(other, DiscordEmoji) and other.id == self.id

    def url_with_format(self, format: str) -> str:
        """Returns a new URL with a different format.

        Parameters
        -----------
        format: :class:`str`
            The new format to change it to. Must be one of
            'png', 'jpg', 'jpeg', 'webp', 'gif'.

            .. warning::

                Validity is not checked if 'gif' is passed because it is not
                practically possible to know whether the emoji is animated, so
                you may end up with a nonfunctional URL if you are not careful.

        Returns
        --------
        :class:`str`
            The emoji's newly updated Discord CDN URL.
        """

        valid_formats = ['png', 'jpg', 'jpeg', 'webp', 'gif']

        if format not in valid_formats:
            raise InvalidArgument(f'format must be one of {valid_formats}')

        url = yarl.URL(self.url)
        path, _ = os.path.splitext(url.path)
        return str(url.with_path(f'{path}.{format}'))


class Emoji(AssetMixin):
    """Represents a team or stock emoji in Guilded.

    .. container:: operations

        .. describe:: x == y

            Checks if two emojis are equal.

        .. describe:: x != y

            Checks if two emojis are not equal.

        .. describe:: str(x)

            Returns the name of the emoji.

        .. describe:: bool(x)

            Checks if the emoji is not deleted.

    Attributes
    -----------
    id: :class:`int`
        The emoji's ID.
    name: :class:`str`
        The emoji's name.
    aliases: List[:class:`str`]
        A list of aliases for the emoji. Likely only applicable to stock
        (unicode and Guilded) emojis.
    created_at: Optional[:class:`datetime.datetime`]
        When the emoji was created.
    discord: Optional[:class:`.DiscordEmoji`]
        The Discord emoji that the emoji corresponds to.
    """

    def __init__(self, *, state, data, **extra):
        self._state = state
        self._team = extra.get('team')

        self.id: int = data.get('id')
        self.name: str = data.get('name')
        self.team_id: Optional[str] = data.get('teamId')
        self.author_id: Optional[str] = data.get('createdBy')
        self.aliases: List[str] = data.get('aliases', [])
        self.created_at: Optional[datetime.datetime] = ISO8601(data.get('createdAt'))
        self.deleted: bool = data.get('isDeleted', False)
        self._animated: bool = data.get('isAnimated', False)

        self._stock_guilded: bool = extra.get('stock') is True and data.get('category') == 'Guilded'
        self._stock_unicode: bool = extra.get('stock') is True and data.get('category') != 'Guilded'

        if self._stock_guilded:
            asset: Asset = Asset._from_guilded_stock_reaction(state, self.name, animated=self._animated)
        elif self._stock_unicode:
            asset: Asset = Asset._from_unicode_stock_reaction(state, self.name, animated=self._animated)
        else:
            url = data.get('webp', data.get('png'))
            asset: Asset = Asset._from_custom_reaction(state, url, animated=self._animated or 'ia=1' in url)

        self._underlying: Asset = asset

        discord_emoji = None
        if data.get('discordEmojiId'):
            discord_emoji = DiscordEmoji(
                state=state,
                data={
                    'id': data['discordEmojiId'],
                    'synced_at': data.get('discordSyncedAt'),
                },
            )
        self.discord: Optional[DiscordEmoji] = discord_emoji

    def __eq__(self, other):
        return isinstance(other, Emoji) and other.id == self.id

    def __str__(self):
        return self.name

    def __bool__(self):
        return not self.deleted

    def __repr__(self):
        return f'<Emoji id={self.id!r} name={self.name!r} team={self.team!r}>'

    @property
    def author(self) -> Optional[Member]:
        """Optional[:class:`.Member`]: The :class:`.Member` who created the
        emoji, if any."""
        return self.team.get_member(self.author_id)

    @property
    def team(self):
        """Optional[:class:`.Team`]: The team that the emoji is from, if any."""
        return self._team or self._state._get_team(self.team_id)

    @property
    def guild(self):
        """|dpyattr|

        This is an alias of :attr:`.team`.
        """
        return self.team

    @property
    def server(self):
        """Optional[:class:`.Team`]: This is an alias of :attr:`.team`."""
        return self.team

    @property
    def animated(self) -> bool:
        """:class:`bool`: Whether the emoji is animated."""
        return self._underlying.animated or 'ia=1' in self.url

    @property
    def stock(self) -> bool:
        """:class:`bool`: Whether the emoji is a stock emoji (Unicode or by Guilded)."""
        return self._stock_guilded or self._stock_unicode

    @property
    def url(self) -> str:
        """:class:`str`: The emoji's CDN URL."""
        return self._underlying.url

    def url_with_format(self, format: str) -> str:
        """Returns a new URL with a different format. By default, the format
        will be ``apng`` if provided, else ``webp``.

        This is functionally a more restricted version of :meth:`Asset.with_format`;
        that is, only formats that are available to emojis can be used in an
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
            The emoji's newly updated CDN URL.
        """

        valid_formats = ['png', 'webp']
        if self._stock_guilded:
            if self.animated:
                valid_formats.append('apng')

        if format not in valid_formats:
            raise InvalidArgument(f'format must be one of {valid_formats}')

        return self._underlying.with_format(format).url

    def url_with_static_format(self, format: str) -> str:
        """Returns a new URL with a different format if the emoji is static,
        else the current (animated) URL is returned.

        This is functionally a more restricted version of :meth:`Asset.with_static_format`;
        that is, only formats that are available to emojis can be used in an
        attempt to avoid generating nonfunctional URLs.

        Parameters
        -----------
        format: :class:`str`
            The new format to change it to. Must be one of 'png' or 'webp'.

        Returns
        --------
        :class:`str`
            The emoji's newly updated CDN URL.
        """

        valid_formats = ['png', 'webp']

        if format not in valid_formats:
            raise InvalidArgument(f'format must be one of {valid_formats}')

        return self._underlying.with_static_format(format).url

    async def delete(self):
        """|coro|

        |onlyuserbot|

        Delete this emoji.
        """
        return await self._state.delete_team_emoji(self.team_id, self.id)
