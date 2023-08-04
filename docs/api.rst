.. currentmodule:: guilded

API Reference
===============

The following section outlines the API of guilded.py.

.. note::

    This module uses the Python logging module to log diagnostic and errors
    in an output independent way. If the logging module is not configured,
    these logs will not be output anywhere. See :doc:`logging` for
    more information on how to set up and use the logging module.

Version Related Info
---------------------

.. data:: __version__

    A string representation of the version. e.g. ``'1.0.0rc1'``.

Clients
--------

Client
~~~~~~~

.. autoclass:: Client
    :members:
    :inherited-members:

.. _guilded-api-events:

Event Reference
---------------

This section outlines the different types of events listened by :class:`Client`.

If an event handler raises an exception, :func:`on_error` will be called
to handle it, which defaults to print a traceback and ignoring the exception.

.. _event-experiment:

You may be interested in the `opt-in event style experiment <https://www.guilded.gg/guilded-api/blog/updates/Event-style-experiment>`_,
which is available post-version 1.3.0. If you have this experiment enabled,
event handlers that correspond to real gateway messages will receive an
instance of a :class:`BaseEvent` subclass as their single parameter.
This is denoted below with notes linking back to this section.

.. warning::

    Event functions must be a |coroutine_link|_.

Announcements
~~~~~~~~~~~~~~

.. function:: on_announcement_create(event)

    |nesonly|

    A announcement was created in an announcement channel.

    :param event: The event containing the payload.
    :type event: :class:`AnnouncementCreateEvent`

.. function:: on_announcement_update(event)

    |nesonly|

    A announcement was updated in an announcement channel.

    :param event: The event containing the payload.
    :type event: :class:`AnnouncementUpdateEvent`

.. function:: on_announcement_delete(event)

    |nesonly|

    A announcement was deleted in an announcement channel.

    :param event: The event containing the payload.
    :type event: :class:`AnnouncementDeleteEvent`

.. function:: on_announcement_reaction_add(event)

    |nesonly|

    A reaction was added to an announcement.

    :param event: The event containing the payload.
    :type event: :class:`AnnouncementReactionAddEvent`

.. function:: on_announcement_reaction_remove(event)

    |nesonly|

    A reaction was removed from an announcement.

    :param event: The event containing the payload.
    :type event: :class:`AnnouncementReactionRemoveEvent`

.. function:: on_announcement_reply_create(event)

    |nesonly|

    A reply was created under an announcement.

    :param event: The event containing the payload.
    :type event: :class:`AnnouncementReplyCreateEvent`

.. function:: on_announcement_reply_update(event)

    |nesonly|

    A announcement reply was updated.

    :param event: The event containing the payload.
    :type event: :class:`AnnouncementReplyUpdateEvent`

.. function:: on_announcement_reply_delete(event)

    |nesonly|

    A announcement reply was deleted.

    :param event: The event containing the payload.
    :type event: :class:`AnnouncementReplyDeleteEvent`

.. function:: on_announcement_reply_reaction_add(event)

    |nesonly|

    A reaction was added to a reply under an announcement.

    :param event: The event containing the payload.
    :type event: :class:`AnnouncementReplyReactionAddEvent`

.. function:: on_announcement_reply_reaction_remove(event)

    |nesonly|

    A reaction was removed from a reply under an announcement.

    :param event: The event containing the payload.
    :type event: :class:`AnnouncementReplyReactionRemoveEvent`

Bots
~~~~~

.. function:: on_bot_add(server, member)

    The client user was added to a server.

    |nestype| :class:`BotAddEvent`

    :param server: The server that the bot was added to.
    :type server: :class:`.Server`

    :param member: The member that added the bot to the server. This may be ``None``, but it is unlikely in most cases.
    :type member: Optional[:class:`.Member`]

.. function:: on_bot_remove(server, member)

    The client user was removed from a server.

    |nestype| :class:`BotRemoveEvent`

    :param server: The server that the bot was removed from.
    :type server: :class:`.Server`

    :param member: The member that removed the bot from the server. This may be ``None``, especially when the server was not previously cached.
    :type member: Optional[:class:`.Member`]

Calendar Events
~~~~~~~~~~~~~~~~

.. function:: on_calendar_event_create(event)

    A calendar event was created in a calendar channel.

    |nestype| :class:`CalendarEventCreateEvent`

    :param event: The event that was created.
    :type event: :class:`.CalendarEvent`

.. function:: on_calendar_event_update(event)

    |nesonly|

    A calendar event was updated in a calendar channel.

    :param event: The event containing the payload.
    :type event: :class:`.CalendarEventUpdateEvent`

.. function:: on_raw_calendar_event_update(event)

    |nesnever|

    A calendar event was updated in a calendar channel.

    :param event: The event that was updated.
    :type event: :class:`.CalendarEvent`

.. function:: on_calendar_event_delete(event)

    A calendar event was deleted in a calendar channel.

    |nestype| :class:`CalendarEventDeleteEvent`

    :param event: The event that was deleted.
    :type event: :class:`.CalendarEvent`

.. function:: on_calendar_event_reaction_add(event)

    |nesonly|

    A reaction was added to a calendar event.

    :param event: The event containing the payload.
    :type event: :class:`CalendarEventReactionAddEvent`

.. function:: on_calendar_event_reaction_remove(event)

    |nesonly|

    A reaction was removed from a calendar event.

    :param event: The event containing the payload.
    :type event: :class:`CalendarEventReactionRemoveEvent`

.. function:: on_calendar_event_reply_create(event)

    |nesonly|

    A reply was created under a calendar event.

    :param event: The event containing the payload.
    :type event: :class:`CalendarEventReplyCreateEvent`

.. function:: on_calendar_event_reply_update(event)

    |nesonly|

    A calendar event reply was updated.

    :param event: The event containing the payload.
    :type event: :class:`CalendarEventReplyUpdateEvent`

.. function:: on_calendar_event_reply_delete(event)

    |nesonly|

    A calendar event reply was deleted.

    :param event: The event containing the payload.
    :type event: :class:`CalendarEventReplyDeleteEvent`

.. function:: on_calendar_event_reply_reaction_add(event)

    |nesonly|

    A reaction was added to a reply under a calendar event.

    :param event: The event containing the payload.
    :type event: :class:`CalendarEventReplyReactionAddEvent`

.. function:: on_calendar_event_reply_reaction_remove(event)

    |nesonly|

    A reaction was removed from a reply under a calendar event.

    :param event: The event containing the payload.
    :type event: :class:`CalendarEventReplyReactionRemoveEvent`

