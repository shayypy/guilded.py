asyncio.Task helpers - ``ext.tasks``
=====================================

``guilded.ext.tasks`` may be used identically to discord.py's ``discord.ext.tasks``.
From `discord.py's documentation <https://discordpy.readthedocs.io/en/latest/ext/tasks/index.html>`_:

    One of the most common operations when making a bot is having a loop run
    in the background at a specified interval. This pattern is very common but
    has a lot of things you need to look out for:

    - How do I handle :exc:`asyncio.CancelledError`?

    - What do I do if the internet goes out?

    - What is the maximum number of seconds I can sleep anyway?

    The goal of this extension is to abstract all these worries away from you.

.. toctree::
    :maxdepth: 2

    recipes
    api
