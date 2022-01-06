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

import io
import os
import re
from typing import Any, Optional, Tuple, Union
from urllib.parse import quote_plus
import yarl

from .errors import GuildedException, InvalidArgument


VALID_STATIC_FORMATS = frozenset({'jpeg', 'jpg', 'webp', 'png'})
VALID_ASSET_FORMATS = VALID_STATIC_FORMATS | {'gif', 'apng'}
VALID_BANNER_SIZES = frozenset({'HeroMd', 'Hero'})
VALID_ASSET_SIZES = {'Small', 'Medium', 'Large'} | VALID_BANNER_SIZES

__all__ = (
    'Asset',
)


def strip_cdn_url(url: str) -> str:
    """Returns the identifying key from an entire CDN URL. This exists because
    the API returns full URLs instead of only hashes/names, but we want to be
    able to modify size and format freely."""
    return re.sub(
        r'^(?:\/asset)?\/([a-zA-Z]+)\/|(?:-(Small|Medium|Large|HeroMd|Hero|Full))?\.(webp|jpeg|jpg|png|gif|apng)(?:\?.+)?$',
        '',
        url.replace(Asset.AWS_BASE, '').replace(Asset.BASE, '').replace('https://www.guilded.gg', '')
        # Any of these three bases, if not more, could be used, so we just try to remove all of them
    )


def convert_int_size(size: int, *, banner: bool = False) -> Optional[str]:
    """Converts an integer passed to Asset.with_size or Asset.replace to a
    Guilded-compliant size for discord.py compatibility."""
    if not size & (size - 1) and 4096 >= size >= 16:
        if size >= 1024:
            return 'Hero' if banner else 'Large'
        elif 1024 > size >= 512:
            return 'HeroMd' if banner else 'Medium'
        elif 0 <= size < 512:
            return 'HeroMd' if banner else 'Small'


class AssetMixin:
    url: str
    _state: Optional[Any]

    async def read(self) -> bytes:
        """|coro|

        Retrieves the content of this asset as a :class:`bytes` object.

        Raises
        ------
        GuildedException
            There was no internal connection state.
        HTTPException
            Downloading the asset failed.
        NotFound
            The asset was deleted.

        Returns
        -------
        :class:`bytes`
            The content of the asset.
        """
        if self._state is None:
            raise GuildedException('Invalid state (none provided)')

        return await self._state.http.read_filelike_data(self)

    async def save(self, fp: Union[str, bytes, os.PathLike, io.BufferedIOBase], *, seek_begin: bool = True) -> int:
        """|coro|

        Saves this asset into a file-like object.

        Parameters
        ----------
        fp: Union[:class:`io.BufferedIOBase`, :class:`os.PathLike`]
            The file-like object to save this attachment to or the filename
            to use. If a filename is passed then a file is created with that
            filename and used instead.
        seek_begin: :class:`bool`
            Whether to seek to the beginning of the file after saving is
            successfully done.

        Raises
        ------
        GuildedException
            There was no internal connection state.
        HTTPException
            Downloading the asset failed.
        NotFound
            The asset was deleted.

        Returns
        --------
        :class:`int`
            The number of bytes written.
        """

        data = await self.read()
        if isinstance(fp, io.BufferedIOBase):
            written = fp.write(data)
            if seek_begin:
                fp.seek(0)
            return written
        else:
            with open(fp, 'wb') as f:
                return f.write(data)

    async def bytesio(self):
        """|coro|

        Fetches the raw data of this asset and wraps it in a
        :class:`io.BytesIO` object.

        Raises
        ------
        GuildedException
            There was no internal connection state.
        HTTPException
            Downloading the asset failed.
        NotFound
            The asset was deleted.

        Returns
        --------
        :class:`io.BytesIO`
            The asset as a ``BytesIO`` object.
        """
        data = await self.read()
        return io.BytesIO(data)


