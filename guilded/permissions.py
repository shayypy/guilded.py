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

from __future__ import annotations
from typing import TYPE_CHECKING, ClassVar, Dict, Iterator, Optional, Set, Tuple

if TYPE_CHECKING:
    from typing_extensions import Self

__all__ = (
    'Permissions',
    'PermissionOverride',
    'PermissionOverwrite',
)


class Permissions:
    """Wraps up permission values in Guilded.

    An instance of this class is constructed by providing a
    list of :gdocs:`permission values <Permissions>`: ::

        # A `Permissions` instance representing the ability
        # to read and send messages.
        guilded.Permissions('CanReadChats', 'CanCreateChats')


    .. container:: operations

        .. describe:: x == y

            Checks if two permissions are equal.

        .. describe:: x != y

            Checks if two permissions are not equal.

    Attributes
    -----------
    values: List[:class:`str`]
        The raw array of permission values.
        This list is not guaranteed to be in any particular order.
        You should use the properties available on this class instead of this
        attribute.
    """

    def __init__(self, *values: str):
        self.values = list(values)

    def __eq__(self, other) -> bool:
        return isinstance(other, Permissions) and set(self.values) == set(other.values)

    def __repr__(self) -> str:
        return f'<Permissions values={len(self.values)}>'

    @classmethod
    def all(cls):
        """A factory method that creates a :class:`Permissions` with all
        permissions set to ``True``."""
        values = []
        for category_values in VALUES_BY_CATEGORY.values():
            values += category_values

        return cls(*values)

    @classmethod
    def none(cls):
        """A factory method that creates a :class:`Permissions` with all
        permissions set to ``False``."""
        return cls()

    @classmethod
    def general(cls):
        """A factory method that creates a :class:`Permissions` with all
        "General" permissions set to ``True``."""
        return cls(*VALUES_BY_CATEGORY['general'])

    @classmethod
    def recruitment(cls):
        """A factory method that creates a :class:`Permissions` with all
        "Recruitment" permissions set to ``True``."""
        return cls(*VALUES_BY_CATEGORY['recruitment'])

    @classmethod
    def announcements(cls):
        """A factory method that creates a :class:`Permissions` with all
        "Announcement" permissions set to ``True``."""
        return cls(*VALUES_BY_CATEGORY['announcements'])

    @classmethod
    def chat(cls):
        """A factory method that creates a :class:`Permissions` with all
        "Chat" permissions set to ``True``."""
        return cls(*VALUES_BY_CATEGORY['chat'])

    @classmethod
    def calendar(cls):
        """A factory method that creates a :class:`Permissions` with all
        "Calendar" permissions set to ``True``."""
        return cls(*VALUES_BY_CATEGORY['calendar'])

    @classmethod
    def forums(cls):
        """A factory method that creates a :class:`Permissions` with all
        "Forum" permissions set to ``True``."""
        return cls(*VALUES_BY_CATEGORY['forums'])

    @classmethod
    def docs(cls):
        """A factory method that creates a :class:`Permissions` with all
        "Docs" permissions set to ``True``."""
        return cls(*VALUES_BY_CATEGORY['docs'])

    @classmethod
    def media(cls):
        """A factory method that creates a :class:`Permissions` with all
        "Media" permissions set to ``True``."""
        return cls(*VALUES_BY_CATEGORY['media'])

    @classmethod
    def voice(cls):
        """A factory method that creates a :class:`Permissions` with all
        "Voice" permissions set to ``True``."""
        return cls(*VALUES_BY_CATEGORY['voice'])

    @classmethod
    def competitive(cls):
        """A factory method that creates a :class:`Permissions` with all
        "Competitive" permissions set to ``True``."""
        return cls(*VALUES_BY_CATEGORY['competitive'])

    @classmethod
    def customization(cls):
        """A factory method that creates a :class:`Permissions` with all
        "Customization" permissions set to ``True``."""
        return cls(*VALUES_BY_CATEGORY['customization'])

    customisation = customization

    @classmethod
    def forms(cls):
        """A factory method that creates a :class:`Permissions` with all
        "Forms" permissions set to ``True``."""
        return cls(*VALUES_BY_CATEGORY['forms'])

    @classmethod
    def lists(cls):
        """A factory method that creates a :class:`Permissions` with all
        "List" permissions set to ``True``."""
        return cls(*VALUES_BY_CATEGORY['lists'])

    @classmethod
    def brackets(cls):
        """A factory method that creates a :class:`Permissions` with all
        "Bracket" permissions set to ``True``."""
        return cls(*VALUES_BY_CATEGORY['brackets'])

    @classmethod
    def scheduling(cls):
        """A factory method that creates a :class:`Permissions` with all
        "Scheduling" permissions set to ``True``."""
        return cls(*VALUES_BY_CATEGORY['scheduling'])

    @classmethod
    def bots(cls):
        """A factory method that creates a :class:`Permissions` with all
        "Bot" permissions set to ``True``."""
        return cls(*VALUES_BY_CATEGORY['bots'])

    @classmethod
    def xp(cls):
        """A factory method that creates a :class:`Permissions` with all
        "XP" permissions set to ``True``."""
        return cls(*VALUES_BY_CATEGORY['xp'])

    @classmethod
    def streams(cls):
        """A factory method that creates a :class:`Permissions` with all
        "Stream" permissions set to ``True``."""
        return cls(*VALUES_BY_CATEGORY['streams'])

    @classmethod
    def socket_events(cls):
        """A factory method that creates a :class:`Permissions` with all
        "Socket event" permissions set to ``True``."""
        return cls(*VALUES_BY_CATEGORY['socket_events'])

    @property
    def administrator(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user has every permission.

        This is a pseudo-permission, i.e., there is no real "administrator"
        permission, and thus this property being ``True`` does not necessarily
        mean that a user will have all the same abilities as a Discord user
        with the administrator permission.
        """
        return self == Permissions.all()

    @property
    def update_server(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can update the server's
        settings."""
        return 'CanUpdateServer' in self.values

    @property
    def manage_server(self) -> bool:
        """:class:`bool`: This is an alias of :attr:`.update_server`."""
        return self.update_server

    @property
    def manage_guild(self) -> bool:
        """:class:`bool`: This is an alias of :attr:`.update_server`."""
        return self.update_server

    @property
    def manage_roles(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can update the server's
        roles."""
        return 'CanManageRoles' in self.values

    @property
    def invite_members(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can directly invite
        members to the server."""
        return 'CanInviteMembers' in self.values

    @property
    def create_instant_invite(self) -> bool:
        """:class:`bool`: This is an alias of :attr:`.invite_members`."""
        return self.invite_members

    @property
    def kick_members(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can kick *or ban* members
        from the server."""
        return 'CanKickMembers' in self.values

    @property
    def ban_members(self) -> bool:
        """:class:`bool`: This is an alias of :attr:`.kick_members`."""
        return self.kick_members

    @property
    def manage_groups(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can create, edit, or
        delete groups."""
        return 'CanManageGroups' in self.values

    @property
    def manage_channels(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can create, edit, or
        delete channels."""
        return 'CanManageChannels' in self.values

    @property
    def manage_webhooks(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can create, edit, or
        delete webhooks."""
        return 'CanManageWebhooks' in self.values

    @property
    def mention_everyone(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can use ``@everyone`` and
        ``@here`` mentions."""
        return 'CanMentionEveryone' in self.values

    @property
    def moderator_view(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can access "moderator
        view" to see private replies."""
        return 'CanModerateChannels' in self.values

    @property
    def slowmode_exempt(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user is exempt from slowmode
        restrictions."""
        return 'CanBypassSlowMode' in self.values

    @property
    def read_applications(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can view server and game
        applications."""
        return 'CanReadApplications' in self.values

    @property
    def approve_applications(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can approve server and
        game applications."""
        return 'CanApproveApplications' in self.values

    @property
    def edit_application_form(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can edit server and game
        applications, and toggle accepting applications."""
        return 'CanEditApplicationForm' in self.values

    @property
    def indicate_lfm_interest(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can indicate interest in
        a player instead of an upvote."""
        return 'CanIndicateLfmInterest' in self.values

    @property
    def modify_lfm_status(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can modify the "Find
        Player" status for the server listing card."""
        return 'CanModifyLfmStatus' in self.values

    @property
    def read_announcements(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can view announcements."""
        return 'CanReadAnnouncements' in self.values

    @property
    def create_announcements(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can create and delete
        announcements."""
        return 'CanCreateAnnouncements' in self.values

    @property
    def manage_announcements(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can delete announcements
        by other members or pin any announcement."""
        return 'CanManageAnnouncements' in self.values

    @property
    def read_messages(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can read chat messages."""
        return 'CanReadChats' in self.values

    @property
    def view_channel(self) -> bool:
        """:class:`bool`: This is an alias of :attr:`.read_messages`."""
        return self.read_messages

    @property
    def send_messages(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can send chat messages."""
        return 'CanCreateChats' in self.values

    @property
    def upload_media(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can upload images and
        videos to chat messages."""
        return 'CanUploadChatMedia' in self.values

    @property
    def create_threads(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can create threads."""
        return 'CanCreateThreads' in self.values

    @property
    def create_public_threads(self) -> bool:
        """:class:`bool`: This is an alias of :attr:`.create_threads`."""
        return self.create_threads

    @property
    def create_private_threads(self) -> bool:
        """:class:`bool`: This is an alias of :attr:`.create_threads`."""
        return self.create_threads

    @property
    def send_messages_in_threads(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can reply to threads."""
        return 'CanCreateThreadMessages' in self.values or 'CanReplyToChatThreads' in self.values

    @property
    def send_private_replies(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can privately reply to
        messages."""
        return 'CanCreatePrivateMessages' in self.values

    @property
    def manage_messages(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can delete messages by
        other members or pin any message."""
        return 'CanManageChats' in self.values

    @property
    def manage_threads(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can archive and restore
        threads."""
        return 'CanManageThreads' in self.values

    @property
    def create_chat_forms(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can create forms."""
        return 'CanCreateChatForms' in self.values

    @property
    def view_events(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can view calendar
        events."""
        return 'CanReadEvents' in self.values

    @property
    def create_events(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can create calendar
        events."""
        return 'CanCreateEvents' in self.values

    @property
    def manage_events(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can update calendar
        events created by other members and move them to other channels."""
        return 'CanEditEvents' in self.values

    @property
    def remove_events(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can remove calendar
        events created by other members."""
        return 'CanDeleteEvents' in self.values

    @property
    def edit_rsvps(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can edit the RSVP status
        for members in a calendar event."""
        return 'CanEditEventRsvps' in self.values

    @property
    def read_forums(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can read forums."""
        return 'CanReadForums' in self.values

    @property
    def create_topics(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can create forum
        topics."""
        return 'CanCreateTopics' in self.values

    @property
    def create_topic_replies(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can create forum topic
        replies."""
        return 'CanCreateTopicReplies' in self.values

    @property
    def manage_topics(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can remove forum topics
        and replies created by other members, or move them to other
        channels."""
        return 'CanDeleteTopics' in self.values

    @property
    def sticky_topics(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can sticky forum topics."""
        return 'CanStickyTopics' in self.values

    @property
    def lock_topics(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can lock forum topics."""
        return 'CanLockTopics' in self.values

    @property
    def view_docs(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can view docs."""
        return 'CanReadDocs' in self.values

    @property
    def read_docs(self) -> bool:
        """:class:`bool`: This is an alias of :attr:`.view_docs`."""
        return self.view_docs

    @property
    def create_docs(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can create docs."""
        return 'CanCreateDocs' in self.values

    @property
    def manage_docs(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can update docs created
        by other members and move them to other channels."""
        return 'CanEditDocs' in self.values

    @property
    def remove_docs(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can remove docs created
        by other members."""
        return 'CanDeleteDocs' in self.values

    @property
    def see_media(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can see media."""
        return 'CanReadMedia' in self.values

    @property
    def read_media(self) -> bool:
        """:class:`bool`: This is an alias of :attr:`.see_media`."""
        return self.see_media

    @property
    def create_media(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can create media."""
        return 'CanAddMedia' in self.values

    @property
    def manage_media(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can update media created
        by other members and move them to other channels."""
        return 'CanEditMedia' in self.values

    @property
    def remove_media(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can remove media created
        by other members."""
        return 'CanRemoveMedia' in self.values

    @property
    def hear_voice(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can listen to voice
        chat."""
        return 'CanListenVoice' in self.values

    @property
    def add_voice(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can talk in voice chat."""
        return 'CanAddVoice' in self.values

    @property
    def speak(self) -> bool:
        """:class:`bool`: This is an alias of :attr:`.add_voice`."""
        return self.add_voice

    @property
    def manage_voice_rooms(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can create, rename, and
        delete voice rooms."""
        return 'CanManageVoiceGroups' in self.values

    @property
    def move_members(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can move members to other
        voice rooms."""
        return 'CanAssignVoiceGroup' in self.values

    @property
    def disconnect_members(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can disconnect members
        from voice or stream rooms."""
        return 'CanDisconnectUsers' in self.values

    @property
    def broadcast(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can broadcast their voice
        to voice rooms lower in the hierarchy when speaking in voice chat."""
        return 'CanBroadcastVoice' in self.values

    @property
    def whisper(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can direct their voice to
        specific members."""
        return 'CanDirectVoice' in self.values

    @property
    def priority_speaker(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can prioritize their
        voice when speaking in voice chat."""
        return 'CanPrioritizeVoice' in self.values

    @property
    def use_voice_activity(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can use the voice
        activity input mode for voice chats."""
        return 'CanUseVoiceActivity' in self.values

    @property
    def use_voice_activation(self) -> bool:
        """:class:`bool`: This is an alias of :attr:`.use_voice_activity`."""
        return self.use_voice_activity

    @property
    def mute_members(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can mute members in voice
        chat."""
        return 'CanMuteMembers' in self.values

    @property
    def deafen_members(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can deafen members in
        voice chat."""
        return 'CanDeafenMembers' in self.values

    @property
    def send_voice_messages(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can send chat messages to
        voice channels."""
        return 'CanSendVoiceMessages' in self.values

    @property
    def create_scrims(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can create matchmaking
        scrims."""
        return 'CanCreateScrims' in self.values

    @property
    def create_tournaments(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can create and manage
        tournaments."""
        return 'CanManageTournaments' in self.values

    @property
    def manage_tournaments(self) -> bool:
        """:class:`bool`: This is an alias of :attr:`.create_tournaments`."""
        return self.create_tournaments

    @property
    def register_for_tournaments(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can register the server
        for tournaments."""
        return 'CanRegisterForTournaments' in self.values

    @property
    def manage_emojis(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can create and manage
        server emojis."""
        return 'CanManageEmotes' in self.values

    @property
    def manage_emotes(self) -> bool:
        """:class:`bool`: This is an alias of :attr:`.manage_emojis`"""
        return self.manage_emojis

    @property
    def change_nickname(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can change their own
        nickname."""
        return 'CanChangeNickname' in self.values

    @property
    def manage_nicknames(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can change the nicknames
        of other members."""
        return 'CanManageNicknames' in self.values

    @property
    def view_form_responses(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can view all form
        responses."""
        return 'CanViewFormResponses' in self.values

    @property
    def view_poll_responses(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can view all poll
        results."""
        return 'CanViewPollResponses' in self.values

    @property
    def view_poll_results(self) -> bool:
        """:class:`bool`: This is an alias of :attr:`.view_poll_responses`."""
        return self.view_poll_responses

    @property
    def view_list_items(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can view list items."""
        return 'CanReadListItems' in self.values

    @property
    def read_list_items(self) -> bool:
        """:class:`bool`: This is an alias of :attr:`.view_list_items`."""
        return self.view_list_items

    @property
    def create_list_items(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can create list items."""
        return 'CanCreateListItems' in self.values

    @property
    def manage_list_items(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can update list items
        created by other members and move them to other channels."""
        return 'CanUpdateListItems' in self.values

    @property
    def remove_list_items(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can remove list items
        created by other members."""
        return 'CanDeleteListItems' in self.values

    @property
    def complete_list_items(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can complete list items
        created by other members."""
        return 'CanCompleteListItems' in self.values

    @property
    def reorder_list_items(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can reorder list items."""
        return 'CanReorderListItems' in self.values

    @property
    def view_brackets(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can view tournament
        brackets."""
        return 'CanViewBracket' in self.values

    @property
    def read_brackets(self) -> bool:
        """:class:`bool`: This is an alias of :attr:`.view_brackets`."""
        return self.view_brackets

    @property
    def report_scores(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can report match scores
        on behalf of the server."""
        return 'CanReportScores' in self.values

    @property
    def view_schedules(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can view members'
        schedules."""
        return 'CanReadSchedules' in self.values

    @property
    def read_schedules(self) -> bool:
        """:class:`bool`: This is an alias of :attr:`.view_schedules`."""
        return self.view_schedules

    @property
    def create_schedules(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can let the server know
        their available schedule."""
        return 'CanCreateSchedule' in self.values

    @property
    def remove_schedules(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can remove availabilities
        created by other members."""
        return 'CanDeleteSchedule' in self.values

    @property
    def manage_bots(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can create and edit
        flowbots."""
        return 'CanManageBots' in self.values

    @property
    def manage_server_xp(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can manage XP for
        members."""
        return 'CanManageServerXp' in self.values

    @property
    def view_streams(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can view streams."""
        return 'CanReadStreams' in self.values

    @property
    def join_stream_voice(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can listen in stream
        channels."""
        return 'CanJoinStreamVoice' in self.values

    @property
    def add_stream(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can stream as well as
        speak in stream channels."""
        return 'CanCreateStreams' in self.values

    @property
    def stream(self) -> bool:
        """:class:`bool`: This is an alias of :attr:`.add_stream`."""
        return self.add_stream

    @property
    def send_stream_messages(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can send messages in
        stream channels."""
        return 'CanSendStreamMessages' in self.values

    @property
    def add_stream_voice(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can speak in stream
        channels."""
        return 'CanAddStreamVoice' in self.values

    @property
    def use_stream_voice_activity(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can use voice activity in
        stream channels."""
        return 'CanUseVoiceActivityInStream' in self.values

    @property
    def receive_all_events(self) -> bool:
        """:class:`bool`: Returns ``True`` if a bot can receive all server
        socket events instead of only those that match its prefix."""
        return 'CanReceiveAllSocketEvents' in self.values


VALUES_BY_CATEGORY = {
    'general': [
        'CanUpdateServer',
        'CanManageRoles',
        'CanInviteMembers',
        'CanKickMembers',
        'CanManageGroups',
        'CanManageChannels',
        'CanManageWebhooks',
        'CanMentionEveryone',
        'CanModerateChannels',
        'CanBypassSlowMode',
    ],
    'recruitment': [
        'CanReadApplications',
        'CanApproveApplications',
        'CanEditApplicationForm',
        'CanIndicateLfmInterest',
        'CanModifyLfmStatus',
    ],
    'announcements': [
        'CanReadAnnouncements',
        'CanCreateAnnouncements',
        'CanManageAnnouncements',
    ],
    'chat': [
        'CanReadChats',
        'CanCreateChats',
        'CanUploadChatMedia',
        'CanCreateThreads',
        'CanCreateThreadMessages',
        'CanCreatePrivateMessages',
        'CanManageChats',
        'CanManageThreads',
        'CanCreateChatForms',
        'CanReplyToChatThreads',
    ],
    'calendar': [
        'CanReadEvents',
        'CanCreateEvents',
        'CanEditEvents',
        'CanDeleteEvents',
        'CanEditEventRsvps',
    ],
    'forums': [
        'CanReadForums',
        'CanCreateTopics',
        'CanCreateTopicReplies',
        'CanDeleteTopics',
        'CanStickyTopics',
        'CanLockTopics',
    ],
    'docs': [
        'CanReadDocs',
        'CanCreateDocs',
        'CanEditDocs',
        'CanDeleteDocs',
    ],
    'media': [
        'CanReadMedia',
        'CanAddMedia',
        'CanEditMedia',
        'CanDeleteMedia',
    ],
    'voice': [
        'CanListenVoice',
        'CanAddVoice',
        'CanManageVoiceGroups',
        'CanAssignVoiceGroup',
        'CanDisconnectUsers',
        'CanBroadcastVoice',
        'CanDirectVoice',
        'CanPrioritizeVoice',
        'CanUseVoiceActivity',
        'CanMuteMembers',
        'CanDeafenMembers',
        'CanSendVoiceMessages',
    ],
    'competitive': [
        'CanCreateScrims',
        'CanManageTournaments',
        'CanRegisterForTournaments',
    ],
    'customization': [
        'CanManageEmotes',
        'CanChangeNickname',
        'CanManageNicknames',
    ],
    'form': [
        'CanViewFormResponses',
        'CanViewPollResponses',
    ],
    'lists': [
        'CanReadListItems',
        'CanCreateListItems',
        'CanUpdateListItems',
        'CanDeleteListItems',
        'CanCompleteListItems',
        'CanReorderListItems',
    ],
    'brackets': [
        'CanViewBracket',
        'CanReportScores',
    ],
    'scheduling': [
        'CanReadSchedules',
        'CanCreateSchedule',
        'CanDeleteSchedule',
    ],
    'bots': [
        'CanManageBots',
    ],
    'xp': [
        'CanManageServerXp',
    ],
    'streams': [
        'CanReadStreams',
        'CanJoinStreamVoice',
        'CanCreateStreams',
        'CanSendStreamMessages',
        'CanAddStreamVoice',
        'CanUseVoiceActivityInStream',
    ],
    'socket_events': [
        'CanReceiveAllSocketEvents',
    ],
}

# Terrible
VALID_NAME_MAP = {
    'update_server': 'CanUpdateServer',
    'manage_server': 'CanUpdateServer',
    'manage_guild': 'CanUpdateServer',
    'manage_roles': 'CanManageRoles',
    'invite_members': 'CanInviteMembers',
    'create_instant_invite': 'CanInviteMembers',
    'kick_members': 'CanKickMembers',
    'ban_members': 'CanKickMembers',
    'manage_groups': 'CanManageGroups',
    'manage_channels': 'CanManageChannels',
    'manage_webhooks': 'CanManageWebhooks',
    'mention_everyone': 'CanMentionEveryone',
    'moderator_view': 'CanModerateChannels',
    'slowmode_exempt': 'CanBypassSlowMode',
    'read_applications': 'CanReadApplications',
    'approve_applications': 'CanApproveApplications',
    'edit_application_form': 'CanEditApplicationForm',
    'indicate_lfm_interest': 'CanIndicateLfmInterest',
    'modify_lfm_status': 'CanModifyLfmStatus',
    'read_announcements': 'CanReadAnnouncements',
    'create_announcements': 'CanCreateAnnouncements',
    'manage_announcements': 'CanManageAnnouncements',
    'read_messages': 'CanReadChats',
    'view_channel': 'CanReadChats',
    'send_messages': 'CanCreateChats',
    'upload_media': 'CanUploadChatMedia',
    'create_threads': 'CanCreateThreads',
    'create_public_threads': 'CanCreateThreads',
    'create_private_threads': 'CanCreateThreads',
    'send_messages_in_threads': 'CanCreateThreadMessages',
    # 'send_messages_in_threads': 'CanReplyToChatThreads',
    'send_private_replies': 'CanCreatePrivateMessages',
    'manage_messages': 'CanManageChats',
    'manage_threads': 'CanManageThreads',
    'create_chat_forms': 'CanCreateChatForms',
    'view_events': 'CanReadEvents',
    'create_events': 'CanCreateEvents',
    'manage_events': 'CanEditEvents',
    'remove_events': 'CanDeleteEvents',
    'edit_rsvps': 'CanEditEventRsvps',
    'read_forums': 'CanReadForums',
    'create_topics': 'CanCreateTopics',
    'create_topic_replies': 'CanCreateTopicReplies',
    'manage_topics': 'CanDeleteTopics',
    'sticky_topics': 'CanStickyTopics',
    'lock_topics': 'CanLockTopics',
    'view_docs': 'CanReadDocs',
    'read_docs': 'CanReadDocs',
    'create_docs': 'CanCreateDocs',
    'manage_docs': 'CanEditDocs',
    'remove_docs': 'CanDeleteDocs',
    'see_media': 'CanReadMedia',
    'read_media': 'CanReadMedia',
    'create_media': 'CanAddMedia',
    'manage_media': 'CanEditMedia',
    'remove_media': 'CanDeleteMedia',
    'hear_voice': 'CanListenVoice',
    'add_voice': 'CanAddVoice',
    'speak': 'CanAddVoice',
    'manage_voice_rooms': 'CanManageVoiceGroups',
    'move_members': 'CanAssignVoiceGroup',
    'disconnect_members': 'CanDisconnectUsers',
    'broadcast': 'CanBroadcastVoice',
    'whisper': 'CanDirectVoice',
    'priority_speaker': 'CanPrioritizeVoice',
    'use_voice_activity': 'CanUseVoiceActivity',
    'use_voice_activation': 'CanUseVoiceActivity',
    'mute_members': 'CanMuteMembers',
    'deafen_members': 'CanDeafenMembers',
    'send_voice_messages': 'CanSendVoiceMessages',
    'create_scrims': 'CanCreateScrims',
    'create_tournaments': 'CanManageTournaments',
    'manage_tournaments': 'CanManageTournaments',
    'register_for_tournaments': 'CanRegisterForTournaments',
    'manage_emojis': 'CanManageEmotes',
    'manage_emotes': 'CanManageEmotes',
    'change_nickname': 'CanChangeNickname',
    'manage_nicknames': 'CanManageNicknames',
    'view_form_responses': 'CanViewFormResponses',
    'view_form_results': 'CanViewFormResponses',
    'view_poll_responses': 'CanViewPollResponses',
    'view_poll_results': 'CanViewPollResponses',
    'view_list_items': 'CanReadListItems',
    'read_list_items': 'CanReadListItems',
    'create_list_items': 'CanCreateListItems',
    'manage_list_items': 'CanUpdateListItems',
    'remove_list_items': 'CanDeleteListItems',
    'complete_list_items': 'CanCompleteListItems',
    'reorder_list_items': 'CanReorderListItems',
    'view_brackets': 'CanViewBracket',
    'read_brackets': 'CanViewBracket',
    'report_scores': 'CanReportScores',
    'view_schedules': 'CanReadSchedules',
    'read_schedules': 'CanReadSchedules',
    'create_schedules': 'CanCreateSchedule',
    'remove_schedules': 'CanDeleteSchedule',
    'manage_bots': 'CanManageBots',
    'manage_server_xp': 'CanManageServerXp',
    'view_streams': 'CanReadStreams',
    'join_stream_voice': 'CanJoinStreamVoice',
    'add_stream': 'CanCreateStreams',
    'stream': 'CanCreateStreams',
    'send_stream_messages': 'CanSendStreamMessages',
    'add_stream_voice': 'CanAddStreamVoice',
    'use_stream_voice_activity': 'CanUseVoiceActivityInStream',
    'receive_all_events': 'CanReceiveAllSocketEvents',
}

# Reverse the map but with no aliases
REVERSE_VALID_NAME_MAP: Dict[str, str] = {}
for key, value in VALID_NAME_MAP.items():
    if value in REVERSE_VALID_NAME_MAP:
        continue
    REVERSE_VALID_NAME_MAP[value] = key

def _augment_with_names(cls):
    cls.VALID_NAMES = set(VALID_NAME_MAP.keys())
    aliases = set()
    appearances: Dict[str, str] = {}

    # make descriptors for all the valid names and aliases
    for name, value in VALID_NAME_MAP.items():
        if value in appearances:
            key = appearances[value]
            aliases.add(name)
        else:
            key = name
            appearances[value] = name

        # god bless Python
        def getter(self, x=key):
            return self._values.get(x)

        def setter(self, value, x=key):
            self._set(x, value)

        prop = property(getter, setter)
        setattr(cls, name, prop)

    cls.PURE_FLAGS = cls.VALID_NAMES - aliases
    return cls


@_augment_with_names
class PermissionOverride:
    r"""Represents a role permission override

    Unlike a regular :class:`Permissions`\, the default value of a
    permission is equivalent to ``None`` and not ``False``. Setting
    a value to ``False`` is **explicitly** denying that permission,
    while setting a value to ``True`` is **explicitly** allowing
    that permission.

    The values supported by this are the same as :class:`Permissions`
    with the added possibility of it being set to ``None``.

    .. container:: operations

        .. describe:: x == y

            Checks if two overrides are equal.

        .. describe:: x != y

            Checks if two overrides are not equal.

        .. describe:: iter(x)

           Returns an iterator of ``(perm, value)`` pairs. This allows it
           to be, for example, constructed as a dict or a list of pairs.
           Note that aliases are not shown.

    Parameters
    -----------
    \*\*kwargs
        Set the value of permissions by their name.
    """

    __slots__: Tuple[str, ...] = ('_values',)

    if TYPE_CHECKING:
        VALID_NAMES: ClassVar[Set[str]]
        PURE_FLAGS: ClassVar[Set[str]]
        # I wish I didn't have to do this
        update_server: Optional[bool]
        manage_server: Optional[bool]
        manage_guild: Optional[bool]
        manage_roles: Optional[bool]
        invite_members: Optional[bool]
        create_instant_invite: Optional[bool]
        kick_members: Optional[bool]
        ban_members: Optional[bool]
        manage_groups: Optional[bool]
        manage_channels: Optional[bool]
        manage_webhooks: Optional[bool]
        mention_everyone: Optional[bool]
        moderator_view: Optional[bool]
        slowmode_exempt: Optional[bool]
        read_applications: Optional[bool]
        approve_applications: Optional[bool]
        edit_application_form: Optional[bool]
        indicate_lfm_interest: Optional[bool]
        modify_lfm_status: Optional[bool]
        read_announcements: Optional[bool]
        create_announcements: Optional[bool]
        manage_announcements: Optional[bool]
        read_messages: Optional[bool]
        view_channel: Optional[bool]
        send_messages: Optional[bool]
        upload_media: Optional[bool]
        create_threads: Optional[bool]
        create_public_threads: Optional[bool]
        create_private_threads: Optional[bool]
        send_messages_in_threads: Optional[bool]
        send_private_replies: Optional[bool]
        manage_messages: Optional[bool]
        manage_threads: Optional[bool]
        create_chat_forms: Optional[bool]
        view_events: Optional[bool]
        create_events: Optional[bool]
        manage_events: Optional[bool]
        remove_events: Optional[bool]
        edit_rsvps: Optional[bool]
        read_forums: Optional[bool]
        create_topics: Optional[bool]
        create_topic_replies: Optional[bool]
        manage_topics: Optional[bool]
        sticky_topics: Optional[bool]
        lock_topics: Optional[bool]
        view_docs: Optional[bool]
        read_docs: Optional[bool]
        create_docs: Optional[bool]
        manage_docs: Optional[bool]
        remove_docs: Optional[bool]
        see_media: Optional[bool]
        read_media: Optional[bool]
        create_media: Optional[bool]
        manage_media: Optional[bool]
        remove_media: Optional[bool]
        hear_voice: Optional[bool]
        add_voice: Optional[bool]
        speak: Optional[bool]
        manage_voice_rooms: Optional[bool]
        move_members: Optional[bool]
        broadcast: Optional[bool]
        whisper: Optional[bool]
        priority_speaker: Optional[bool]
        use_voice_activity: Optional[bool]
        use_voice_activation: Optional[bool]
        mute_members: Optional[bool]
        deafen_members: Optional[bool]
        send_voice_messages: Optional[bool]
        create_scrims: Optional[bool]
        create_tournaments: Optional[bool]
        manage_tournaments: Optional[bool]
        register_for_tournaments: Optional[bool]
        manage_emojis: Optional[bool]
        manage_emotes: Optional[bool]
        change_nickname: Optional[bool]
        manage_nicknames: Optional[bool]
        view_form_responses: Optional[bool]
        view_form_results: Optional[bool]
        view_poll_responses: Optional[bool]
        view_poll_results: Optional[bool]
        view_list_items: Optional[bool]
        read_list_items: Optional[bool]
        create_list_items: Optional[bool]
        manage_list_items: Optional[bool]
        remove_list_items: Optional[bool]
        complete_list_items: Optional[bool]
        reorder_list_items: Optional[bool]
        view_brackets: Optional[bool]
        read_brackets: Optional[bool]
        report_scores: Optional[bool]
        view_schedules: Optional[bool]
        read_schedules: Optional[bool]
        create_schedules: Optional[bool]
        remove_schedules: Optional[bool]
        manage_bots: Optional[bool]
        manage_server_xp: Optional[bool]
        view_streams: Optional[bool]
        join_stream_voice: Optional[bool]
        add_stream: Optional[bool]
        stream: Optional[bool]
        send_stream_messages: Optional[bool]
        add_stream_voice: Optional[bool]
        use_stream_voice_activity: Optional[bool]
        receive_all_events: Optional[bool]

    def __init__(self, **kwargs: Optional[bool]):
        self._values: Dict[str, Optional[bool]] = {}

        for key, value in kwargs.items():
            if key not in VALID_NAME_MAP:
                raise ValueError(f'No such permission: {key}')

            setattr(self, key, value)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, PermissionOverride) and self._values == other._values

    def __repr__(self) -> str:
        return f'<PermissionOverride values={len(self._values)}>'

    def _set(self, key: str, value: Optional[bool]) -> None:
        if value not in (True, None, False):
            raise TypeError(f'Expected bool or NoneType, received {value.__class__.__name__}')

        if value is None:
            self._values.pop(key, None)
        else:
            self._values[key] = value

    def pair(self) -> Tuple[Permissions, Permissions]:
        """Tuple[:class:`Permissions`, :class:`Permissions`]: Returns the (allow, deny) pair from this override."""

        allow = set()
        deny = set()

        for key, value in self._values.items():
            if value is True:
                allow.add(VALID_NAME_MAP[key])
            elif value is False:
                deny.add(VALID_NAME_MAP[key])

        return Permissions(*allow), Permissions(*deny)

    @classmethod
    def from_pair(cls, allow: Permissions, deny: Permissions) -> Self:
        """Creates an override from an allow/deny pair of :class:`Permissions`."""
        self = cls()
        for value in allow.values:
            key = REVERSE_VALID_NAME_MAP[value]
            setattr(self, key, True)

        for value in deny.values:
            key = REVERSE_VALID_NAME_MAP[value]
            setattr(self, key, False)

        return self

    def is_empty(self) -> bool:
        """Checks if the permission override is currently empty.

        An empty permission override is one that has no overrides set
        to ``True`` or ``False``.

        Returns
        -------
        :class:`bool`
            Indicates if the override is empty.
        """
        return len(self._values) == 0

    def update(self, **kwargs: Optional[bool]) -> None:
        r"""Bulk updates this permission override object.

        Allows you to set multiple attributes by using keyword
        arguments. The names must be equivalent to the properties
        listed. Extraneous key/value pairs will be silently ignored.

        Parameters
        ------------
        \*\*kwargs
            A list of key/value pairs to bulk update with.
        """
        for key, value in kwargs.items():
            if key not in self.VALID_NAMES:
                continue

            setattr(self, key, value)

    def to_dict(self) -> Dict[str, Optional[bool]]:
        """Dict[:class:`str`, Optional[:class:`bool`]]: Converts this override object into a dict."""

        result: Dict[str, Optional[bool]] = {}
        for key, value in self._values.items():
            result[VALID_NAME_MAP[key]] = value
        return result

    def __iter__(self) -> Iterator[Tuple[str, Optional[bool]]]:
        for key in self.PURE_FLAGS:
            yield key, self._values.get(key)

PermissionOverwrite = PermissionOverride  # discord.py


class _OldPermissions:
    """Wraps up permission values in Guilded.

    An instance of this class is constructed by providing kwargs of
    permission category names to the integer value of the category itself: ::

        _OldPermissions(general=64, chat=128, ...)


    .. container:: operations

        .. describe:: x == y

            Checks if two permissions are equal.

        .. describe:: x != y

            Checks if two permissions are not equal.

    Attributes
    -----------
    general_value: :class:`int`
        The raw value of the "general" category.
    recruitment_value: :class:`int`
        The raw value of the "recruitment" category.
    announcements_value: :class:`int`
        The raw value of the "announcements" category.
    chat_value: :class:`int`
        The raw value of the "chat" category.
    calendar_value: :class:`int`
        The raw value of the "calendar" category.
    forums_value: :class:`int`
        The raw value of the "forums" category.
    docs_value: :class:`int`
        The raw value of the "docs" category.
    media_value: :class:`int`
        The raw value of the "media" category.
    voice_value: :class:`int`
        The raw value of the "voice" category.
    matchmaking_value: :class:`int`
        The raw value of the "matchmaking" category.
    customization_value: :class:`int`
        The raw value of the "customization" category.
    forms_value: :class:`int`
        The raw value of the "forms" category.
    lists_value: :class:`int`
        The raw value of the "lists" category.
    brackets_value: :class:`int`
        The raw value of the "brackets" category.
    scheduling_value: :class:`int`
        The raw value of the "scheduling" category.
    bots_value: :class:`int`
        The raw value of the "bots" category.
    xp_value: :class:`int`
        The raw value of the "xp" category.
    streams_value: :class:`int`
        The raw value of the "streams" category.
    """

    def __init__(self, **values):
        self.general_value: int = values.get('general', 0)
        self.recruitment_value: int = values.get('recruitment', 0)
        self.announcements_value: int = values.get('announcements', 0)
        self.chat_value: int = values.get('chat', 0)
        self.calendar_value: int = values.get('calendar', 0)
        self.forums_value: int = values.get('forums', 0)
        self.docs_value: int = values.get('docs', 0)
        self.media_value: int = values.get('media', 0)
        self.voice_value: int = values.get('voice', 0)
        self.matchmaking_value: int = values.get('matchmaking', 0)
        self.customization_value: int = values.get('customization', 0)
        self.forms_value: int = values.get('forms', 0)
        self.lists_value: int = values.get('lists', 0)
        self.brackets_value: int = values.get('brackets', 0)
        self.scheduling_value: int = values.get('scheduling', 0)
        self.bots_value: int = values.get('bots', 0)
        self.xp_value: int = values.get('xp', 0)
        self.streams_value: int = values.get('streams', 0)
        self.socket_events_value: int = values.get('socketevents', 0)

    def __eq__(self, other) -> bool:
        return isinstance(other, Permissions) and (
            self.general_value == other.general_value
            and self.recruitment_value == other.recruitment_value
            and self.announcements_value == other.announcements_value
            and self.chat_value == other.chat_value
            and self.calendar_value == other.calendar_value
            and self.forums_value == other.forums_value
            and self.docs_value == other.docs_value
            and self.media_value == other.media_value
            and self.voice_value == other.voice_value
            and self.matchmaking_value == other.matchmaking_value
            and self.customization_value == other.customization_value
            and self.forms_value == other.forms_value
            and self.lists_value == other.lists_value
            and self.brackets_value == other.brackets_value
            and self.scheduling_value == other.scheduling_value
            and self.bots_value == other.bots_value
            and self.xp_value == other.xp_value
            and self.streams_value == other.streams_value
            and self.socket_events_value == other.socket_events_value
        )

    def __repr__(self) -> str:
        return (
            '<Permissions '
            f'general={self.general_value} '
            f'recruitment={self.recruitment_value} '
            f'announcements={self.announcements_value} '
            f'chat={self.chat_value} '
            f'calendar={self.calendar_value} '
            f'forums={self.forums_value} '
            f'docs={self.docs_value} '
            f'media={self.media_value} '
            f'voice={self.voice_value} '
            f'matchmaking={self.matchmaking_value} '
            f'customization={self.customization_value} '
            f'forms={self.forms_value} '
            f'lists={self.lists_value} '
            f'brackets={self.brackets_value} '
            f'scheduling={self.scheduling_value} '
            f'bots={self.bots_value} '
            f'xp={self.xp_value} '
            f'streams={self.streams_value} '
            f'socket_events={self.socket_events_value}>'
        )

    @classmethod
    def all(cls):
        """A factory method that creates a :class:`Permissions` with all
        permissions set to ``True``."""
        return cls(
            general=130100,
            recruitment=55,
            announcements=7,
            chat=503,
            calendar=31,
            forums=123,
            docs=15,
            media=15,
            voice=8179,
            matchmaking=21,
            customization=49,
            forms=18,
            lists=63,
            brackets=3,
            scheduling=11,
            bots=1,
            xp=1,
            streams=51,
            socket_events=16,
        )

    @classmethod
    def none(cls):
        """A factory method that creates a :class:`Permissions` with all
        permissions set to ``False``."""
        return cls()

    @classmethod
    def general(cls):
        """A factory method that creates a :class:`Permissions` with all
        "General" permissions set to ``True``."""
        return cls(general=130100)

    @classmethod
    def recruitment(cls):
        """A factory method that creates a :class:`Permissions` with all
        "Recruitment" permissions set to ``True``."""
        return cls(recruitment=55)

    @classmethod
    def announcements(cls):
        """A factory method that creates a :class:`Permissions` with all
        "Announcement" permissions set to ``True``."""
        return cls(announcements=7)

    @classmethod
    def chat(cls):
        """A factory method that creates a :class:`Permissions` with all
        "Chat" permissions set to ``True``."""
        return cls(chat=503)

    @classmethod
    def calendar(cls):
        """A factory method that creates a :class:`Permissions` with all
        "Calendar" permissions set to ``True``."""
        return cls(calendar=31)

    @classmethod
    def forums(cls):
        """A factory method that creates a :class:`Permissions` with all
        "Forum" permissions set to ``True``."""
        return cls(forums=123)

    @classmethod
    def docs(cls):
        """A factory method that creates a :class:`Permissions` with all
        "Docs" permissions set to ``True``."""
        return cls(docs=15)

    @classmethod
    def media(cls):
        """A factory method that creates a :class:`Permissions` with all
        "Media" permissions set to ``True``."""
        return cls(media=15)

    @classmethod
    def voice(cls):
        """A factory method that creates a :class:`Permissions` with all
        "Voice" permissions set to ``True``."""
        return cls(voice=8179)

    @classmethod
    def matchmaking(cls):
        """A factory method that creates a :class:`Permissions` with all
        "Matchmaking" permissions set to ``True``."""
        return cls(matchmaking=21)

    @classmethod
    def customization(cls):
        """A factory method that creates a :class:`Permissions` with all
        "Customization" permissions set to ``True``."""
        return cls(customization=49)

    @classmethod
    def forms(cls):
        """A factory method that creates a :class:`Permissions` with all
        "Forms" permissions set to ``True``."""
        return cls(forms=18)

    @classmethod
    def lists(cls):
        """A factory method that creates a :class:`Permissions` with all
        "Lists" permissions set to ``True``."""
        return cls(lists=63)

    @classmethod
    def brackets(cls):
        """A factory method that creates a :class:`Permissions` with all
        "Bracket" permissions set to ``True``."""
        return cls(brackets=3)

    @classmethod
    def scheduling(cls):
        """A factory method that creates a :class:`Permissions` with all
        "Scheduling" permissions set to ``True``."""
        return cls(scheduling=11)

    @classmethod
    def bots(cls):
        """A factory method that creates a :class:`Permissions` with all
        "Bot" permissions set to ``True``."""
        return cls(bots=1)

    @classmethod
    def xp(cls):
        """A factory method that creates a :class:`Permissions` with all
        "XP" permissions set to ``True``."""
        return cls(xp=1)

    @classmethod
    def streams(cls):
        """A factory method that creates a :class:`Permissions` with all
        "Stream" permissions set to ``True``."""
        return cls(streams=51)

    @classmethod
    def socket_events(cls):
        """A factory method that creates a :class:`Permissions` with all
        "Socket Events" permissions set to ``True``."""
        return cls(socket_events=16)

    @property
    def administrator(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user has every permission.

        This is a pseudo-permission, i.e., there is no "administrator"
        permission that Guilded recognizes, and thus this property being
        ``True`` does not necessarily mean that a user will have all the same
        exemptions as a Discord user with the administrator permission.
        """
        return self == Permissions.all()

    @property
    def update_server(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can update the server's
        settings."""
        return (self.general_value & 4) == 4

    @property
    def manage_server(self) -> bool:
        """:class:`bool`: This is an alias of :attr:`.update_server`."""
        return self.update_server

    @property
    def manage_guild(self) -> bool:
        """:class:`bool`: This is an alias of :attr:`.update_server`."""
        return self.update_server

    @property
    def manage_roles(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can update the server's
        roles."""
        return (self.general_value & 16384) == 16384

    @property
    def invite_members(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can directly invite
        members to the server."""
        return (self.general_value & 16) == 16

    @property
    def create_instant_invite(self) -> bool:
        """:class:`bool`: This is an alias of :attr:`.invite_members`."""
        return self.invite_members

    @property
    def kick_members(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can kick *or ban* members
        from the server."""
        return (self.general_value & 32) == 32

    @property
    def ban_members(self) -> bool:
        """:class:`bool`: This is an alias of :attr:`.kick_members`."""
        return self.kick_members

    @property
    def manage_groups(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can create, edit, or
        delete groups."""
        return (self.general_value & 4096) == 4096

    @property
    def manage_channels(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can create, edit, or
        delete channels."""
        return (self.general_value & 1024) == 1024

    @property
    def manage_webhooks(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can create, edit, or
        delete webhooks."""
        return (self.general_value & 2048) == 2048

    @property
    def mention_everyone(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can use ``@everyone`` and
        ``@here`` mentions."""
        return (self.general_value & 8192) == 8192

    @property
    def moderator_view(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can access "moderator
        view" to see private replies."""
        return (self.general_value & 32768) == 32768

    @property
    def slowmode_exempt(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user is exempt from slowmode
        restrictions."""
        return (self.general_value & 65536) == 65536

    @property
    def read_applications(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can view server and game
        applications."""
        return (self.recruitment_value & 2) == 2

    @property
    def approve_applications(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can approve server and
        game applications."""
        return (self.recruitment_value & 1) == 1

    @property
    def edit_application_form(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can edit server and game
        applications, and toggle accepting applications."""
        return (self.recruitment_value & 4) == 4

    @property
    def indicate_lfm_interest(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can indicate interest in
        a player instead of an upvote."""
        return (self.recruitment_value & 16) == 16

    @property
    def modify_lfm_status(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can modify the "Find
        Player" status for the server listing card."""
        return (self.recruitment_value & 32) == 32

    @property
    def read_announcements(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can view announcements."""
        return (self.announcements_value & 2) == 2

    @property
    def create_announcements(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can create and delete
        announcements."""
        return (self.announcements_value & 1) == 1

    @property
    def manage_announcements(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can delete announcements
        by other members or pin any announcement."""
        return (self.announcements_value & 4) == 4

    @property
    def read_messages(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can read chat messages."""
        return (self.chat_value & 2) == 2

    @property
    def view_channel(self) -> bool:
        """:class:`bool`: This is an alias of :attr:`.read_messages`."""
        return self.read_messages

    @property
    def send_messages(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can send chat messages."""
        return (self.chat_value & 1) == 1

    @property
    def upload_media(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can upload images and
        videos to chat messages."""
        return (self.chat_value & 128) == 128

    @property
    def create_threads(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can create threads."""
        return (self.chat_value & 16) == 16

    @property
    def create_public_threads(self) -> bool:
        """:class:`bool`: This is an alias of :attr:`.create_threads`."""
        return self.create_threads

    @property
    def create_private_threads(self) -> bool:
        """:class:`bool`: This is an alias of :attr:`.create_threads`."""
        return self.create_threads

    @property
    def send_messages_in_threads(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can reply to threads."""
        return (self.chat_value & 32) == 32

    @property
    def send_private_replies(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can privately reply to
        messages."""
        return (self.chat_value & 128) == 128

    @property
    def manage_messages(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can delete messages by
        other members or pin any message."""
        return (self.chat_value & 4) == 4

    @property
    def manage_threads(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can archive and restore
        threads."""
        return (self.chat_value & 64) == 64

    @property
    def create_chat_forms(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can create forms."""
        return (self.chat_value & 512) == 512

    @property
    def view_events(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can view calendar
        events."""
        return (self.calendar_value & 2) == 2

    @property
    def create_events(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can create calendar
        events."""
        return (self.calendar_value & 1) == 1

    @property
    def manage_events(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can update calendar
        events created by other members and move them to other channels."""
        return (self.calendar_value & 4) == 4

    @property
    def remove_events(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can remove calendar
        events created by other members."""
        return (self.calendar_value & 8) == 8

    @property
    def edit_rsvps(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can edit the RSVP status
        for members in a calendar event."""
        return (self.calendar_value & 16) == 16

    @property
    def read_forums(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can read forums."""
        return (self.forums_value & 2) == 2

    @property
    def create_topics(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can create forum
        topics."""
        return (self.forums_value & 1) == 1

    @property
    def create_topic_replies(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can create forum topic
        replies."""
        return (self.forums_value & 64) == 64

    @property
    def manage_topics(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can remove forum topics
        and replies created by other members, or move them to other
        channels."""
        return (self.forums_value & 8) == 8

    @property
    def sticky_topics(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can sticky forum topics."""
        return (self.forums_value & 16) == 16

    @property
    def lock_topics(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can lock forum topics."""
        return (self.forums_value & 32) == 32

    @property
    def view_docs(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can view docs."""
        return (self.docs_value & 2) == 2

    @property
    def read_docs(self) -> bool:
        """:class:`bool`: This is an alias of :attr:`.view_docs`."""
        return self.view_docs

    @property
    def create_docs(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can create docs."""
        return (self.docs_value & 1) == 1

    @property
    def manage_docs(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can update docs created
        by other members and move them to other channels."""
        return (self.docs_value & 4) == 4

    @property
    def remove_docs(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can remove docs created
        by other members."""
        return (self.docs_value & 8) == 8

    @property
    def see_media(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can see media."""
        return (self.media_value & 2) == 2

    @property
    def read_media(self) -> bool:
        """:class:`bool`: This is an alias of :attr:`.see_media`."""
        return self.see_media

    @property
    def create_media(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can create media."""
        return (self.media_value & 1) == 1

    @property
    def manage_media(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can update media created
        by other members and move them to other channels."""
        return (self.media_value & 4) == 4

    @property
    def remove_media(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can remove media created
        by other members."""
        return (self.media_value & 8) == 8

    @property
    def hear_voice(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can listen to voice
        chat."""
        return (self.voice_value & 2) == 2

    @property
    def add_voice(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can talk in voice chat."""
        return (self.voice_value & 1) == 1

    @property
    def speak(self) -> bool:
        """:class:`bool`: This is an alias of :attr:`.add_voice`."""
        return self.add_voice

    @property
    def manage_voice_rooms(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can create, rename, and
        delete voice rooms."""
        return (self.voice_value & 512) == 512

    @property
    def move_members(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can move members to other
        voice rooms."""
        return (self.voice_value & 16) == 16

    @property
    def broadcast(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can broadcast their voice
        to voice rooms lower in the hierarchy when speaking in voice chat."""
        return (self.voice_value & 1024) == 1024

    @property
    def whisper(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can direct their voice to
        specific members."""
        return (self.voice_value & 2048) == 2048

    @property
    def priority_speaker(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can prioritize their
        voice when speaking in voice chat."""
        return (self.voice_value & 32) == 32

    @property
    def use_voice_activity(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can use the voice
        activity input mode for voice chats."""
        return (self.voice_value & 64) == 64

    @property
    def use_voice_activation(self) -> bool:
        """:class:`bool`: This is an alias of :attr:`.use_voice_activity`."""
        return self.use_voice_activity

    @property
    def mute_members(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can mute members in voice
        chat."""
        return (self.voice_value & 128) == 128

    @property
    def deafen_members(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can deafen members in
        voice chat."""
        return (self.voice_value & 256) == 256

    @property
    def send_voice_messages(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can send chat messages to
        voice channels."""
        return (self.voice_value & 4096) == 4096

    @property
    def create_scrims(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can create matchmaking
        scrims."""
        return (self.matchmaking_value & 1) == 1

    @property
    def create_tournaments(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can create and manage
        tournaments."""
        return (self.matchmaking_value & 16) == 16

    @property
    def manage_tournaments(self) -> bool:
        """:class:`bool`: This is an alias of :attr:`.create_tournaments`."""
        return self.create_tournaments

    @property
    def register_for_tournaments(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can register the server
        for tournaments."""
        return (self.matchmaking_value & 4) == 4

    @property
    def manage_emojis(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can create and manage
        server emojis."""
        return (self.customization_value & 1) == 1

    @property
    def manage_emotes(self) -> bool:
        """:class:`bool`: This is an alias of :attr:`.manage_emojis`"""
        return self.manage_emojis

    @property
    def change_nickname(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can change their own
        nickname."""
        return (self.customization_value & 16) == 16

    @property
    def manage_nicknames(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can change the nicknames
        of other members."""
        return (self.customization_value & 32) == 32

    @property
    def view_form_responses(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can view all form
        responses."""
        return (self.forms_value & 2) == 2

    @property
    def view_poll_responses(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can view all poll
        results."""
        return (self.forms_value & 16) == 16

    @property
    def view_poll_results(self) -> bool:
        """:class:`bool`: This is an alias of :attr:`.view_poll_responses`."""
        return self.view_poll_responses

    @property
    def view_list_items(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can view list items."""
        return (self.lists_value & 2) == 2

    @property
    def read_list_items(self) -> bool:
        """:class:`bool`: This is an alias of :attr:`.view_list_items`."""
        return self.view_list_items

    @property
    def create_list_items(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can create list items."""
        return (self.lists_value & 1) == 1

    @property
    def manage_list_items(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can update list items
        created by other members and move them to other channels."""
        return (self.lists_value & 4) == 4

    @property
    def remove_list_items(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can remove list items
        created by other members."""
        return (self.lists_value & 8) == 8

    @property
    def complete_list_items(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can complete list items
        created by other members."""
        return (self.lists_value & 16) == 16

    @property
    def reorder_list_items(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can reorder list items."""
        return (self.lists_value & 32) == 32

    @property
    def view_brackets(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can view tournament
        brackets."""
        return (self.brackets_value & 2) == 2

    @property
    def read_brackets(self) -> bool:
        """:class:`bool`: This is an alias of :attr:`.view_brackets`."""
        return self.view_brackets

    @property
    def report_scores(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can report match scores
        on behalf of the server."""
        return (self.brackets_value & 1) == 1

    @property
    def view_schedules(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can view members'
        schedules."""
        return (self.scheduling_value & 2) == 2

    @property
    def read_schedules(self) -> bool:
        """:class:`bool`: This is an alias of :attr:`.view_schedules`."""
        return self.view_schedules

    @property
    def create_schedules(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can let the server know
        their available schedule."""
        return (self.scheduling_value & 1) == 1

    @property
    def remove_schedules(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can remove availabilities
        created by other members."""
        return (self.scheduling_value & 8) == 8

    @property
    def manage_bots(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can create and edit
        flowbots."""
        return (self.bots_value & 1) == 1

    @property
    def manage_server_xp(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can manage XP for
        members."""
        return (self.xp_value & 1) == 1

    @property
    def view_streams(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can view streams."""
        return (self.streams_value & 2) == 2

    @property
    def join_stream_voice(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can speak in stream
        channels."""
        return (self.streams_value & 16) == 16

    @property
    def add_stream(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can stream as well as
        speak in stream channels."""
        return (self.streams_value & 1) == 1

    @property
    def stream(self) -> bool:
        """:class:`bool`: This is an alias of :attr:`.add_stream`."""
        return self.add_stream

    @property
    def send_stream_messages(self) -> bool:
        """:class:`bool`: Returns ``True`` if a user can send messages in
        stream channels."""
        return (self.streams_value & 32) == 32

    @property
    def receive_all_events(self) -> bool:
        """:class:`bool`: Returns ``True`` if a bot can receive all server
        socket events instead of only those that match its prefix."""
        return (self.socket_events_value & 16) == 16

    def update_values(self, **values):
        r"""Bulk updates this permission object with raw integer values."""
        for key, value in values.items():
            key = f'{key}_value'
            if not hasattr(self, key):
                raise ValueError(f'No permissions category named {key!r} exists')
            if not isinstance(value, int):
                raise TypeError(f'value must be type int, not {value.__class__.__name__}')

            setattr(self, key, value)
