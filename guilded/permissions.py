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

__all__ = (
    'Permissions',
)


class Permissions:
    """Wraps up permission values in Guilded.

    An instance of this class is constructed by providing kwargs of
    permission category names to the integer value of the category itself: ::

        guilded.Permissions(general=64, chat=128, ...)


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
