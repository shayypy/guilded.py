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

from io import BytesIO


class Asset:
    """An asset in Guilded.

    .. container:: operations

        .. describe:: x == y

            Checks if two assets are equal (have the same URL and type).

        .. describe:: x != y

            Checks if two assets are not equal.

        .. describe:: str(x)

            Returns the URL of the asset.

        .. describe:: len(x)

            Returns the length of the asset's URL.

        .. describe:: bool(x)

            Returns ``True`` if the asset has a URL.

    Attributes
    -----------
    type: :class:`str`
        The type of asset, like ``profilePicture``. This is mostly for
        internal use.
    url: Optional[:class:`str`]
        The URL of the asset.
    """
    FRIENDLY = {
        'sm': 'small',
        'md': 'medium',
        'lg': 'large'
    }
    def __init__(self, type, *, state, data):
        self._state = state
        self.type = type

        self.url = data.get(self.type)
        for key, value in data.items():
            if key.startswith(self.type):
                fmt = key.replace(self.type, '', 1)
                setattr(self, self.FRIENDLY.get(fmt.lower(), fmt), Asset(self.type, state=self._state, data={}))

        if self.url is None:
            self.url = getattr(self, 'large', getattr(self, 'medium', getattr(self, 'small', getattr(self, 'png', getattr(self, 'webp', self))))).url

    def __str__(self):
        return self.url

    def __bool__(self):
        return self.url is not None

    def __len__(self):
        return len(str(self))

    def __eq__(self, other):
        return isinstance(other, Asset) and self.url is not None and other.url is not None and self.url == other.url and self.type == other.type

    async def read(self):
        """|coro|

        Fetches the raw data of this asset as a :class:`bytes`.

        Returns
        --------
        :class:`bytes`
            The raw data of this asset.
        """
        return await self._state.read_filelike_data(self)

    async def bytesio(self):
        """|coro|

        Fetches the raw data of this asset and wraps it in a
        :class:`io.BytesIO` object.

        Returns
        --------
        :class:`io.BytesIO`
            The asset as a ``BytesIO`` object.
        """
        data = await self.read()
        return BytesIO(data)
