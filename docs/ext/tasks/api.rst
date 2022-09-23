.. currentmodule:: guilded.ext.tasks

API Reference
==============

Loop
-----

.. autoclass:: Loop()
    :members:
    :special-members: __call__
    :exclude-members: after_loop, before_loop, error

    .. automethod:: Loop.after_loop()
        :decorator:

    .. automethod:: Loop.before_loop()
        :decorator:

    .. automethod:: Loop.error()
        :decorator:

loop
-----

.. autofunction:: loop
