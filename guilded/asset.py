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

import datetime
import io
import os
import re
from typing import TYPE_CHECKING, Any, List, Optional, Tuple, Union
from urllib.parse import parse_qs, parse_qsl, quote_plus, urlencode, urlparse
import yarl

from .errors import GuildedException, InvalidArgument

if TYPE_CHECKING:
    from typing_extensions import Self

    from .types.asset import UrlSignature


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
    # We were having issues matching `cdn.gilcdn` so we just take the origin
    # out of the equation.
    path = yarl.URL(url).path
    match = re.search(r'\/(?P<key>[a-zA-Z0-9]+)(?:-(?P<size>\w+))?\.(?P<format>[a-z]+)', path)
    if match:
        return match.group('key')
    raise ValueError(f'Invalid CDN URL: {url}')


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


def url_with_signature(url: str, signature: str) -> str:
    parsed = yarl.URL(url)
    return str(parsed.update_query(parse_qs(signature)))


class AssetMixin:
    url: str
    _state: Optional[Any]

    @property
    def signed(self) -> bool:
        parsed = parse_qs(urlparse(self.url).query)
        # Unix time in seconds
        expires = parsed.get("Expires")
        if not expires or not parsed.get("Signature"):
            return False

        try:
            remaining = int(expires[0]) - datetime.datetime.now(tz=datetime.timezone.utc).timestamp()
            return remaining > 5
        except:
            return False

    async def sign(self) -> Self:
        """|coro|

        Signs the asset. This is required to read assets as of June 30th,
        2024. This method modifies the Asset in place with its signed URL
        and consequently causes :attr:`.signed` to return ``True``, until
        the signature expiry is reached.

        You may do this once per day per asset and are expected to store
        the contents of assets after having signed and read them. guilded.py
        provides no assistance with asset caching, but will automatically sign
        URLs when necessary.

        .. versionadded:: 1.13.1

        Raises
        -------
        GuildedException
            The asset is already signed or there is no internal connection
            state.
        """
        if self._state is None:
            raise GuildedException('Invalid state (none provided)')
        if self.signed:
            raise GuildedException('Asset is already signed')

        valid = await self._state.refresh_signature()
        if valid:
            self.url = url_with_signature(self.url, self._state.cdn_qs)
        else:
            urls: List[UrlSignature] = await self._state.create_url_signatures([self.url])
            if not urls[0].get("signature") and self._state.cdn_qs:
                # We may have just received a valid token with the sign
                # request that refresh_signature was unable to retrieve.
                self.url = url_with_signature(self.url, self._state.cdn_qs)
            else:
                self.url = urls[0].get("signature") or urls[0]["url"]

        return self

    async def read(self) -> bytes:
        """|coro|

        Retrieves the content of this asset as a :class:`bytes` object.

        Raises
        -------
        GuildedException
            There was no internal connection state.
        HTTPException
            Downloading the asset failed.
        NotFound
            The asset was deleted.

        Returns
        --------
        :class:`bytes`
            The content of the asset.
        """
        if self._state is None:
            raise GuildedException('Invalid state (none provided)')
        if not self.signed:
            await self.sign()

        return await self._state.read_filelike_data(self)

    async def save(self, fp: Union[str, bytes, os.PathLike, io.BufferedIOBase], *, seek_begin: bool = True) -> int:
        """|coro|

        Saves this asset into a file-like object.

        Parameters
        -----------
        fp: Union[:class:`io.BufferedIOBase`, :class:`os.PathLike`]
            The file-like object to save this attachment to or the filename
            to use. If a filename is passed then a file is created with that
            filename and used instead.
        seek_begin: :class:`bool`
            Whether to seek to the beginning of the file after saving is
            successfully done.

        Raises
        -------
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
        -------
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

    BASE = 'https://cdn.gldcdn.com'
    AWS_BASE = 'https://s3-us-west-2.amazonaws.com/www.guilded.gg'

    def __init__(
        self,
        state,
        *,
        url: str,
        key: str,
        animated: bool = False,
        maybe_animated: bool = False,
        banner: bool = False,
    ):
        self._state = state
        self._url = url
        if not state.cdn_qs_expired:
            # Avoid the signing dance if possible. This makes it possible for
            # users to use URLs straight from the library without having to
            # read (and thus sign) them first.
            self._url = url_with_signature(self._url, state.cdn_qs)

        # Force unity if we know a value of one that should affect the other
        if animated:
            maybe_animated = True
        if not maybe_animated:
            animated = False

        self._animated = animated
        self._maybe_animated = maybe_animated
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
    def _from_user_avatar(cls, state, image_url: str):
        animated = 'ia=1' in image_url
        maybe_animated = '.webp' in image_url
        format = 'webp' if animated or maybe_animated else 'png'
        image_hash = strip_cdn_url(image_url)
        return cls(
            state,
            url=f'{cls.BASE}/UserAvatar/{image_hash}-Large.{format}',
            key=image_hash,
            animated=animated,
            maybe_animated=maybe_animated,
        )

    @classmethod
    def _from_user_banner(cls, state, image_url: str):
        image_hash = strip_cdn_url(image_url)
        return cls(
            state,
            url=f'{cls.BASE}/UserBanner/{image_hash}-Hero.png',
            key=image_hash,
            banner=True,
        )

    @classmethod
    def _from_team_avatar(cls, state, image_url: str):
        image_hash = strip_cdn_url(image_url)
        return cls(
            state,
            url=f'{cls.BASE}/TeamAvatar/{image_hash}-Large.png',
            key=image_hash,
        )

    @classmethod
    def _from_team_banner(cls, state, image_url: str):
        image_hash = strip_cdn_url(image_url)
        return cls(
            state,
            url=f'{cls.BASE}/TeamBanner/{image_hash}-Hero.png',
            key=image_hash,
            banner=True,
        )

    @classmethod
    def _from_group_avatar(cls, state, image_url: str):
        image_hash = strip_cdn_url(image_url)
        return cls(
            state,
            url=f'{cls.BASE}/GroupAvatar/{image_hash}-Large.png',
            key=image_hash,
        )

    @classmethod
    def _from_group_banner(cls, state, image_url: str):
        image_hash = strip_cdn_url(image_url)
        return cls(
            state,
            url=f'{cls.BASE}/GroupBanner/{image_hash}-Large.png',
            key=image_hash,
        )

    @classmethod
    def _from_custom_reaction(cls, state, image_url: str, animated: bool = False):
        image_hash = strip_cdn_url(image_url)
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

    @classmethod
    def _from_webhook_thumbnail(cls, state, image_url: str):
        animated = 'ia=1' in image_url
        image_hash = strip_cdn_url(image_url)
        return cls(
            state,
            url=f'{cls.BASE}/WebhookThumbnail/{image_hash}-Full.webp',
            key=image_hash,
            animated=animated,
            maybe_animated=True,
        )

    @classmethod
    def _from_media_thumbnail(cls, state, url: str):
        image_hash = strip_cdn_url(url)
        return cls(
            state,
            url=url,
            key=image_hash,
        )
        # We use the original URL here because in testing I could not find an example
        # of a media thumbnail. It may be an old property that is no longer ever populated

    @classmethod
    def _from_default_asset(cls, state, name: str):
        name = quote_plus(name)
        return cls(
            state,
            url=f'{cls.BASE}/asset/Default/{name}-lg.png',
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
        """:class:`str`: The underlying URL of the asset on AWS.

        .. deprecated:: 1.13
            This type of URL should no longer be required, and it seems
            to be getting phased out by Guilded. Use :attr:`.url` instead.
        """
        return self._url.replace(self.BASE, self.AWS_BASE)

    def is_animated(self) -> bool:
        """:class:`bool`: Returns whether the asset is animated.

        .. note::

            This may return false negatives for assets like user or bot
            avatars which have no definitive indicator.
        """
        return self._animated

    def replace(
        self,
        *,
        size: str = None,
        format: str = None,
        static_format: str = None,
    ):
        """Returns a new asset with the passed components replaced.

        .. warning::

            If this asset is a user or bot avatar, you should not replace
            ``format`` because avatars uploaded after 10 May 2022 can only
            use the ``webp`` format.

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
            if self._maybe_animated:
                if format not in VALID_ASSET_FORMATS:
                    raise InvalidArgument(f'format must be one of {VALID_ASSET_FORMATS}')
            else:
                if format not in VALID_STATIC_FORMATS:
                    raise InvalidArgument(f'format must be one of {VALID_STATIC_FORMATS}')
            url = url.with_path(f'{path}.{format}')
            extension = format

        if static_format is not None and not self._maybe_animated:
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
        return Asset(state=self._state, url=url, key=self._key, animated=self._animated, maybe_animated=self._maybe_animated, banner=self._banner)

    def with_size(self, size: str):
        """Returns a new asset with the specified size.

        Parameters
        -----------
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
        return Asset(state=self._state, url=url, key=self._key, animated=self._animated, maybe_animated=self._maybe_animated)

    def with_format(self, format: str):
        """Returns a new asset with the specified format.

        .. warning::

            If this asset is a user or bot avatar, you should not use this
            method because avatars uploaded after 10 May 2022 can only use the
            ``webp`` format.

        Parameters
        -----------
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

        if self._maybe_animated:
            if format not in VALID_ASSET_FORMATS:
                raise InvalidArgument(f'format must be one of {VALID_ASSET_FORMATS}')
        else:
            if format not in VALID_STATIC_FORMATS:
                raise InvalidArgument(f'format must be one of {VALID_STATIC_FORMATS}')

        url = yarl.URL(self._url)
        path, _ = os.path.splitext(url.path)
        url = str(url.with_path(f'{path}.{format}'))
        return Asset(state=self._state, url=url, key=self._key, animated=self._animated, maybe_animated=self._maybe_animated)

    def with_static_format(self, format: str):
        """Returns a new asset with the specified static format.

        This only changes the format if the underlying asset is
        not animated. Otherwise, the asset is not changed.

        Parameters
        -----------
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

        if self._maybe_animated:
            return self
        return self.with_format(format)
