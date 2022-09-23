Setting up Guilded.py
======================

Requirements
-------------

guilded.py requires Python 3.8 or higher. It also requires `aiohttp <https://docs.aiohttp.org/en/stable/index.html>`_,
but pip should handle installing that for you.

Installing
-----------

You may install the library from PyPI using pip:

.. code-block:: shell

    python3 -m pip install -U guilded.py

Or if you're using Windows:

.. code-block:: shell

    py -3 -m pip install -U guilded.py

Logging
--------

guilded.py uses Python's `logging <https://docs.python.org/3/library/logging.html#module-logging>`_
module to log errors, warnings, and other debug information to the program's
``stdout`` or a specified file.

Logging for guilded.py can be set up in the same manner as `a discord.py configuration <https://discordpy.readthedocs.io/en/latest/logging.html>`_,
with the obvious exception that the module is called ``guilded`` and not ``discord``\.