.. function:: on_rsvp_update(event)

    |nesonly|

    An RSVP to a calendar event was created or deleted.

    :param event: The event containing the payload.
    :type event: :class:`RsvpUpdateEvent`

.. function:: on_raw_calendar_event_rsvp_update(event)

    |nesnever|

    An RSVP to a calendar event was created or deleted.

    :param rsvp: The RSVP that was created or updated.
    :type rsvp: :class:`.CalendarEventRSVP`

.. function:: on_bulk_rsvp_create(event)

    |nesonly|

    One or multiple RSVPs to a calendar event were created in bulk.

    :param event: The event containing the payload.
    :type event: :class:`BulkRsvpCreateEvent`

.. function:: on_bulk_calendar_event_rsvp_create(rsvps)

    |nesnever|

    One or multiple RSVPs to a calendar event were created in bulk.

    :param rsvps: The RSVPs that were created.
    :type rsvps: List[:class:`.CalendarEventRSVP`]

.. function:: on_rsvp_delete(event)

    |nesonly|

    An RSVP to a calendar event was deleted.

    :param event: The event containing the payload.
    :type event: :class:`RsvpDeleteEvent`

.. function:: on_calendar_event_rsvp_delete(event)

    |nesnever|

    An RSVP to a calendar event was deleted.

    :param rsvp: The rsvp that was deleted.
    :type rsvp: :class:`.CalendarEventRSVP`

Channels
~~~~~~~~~

.. function:: on_server_channel_create(channel)

    A channel was created in a server.

    |nestype| :class:`ServerChannelCreateEvent`

    :param channel: The channel that was created.
    :type channel: :class:`.abc.ServerChannel`

.. function:: on_server_channel_update(before, after)

    A server channel was updated.

    |nestype| :class:`ServerChannelUpdateEvent`

    :param before: The channel before being updated.
    :type before: :class:`.abc.ServerChannel`

    :param after: The channel that was updated.
    :type after: :class:`.abc.ServerChannel`

.. function:: on_server_channel_delete(channel)

    A server channel was deleted.

    |nestype| :class:`ServerChannelDeleteEvent`

    :param channel: The channel that was deleted.
    :type channel: :class:`.abc.ServerChannel`

Debug
~~~~~~

.. function:: on_error(event, *args, **kwargs)

    Usually when an event raises an uncaught exception, a traceback is
    printed to stderr and the exception is ignored. If you want to
    change this behaviour and handle the exception for whatever reason
    yourself, this event can be overridden. Which, when done, will
    suppress the default action of printing the traceback.

    The information of the exception raised and the exception itself can
    be retrieved with a standard call to :func:`sys.exc_info`.

    If you want exception to propagate out of the :class:`Client` class
    you can define an ``on_error`` handler consisting of a single empty
    :ref:`py:raise`. Exceptions raised by ``on_error`` will not be
    handled in any way by :class:`Client`.

    :param event: The name of the event that raised the exception.
    :type event: :class:`str`

    :param args: The positional arguments for the event that raised the
        exception.
    :param kwargs: The keyword arguments for the event that raised the
        exception.

.. function:: on_socket_raw_receive(msg)

    Called whenever a message is received from the gateway. The data provided
    here is not parsed in any way. This event is dispatched before the library
    does anything else with the data.

    :param msg: The message received from the WebSocket connection
    :type msg: :class:`str`

Docs
~~~~~

.. function:: on_doc_create(event)

    |nesonly|

    A doc was created in a docs channel.

    :param event: The event containing the payload.
    :type event: :class:`DocCreateEvent`

.. function:: on_doc_update(event)

    |nesonly|

    A doc was updated in a docs channel.

    :param event: The event containing the payload.
    :type event: :class:`DocUpdateEvent`

.. function:: on_doc_delete(event)

    |nesonly|

    A doc was deleted in a docs channel.

    :param event: The event containing the payload.
    :type event: :class:`DocDeleteEvent`

.. function:: on_doc_reaction_add(event)

    |nesonly|

    A reaction was added to a doc.

    :param event: The event containing the payload.
    :type event: :class:`DocReactionAddEvent`

.. function:: on_doc_reaction_remove(event)

    |nesonly|

    A reaction was removed from a doc.

    :param event: The event containing the payload.
    :type event: :class:`DocReactionRemoveEvent`

.. function:: on_doc_reply_create(event)

    |nesonly|

    A reply was created under a doc.

    :param event: The event containing the payload.
    :type event: :class:`DocReplyCreateEvent`

.. function:: on_doc_reply_update(event)

    |nesonly|

    A doc reply was updated.

    :param event: The event containing the payload.
    :type event: :class:`DocReplyUpdateEvent`

.. function:: on_doc_reply_delete(event)

    |nesonly|

    A doc reply was deleted.

    :param event: The event containing the payload.
    :type event: :class:`DocReplyDeleteEvent`

.. function:: on_doc_reply_reaction_add(event)

    |nesonly|

    A reaction was added to a reply under a doc.

    :param event: The event containing the payload.
    :type event: :class:`DocReplyReactionAddEvent`

.. function:: on_doc_reply_reaction_remove(event)

    |nesonly|

    A reaction was removed from a reply under a doc.

    :param event: The event containing the payload.
    :type event: :class:`DocReplyReactionRemoveEvent`

Forums
~~~~~~~

.. function:: on_forum_topic_create(topic)

    A forum topic was created.

    |nestype| :class:`ForumTopicCreateEvent`

    :param topic: The topic that was created.
    :type topic: :class:`ForumTopic`

.. function:: on_forum_topic_update(event)

    |nesonly|

    A forum topic was updated.

    :param event: The event containing the payload.
    :type event: :class:`ForumTopicUpdateEvent`

.. function:: on_raw_forum_topic_update(topic)

    |nesnever|

    A forum topic was updated.

    :param topic: The topic that was updated.
    :type topic: :class:`ForumTopic`

.. function:: on_forum_topic_delete(topic)

    A forum topic was deleted.

    |nestype| :class:`ForumTopicDeleteEvent`

    :param topic: The topic that was deleted.
    :type topic: :class:`ForumTopic`

.. function:: on_forum_topic_pin(event)

    |nesonly|

    A forum topic was pinned.

    :param event: The event containing the payload.
    :type event: :class:`ForumTopicPinEvent`

.. function:: on_forum_topic_unpin(event)

    |nesonly|

    A forum topic was unpinned.

    :param event: The event containing the payload.
    :type event: :class:`ForumTopicUnpinEvent`

.. function:: on_forum_topic_lock(event)

    |nesonly|

    A forum topic was locked.

    :param event: The event containing the payload.
    :type event: :class:`ForumTopicLockEvent`

