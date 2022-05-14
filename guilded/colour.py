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

from __future__ import annotations

import colorsys
import random
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing_extensions import Self


__all__ = (
    'Colour',
    'Color',
)


def parse_hex_number(argument: str) -> Colour:
    from .colour import Colour

    arg = ''.join([i * 2 for i in argument]) if len(argument) == 3 else argument
    try:
        value = int(arg, base=16)
        if not (0 <= value <= 0xFFFFFF):
            raise ValueError(argument)
    except ValueError as e:
        raise ValueError(argument) from e
    else:
        return Colour(value=value)


def parse_rgb_number(number: str) -> int:
    if number[-1] == '%':
        value = float(number[:-1])
        if not (0 <= value <= 100):
            raise ValueError('rgb percentage can only be between 0 to 100')
        return round(255 * (value / 100))

    value = int(number)
    if not (0 <= value <= 255):
        raise ValueError('rgb number can only be between 0 to 255')
    return value


RGB_REGEX = re.compile(r'rgb\s*\((?P<r>[0-9.]+%?)\s*,\s*(?P<g>[0-9.]+%?)\s*,\s*(?P<b>[0-9.]+%?)\s*\)')

def parse_rgb(argument: str, *, regex: re.Pattern[str] = RGB_REGEX) -> Colour:
    from .colour import Colour

    match = regex.match(argument)
    if match is None:
        raise ValueError('invalid rgb syntax found')

    red = parse_rgb_number(match.group('r'))
    green = parse_rgb_number(match.group('g'))
    blue = parse_rgb_number(match.group('b'))
    return Colour.from_rgb(red, green, blue)


