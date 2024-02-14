.. guilded.py documentation master file, created by
   sphinx-quickstart on Tue Apr 13 18:59:34 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to guilded.py
======================

guilded.py is an easy to use, asynchronous API wrapper for Guilded's user and
bot APIs, based heavily on the design of discord.py to make migrating as easy
as possible. Much of this documentation paraphrases or includes content
directly from discord.py's own documentation.

**Features:**

- Modern Pythonic API using ``async``\/``await`` syntax
- :gdocs:`Compliant rate limit backoff <http_rate_limits>`
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

Additional Extensions
~~~~~~~~~~~~~~~~~~~~~~

These packages are not included with the library and must be installed separately if you wish to use them.

- `guilded.ext.menus <https://github.com/shayypy/guilded-ext-menus>`_

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
