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

import types
from collections import namedtuple
from typing import Any, ClassVar, Dict, List, TYPE_CHECKING, Type, TypeVar


__all__ = (
    'ChannelType',
    'MessageType',
    'FileType',
    'MediaType',
    'FlowActionType',
    'FlowTriggerType',
    'ServerType',
    'UserType',
)


def _create_value_cls(name, comparable):
    cls = namedtuple('_EnumValue_' + name, 'name value')
    cls.__repr__ = lambda self: f'<{name}.{self.name}: {self.value!r}>'
    cls.__str__ = lambda self: f'{name}.{self.name}'
    if comparable:
        cls.__le__ = lambda self, other: isinstance(other, self.__class__) and self.value <= other.value
        cls.__ge__ = lambda self, other: isinstance(other, self.__class__) and self.value >= other.value
        cls.__lt__ = lambda self, other: isinstance(other, self.__class__) and self.value < other.value
        cls.__gt__ = lambda self, other: isinstance(other, self.__class__) and self.value > other.value
    return cls


def _is_descriptor(obj):
    return hasattr(obj, '__get__') or hasattr(obj, '__set__') or hasattr(obj, '__delete__')


class EnumMeta(type):
    if TYPE_CHECKING:
        __name__: ClassVar[str]
        _enum_member_names_: ClassVar[List[str]]
        _enum_member_map_: ClassVar[Dict[str, Any]]
        _enum_value_map_: ClassVar[Dict[Any, Any]]

    def __new__(cls, name, bases, attrs, *, comparable: bool = False):
        value_mapping = {}
        member_mapping = {}
        member_names = []

        value_cls = _create_value_cls(name, comparable)
        for key, value in list(attrs.items()):
            is_descriptor = _is_descriptor(value)
            if key[0] == '_' and not is_descriptor:
                continue

            # Special case classmethod to just pass through
            if isinstance(value, classmethod):
                continue

            if is_descriptor:
                setattr(value_cls, key, value)
                del attrs[key]
                continue

            try:
                new_value = value_mapping[value]
            except KeyError:
                new_value = value_cls(name=key, value=value)
                value_mapping[value] = new_value
                member_names.append(key)

            member_mapping[key] = new_value
            attrs[key] = new_value

        attrs['_enum_value_map_'] = value_mapping
        attrs['_enum_member_map_'] = member_mapping
        attrs['_enum_member_names_'] = member_names
        attrs['_enum_value_cls_'] = value_cls
        actual_cls = super().__new__(cls, name, bases, attrs)
        value_cls._actual_enum_cls_ = actual_cls  # type: ignore
        return actual_cls

    def __iter__(cls):
        return (cls._enum_member_map_[name] for name in cls._enum_member_names_)

    def __reversed__(cls):
        return (cls._enum_member_map_[name] for name in reversed(cls._enum_member_names_))

    def __len__(cls):
        return len(cls._enum_member_names_)

    def __repr__(cls):
        return f'<enum {cls.__name__}>'

    @property
    def __members__(cls):
        return types.MappingProxyType(cls._enum_member_map_)

    def __call__(cls, value):
        try:
            return cls._enum_value_map_[value]
        except (KeyError, TypeError):
            raise ValueError(f"{value!r} is not a valid {cls.__name__}")

    def __getitem__(cls, key):
        return cls._enum_member_map_[key]

    def __setattr__(cls, name, value):
        raise TypeError('Enums are immutable.')

    def __delattr__(cls, attr):
        raise TypeError('Enums are immutable')

    def __instancecheck__(self, instance):
        # isinstance(x, Y)
        # -> __instancecheck__(Y, x)
        try:
            return instance._actual_enum_cls_ is self
        except AttributeError:
            return False


if TYPE_CHECKING:
    from enum import Enum
else:

    class Enum(metaclass=EnumMeta):
        @classmethod
        def try_value(cls, value):
            try:
                return cls._enum_value_map_[value]
            except (KeyError, TypeError):
                return value


class ChannelType(Enum):
    announcements = 'announcements'
    calendar = 'calendar'
    chat = 'chat'
    docs = 'docs'
    dm = 'DM'
    forums = 'forums'
    media = 'media'
    list = 'list'
    scheduling = 'scheduling'
    stream = 'stream'
    thread = 'temporal'
    voice = 'voice'

    # aliases
    announcement = 'announcements'
    doc = 'docs'
    forum = 'forums'
    streaming = 'stream'

    # discord.py
    text = 'chat'
    news = 'announcements'

    def __str__(self):
        return self.value


class MessageType(Enum):
    default = 'default'
    system = 'system'

    def __str__(self):
        return self.name


class MediaType(Enum):
    """Represents a file/attachment's media type in Guilded."""
    content_media = 'ContentMedia'
    content_media_generic_files = 'ContentMediaGenericFiles'
    webhook_media = 'WebhookPrimaryMedia'
    custom_reaction = 'CustomReaction'
    user_avatar = 'UserAvatar'
    user_banner = 'UserBanner'
    team_avatar = 'TeamAvatar'
    team_banner = 'TeamBanner'
    group_icon = 'GroupAvatar'
    group_avatar = 'GroupAvatar'
    group_banner = 'GroupBanner'
    embed_image = 'ExternalOGEmbedImage'
    media_channel_upload = 'MediaChannelUpload'

    # Aliases
    attachment = 'ContentMedia'
    emote = 'CustomReaction'
    emoji = 'CustomReaction'
    avatar = 'UserAvatar'
    profile_avatar = 'UserAvatar'
    banner = 'UserBanner'
    profile_banner = 'UserBanner'
    team_icon = 'TeamAvatar'

    def __str__(self):
        return self.value