.. function:: on_forum_topic_unlock(event)

    |nesonly|

    A forum topic was unlocked.

    :param event: The event containing the payload.
    :type event: :class:`ForumTopicUnlockEvent`


.. function:: on_forum_topic_reaction_add(event)

    |nesonly|

    A reaction was added to a forum topic.

    :param event: The event containing the payload.
    :type event: :class:`ForumTopicReactionAddEvent`

.. function:: on_forum_topic_reaction_remove(event)

    |nesonly|

    A reaction was removed from a forum topic.

    :param event: The event containing the payload.
    :type event: :class:`ForumTopicReactionRemoveEvent`

.. function:: on_forum_topic_reply_create(event)

    |nesonly|

    A reply was created under a forum topic.

    :param event: The event containing the payload.
    :type event: :class:`ForumTopicReplyCreateEvent`

.. function:: on_forum_topic_reply_update(event)

    |nesonly|

    A forum topic reply was updated.

    :param event: The event containing the payload.
    :type event: :class:`ForumTopicReplyUpdateEvent`

.. function:: on_forum_topic_reply_delete(event)

    |nesonly|

    A forum topic reply was deleted.

    :param event: The event containing the payload.
    :type event: :class:`ForumTopicReplyDeleteEvent`

.. function:: on_forum_topic_reply_reaction_add(event)

    |nesonly|

    A reaction was added to a reply under a forum topic.

    :param event: The event containing the payload.
    :type event: :class:`ForumTopicReplyReactionAddEvent`

.. function:: on_forum_topic_reply_reaction_remove(event)

    |nesonly|

    A reaction was removed from a reply under a forum topic.

    :param event: The event containing the payload.
    :type event: :class:`ForumTopicReplyReactionRemoveEvent`

Gateway
~~~~~~~~

.. function:: on_ready()

    Called when the client has connected to the gateway and filled its internal cache automatically.

    .. warning::

        This event will be called multiple times thoughout a process's lifetime when the client
        resumes dropped gateway connections, so you should not do anything in a ``ready`` handler
        that you do not want to be done twice.

        For initial setup like loading extensions and cogs, use :meth:`Client.setup_hook`.

.. function:: on_connect()

    Called when the client has successfully connected to Guilded. This is not
    the same as the client being fully prepared, see :func:`on_ready` for that.

.. function:: on_disconnect()

    Called when the client has disconnected from Guilded. This could happen either
    through the internet being disconnected, explicit calls to :meth:`.Client.close`,
    or Guilded terminating the connection one way or the other.

    This function can be called many times without a corresponding :func:`on_connect` call.

Groups
~~~~~~~

.. function:: on_group_create(group)

    A group was created in a server.

    |nestype| :class:`GroupCreateEvent`

    :param group: The group that was created.
    :type group: :class:`.Group`

.. function:: on_group_update(event)

    |nesonly|

    A group was updated in a server.

    :param event: The event containing the payload.
    :type event: :class:`.GroupUpdateEvent`

.. function:: on_raw_group_update(group)

    |nesnever|

    A group was updated in a server.

    :param group: The group that was updated.
    :type group: :class:`.Group`

.. function:: on_group_delete(group)

    A group was deleted in a server.

    |nestype| :class:`GroupDeleteEvent`

    :param group: The group that was deleted.
    :type group: :class:`.Group`

List Items
~~~~~~~~~~~

.. function:: on_list_item_create(event)

    |nesonly|

    A list item was created.

    :param event: The event containing the payload.
    :type event: :class:`ListItemCreateEvent`

.. function:: on_list_item_update(event)

    |nesonly|

    A list item was updated.

    :param event: The event containing the payload.
    :type event: :class:`ListItemUpdateEvent`

.. function:: on_list_item_delete(event)

    |nesonly|

    A list item was deleted.

    :param event: The event containing the payload.
    :type event: :class:`ListItemDeleteEvent`

.. function:: on_list_item_complete(event)

    |nesonly|

    A list item was marked as complete.

    :param event: The event containing the payload.
    :type event: :class:`ListItemPinEvent`

.. function:: on_list_item_uncomplete(event)

    |nesonly|

    A list item was unmarked as complete.

    :param event: The event containing the payload.
    :type event: :class:`ListItemUnpinEvent`

Members
~~~~~~~~

.. function:: on_member_join(member)

    A member joined a server.

    This event will also be dispatched if the member is the current user,
    which is a case you may want to explicitly ignore.

    |nestype| :class:`MemberJoinEvent`

    :param member: The member that joined.
    :type member: :class:`.Member`

.. function:: on_member_remove(member)

    A member left or was forcibly removed from their server.

    This event encompasses three cases of member removal.
    If the style experiment is disabled, you must use
    :func:`.on_member_leave`, :func:`.on_member_kick`, or :func:`.on_member_ban`
    to fine-tune which cases you process in your code.
    Otherwise, you can check the attributes on the dispatched :class:`MemberRemoveEvent` object.

    |nestype| :class:`MemberRemoveEvent`

    :param member: The member that was removed.
    :type member: :class:`.Member`

.. function:: on_member_leave(member)

    |nesnever|

    A member manually left their server or their account was deleted.

    :param member: The member that left.
    :type member: :class:`.Member`

.. function:: on_member_kick(member)

    |nesnever|

    A member was kicked from their server.

    :param member: The member that was kicked.
    :type member: :class:`.Member`

.. function:: on_member_ban(member)

    |nesnever|

    A member was banned from their server.

    :param member: The member that was banned.
    :type member: :class:`.Member`

.. function:: on_member_update(before, after)

    A member was updated.

    If the style experiment is disabled, then this event is only dispatched if
    the member was cached before being updated.

    Any of the following attributes may have changed to cause this event to be
    dispatched:

    * :attr:`.Member.nickname`

    .. If the style experiment is disabled, this list also includes :attr:`.Member.roles`.

    |nestype| :class:`MemberUpdateEvent`

    :param before: The member before they were updated.
    :type before: :class:`.Member`

    :param after: The member that was updated.
    :type after: :class:`.Member`

.. function:: on_member_social_link_create(event)

    |nesonly|

    A member created a social link on their profile.

    :param event: The event containing the payload.
    :type event: :class:`MemberSocialLinkCreateEvent`

.. function:: on_member_social_link_update(event)

    |nesonly|

    A member updated one of their profile social links.

    :param event: The event containing the payload.
    :type event: :class:`MemberSocialLinkUpdateEvent`

