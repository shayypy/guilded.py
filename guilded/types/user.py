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
from typing import Any, Dict, List, Literal, Optional, TypedDict, Union
from typing_extensions import NotRequired


class UserStatus(TypedDict):
    content: NotRequired[str]
    emoteId: int


class UserSummary(TypedDict):
    id: str
    type: NotRequired[Literal['user', 'bot']]
    name: str
    avatar: NotRequired[Optional[str]]


class User(UserSummary):
    botId: NotRequired[str]
    createdBy: NotRequired[str]
    profilePicture: NotRequired[str]
    profilePictureSm: NotRequired[str]
    profilePictureLg: NotRequired[str]
    profilePictureBlur: NotRequired[str]
    banner: NotRequired[str]
    profileBannerSm: NotRequired[str]
    profileBannerLg: NotRequired[str]
    profileBannerBlur: NotRequired[str]
    createdAt: str
    subdomain: NotRequired[Optional[str]]
    email: NotRequired[Optional[str]]
    serviceEmail: NotRequired[Optional[str]]
    joinDate: NotRequired[str]
    robloxId: NotRequired[Optional[str]]
    lastOnline: NotRequired[str]
    steamId: NotRequired[str]
    stonks: NotRequired[int]
    badges: NotRequired[List[str]]
    flairInfos: NotRequired[Dict[str, Any]]
    teams: NotRequired[Union[Literal[False], List[Dict[str, Any]]]]
    status: NotRequired[UserStatus]


class ServerMemberSummary(TypedDict):
    user: UserSummary
    roleIds: List[int]


class ServerMember(ServerMemberSummary):
    user: User
    nickname: NotRequired[str]
    joinedAt: str
    isOwner: NotRequired[bool]


class ServerMemberBan(TypedDict):
    user: UserSummary
    reason: Optional[str]
    createdBy: str
    createdAt: str
