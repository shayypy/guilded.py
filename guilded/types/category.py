
from typing import NotRequired, TypedDict


class Category(TypedDict):
    id: int
    serverId: str
    groupId: str
    createdAt: str
    updatedAt: NotRequired[str]
    name: str