.. function:: on_member_social_link_delete(event)

    |nesonly|

    A member deleted one of their profile social links.

    :param event: The event containing the payload.
    :type event: :class:`MemberSocialLinkDeleteEvent`

.. function:: on_ban_create(event)

    |nesonly|

    A ban was created in a server (a member was banned).
    This is not necessarily equivalent to member removal.

    :param event: The event containing the payload.
    :type event: :class:`BanCreateEvent`

.. function:: on_ban_delete(event)

    |nesonly|

    A ban was deleted in a server (a member was unbanned).

    :param event: The event containing the payload.
    :type event: :class:`BanDeleteEvent`

.. function:: on_bulk_member_roles_update(event)

    |nesonly|

    A member's roles were updated.

    :param event: The event containing the payload.
    :type event: :class:`BulkMemberRolesUpdateEvent`

.. function:: on_bulk_member_xp_add(event)

    |nesonly|

    One or more members were awarded XP.

    :param event: The event containing the payload.
    :type event: :class:`BulkMemberXpAddEvent`

Messages
~~~~~~~~~

.. function:: on_message(message)

    A message was sent in a server or DM.

    |nestype| :class:`MessageEvent`

    :param message: The message that was sent.
    :type message: :class:`.ChatMessage`

.. function:: on_message_edit(before, after)

    |nesnever|

    A message was updated.

    This event is only dispatched if the message was cached before being updated.
    If you want to handle message updates regardless of state,
    see :func:`.on_raw_message_edit`.

    :param before: The message before it was edited.
    :type before: :class:`.ChatMessage`

    :param after: The message that was edited in its current state.
    :type after: :class:`.ChatMessage`

.. function:: on_message_update(event)

    |nesonly|

    A message was updated.

    :param event: The event containing the payload.
    :type event: :class:`MessageUpdateEvent`

.. function:: on_message_delete(message)

    A message was deleted.

    |nestype| :class:`MessageDeleteEvent`

    If the style experiment is disabled, then this event is only dispatched if
    the message was cached before being deleted. If you want to handle message
    deletions regardless of state, see :func:`.on_raw_message_delete`.

    :param message: The message that was deleted.
    :type message: :class:`.Message`

.. function:: on_raw_message_delete(data)

    |nesnever|

    A message was deleted.

    :param data:
    :type data: :class:`dict`

.. function:: on_message_reaction_add(reaction)

    A reaction was added to a message.

    |nestype| :class:`MessageReactionAddEvent`

    :param reaction: The reaction that was added.
    :type reaction: :class:`Reaction`

.. function:: on_message_reaction_remove(reaction)

    A reaction was removed from a message.

    |nestype| :class:`MessageReactionRemoveEvent`

    :param reaction: The reaction that was removed.
    :type reaction: :class:`Reaction`

.. function:: on_bulk_message_reaction_remove(event)

    |nesonly|

    One or multiple reactions were bulk removed from a message.

    .. versionadded: 1.9

    :param event: The event containing the payload.
    :type event: :class:`BulkMessageReactionRemoveEvent`

Roles
~~~~~~

.. function:: on_role_create(role)

    A role was created in a server.

    |nestype| :class:`RoleCreateEvent`

    :param role: The role that was created.
    :type role: :class:`.Role`

.. function:: on_role_update(before, after)

    A role was updated.

    |nestype| :class:`RoleUpdateEvent`

    :param before: The role before modification.
    :type before: :class:`.Role`

    :param after: The role after modification.
    :type after: :class:`.Role`

.. function:: on_role_delete(role)

    A role was deleted.

    |nestype| :class:`RoleDeleteEvent`

    :param role: The role that was deleted.
    :type role: :class:`.Role`

Webhooks
~~~~~~~~~

.. function:: on_webhook_create(webhook)

    A webhook was created in a server.

    |nestype| :class:`WebhookCreateEvent`

    :param webhook: The webhook that was created.
    :type webhook: :class:`.Webhook`

.. function:: on_webhook_update(event)

    |nesonly|

    A webhook was updated or deleted in a server.

    :param event: The event containing the payload.
    :type event: :class:`WebhookUpdateEvent`

.. function:: on_raw_webhook_update(webhook)

    |nesnever|

    A webhook was updated or deleted in a server.

    If the webhook was deleted, its :attr:`.Webhook.deleted_at` attribute will
    be set.

    :param webhook: The webhook that was updated.
    :type webhook: :class:`.Webhook`

Users
~~~~~~

.. function:: on_user_status_create(user, status, expires_at)

    .. warning::

        Due to a Guilded bug, this event is currently not sent.

    A user set their status.

    |nestype| :class:`UserStatusCreateEvent`

    :param user: The user that updated their status.
    :type user: :class:`~guilded.User`

    :param status: The new status.
    :type status: :class:`.Status`

    :param expires_at: When the status will expire, if applicable.
    :type expires_at: Optional[:class:`datetime.datetime`]

.. function:: on_user_status_delete(user, status)

    .. warning::

        Due to a Guilded bug, this event is currently not sent.

    A user deleted their status.

    |nestype| :class:`UserStatusDeleteEvent`

    :param user: The user that deleted their status.
    :type user: :class:`~guilded.User`

    :param status: The status that was deleted.
    :type status: :class:`.Status`

Event Wrappers
---------------

With the :ref:`event style experiment <event-experiment>` enabled, many event
handlers will receive one of the following subclasses. The basic structure of
these event wrappers closely mirror the payloads provided by the Guilded API.

.. versionadded:: 1.3

.. autoclass:: BaseEvent()
    :members:

.. autoclass:: MessageEvent()
    :members:
    :inherited-members:

.. autoclass:: MessageUpdateEvent()
    :members:
    :inherited-members:

.. autoclass:: MessageDeleteEvent()
    :members:
    :inherited-members:

.. autoclass:: BotAddEvent()
    :members:
    :inherited-members:

.. autoclass:: BotRemoveEvent()
    :members:
    :inherited-members:

.. autoclass:: MemberJoinEvent()
    :members:
    :inherited-members:

.. autoclass:: MemberRemoveEvent()
    :members:
    :inherited-members:

.. autoclass:: BanCreateEvent()
    :members:
    :inherited-members:

.. autoclass:: BanDeleteEvent()
    :members:
    :inherited-members:

.. autoclass:: MemberUpdateEvent()
    :members:
    :inherited-members:

.. autoclass:: BulkMemberRolesUpdateEvent()
    :members:
    :inherited-members:

.. autoclass:: MemberSocialLinkCreateEvent()
    :members:
    :inherited-members:

.. autoclass:: MemberSocialLinkUpdateEvent()
    :members:
    :inherited-members:

