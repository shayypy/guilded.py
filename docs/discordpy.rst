.. currentmodule:: guilded

Discord.py Differences
=======================

guilded.py was designed with discord.py compatibility in mind; You shouldn't
have to rewrite your bot to make it Guilded-ready. The libraries are not
identical, though--here are some notable differences.

These lists are not exhaustive.

Breaking
---------

Below is a list of "breaking" differences between discord.py and guilded.py;
If you use any of the below methods, attributes, or parameters, you **must** change your
code in order for your bot to work with this library.

Modified
~~~~~~~~~

**Guilded/Discord API differences**

* All ``.id``\s are `strings or non-snowflake integers <https://guildedapi.com/reference/#ids>`_.
* :meth:`.Webhook.fetch`,
  :meth:`.Webhook.edit`,
  :meth:`.Webhook.delete`,
  :meth:`.WebhookMessage.delete`,
  :meth:`.Webhook.delete_message`,
  and :meth:`.Webhook.fetch_message`
  require the webhook instance to have authentication info associated with it
  as webhooks cannot perform these actions on their own.
* :meth:`.Server.webhooks` cannot fetch the required information in a single request, so it makes multiple for each compatible channel.
* :meth:`.Webhook.fetch`, :meth:`.Webhook.edit`, and :meth:`.Webhook.delete` require
  :attr:`.Webhook.server_id` to be filled or for you to provide the ``server``
  parameter to the respective method.
* :meth:`.Client.fetch_invite` does not accept URLs or vanity codes.
* :meth:`.Client.fetch_servers` returns a list of :class:`.Server` instead of an async iterator.
* :meth:`.Server.fetch_channel` does not accept category IDs. Use :meth:`.Server.fetch_category` instead.

Not present
~~~~~~~~~~~~

**Methods**

* ``Client.add_view``
* ``Client.application_info``
* ``Client.before_identify_hook``
* ``Client.change_presence``
* ``Client.create_dm``
* ``Client.create_guild`` (``create_server``)
* ``Client.delete_invite``
* ``Client.fetch_guilds``
* ``Client.fetch_premium_sticker_packs``
* ``Client.fetch_stage_instance``
* ``Client.fetch_sticker``
* ``Client.fetch_template``
* ``Client.fetch_webhook``
* ``Client.fetch_widget``
* ``Client.get_partial_messageable``
* ``Client.get_stage_instance``
* ``Client.get_sticker``
* ``Client.is_ws_ratelimited``
* ``Guild.edit``
* ``Guild.delete``
* ``Category.clone``
* ``Category.invites``
* ``Category.move``
* ``Category.overwrites_for``
* ``Category.permissions_for``
* ``Category.set_permissions``

**Parameters**

* :meth:`Server.create_webhook`, :meth:`ChatChannel.create_webhook`, :meth:`ListChannel.create_webhook`: ``avatar``, ``reason``

**Classes**

* Clients:

  * :class:`~discord.AutoShardedClient`
  * :class:`~discord.ext.commands.AutoShardedBot`

* Application Info:

  * :class:`~discord.AppInfo`
  * :class:`~discord.PartialAppInfo`
  * :class:`~discord.AppInstallParams`
  * :class:`~discord.Team`
  * :class:`~discord.TeamMember`

* `Voice Related <https://discordpy.readthedocs.io/en/latest/api.html#voice-related>`_
* `Audit Log Data <https://discordpy.readthedocs.io/en/latest/api.html#audit-log-data>`_

* Webhooks:

  * :class:`~discord.SyncWebhook`
  * :class:`~discord.SyncWebhookMessage`

* Abstract Base Classes:

  * :class:`~discord.abc.Snowflake`
  * :class:`~discord.abc.PrivateChannel`
  * :class:`~discord.abc.Connectable`

* Models:

  * :class:`~discord.AutoMod`
  * :class:`~discord.DeletedReferencedMessage`
  * :class:`~discord.ScheduledEvent`
  * :class:`~discord.Integration`
  * :class:`~discord.Spotify`
  * :class:`~discord.VoiceState`
  * :class:`~discord.PartialEmoji`
  * :class:`~discord.RoleTags`
  * :class:`~discord.PartialMessageable`
  * :class:`~discord.ThreadMember`
  * :class:`~discord.StageChannel`
  * :class:`~discord.StageInstance`
  * :class:`~discord.GroupChannel`
  * :class:`~discord.PartialInviteGuild`
  * :class:`~discord.PartialInviteChannel`
  * :class:`~discord.Template`
  * :class:`~discord.WelcomeScreen`
  * :class:`~discord.WelcomeChannel`
  * :class:`~discord.WidgetChannel`
  * :class:`~discord.WidgetMember`
  * :class:`~discord.Widget`
  * :class:`~discord.StickerPack`
  * :class:`~discord.StickerItem`
  * :class:`~discord.Sticker`
  * :class:`~discord.StandardSticker`
  * :class:`~discord.GuildSticker`
  * :class:`~discord.RawMessageDeleteEvent`
  * :class:`~discord.RawBulkMessageDeleteEvent`
  * :class:`~discord.RawMessageUpdateEvent`
  * :class:`~discord.RawReactionClearEvent`
  * :class:`~discord.RawReactionClearEmojiEvent`
  * :class:`~discord.RawIntegrationDeleteEvent`
  * :class:`~discord.RawThreadUpdateEvent`
  * :class:`~discord.RawThreadMembersUpdate`
  * :class:`~discord.RawThreadDeleteEvent`
  * :class:`~discord.RawTypingEvent`
  * :class:`~discord.RawMemberRemoveEvent`
  * :class:`~discord.PartialWebhookGuild`
  * :class:`~discord.PartialWebhookChannel`

* Data Classes:

  * :class:`~discord.AllowedMentions`
  * :class:`~discord.MessageReference`
  * :class:`~discord.PartialMessage`
  * :class:`~discord.MessageApplication`
  * :class:`~discord.Intents`
  * :class:`~discord.MemberCacheFlags`
  * :class:`~discord.ApplicationFlags`
  * :class:`~discord.ChannelFlags`
  * :class:`~discord.AutoModPresets`
  * :class:`~discord.AutoModRuleAction`
  * :class:`~discord.AutoModTrigger`
  * :class:`~discord.BaseActivity`
  * :class:`~discord.Activity`
  * :class:`~discord.Streaming`
  * :class:`~discord.CustomActivity`
  * :class:`~discord.PermissionOverwrite`
  * :class:`~discord.ShardInfo`
  * :class:`~discord.SystemChannelFlags`
  * :class:`~discord.MessageFlags`
  * :class:`~discord.PublicUserFlags`

* All of ``ui.*``
* All of ``app_commands.*``

Non-breaking
-------------

Below is a list of non-"breaking" differences between discord.py and
guilded.py; You will be able to use guilded.py without complying with
any of the below changes. This list is not exhaustive.

* The ``on_webhooks_update`` event does not exist; Use :func:`guilded.on_webhook_create`
  and :func:`guilded.on_raw_webhook_update` / :func:`guilded.on_webhook_update` instead.