class FileType(Enum):
    """Represents a type of file in Guilded. In the case of uploading
    files, this usually does not have to be set manually, but if the
    library fails to detect the type of file from its extension, you
    can pass this into :class:`File`\'s ``file_type`` keyword argument."""
    image = 'image'
    video = 'video'
    file = 'fileUpload'

    def __str__(self):
        return self.value


class FlowTriggerType(Enum):
    server_updated = 'TeamAuditLogTeamUpdated'
    member_muted = 'TeamAuditLogMemberMuted'
    member_sent_message_to_channel = 'BotTriggerSendMessageToTeamChannel'
    member_joined = 'BotTriggerMemberJoined'
    application_received = 'TeamAuditLogApplicationReceived'
    toggle_list_item = 'BotTriggerChangeListItemState'
    event_created = 'BotTriggerCalendarEventCreated'
    event_updated = 'BotTriggerCalendarEventUpdated'
    event_removed = 'BotTriggerCalendarEventDeleted'
    forum_topic_created = 'BotTriggerForumTopicCreated'
    forum_topic_updated = 'BotTriggerForumTopicUpdated'
    forum_topic_deleted = 'BotTriggerForumTopicDeleted'
    list_item_created = 'BotTriggerListItemCreated'
    list_item_updated = 'BotTriggerListItemUpdated'
    list_item_deleted = 'BotTriggerListItemDeleted'
    doc_created = 'BotTriggerDocCreated'
    doc_updated = 'BotTriggerDocUpdated'
    doc_deleted = 'BotTriggerDocDeleted'
    media_created = 'BotTriggerMediaCreated'
    media_updated = 'BotTriggerMediaUpdated'
    media_deleted = 'BotTriggerMediaDeleted'
    announcement_created = 'BotTriggerAnnouncementCreated'
    announcement_updated = 'BotTriggerAnnouncementUpdated'
    announcement_deleted = 'BotTriggerAnnouncementDeleted'
    voice_group_joined = 'BotTriggerVoiceChannelGroupJoined'
    voice_group_left = 'BotTriggerVoiceChannelGroupLeft'
    twitch_stream_online = 'BotTriggerTwitchStreamOnline'
    twitch_stream_offline = 'BotTriggerTwitchStreamOffline'
    twitch_stream_subscribed = 'BotTriggerTwitchStreamSubscribed'
    twitch_stream_followed = 'BotTriggerTwitchStreamFollowed'
    twitch_stream_unfollowed = 'BotTriggerTwitchStreamUnfollowed'
    twitch_stream_unsubscribed = 'BotTriggerTwitchStreamUnsubscribed'
    patreon_tiered_membership_created = 'BotTriggerPatreonTieredMembershipCreated'
    patreon_tiered_membership_updated = 'BotTriggerPatreonTieredMembershipUpdated'
    patreon_tiered_membership_cancelled = 'BotTriggerPatreonTieredMembershipRemoved'
    subscription_created = 'TeamAuditLogServerSubscriptionsSubscriptionCreated'
    subscription_updated = 'BotTriggerServerSubscriptionsSubscriptionUpdated'
    subscription_canceled = 'TeamAuditLogServerSubscriptionsSubscriptionCanceled'
    scheduling_availability_started = 'BotTriggerSchedulingAvailabilityDurationStarted'
    scheduling_availability_ended = 'BotTriggerSchedulingAvailabilityDurationEnded'
    youtube_video_published = 'BotTriggerYoutubeVideoPublished'


class FlowActionType(Enum):
    send_a_custom_message = 'SendMessageToTeamChannel'
    assign_role = 'AssignRoleToMember'
    add_xp_to_member = 'AddTeamXpToMember'
    edit_group_membership = 'EditGroupMembership'
    create_a_forum_topic = 'CreateForumThread'
    create_a_list_item = 'CreateListItem'
    remove_role = 'RemoveRoleFromMember'
    delete_a_message = 'DeleteChannelMessage'
    create_a_doc = 'CreateDoc'


class ServerType(Enum):
    team = 'team'
    organization = 'organization'
    community = 'community'
    clan = 'clan'
    guild = 'guild'
    friends = 'friends'
    streaming = 'streaming'
    other = 'other'


class UserType(Enum):
    user = 'user'
    bot = 'bot'


T = TypeVar('T')


def create_unknown_value(cls: Type[T], val: Any) -> T:
    value_cls = cls._enum_value_cls_  # type: ignore
    name = f'unknown_{val}'
    return value_cls(name=name, value=val)


def try_enum(cls: Type[T], val: Any) -> T:
    """A function that tries to turn the value into enum ``cls``.
    If it fails it returns a proxy invalid value instead.
    """
    try:
        return cls._enum_value_map_[val]  # type: ignore
    except (KeyError, TypeError, AttributeError):
        return create_unknown_value(cls, val)