.. autoclass:: MemberSocialLinkDeleteEvent()
    :members:
    :inherited-members:

.. autoclass:: BulkMemberXpAddEvent()
    :members:
    :inherited-members:

.. autoclass:: ServerChannelCreateEvent()
    :members:
    :inherited-members:

.. autoclass:: ServerChannelUpdateEvent()
    :members:
    :inherited-members:

.. autoclass:: ServerChannelDeleteEvent()
    :members:
    :inherited-members:

.. autoclass:: WebhookCreateEvent()
    :members:
    :inherited-members:

.. autoclass:: WebhookUpdateEvent()
    :members:
    :inherited-members:

.. autoclass:: AnnouncementCreateEvent()
    :members:
    :inherited-members:

.. autoclass:: AnnouncementUpdateEvent()
    :members:
    :inherited-members:

.. autoclass:: AnnouncementDeleteEvent()
    :members:
    :inherited-members:

.. autoclass:: AnnouncementReactionAddEvent()
    :members:
    :inherited-members:

.. autoclass:: AnnouncementReactionRemoveEvent()
    :members:
    :inherited-members:

.. autoclass:: AnnouncementReplyCreateEvent()
    :members:
    :inherited-members:

.. autoclass:: AnnouncementReplyUpdateEvent()
    :members:
    :inherited-members:

.. autoclass:: AnnouncementReplyDeleteEvent()
    :members:
    :inherited-members:

.. autoclass:: AnnouncementReplyReactionAddEvent()
    :members:
    :inherited-members:

.. autoclass:: AnnouncementReplyReactionRemoveEvent()
    :members:
    :inherited-members:

.. autoclass:: DocCreateEvent()
    :members:
    :inherited-members:

.. autoclass:: DocUpdateEvent()
    :members:
    :inherited-members:

.. autoclass:: DocDeleteEvent()
    :members:
    :inherited-members:

.. autoclass:: DocReactionAddEvent()
    :members:
    :inherited-members:

.. autoclass:: DocReactionRemoveEvent()
    :members:
    :inherited-members:

.. autoclass:: DocReplyCreateEvent()
    :members:
    :inherited-members:

.. autoclass:: DocReplyUpdateEvent()
    :members:
    :inherited-members:

.. autoclass:: DocReplyDeleteEvent()
    :members:
    :inherited-members:

.. autoclass:: DocReplyReactionAddEvent()
    :members:
    :inherited-members:

.. autoclass:: DocReplyReactionRemoveEvent()
    :members:
    :inherited-members:

.. autoclass:: CalendarEventCreateEvent()
    :members:
    :inherited-members:

.. autoclass:: CalendarEventUpdateEvent()
    :members:
    :inherited-members:

.. autoclass:: CalendarEventDeleteEvent()
    :members:
    :inherited-members:

.. autoclass:: CalendarEventReactionAddEvent()
    :members:
    :inherited-members:

.. autoclass:: CalendarEventReactionRemoveEvent()
    :members:
    :inherited-members:

.. autoclass:: CalendarEventReplyCreateEvent()
    :members:
    :inherited-members:

.. autoclass:: CalendarEventReplyUpdateEvent()
    :members:
    :inherited-members:

.. autoclass:: CalendarEventReplyDeleteEvent()
    :members:
    :inherited-members:

.. autoclass:: CalendarEventReplyReactionAddEvent()
    :members:
    :inherited-members:

.. autoclass:: CalendarEventReplyReactionRemoveEvent()
    :members:
    :inherited-members:

.. autoclass:: RsvpUpdateEvent()
    :members:
    :inherited-members:

.. autoclass:: RsvpDeleteEvent()
    :members:
    :inherited-members:

.. autoclass:: BulkRsvpCreateEvent()
    :members:
    :inherited-members:

.. autoclass:: ForumTopicCreateEvent()
    :members:
    :inherited-members:

.. autoclass:: ForumTopicUpdateEvent()
    :members:
    :inherited-members:

.. autoclass:: ForumTopicDeleteEvent()
    :members:
    :inherited-members:

.. autoclass:: ForumTopicPinEvent()
    :members:
    :inherited-members:

.. autoclass:: ForumTopicUnpinEvent()
    :members:
    :inherited-members:

.. autoclass:: ForumTopicLockEvent()
    :members:
    :inherited-members:

.. autoclass:: ForumTopicUnlockEvent()
    :members:
    :inherited-members:

.. autoclass:: ForumTopicReactionAddEvent()
    :members:
    :inherited-members:

.. autoclass:: ForumTopicReactionRemoveEvent()
    :members:
    :inherited-members:

.. autoclass:: ForumTopicReplyCreateEvent()
    :members:
    :inherited-members:

.. autoclass:: ForumTopicReplyUpdateEvent()
    :members:
    :inherited-members:

.. autoclass:: ForumTopicReplyDeleteEvent()
    :members:
    :inherited-members:

.. autoclass:: ForumTopicReplyReactionAddEvent()
    :members:
    :inherited-members:

.. autoclass:: ForumTopicReplyReactionRemoveEvent()
    :members:
    :inherited-members:

.. autoclass:: GroupCreateEvent()
    :members:
    :inherited-members:

.. autoclass:: GroupUpdateEvent()
    :members:
    :inherited-members:

.. autoclass:: GroupDeleteEvent()
    :members:
    :inherited-members:

.. autoclass:: ListItemCreateEvent()
    :members:
    :inherited-members:

.. autoclass:: ListItemUpdateEvent()
    :members:
    :inherited-members:

.. autoclass:: ListItemDeleteEvent()
    :members:
    :inherited-members:

.. autoclass:: ListItemCompleteEvent()
    :members:
    :inherited-members:

.. autoclass:: ListItemUncompleteEvent()
    :members:
    :inherited-members:

.. autoclass:: MessageReactionAddEvent()
    :members:
    :inherited-members:

.. autoclass:: MessageReactionRemoveEvent()
    :members:
    :inherited-members:

.. autoclass:: BulkMessageReactionRemoveEvent()
    :members:
    :inherited-members:

.. autoclass:: RoleCreateEvent()
    :members:
    :inherited-members:

.. autoclass:: RoleUpdateEvent()
    :members:
    :inherited-members:

.. autoclass:: RoleDeleteEvent()
    :members:
    :inherited-members:

.. autoclass:: UserStatusCreateEvent()
    :members:
    :inherited-members:

.. autoclass:: UserStatusDeleteEvent()
    :members:
    :inherited-members:

Enumerations
-------------

The API provides some enumerations for certain types of strings to avoid the
API from being stringly typed in case the strings change in the future.

