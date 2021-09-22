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

from typing import List, Optional

from .asset import Asset
from .user import Member
from .utils import ISO8601


class DiscordEmoji:
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
    def __init__(self, *, id, synced_at):
        self.id: int = int(id)
        self.synced_at: datetime.datetime = ISO8601(synced_at)

    @property
    def url(self) -> str:
        """:class:`str`: The Discord CDN URL of the emoji.

        Does not include a file extension as the animated status of the emoji
        cannot be practically known. If you need a file extension, appending
        ``.png`` will return a valid static image regardless of if the emoji
        is animated.
        """
        return f'https://cdn.discordapp.com/emojis/{self.id}'

    def __eq__(self, other):
        return isinstance(other, DiscordEmoji) and other.id == self.id

class Emoji:
    """Represents a team emoji in Guilded.

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
    author_id: :class:`str`
        The emoji's author's ID.
    url: :class:`Asset`
        The emoji's CDN URL.
    aliases: List[:class:`str`]
        A list of aliases for the emoji. Likely only applicable to standard
        (unicode) emojis.
    created_at: Optional[:class:`datetime.datetime`]
        When the emoji was created.
    discord: Optional[:class:`.DiscordEmoji`]
        The Discord emoji that the emoji corresponds to.
    """
    def __init__(self, *, state, team, data):
        self._state = state
        self.team = team

        self.id: int = data.get('id')
        self.name: str = data.get('name')
        self.author_id: str = data.get('createdBy')
        self.aliases: List[str] = data.get('aliases', [])
        self.created_at: Optional[datetime.datetime] = ISO8601(data.get('createdAt'))

        urls = {
            'customReaction': data.get('apng') or data.get('gif') or data.get('png') or data.get('webp'),
            # assume animated first, even though guilded seems to simply append ?ia=1 rather than using their apng field.
            'customReactionPNG': data.get('png'),
            'customReactionWEBP': data.get('webp'),
            'customReactionAPNG': data.get('apng'),
            'customReactionGIF': data.get('gif')
        }
        self.url: Asset = Asset('customReaction', state=self._state, data=urls)

        self.discord: Optional[DiscordEmoji] = None
        if data.get('discordEmojiId'):
            self.discord = DiscordEmoji = DiscordEmoji(id=data.get('discordEmojiId'), synced_at=data.get('discordSyncedAt'))

        self.deleted: bool = data.get('isDeleted', False)

    @property
    def author(self) -> Optional[Member]:
        """Optional[:class:`.Member`]: The :class:`.Member` who created the emoji."""
        return self.team.get_member(self.author_id)

    @property
    def team_id(self) -> str:
        """Optional[:class:`str`]: The ID of the team that the emoji is from."""
        return self.team.id if self.team else None

    @property
    def animated(self) -> bool:
        """:class:`bool`: Whether the emoji is animated."""
        if getattr(self.url, 'apng', None) is not None or 'ia=1' in self.url:
            return True
        else:
            return False

    def __eq__(self, other):
        return isinstance(other, Emoji) and other.id == self.id

    def __str__(self):
        return self.name

    def __bool__(self):
        return not self.deleted

    def __repr__(self):
        return f'<Emoji id={self.id!r} name={self.name!r} team={self.team!r}>'

    async def delete(self):
        """|coro|

        Delete this emoji.
        """
        return await self._state.delete_team_emoji(self.team_id, self.id)
