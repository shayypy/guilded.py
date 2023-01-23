from typing import NotRequired, Optional, TypedDict


class ContentComment(TypedDict):
    id: int
    content: str
    createdAt: str
    updatedAt: NotRequired[Optional[str]]
    channelId: str
    createdBy: str
