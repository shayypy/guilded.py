.. currentmodule:: guilded

How to Create Client Accounts
==============================

At present, the bot API uses the flowbot interface as a way to manage bots. This will change in the future.

1. Navigate to the bots page in your whitelisted server and press "Create a bot".

    .. image:: /images/creating/bot-create_a_bot.png

2. Give your bot a name and click "Save changes" at the bottom-left of the interface. Don't worry about flows, you don't need to add any.

    .. image:: /images/creating/bot-name_save.png

3. Open the bot's context menu by clicking on the three dots, then select "Manage auth tokens".

    .. image:: /images/creating/bot-manage_auth_tokens.png

4. Click the "Generate token" button and copy the newly generated token.

    - Guilded will never show you this token again. You may create multiple auth tokens and delete them individually in the event that one of them gets leaked.
    - You can see when a token was last used in this auth tokens menu in case you are suspicious that it has been leaked.
      This timestamp ("Last used") exposes when an API request was last made with it, or when it was last used to connect to the gateway.

    .. image:: /images/creating/bot-generate_token.png

    .. danger::

        Obviously, do not share any auth tokens you create. This token can be used by bad actors to do *anything* that *you* can do with it.

You can now use this auth token (or any others you create) to authenticate with Guilded's bot API:

.. code-block:: python3

    client = guilded.Client()

    client.run(auth_token)

Publishing Your Bot
--------------------

Once your bot is ready to release into the wild, you can publish it by pressing "Publish" in the bot's context menu.

.. image:: /images/publishing/publish_bot.png

.. warning::

    Currently, you cannot unpublish or delete a bot once it has been published.

This will create a link that anyone can use to invite your bot to their server.
It has permissions built-in; the bot's permissions as dictated by its highest
role in the internal server will be the default permissions that users see when
they invite your bot.

.. image:: /images/publishing/published.png