.. class:: MediaType

    Represents a file/attachment's media type in Guilded.

    .. attribute:: attachment

        the media is an :class:`Attachment`.

    .. attribute:: content_media

        the media is an :class:`Attachment`.

    .. attribute:: emoji

        the media is an emoji.

    .. attribute:: custom_reaction

        the media is an emoji.

    .. attribute:: avatar

        the media is a :class:`User` or :class:`Member` avatar.

    .. attribute:: user_avatar

        the media is a :class:`User` or :class:`Member` avatar.

    .. attribute:: profile_avatar

        the media is a :class:`User` or :class:`Member` avatar.

    .. attribute:: banner

        the media is a :class:`User` or :class:`Member` banner.

    .. attribute:: user_banner

        the media is a :class:`User` or :class:`Member` banner.

    .. attribute:: profile_banner

        the media is a :class:`User` or :class:`Member` banner.

    .. attribute:: server_icon

        the media is a :class:`Server` avatar.

    .. attribute:: team_avatar

        the media is a :class:`Server` avatar.

    .. attribute:: team_banner

        the media is a :class:`Server` banner.

    .. attribute:: group_icon

        the media is a :class:`Group` avatar.

    .. attribute:: group_avatar

        the media is a :class:`Group` avatar.

    .. attribute:: group_banner

        the media is a :class:`Group` banner.

    .. attribute:: embed_image

        the media is a proxied image in a link embed.

.. class:: FileType

    Represents a type of file in Guilded. In the case of uploading
    files, this usually does not have to be set manually, but if the
    library fails to detect the type of file from its extension, you
    can pass this into :class:`File`\'s ``file_type`` parameter.

    .. attribute:: image

        the file is an image

    .. attribute:: video

        the file is a video

.. class:: ChannelType

    A type of channel.

    .. attribute:: announcements

        the channel is an announcement channel.

    .. attribute:: calendar

        the channel is a calendar channel.

    .. attribute:: chat

        the channel is a chat or "text" channel.

    .. attribute:: docs

        the channel is a docs channel.

    .. attribute:: forums

        the channel is a forums channel.

    .. attribute:: media

        the channel is a media channel.

    .. attribute:: news

        the channel is an announcement channel.
        this is an alias of :attr:`.announcements`.

    .. attribute:: list

        the channel is a list channel.

    .. attribute:: scheduling

        the channel is a scheduling channel.

    .. attribute:: stream

        the channel is a stream channel.

    .. attribute:: text

        the channel is a chat or "text" channel.
        this is an alias of :attr:`.chat`.

    .. attribute:: voice

        the channel is a voice channel.

.. class:: ChannelVisibility

    Restricts what users can view a channel.

    .. attribute:: public

        Visible to everyone, including members who are not part of the server.
        Threads cannot be ``public``.

    .. attribute:: private

        Visible only to members who have been explicitly mentioned.
        Non-thread channels cannot be ``private``.

.. class:: FlowTriggerType

    A type of flow trigger for :class:`.FlowBot`\s.

    .. attribute:: server_updated

        Server settings on the overview page changed

    .. attribute:: member_muted

        A member is muted on the server

    .. attribute:: member_sent_message_to_channel

        When someone sends a message to a channel

    .. attribute:: member_joined

        Via an application, an invite, or any other means

    .. attribute:: application_received

        When a user applies to the server

    .. attribute:: toggle_list_item

        When a :class:`.ListItem` is marked as complete or incomplete

    .. attribute:: event_created

        An event is created in a calendar channel

    .. attribute:: event_updated

        An event is updated in a calendar channel

    .. attribute:: event_removed

        An event is deleted in a calendar channel

    .. attribute:: forum_topic_created

        A topic is created in a :class:`.ForumChannel`

    .. attribute:: forum_topic_updated

        A topic is updated in a :class:`.ForumChannel`

    .. attribute:: forum_topic_deleted

        A topic is deleted in a :class:`.ForumChannel`

    .. attribute:: list_item_created

        A list item's content is created in a :class:`.ListChannel`

    .. attribute:: list_item_updated

        A list item's content is updated in a :class:`.ListChannel`

    .. attribute:: list_item_deleted

        A list item's content is deleted in a :class:`.ListChannel`

    .. attribute:: doc_created

        A doc is created in a :class:`.DocsChannel`

    .. attribute:: doc_updated

        A doc is updated in a :class:`.DocsChannel`

    .. attribute:: doc_deleted

        A doc is deleted in a :class:`.DocsChannel`

    .. attribute:: media_created

        Media is created in a :class:`.MediaChannel`

    .. attribute:: media_updated

        Media is updated in a :class:`.MediaChannel`

    .. attribute:: media_deleted

        Media is deleted in a :class:`.MediaChannel`

    .. attribute:: announcement_created

        An announcement is created in an :class:`.AnnouncementChannel`

    .. attribute:: announcement_updated

        An announcement is updated in an :class:`.AnnouncementChannel`

    .. attribute:: announcement_deleted

        An announcement is deleted in an :class:`.AnnouncementChannel`

    .. attribute:: voice_group_joined

        A voice group is joined in a :class:`.VoiceChannel`

    .. attribute:: voice_group_left

        A voice group is left in a :class:`.VoiceChannel`

    .. attribute:: twitch_stream_online

        A Twitch stream has started

    .. attribute:: twitch_stream_offline

        A Twitch stream has stopped

    .. attribute:: twitch_stream_subscribed

        A user has subscribed to a Twitch stream

    .. attribute:: twitch_stream_followed

        A user has followed a Twitch stream

    .. attribute:: twitch_stream_unfollowed

        A user has unfollowed a Twitch stream

    .. attribute:: twitch_stream_unsubscribed

        A user has unsubscribed to a Twitch stream

    .. attribute:: patreon_tiered_membership_created

        A user has pledged to a campaign's tier

    .. attribute:: patreon_tiered_membership_updated

        A user has updated their pledged tier in a campaign

    .. attribute:: patreon_tiered_membership_cancelled

        A user has cancelled their pledge to a campaign's tier

    .. attribute:: subscription_created

        A member subscribes to the server

    .. attribute:: subscription_updated

        A member upgrades or downgrades their server subscription

    .. attribute:: subscription_canceled

        A member cancels their server subscription

    .. attribute:: scheduling_availability_started

        Availability started in a scheduling channel

    .. attribute:: scheduling_availability_ended

        Availability ended in a scheduling channel

    .. attribute:: Missing youtube_video_published

        New video posted from specified channel

