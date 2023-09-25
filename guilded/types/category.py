
from typing import Dict, NotRequired, TypedDict


class Category(TypedDict):
    id: int
    serverId: str
    groupId: str
    createdAt: str
    updatedAt: NotRequired[str]
    name: str


class ChannelCategoryRolePermission(TypedDict):
    permissions: Dict[str, bool]
    createdAt: str
    updatedAt: NotRequired[str]
    roleId: int
    categoryId: int


class ChannelCategoryUserPermission(TypedDict):
    permissions: Dict[str, bool]
    createdAt: str
    updatedAt: NotRequired[str]
    userId: str
    categoryId: int
