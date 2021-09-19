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
from typing import Optional

from .asset import Asset
from .errors import InvalidArgument
from .file import File, MediaType
from .status import Game
from .utils import ISO8601


class Group:
    """Represents a team group in Guilded.

    Attributes
    -----------
    team: :class:`Team`
        The team that the group belongs to.
    id: :class:`str`
        The group's id.
    name: :class:`str`
        The group's name.
    description: Optional[:class:`str`]
        The group's description.
    position: Optional[:class:`int`]
        The group's position on the sidebar. Will be ``None`` if :attr:`.base`
        is ``True``\.
    base: :class:`bool`
        Whether the group is the base or "home" group of its team.
    public: :class:`bool`
        Whether the group is public.
    """
    def __init__(self, *, state, team, data):
        self._state = state
        self.team = team
        data = data.get('group', data)

        self.id: str = data.get('id')
        self.name: str = data.get('name')
        self.type: str = data.get('type', 'team')
        self.description: str = data.get('description') or ''
        self.position: Optional[int] = data.get('priority')
        self.team_id: str = data.get('teamId', team.id)

        self.game_id: Optional[int] = data.get('gameId')
        self.base: bool = data.get('isBase')
        self.public: bool = data.get('isPublic')

        self.created_by = self.team.get_member(data.get('createdBy')) or data.get('createdBy')
        self.updated_by = self.team.get_member(data.get('updatedBy')) or data.get('updatedBy')
        self.archived_by = self.team.get_member(data.get('archivedBy')) or data.get('archivedBy')

        self.created_at: datetime.datetime = ISO8601(data.get('createdAt'))
        self.updated_at: datetime.datetime = ISO8601(data.get('updatedAt'))
        self.deleted_at: datetime.datetime = ISO8601(data.get('deletedAt'))
        self.archived_at: datetime.datetime = ISO8601(data.get('archivedAt'))

        icon_url = data.get('avatar')
        if icon_url:
            self.icon_url = Asset('avatar', state=self._state, data=data)
        else:
            self.icon_url = None

        banner_url = data.get('banner')
        if banner_url:
            self.banner_url = Asset('banner', state=self._state, data=data)
        else:
            self.banner_url = None

    @property
    def game(self) -> Game:
        """Optional[:class:`Game`]: The game that the group is for."""
        if self.game_id:
            return Game(game_id=self.game_id)
        return None

    @property
    def archived(self) -> bool:
        """:class:`bool`: Whether this group is archived."""
        return self.archived_at is not None or self.archived_by is not None

    def __str__(self):
        return self.name

    def __repr__(self):
        return f'<Group id={self.id!r} name={self.name!r} team_id={self.team_id!r}>'

    async def delete(self):
        """|coro|

        Delete this group.
        """
        return await self._state.delete_team_group(self.team.id, self.id)

    async def edit(self, **fields):
        """|coro|

        Edit this group.

        All parameters are optional.

        Parameters
        -----------
        icon: Union[:class:`str`, :class:`File`]
            The file to upload or an existing CDN URL to use for this
            group's icon.
        """
        try:
            icon = fields.pop('icon')
        except KeyError:
            pass
        else:
            if isinstance(icon, str):
                fields['icon_url'] = fields.get('icon')
            elif isinstance(icon, File):
                icon.set_media_type(MediaType.group_icon)
                fields['icon_url'] = await icon._upload(self._state)
            elif isinstance(icon, None):
                fields['icon_url'] = None
            else:
                raise InvalidArgument(f'icon must be type str, File, or None, not {icon.__class__.__name__}')

        return await self._state.update_team_group(self.team.id, self.id, **fields)