.. class:: FlowActionType

    An action to perform when a :class:`.FlowTriggerType` is activated.

    .. attribute:: send_a_custom_message

        Send a custom message

    .. attribute:: assign_role

        Assign a role

    .. attribute:: add_xp_to_member

        Add XP to a member

    .. attribute:: edit_group_membership

        Edit group membership

    .. attribute:: create_a_forum_topic

        Create a forum topic

    .. attribute:: create_a_list_item

        Create a list item

    .. attribute:: remove_role

        Remove a role

    .. attribute:: delete_a_message

        Delete a message

    .. attribute:: create_a_doc

        Create a doc

.. class:: Presence

    Represents a :class:`User`\'s presence - the colored circle on their
    avatar in the client.

    .. attribute:: online

        the user is online

    .. attribute:: idle

        the user is idle

    .. attribute:: dnd

        the user is on "do not disturb" mode

    .. attribute:: do_not_disturb

        the user is on "do not disturb" mode

    .. attribute:: invisible

        the user is offline or invisible

    .. attribute:: offline

        the user is offline or invisible

.. class:: ServerType

    A type of server.

    .. attribute:: team

        The server's type is "Team".

    .. attribute:: organization

        The server's type is "Organization".

    .. attribute:: community

        The server's type is "Community".

    .. attribute:: clan

        The server's type is "Clan".

    .. attribute:: guild

        The server's type is "Guild".

    .. attribute:: friends

        The server's type is "Friends".

    .. attribute:: streaming

        The server's type is "Streaming".

    .. attribute:: other

        The server's type is "Other".

.. class:: SocialLinkType

    A type of social link.

    .. versionadded:: 1.3

    .. attribute:: twitch

        The social link is a Twitch connection.

    .. attribute:: bnet

        The social link is a Battle.net connection.

    .. attribute:: battlenet

        The social link is a Battle.net connection.
        This is an alias of :attr:`.bnet`.

    .. attribute:: psn

        The social link is a Playstation Network connection.

    .. attribute:: playstation

        The social link is a Playstation Network connection.
        This is an alias of :attr:`.psn`.

    .. attribute:: xbox

        The social link is an Xbox connection.

    .. attribute:: steam

        The social link is a Steam connection.

    .. attribute:: origin

        The social link is an Origin connection.

    .. attribute:: youtube

        The social link is a YouTube connection.

    .. attribute:: twitter

        The social link is a Twitter connection.

    .. attribute:: facebook

        The social link is a Facebook connection.

    .. attribute:: switch

        The social link is a Nintendo Switch connection.

    .. attribute:: patreon

        The social link is a Patreon connection.

    .. attribute:: roblox

        The social link is a Roblox connection.

    .. attribute:: epic

        The social link is an Epic Games connection.

    .. attribute:: epicgames

        The social link is an Epic Games connection.
        This is an alias of :attr:`.epic`.

.. class:: RepeatInterval

    A basic repeat interval setting for calendar events.

    .. versionadded:: 1.7

    .. attribute:: once

        The event will repeat once.

    .. attribute:: daily

        The event will repeat every day.

    .. attribute:: weekly

        The event will repeat every week.

    .. attribute:: monthly

        The event will repeat every month.

    .. attribute:: custom

        A custom repeat interval. When constructing a :class:`RepeatInfo`,
        use :class:`CustomRepeatInterval` instead of this enum value.

.. class:: CustomRepeatInterval

    A custom repeat interval setting for calendar events. These intervals
    allow for more advanced repeat info.

    .. versionadded:: 1.7

    .. attribute:: daily

        The event will repeat every day.

    .. attribute:: weekly

        The event will repeat every week.

    .. attribute:: monthly

        The event will repeat every month.

    .. attribute:: yearly

        The event will repeat every year.

        There is an alias for this attribute called :attr:`.annually`.

    .. attribute:: annually

        The event will repeat every year.

        There is an alias for this attribute called :attr:`.yearly`.

.. class:: Weekday

    A day of the week for :class:`RepeatInfo` with the
    :attr:`CustomRepeatInterval.weekly` interval.

    .. versionadded:: 1.7

    .. attribute:: sunday

        The event will repeat every Sunday.

    .. attribute:: monday

        The event will repeat every Monday.

    .. attribute:: tuesday

        The event will repeat every Tuesday.

    .. attribute:: wednesday

        The event will repeat every Wednesday.

    .. attribute:: thursday

        The event will repeat every Thursday.

    .. attribute:: friday

        The event will repeat every Friday.

    .. attribute:: saturday

        The event will repeat every Saturday.

.. class:: DeleteSeriesType

    Controls deletion behavior of calendar events in a series.

    .. versionadded:: 1.7

    .. attribute:: all

        All events in the series will be deleted.

    .. attribute:: forward

        Only the event and future items in its series will be deleted.

.. class:: ServerSubscriptionTierType

    A type of server subscription tier.

    .. versionadded:: 1.9

    .. attribute:: gold

        The tier type is "Gold".

    .. attribute:: silver

        The tier type is "Silver".

    .. attribute:: copper

        The tier type is "Copper".


Utility Functions
------------------

.. autofunction:: guilded.utils.hyperlink

.. autofunction:: guilded.utils.link

.. autofunction:: guilded.utils.new_uuid

.. autofunction:: guilded.utils.sleep_until

.. autofunction:: guilded.utils.find

.. autofunction:: guilded.utils.get

.. autofunction:: guilded.utils.remove_markdown

.. autofunction:: guilded.utils.escape_markdown

.. autofunction:: guilded.utils.escape_mentions

Webhooks
---------

Webhooks are a convenient way to send messages to channels without any user or
bot authentication.

Webhook
~~~~~~~~

.. autoclass:: guilded.Webhook()
    :inherited-members:
    :members:

WebhookMessage
~~~~~~~~~~~~~~~

.. autoclass:: guilded.WebhookMessage()
    :inherited-members:
    :members:

Abtract Base Classes
---------------------

Abtract base classes are classes that some models inherit from in order to get
their behaviour. They are not to be user-instantiated.

Messageable
~~~~~~~~~~~~

.. autoclass:: guilded.abc.Messageable()
    :members:

User
~~~~~

.. autoclass:: guilded.abc.User()
    :members:

ServerChannel
~~~~~~~~~~~~~~

.. autoclass:: guilded.abc.ServerChannel()
    :members:

Reply
~~~~~~~~~~~~~~

.. autoclass:: guilded.abc.Reply()
    :members:

.. _guilded_api_models:

Guilded Models
---------------

Models are classes that are constructed using data recieved directly from
Guilded and are not meant to be created by the user of the library.

