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

import asyncio
import datetime
from inspect import isawaitable as _isawaitable, signature as _signature
from operator import attrgetter
import re
from typing import Any, AsyncIterable, Callable, Coroutine, Iterable, Optional, TypeVar, Union
import unicodedata
from uuid import uuid1, UUID


GUILDED_EPOCH_DATETIME = datetime.datetime(2016, 1, 1)
GUILDED_EPOCH_ISO8601 = GUILDED_EPOCH_DATETIME.isoformat() + 'Z'
GUILDED_EPOCH = int(GUILDED_EPOCH_DATETIME.timestamp())

valid_image_extensions = ['png', 'webp', 'jpg', 'jpeg', 'gif', 'jif', 'tif', 'tiff', 'apng', 'bmp', 'svg']
valid_video_extensions = ['mp4', 'mpeg', 'mpg', 'mov', 'avi', 'wmv', 'qt', 'webm']


T = TypeVar('T')
T_co = TypeVar('T_co', covariant=True)
_Iter = Union[Iterable[T], AsyncIterable[T]]
Coro = Coroutine[Any, Any, T]


class _MissingSentinel:
    def __eq__(self, _) -> bool:
        return False

    def __bool__(self) -> bool:
        return False

    def __repr__(self) -> str:
        return '...'

MISSING: Any = _MissingSentinel()


def ISO8601(string: str):
    if string is None:
        return None

    try:
        return datetime.datetime.strptime(string, '%Y-%m-%dT%H:%M:%S.%fZ')
    except:
        try:
            return datetime.datetime.strptime(string, '%Y-%m-%dT%H:%M:%SZ')
        except:
            # get rid of milliseconds entirely since Guilded may sometimes
            # send a number of digits that datetime.fromisoformat does not
            # accept
            string = re.sub(r'\.\d{1,6}', '', string)
            try:
                return datetime.datetime.fromisoformat(string)
            except:
                pass
        raise TypeError(f'{string} is not a valid ISO8601 datetime.')


def hyperlink(link: str, *, title: str = None) -> str:
    """A helper function to make links clickable when sent into chat.

    Returns a markdown "named link", e.g. ``[Guilded](https://guilded.gg)``.
    """
    return f'[{title or link}]({link})'


def link(link: str, *, title: str = None) -> str:
    """Alias of :func:`hyperlink`\."""
    return hyperlink(link, title=title)


def new_uuid() -> str:
    """Generate a new, Guilded-compliant UUID."""
    return str(uuid1())


def find(predicate: Callable[[T], Any], sequence: _Iter[T]) -> Union[Optional[T], Coro[Optional[T]]]:
    """Iterate through ``sequence`` to find a matching object for ``predicate``.

    If nothing is found, ``None`` is returned.

    Parameters
    -----------
    predicate: Callable
        A function that returns a boolean or boolean-like result.
    sequence
        An iterable to search through.
    """
    for element in sequence:
        if predicate(element):
            return element
    return None


def get(sequence, **attributes):
    """Return an object from ``sequence`` that matches the ``attributes``.

    If nothing is found, ``None`` is returned.

    Parameters
    -----------
    sequence
        An iterable to search through.
    **attrs
        Keyword arguments representing attributes of each item to match with.
    """
    # global -> local
    _all = all
    attrget = attrgetter

    # Special case the single element call
    if len(attributes) == 1:
        k, v = attributes.popitem()
        pred = attrget(k.replace('__', '.'))
        for elem in sequence:
            if pred(elem) == v:
                return elem
        return None

    converted = [
        (attrget(attr.replace('__', '.')), value)
        for attr, value in attributes.items()
    ]

    for elem in sequence:
        if _all(pred(elem) == value for pred, value in converted):
            return elem
    return None


async def sleep_until(when, result=None):
    """|coro|

    Sleep until a specified time.

    Parameters
    -----------
    when: :class:`datetime.datetime`
        The datetime to sleep until.
    result: Any
        Returned when the function finishes, if provided.
    """
    if when.tzinfo is None:
        when = when.replace(tzinfo=datetime.timezone.utc)
    now = datetime.datetime.now(datetime.timezone.utc)
    delta = (when - now).total_seconds()
    while delta > 3456000:  # max asyncio time
        await asyncio.sleep(3456000)
        delta -= 3456000
    return await asyncio.sleep(max(delta, 0), result)


_MARKDOWN_ESCAPE_SUBREGEX = '|'.join(r'\{0}(?=([\s\S]*((?<!\{0})\{0})))'.format(c)
                                     for c in ('*', '`', '_', '~', '|'))

_MARKDOWN_ESCAPE_COMMON = r'^>(?:>>)?\s|\[.+\]\(.+\)'

