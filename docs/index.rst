.. guilded.py documentation master file, created by
   sphinx-quickstart on Tue Apr 13 18:59:34 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. role:: strike
    :class: strike

Welcome to guilded.py
======================

guilded.py is an easy to use, asynchronous API wrapper for Guilded's user and
bot APIs, based heavily on the design of discord.py to make migrating as easy
as possible. Much of this documentation paraphrases or includes content
directly from discord.py's own documentation.

**Features:**

- Modern Pythonic API using ``async``\/``await`` syntax
- :strike:`Sane rate limit handling that prevents 429s` Guilded does not return rate limit headers outside of a Retry-After on 429 responses, so in this event, that header is used.
- Implements 100% of the Guilded API
- Command extension to aid with bot creation
- Easy to use with an object oriented design
- Based on the design of discord.py for ease of transferring

Getting Started
----------------

These pages provide some help to new users of the library.

.. toctree::
    :maxdepth: 1

    gettingstarted
    accounts
    discordpy

Support
--------

If you're having trouble with something, these resources might help.

- If you're looking for something specific, try the :ref:`index <genindex>` or :ref:`searching <search>`.
- Join the `guilded.py server <https://guilded.gg/gpy>`_.
- Report bugs in the :resource:`issue tracker <issues>`.

Extensions
-----------

.. toctree::
    :maxdepth: 1

    ext/commands/index.rst
    ext/tasks/index.rst

Reference Pages
----------------

.. toctree::
    :maxdepth: 1

    api
    Commands Extension API Reference <ext/commands/api.rst>
    Tasks Extension API Reference <ext/tasks/api.rst>

News
-----

Visit `the #updates blog feed on the Guilded API server <https://www.guilded.gg/guilded-api/blog/updates>`_.