.. danger::

    The classes listed below are **not intended to be created by users**.

    For example, this means that you should not make your own :class:`User`
    instances nor should you modify a :class:`User` instance yourself.

    If you want to get one of these model classes instances they'd have to be
    through the cache, and a common way of doing so is through the :meth:`utils.find`
    function or attributes of model classes that you receive from the events
    specified in the Event Reference.

Announcement
~~~~~~~~~~~~~

.. autoclass:: Announcement()
    :members:
    :inherited-members:

AnnouncementChannel
~~~~~~~~~~~~~~~~~~~~

.. autoclass:: AnnouncementChannel()
    :members:
    :inherited-members:

AnnouncementReply
~~~~~~~~~~~~~~~~~~

.. autoclass:: AnnouncementReply()
    :members:
    :inherited-members:

Asset
~~~~~~

.. autoclass:: Asset()
    :members:

Attachment
~~~~~~~~~~~

.. autoclass:: Attachment()
    :members:

Availability
~~~~~~~~~~~~~

.. autoclass:: Availability()
    :members:

CalendarChannel
~~~~~~~~~~~~~~~~

.. autoclass:: CalendarChannel()
    :members:
    :inherited-members:

CalendarEvent
~~~~~~~~~~~~~~

.. autoclass:: CalendarEvent()
    :members:
    :inherited-members:

CalendarEventReply
~~~~~~~~~~~~~~~~~~~

.. autoclass:: CalendarEventReply()
    :members:
    :inherited-members:

CalendarEventRSVP
~~~~~~~~~~~~~~~~~~

.. autoclass:: CalendarEventRSVP()
    :members:
    :inherited-members:

Category
~~~~~~~~~

.. autoclass:: Category()
    :members:
    :inherited-members:

ClientUser
~~~~~~~~~~~

.. autoclass:: ClientUser()
    :members:
    :inherited-members:

ChatChannel
~~~~~~~~~~~~

.. autoclass:: ChatChannel()
    :members:
    :inherited-members:

ChatMessage
~~~~~~~~~~~~

.. autoclass:: ChatMessage()
    :members:
    :inherited-members:

Doc
~~~~

.. autoclass:: Doc()
    :members:
    :inherited-members:

DocReply
~~~~~~~~~

.. autoclass:: DocReply()
    :members:
    :inherited-members:

DocsChannel
~~~~~~~~~~~~

.. autoclass:: DocsChannel()
    :members:
    :inherited-members:

Emote
~~~~~~

.. autoclass:: Emote()
    :members:

File
~~~~~

.. autoclass:: File()
    :members:

FlowBot
~~~~~~~~

.. autoclass:: FlowBot()
    :members:

ForumChannel
~~~~~~~~~~~~~

.. autoclass:: ForumChannel()
    :members:
    :inherited-members:

ForumTopic
~~~~~~~~~~~

.. autoclass:: ForumTopic()
    :members:
    :inherited-members:

ForumTopicReply
~~~~~~~~~~~~~~~~

.. autoclass:: ForumTopicReply()
    :members:
    :inherited-members:

Group
~~~~~~

.. autoclass:: Group()
    :members:

Invite
~~~~~~~

.. autoclass:: Invite()
    :members:

ListChannel
~~~~~~~~~~~~

.. autoclass:: ListChannel()
    :members:
    :inherited-members:

ListItem
~~~~~~~~~

.. autoclass:: ListItem()
    :members:
    :inherited-members:

ListItemNote
~~~~~~~~~~~~~

.. autoclass:: ListItemNote()
    :members:
    :inherited-members:

Media
~~~~~~

.. autoclass:: Media()
    :members:

MediaChannel
~~~~~~~~~~~~~

.. autoclass:: MediaChannel()
    :members:
    :inherited-members:

Member
~~~~~~~

.. autoclass:: Member()
    :members:
    :inherited-members:

MemberBan
~~~~~~~~~~

.. autoclass:: MemberBan()
    :members:

Mentions
~~~~~~~~~

.. autoclass:: Mentions()
    :members:

PartialMessageable
~~~~~~~~~~~~~~~~~~~

.. autoclass:: PartialMessageable()
    :members:
    :inherited-members:

Reaction
~~~~~~~~~

.. autoclass:: Reaction()
    :members:

Role
~~~~~

.. autoclass:: Role()
    :members:

SchedulingChannel
~~~~~~~~~~~~~~~~~~

.. autoclass:: SchedulingChannel()
    :members:
    :inherited-members:

Server
~~~~~~~

.. autoclass:: Server()
    :members:

ServerSubscriptionTier
~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: ServerSubscriptionTier()
    :members:

StreamChannel
~~~~~~~~~~~~~~

.. autoclass:: StreamChannel()
    :members:
    :inherited-members:

Thread
~~~~~~~

.. autoclass:: Thread()
    :members:
    :inherited-members:

User
~~~~~

.. autoclass:: User()
    :members:
    :inherited-members:

VoiceChannel
~~~~~~~~~~~~~

.. autoclass:: VoiceChannel()
    :members:
    :inherited-members:

Data Classes
-------------

Below are some classes that primarily just wrap data. You are able to create
most of these yourself.

Embed
~~~~~~

.. autoclass:: Embed()
    :members:

Colour
~~~~~~~

.. autoclass:: Colour()
    :members:

Object
~~~~~~~

.. autoclass:: Object()
    :members:

Permissions
~~~~~~~~~~~~

.. autoclass:: Permissions()
    :members:

RawReactionActionEvent
~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: RawReactionActionEvent()
    :members:

RepeatInfo
~~~~~~~~~~~

.. autoclass:: RepeatInfo()
    :members:

SocialLink
~~~~~~~~~~~

.. autoclass:: SocialLink()
    :members:

Status
~~~~~~~

.. autoclass:: Status()
    :members:

Exceptions
-----------

.. autoexception:: GuildedException

.. autoexception:: ClientException

.. autoexception:: HTTPException

.. autoexception:: BadRequest

.. autoexception:: Forbidden

.. autoexception:: NotFound

.. autoexception:: ImATeapot

.. autoexception:: TooManyRequests

.. autoexception:: GuildedServerError

.. autoexception:: InvalidArgument

.. _api_exception_hierarchy:

Hierarchy
~~~~~~~~~~

* :exc:`Exception`

    * :exc:`GuildedException`

        * :exc:`ClientException`

            * :exc:`InvalidArgument`

        * :exc:`HTTPException`

            * :exc:`BadRequest`
            * :exc:`Forbidden`
            * :exc:`NotFound`
            * :exc:`ImATeapot`
            * :exc:`TooManyRequests`
            * :exc:`GuildedServerError`
