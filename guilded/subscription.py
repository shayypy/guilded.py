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

from typing import TYPE_CHECKING, Optional, Tuple

from .enums import try_enum, ServerSubscriptionTierType
from .utils import ISO8601

if TYPE_CHECKING:
    from .types.subscription import ServerSubscriptionTier as ServerSubscriptionTierPayload

    from .role import Role
    from .server import Server


__all__ = (
    'ServerSubscriptionTier',
)


class ServerSubscriptionTier:
    """Represents a subscription tier in a server.

    .. container:: operations

        .. describe:: x == y

            Checks if two tiers are equal.

        .. describe:: x != y

            Checks if two tiers are not equal.

    .. versionadded:: 1.9

    Attributes
    -----------
    type: :class:`.ServerSubscriptionTierType`
        The type of the tier.
    server_id: :class:`str`
        The ID of the server that the tier is in.
    role_id: Optional[:class:`int`]
        The ID of the role that the tier is linked to.
    description: Optional[:class:`str`]
        The description of the tier.
    cost: :class:`int`
        The cost of the tier in USD cents per month.
    created_at: :class:`datetime.datetime`
        When the tier was created.
    """

    __slots__: Tuple[str, ...] = (
        '_state',
        'type',
        'server_id',
        'description',
        'role_id',
        'cost',
        'created_at',
    )

    def __init__(self, *, state, data: ServerSubscriptionTierPayload):
        self._state = state
        self.type = try_enum(ServerSubscriptionTierType, data['type'])
        self.server_id = data.get('serverId')
        self.role_id = data.get('roleId')
        self.description = data.get('description')
        self.cost = data['cost']
        self.created_at = ISO8601(data.get('createdAt'))

    def __eq__(self, other: ServerSubscriptionTier) -> bool:
        return isinstance(other, ServerSubscriptionTier) and self.type == other.type and self.server_id == other.server_id

    @property
    def server(self) -> Optional[Server]:
        """Optional[:class:`.Server`]: The server that the subscription tier is in."""
        return self._state._get_server(self.server_id)

    @property
    def role(self) -> Optional[Role]:
        """Optional[:class:`.Role`]: The role that the subscription tier is linked to."""
        if self.role_id:
            return self._state._get_server_role(self.server_id, self.role_id)
