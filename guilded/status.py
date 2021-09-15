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

import logging

log = logging.getLogger(__name__)

__all__ = (
    'TransientStatus',
    'Game'
)

class TransientStatus:
    def __init__(self, *, state, data, **extra):
        self.id = data.get('id')
        self.game_id = data.get('id')

class Game(TransientStatus):
    """A transient status representing a game. This shows up next to
    "Playing" in the client.

    .. warn::
        You cannot pass custom strings to this class. To avoid hard-coding
        every Guilded-supported game into this library as an enum, you can
        find a list of valid game IDs next to their names
        `on the API docs<https://guildedapi.com/resources/user#game-ids>`_\.

    Parameters
    -----------
    game_id: Optional[:class:`int`]
        The game's ID that this Game should represent.
    name: Optional[:class:`str`]
        The game's name that this Game should represent. Case-specific to the
        table linked above.

    Raises
    -------
    ValueError
        You passed neither ``id`` nor ``name``, or you passed an unknown game
        name.

    Attributes
    -----------
    MAPPING: :class`dict`
        The internal mapping of valid game IDs to game names. This list can be
        found externally `right here<https://github.com/GuildedAPI/datatables/blob/main/games.json>`_\.
        It is not fetched on startup, so it is recommended for you to do so
        if you prefer to pass names to this class instead of IDs.
    game_id: :class:`int`
        The game's ID.
    name: :class:`str`
        The game's name, displays in the client alongside "Playing".
    """
    MAPPING = {}
    def __init__(self, name: str = None, game_id: int = None):
        if not self.MAPPING:
            log.warning('The internal game cache is empty. Call the Client.fill_game_list coroutine to fill it automatically.')

        if game_id is None and name is None:
            raise ValueError('One of game_id, name must be specified.')

        if game_id is None:
            reverse_mapping = {name_: id_ for id_, name_ in self.MAPPING.items()}
            game_id = reverse_mapping.get(name)
            if game_id is None:
                raise ValueError('A game with that name could not be found. Refer to the list of valid games: https://guildedapi.com/resources/user#game-ids')

        self.game_id = game_id

    @property
    def name(self):
        return self.MAPPING.get(str(id))

    def __str__(self):
        return self.name