class Asset(AssetMixin):
    """Represents an asset in Guilded.

    .. container:: operations

        .. describe:: x == y

            Checks if two assets are equal (have the same URL).

        .. describe:: x != y

            Checks if two assets are not equal.

        .. describe:: str(x)

            Returns the URL of the asset.

        .. describe:: len(x)

            Returns the length of the asset's URL.

        .. describe:: bool(x)

            Returns ``True`` if the asset has a URL.
    """

    __slots__: Tuple[str, ...] = (
        '_state',
        '_url',
        '_animated',
        '_key',
    )

    BASE = 'https://img.guildedcdn.com'
    AWS_BASE = 'https://s3-us-west-2.amazonaws.com/www.guilded.gg'

    def __init__(self, state, *, url: str, key: str, animated: bool = False, banner: bool = False):
        self._state = state
        self._url = url
        self._animated = animated
        self._key = key
        self._banner = banner

    @classmethod
    def _from_default_user_avatar(cls, state, number: int):
        key = f'profile_{number}'
        return cls(
            state,
            url=f'{cls.BASE}/asset/DefaultUserAvatars/{key}.png',
            key=key,
        )

    @classmethod
    def _from_user_avatar(cls, state, image_hash: str):
        image_hash = strip_cdn_url(image_hash)
        return cls(
            state,
            url=f'{cls.BASE}/UserAvatar/{image_hash}-Large.png',
            key=image_hash,
        )

    @classmethod
    def _from_user_banner(cls, state, image_hash: str):
        image_hash = strip_cdn_url(image_hash)
        return cls(
            state,
            url=f'{cls.BASE}/UserBanner/{image_hash}-Hero.png',
            key=image_hash,
            banner=True,
        )

    @classmethod
    def _from_team_avatar(cls, state, image_hash: str):
        image_hash = strip_cdn_url(image_hash)
        return cls(
            state,
            url=f'{cls.BASE}/TeamAvatar/{image_hash}-Large.png',
            key=image_hash,
        )

    @classmethod
    def _from_team_banner(cls, state, image_hash: str):
        image_hash = strip_cdn_url(image_hash)
        return cls(
            state,
            url=f'{cls.BASE}/TeamBanner/{image_hash}-Hero.png',
            key=image_hash,
            banner=True,
        )

    @classmethod
    def _from_group_avatar(cls, state, image_hash: str):
        image_hash = strip_cdn_url(image_hash)
        return cls(
            state,
            url=f'{cls.BASE}/GroupAvatar/{image_hash}-Large.png',
            key=image_hash,
        )

    @classmethod
    def _from_group_banner(cls, state, image_hash: str):
        image_hash = strip_cdn_url(image_hash)
        return cls(
            state,
            url=f'{cls.BASE}/GroupBanner/{image_hash}-Large.png',
            key=image_hash,
        )

    @classmethod
    def _from_custom_reaction(cls, state, image_hash: str, animated: bool = False):
        image_hash = strip_cdn_url(image_hash)
        format = 'apng' if animated else 'webp'
        return cls(
            state,
            url=f'{cls.BASE}/CustomReaction/{image_hash}-Full.{format}',
            key=image_hash,
            animated=animated,
        )

    @classmethod
    def _from_guilded_stock_reaction(cls, state, name: str, animated: bool = False):
        format = 'apng' if animated else 'webp'
        name = quote_plus(name)
        return cls(
            state,
            url=f'{cls.BASE}/asset/Emojis/Custom/{name}.{format}',
            key=name,
            animated=animated,
        )

    @classmethod
    def _from_unicode_stock_reaction(cls, state, name: str, animated: bool = False):
        format = 'apng' if animated else 'webp'
        name = quote_plus(name)
        return cls(
            state,
            url=f'{cls.BASE}/asset/Emojis/{name}.{format}',
            key=name,
            animated=animated,
        )

    @classmethod
    def _from_default_bot_avatar(cls, state, url: str):
        name = strip_cdn_url(url)
        return cls(
            state,
            url=f'{cls.BASE}/asset/DefaultBotAvatars/{name}.png',
            key=name,
        )

    def __str__(self) -> str:
        return self._url

    def __len__(self) -> int:
        return len(self._url)

    def __repr__(self):
        shorten = self._url.replace(self.BASE, '')
        return f'<Asset url={shorten!r}>'

    def __eq__(self, other):
        return isinstance(other, Asset) and self._url == other._url

    def __hash__(self):
        return hash(self._url)

    @property
    def url(self) -> str:
        """:class:`str`: The underlying URL of the asset."""
        return self._url

    @property
    def key(self) -> str:
        """:class:`str`: The identifying key of the asset."""
        return self._key

    @property
    def aws_url(self) -> str:
        """:class:`str`: The underlying URL of the asset on AWS."""
        return self._url.replace(self.BASE, self.AWS_BASE)

    def is_animated(self) -> bool:
        """:class:`bool`: Returns whether the asset is animated."""
        return self._animated

    def replace(
        self,
        *,
        size: str = None,
        format: str = None,
        static_format: str = None,
    ):
        """Returns a new asset with the passed components replaced.

        Parameters
        -----------
        size: :class:`str`
            The new size of the asset. Must be one of
            'Small', 'Medium', 'Large', or 'HeroMd' or 'Hero' if it's a banner.
        format: :class:`str`
            The new format to change it to. Must be one of
            'webp', 'jpeg', 'jpg', 'png', or 'gif' or 'apng' if it's animated.
        static_format: :class:`str`
            The new format to change it to if the asset isn't animated.
            Must be either 'webp', 'jpeg', 'jpg', or 'png'.

        Raises
        -------
        InvalidArgument
            An invalid size or format was passed.

        Returns
        --------
        :class:`.Asset`
            The newly updated asset.
        """
        url = yarl.URL(self._url)
        path, extension = os.path.splitext(url.path)
        extension = extension.lstrip('.')
        current_size = url.path.split('-')[1].replace(f'.{extension}', '')

        if format is not None:
            if self._animated:
                if format not in VALID_ASSET_FORMATS:
                    raise InvalidArgument(f'format must be one of {VALID_ASSET_FORMATS}')
            else:
                if format not in VALID_STATIC_FORMATS:
                    raise InvalidArgument(f'format must be one of {VALID_STATIC_FORMATS}')
            url = url.with_path(f'{path}.{format}')
            extension = format

        if static_format is not None and not self._animated:
            if static_format not in VALID_STATIC_FORMATS:
                raise InvalidArgument(f'static_format must be one of {VALID_STATIC_FORMATS}')
            url = url.with_path(f'{path}.{static_format}')
            extension = static_format

        if size is not None:
            if isinstance(size, int):
                size = convert_int_size(size, banner=self._banner)
            if self._banner:
                if size not in VALID_BANNER_SIZES:
                    raise InvalidArgument(f'size must be one of {VALID_BANNER_SIZES} or be a power of 2 between 16 and 4096')
            else:
                if size not in VALID_ASSET_SIZES:
                    raise InvalidArgument(f'size must be one of {VALID_ASSET_SIZES} or be a power of 2 between 16 and 4096')

            url = url.with_path(f'{path.replace(current_size, size)}.{extension}')

        url = str(url)
        return Asset(state=self._state, url=url, key=self._key, animated=self._animated, banner=self._banner)

    def with_size(self, size: str):
        """Returns a new asset with the specified size.

        Parameters
        ------------
        size: :class:`str`
            The new size of the asset. Must be one of
            'Small', 'Medium', 'Large', or 'HeroMd' or 'Hero' if it's a banner.

        Raises
        -------
        InvalidArgument
            The asset had an invalid size.

        Returns
        --------
        :class:`.Asset`
            The newly updated asset.
        """
        if isinstance(size, int):
            size = convert_int_size(size, banner=self._banner)
        if self._banner:
            if size not in VALID_BANNER_SIZES:
                raise InvalidArgument(f'size must be one of {VALID_BANNER_SIZES} or be a power of 2 between 16 and 4096')
        else:
            if size not in VALID_ASSET_SIZES:
                raise InvalidArgument(f'size must be one of {VALID_ASSET_SIZES} or be a power of 2 between 16 and 4096')

        url = yarl.URL(self._url)
        path, extension = os.path.splitext(url.path)
        extension = extension.lstrip('.')
        current_size = url.path.split('-')[1].replace(f'.{extension}', '')
        url = str(url.with_path(f'{path.replace(current_size, size)}.{extension}'))
        return Asset(state=self._state, url=url, key=self._key, animated=self._animated)

    def with_format(self, format: str):
        """Returns a new asset with the specified format.

        Parameters
        ------------
        format: :class:`str`
            The new format of the asset.

        Raises
        -------
        InvalidArgument
            The asset had an invalid format.

        Returns
        --------
        :class:`.Asset`
            The newly updated asset.
        """

        if self._animated:
            if format not in VALID_ASSET_FORMATS:
                raise InvalidArgument(f'format must be one of {VALID_ASSET_FORMATS}')
        else:
            if format not in VALID_STATIC_FORMATS:
                raise InvalidArgument(f'format must be one of {VALID_STATIC_FORMATS}')

        url = yarl.URL(self._url)
        path, _ = os.path.splitext(url.path)
        url = str(url.with_path(f'{path}.{format}'))
        return Asset(state=self._state, url=url, key=self._key, animated=self._animated)

    def with_static_format(self, format: str):
        """Returns a new asset with the specified static format.

        This only changes the format if the underlying asset is
        not animated. Otherwise, the asset is not changed.

        Parameters
        ------------
        format: :class:`str`
            The new static format of the asset.

        Raises
        -------
        InvalidArgument
            The asset had an invalid format.

        Returns
        --------
        :class:`.Asset`
            The newly updated asset.
        """

        if self._animated:
            return self
        return self.with_format(format)