_MARKDOWN_ESCAPE_REGEX = re.compile(r'(?P<markdown>%s|%s)' % (_MARKDOWN_ESCAPE_SUBREGEX, _MARKDOWN_ESCAPE_COMMON), re.MULTILINE)


def escape_markdown(text, *, as_needed=False, ignore_links=True):
    r"""A helper function that escapes markdown.

    Parameters
    -----------
    text: :class:`str`
        The text to escape markdown from.
    as_needed: :class:`bool`
        Whether to escape the markdown characters as needed. This
        means that it does not escape extraneous characters if it's
        not necessary, e.g. ``**hello**`` is escaped into ``\*\*hello**``
        instead of ``\*\*hello\*\*``. Note however that this can open
        you up to some clever syntax abuse. Defaults to ``False``.
    ignore_links: :class:`bool`
        Whether to leave links alone when escaping markdown. For example,
        if a URL in the text contains characters such as ``_`` then it will
        be left alone. This option is not supported with ``as_needed``.
        Defaults to ``True``.

    Returns
    --------
    :class:`str`
        The text with the markdown special characters escaped with a slash.
    """
    if not as_needed:
        url_regex = r'(?P<url><[^: >]+:\/[^ >]+>|(?:https?|steam):\/\/[^\s<]+[^<.,:;\"\'\]\s])'
        def replacement(match):
            groupdict = match.groupdict()
            is_url = groupdict.get('url')
            if is_url:
                return is_url
            return '\\' + groupdict['markdown']

        regex = r'(?P<markdown>[_\\~|\*`]|%s)' % _MARKDOWN_ESCAPE_COMMON
        if ignore_links:
            regex = '(?:%s|%s)' % (url_regex, regex)
        return re.sub(regex, replacement, text, 0, re.MULTILINE)
    else:
        text = re.sub(r'\\', r'\\\\', text)
        return _MARKDOWN_ESCAPE_REGEX.sub(r'\\\1', text)


async def maybe_coroutine(f, *args, **kwargs):
    value = f(*args, **kwargs)
    if _isawaitable(value):
        return await value
    else:
        return value


async def async_all(gen, *, check=_isawaitable):
    for elem in gen:
        if check(elem):
            elem = await elem
        if not elem:
            return False
    return True


_IS_ASCII = re.compile(r'^[\x00-\x7f]+$')

def _string_width(string: str, *, _IS_ASCII=_IS_ASCII) -> int:
    """Returns string's width."""
    match = _IS_ASCII.match(string)
    if match:
        return match.endpos

    UNICODE_WIDE_CHAR_TYPE = 'WFA'
    func = unicodedata.east_asian_width
    return sum(2 if func(char) in UNICODE_WIDE_CHAR_TYPE else 1 for char in string)


def copy_doc(original: Callable) -> Callable[[T], T]:
    def decorator(overridden: T) -> T:
        overridden.__doc__ = original.__doc__
        overridden.__signature__ = _signature(original)  # type: ignore
        return overridden

    return decorator


_GENERIC_ID_REGEX = re.compile(r'^[a-zA-Z0-9]{8,10}$')

class Object:
    """Represents a generic Guilded object.

    This class is especially useful when interfacing with the early access bot
    API, in which often only an object's ID is available.

    .. warning::

        Because Guilded IDs are not meaningful in the way that `snowflakes <https://discord.com/developers/docs/reference#snowflakes>`_
        are, a creation date is impossible to attain from only an ID. As a
        result, :attr:`.created_at` will always return 1/1/2016 for backwards
        compatibility with applications that implement :attr:`discord.Object.created_at`.


    .. container:: operations

        .. describe:: x == y

            Checks if two objects are equal.

        .. describe:: x != y

            Checks if two objects are not equal.

    Attributes
    -----------
    id: Union[:class:`str`, :class:`int`]
        The ID of the object.
    created_at: :class:`datetime.datetime`
        |dpyattr|

        Always returns 1/1/2016.
    """

    def __init__(self, id: Union[str, int]):
        if not isinstance(id, (str, int)):
            raise TypeError(f'id must be type str or int, not {id.__class__.__name__}')

        if isinstance(id, str):
            # Could be a UUID (https://guildedapi.com/reference/#snowflakes-uuids) or generic ID (https://guildedapi.com/reference/#generic-object-ids)
            try:
                UUID(id)
            except ValueError:
                if not _GENERIC_ID_REGEX.match(id):
                    raise ValueError(f'not a valid ID: {id!r}')

        # Else, could be a role or emoji ID, or even a Discord snowflake in
        # the case of syncing.

        self.id: Union[str, int] = id
        self.created_at: datetime.datetime = GUILDED_EPOCH_DATETIME

    def __repr__(self) -> str:
        return f'<Object id={self.id!r}>'

    def __eq__(self, other) -> bool:
        return hasattr(other, 'id') and self.id == other.id
