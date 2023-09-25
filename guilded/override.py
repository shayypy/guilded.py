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
from typing import TYPE_CHECKING, Optional, Tuple, Union

from .permissions import REVERSE_VALID_NAME_MAP, PermissionOverride
from .utils import ISO8601

if TYPE_CHECKING:
    from .types.category import (
        ChannelCategoryRolePermission as ChannelCategoryRolePermissionPayload,
        ChannelCategoryRolePermission as ChannelCategoryUserPermissionPayload,
    )
    from .types.channel import (
        ChannelRolePermission as ChannelRolePermissionPayload,
        ChannelUserPermission as ChannelUserPermissionPayload,
    )

    from .server import Server


__all__ = (
    'ChannelRoleOverride',
    'ChannelUserOverride',
    'CategoryRoleOverride',
)


class _ChannelPermissionOverride:
    __slots__: Tuple[str, ...] = (
        'override',
        'created_at',
        'updated_at',
        'channel_id',
        'channel',
    )

    def __init__(
        self,
        *,
        data: Union[ChannelRolePermissionPayload, ChannelUserPermissionPayload],
        server: Optional[Server] = None,
    ):
        self.override = PermissionOverride(**{ REVERSE_VALID_NAME_MAP[key]: value for key, value in data['permissions'].items() })
        self.created_at = ISO8601(data['createdAt'])
        self.updated_at = ISO8601(data.get('updatedAt'))
        self.channel_id = data['channelId']
        self.channel = server.get_channel(self.channel_id) if server else None


class ChannelRoleOverride(_ChannelPermissionOverride):
    """Represents a role-based permission override in a channel.

    .. versionadded:: 1.11

    Attributes
    -----------
    role: Optional[:class:`.Role`]
        The role whose permissions are to be overridden.
    role_id: :class:`str`
        The ID of the role.
    override: :class:`.PermissionOverride`
        The permission values overridden for the role.
    channel: Optional[:class:`.abc.ServerChannel`]
        The channel that the override is in.
    channel_id: :class:`str`
        The ID of the channel.
    created_at: :class:`datetime.datetime`
        When the override was created.
    updated_at: Optional[:class:`datetime.datetime`]
        When the override was last updated.
    """

    __slots__: Tuple[str, ...] = (
        'role_id',
        'role',
    )

    def __init__(self, *, data: ChannelRolePermissionPayload, server: Optional[Server] = None):
        super().__init__(data=data, server=server)
        self.role_id = data['roleId']
        self.role = server.get_role(self.role_id) if server else None

    def __repr__(self) -> str:
        return f'<ChannelRoleOverride override={self.override!r} channel_id={self.channel_id!r} role_id={self.role_id!r}>'


class ChannelUserOverride(_ChannelPermissionOverride):
    """Represents a user-based permission override in a channel.

    .. versionadded:: 1.11

    Attributes
    -----------
    override: :class:`.PermissionOverride`
        The permission values overridden for the role.
    user: Optional[:class:`.Member`]
        The user whose permissions are to be overridden.
    user_id: :class:`str`
        The ID of the user.
    channel: Optional[:class:`.abc.ServerChannel`]
        The channel that the override is in.
    channel_id: :class:`str`
        The ID of the channel.
    created_at: :class:`datetime.datetime`
        When the override was created.
    updated_at: Optional[:class:`datetime.datetime`]
        When the override was last updated.
    """

    __slots__: Tuple[str, ...] = (
        'user_id',
        'user',
    )

    def __init__(self, *, data: ChannelUserPermissionPayload, server: Optional[Server] = None):
        super().__init__(data=data, server=server)
        self.user_id = data['userId']
        self.user = server.get_member(self.user_id) if server else None

    def __repr__(self) -> str:
        return f'<ChannelUserOverride override={self.override!r} channel_id={self.channel_id!r} user_id={self.user_id!r}>'


class _CategoryPermissionOverride:
    __slots__: Tuple[str, ...] = (
        'override',
        'created_at',
        'updated_at',
        'category_id',
        'category',
    )

    def __init__(
        self,
        *,
        data: Union[ChannelCategoryRolePermissionPayload, ChannelCategoryUserPermissionPayload],
        server: Optional[Server] = None,
    ):
        self.override = PermissionOverride(**{ REVERSE_VALID_NAME_MAP[key]: value for key, value in data['permissions'].items() })
        self.created_at = ISO8601(data['createdAt'])
        self.updated_at = ISO8601(data.get('updatedAt'))
        self.category_id = data['categoryId']
        self.category = server.get_category(self.category_id) if server else None


class CategoryRoleOverride(_CategoryPermissionOverride):
    """Represents a role-based permission override in a category.

    .. versionadded:: 1.11

    Attributes
    -----------
    role: Optional[:class:`.Role`]
        The role whose permissions are to be overridden.
    role_id: :class:`str`
        The ID of the role.
    override: :class:`.PermissionOverride`
        The permission values overridden for the role.
    category: Optional[:class:`.Category`]
        The category that the override is in.
    category_id: :class:`int`
        The ID of the category.
    created_at: :class:`datetime.datetime`
        When the override was created.
    updated_at: Optional[:class:`datetime.datetime`]
        When the override was last updated.
    """

    __slots__: Tuple[str, ...] = (
        'role_id',
        'role',
    )

    def __init__(self, *, data: ChannelRolePermissionPayload, server: Optional[Server] = None):
        super().__init__(data=data, server=server)
        self.role_id = data['roleId']
        self.role = server.get_role(self.role_id) if server else None

    def __repr__(self) -> str:
        return f'<CategoryRoleOverride override={self.override!r} category_id={self.category_id!r} role_id={self.role_id!r}>'