class Colour:
    """Represents a colour in Guilded, such as in embeds or roles.
    This class is similar to a (red, green, blue) :class:`tuple`.

    There is an alias for this called Color.

    .. container:: operations

        .. describe:: x == y

             Checks if two colours are equal.

        .. describe:: x != y

             Checks if two colours are not equal.

        .. describe:: hash(x)

             Return the colour's hash.

        .. describe:: str(x)

             Returns the hex format for the colour.

    Attributes
    ------------
    value: :class:`int`
        The raw integer colour value.
    """

    __slots__ = ('value',)

    def __init__(self, value: int):
        if not isinstance(value, int):
            raise TypeError('Expected int parameter, received %s instead.' % value.__class__.__name__)

        self.value = value

    def _get_byte(self, byte: int) -> int:
        return (self.value >> (8 * byte)) & 0xff

    def __eq__(self, other) -> bool:
        return isinstance(other, Colour) and self.value == other.value

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)

    def __str__(self) -> str:
        return '#{:0>6x}'.format(self.value)

    def __int__(self) -> int:
        return self.value

    def __repr__(self) -> str:
        return f'<Colour value={self.value}>'

    def __hash__(self) -> int:
        return hash(self.value)

    @property
    def r(self):
        """:class:`int`: Returns the red component of the colour."""
        return self._get_byte(2)

    @property
    def g(self):
        """:class:`int`: Returns the green component of the colour."""
        return self._get_byte(1)

    @property
    def b(self):
        """:class:`int`: Returns the blue component of the colour."""
        return self._get_byte(0)

    def to_rgb(self):
        """Tuple[:class:`int`, :class:`int`, :class:`int`]: Returns an (r, g, b) tuple representing the colour."""
        return (self.r, self.g, self.b)

    @classmethod
    def from_rgb(cls, r, g, b) -> Self:
        """Constructs a :class:`Colour` from an RGB tuple."""
        return cls((r << 16) + (g << 8) + b)

    @classmethod
    def from_hsv(cls, h, s, v) -> Self:
        """Constructs a :class:`Colour` from an HSV tuple."""
        rgb = colorsys.hsv_to_rgb(h, s, v)
        return cls.from_rgb(*(int(x * 255) for x in rgb))

    @classmethod
    def from_str(cls, value: str) -> Self:
        """Constructs a :class:`Colour` from a string.

        The following formats are accepted:

        - ``0x<hex>``
        - ``#<hex>``
        - ``0x#<hex>``
        - ``rgb(<number>, <number>, <number>)``

        Like CSS, ``<number>`` can be either 0-255 or 0-100% and ``<hex>`` can be
        either a 6 digit hex number or a 3 digit hex shortcut (e.g. #fff).

        Raises
        -------
        ValueError
            The string could not be converted into a colour.
        """

        if value[0] == '#':
            return parse_hex_number(value[1:])

        if value[0:2] == '0x':
            rest = value[2:]
            # Legacy backwards compatible syntax
            if rest.startswith('#'):
                return parse_hex_number(rest[1:])
            return parse_hex_number(rest)

        arg = value.lower()
        if arg[0:3] == 'rgb':
            return parse_rgb(arg)

        raise ValueError('unknown colour format given')

    @classmethod
    def default(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0``."""
        return cls(0)

    @classmethod
    def random(cls, *, seed=None):
        """A factory method that returns a :class:`Colour` with a random hue.
        .. note::
            The random algorithm works by choosing a colour with a random hue but
            with maxed out saturation and value.
        Parameters
        ------------
        seed: Optional[Union[:class:`int`, :class:`str`, :class:`float`, :class:`bytes`, :class:`bytearray`]]
            The seed to initialize the RNG with. If ``None`` is passed the default RNG is used. 
        """
        rand = random if seed is None else random.Random(seed)
        return cls.from_hsv(rand.random(), 1, 1)

    @classmethod
    def teal(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x1abc9c``."""
        return cls(0x1abc9c)

    @classmethod
    def dark_teal(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x11806a``."""
        return cls(0x11806a)

    @classmethod
    def green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x2ecc71``."""
        return cls(0x2ecc71)

    @classmethod
    def dark_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x1f8b4c``."""
        return cls(0x1f8b4c)

    @classmethod
    def blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x3498db``."""
        return cls(0x3498db)

    @classmethod
    def dark_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x206694``."""
        return cls(0x206694)

    @classmethod
    def purple(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x9b59b6``."""
        return cls(0x9b59b6)

    @classmethod
    def dark_purple(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x71368a``."""
        return cls(0x71368a)

    @classmethod
    def magenta(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xe91e63``."""
        return cls(0xe91e63)

    @classmethod
    def dark_magenta(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xad1457``."""
        return cls(0xad1457)

    @classmethod
    def gold(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xf1c40f``."""
        return cls(0xf1c40f)

    @classmethod
    def dark_gold(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xc27c0e``."""
        return cls(0xc27c0e)

    @classmethod
    def orange(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xe67e22``."""
        return cls(0xe67e22)

    @classmethod
    def dark_orange(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xa84300``."""
        return cls(0xa84300)

    @classmethod
    def red(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xe74c3c``."""
        return cls(0xe74c3c)

    @classmethod
    def dark_red(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x992d22``."""
        return cls(0x992d22)

    @classmethod
    def lighter_grey(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x95a5a6``."""
        return cls(0x95a5a6)

    lighter_gray = lighter_grey

    @classmethod
    def dark_grey(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x607d8b``."""
        return cls(0x607d8b)

    dark_gray = dark_grey

    @classmethod
    def light_grey(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x979c9f``."""
        return cls(0x979c9f)

    light_gray = light_grey

    @classmethod
    def darker_grey(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x546e7a``."""
        return cls(0x546e7a)

    darker_gray = darker_grey

    @classmethod
    def gilded(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xf5c400``."""
        return cls(0xf5c400)

    @classmethod
    def greyple(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x99aab5``."""
        return cls(0x99aab5)

    @classmethod
    def dark_theme(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x373943``.
        This will appear transparent in chat."""
        return cls(0x373943)

    @classmethod
    def dark_theme_embed(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x32343d``.
        This will appear to blend with embed backgrounds."""
        return cls(0x32343d)

    @classmethod
    def black(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x111820``."""
        return cls(0x111820)

    @classmethod
    def grey(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x36363D``."""
        return cls(0x36363D)

    gray = grey

Color = Colour
