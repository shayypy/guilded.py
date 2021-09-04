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
from inspect import isawaitable as _isawaitable
import re
from operator import attrgetter
import unicodedata
from uuid import uuid1

from .colour import Colour

GUILDED_EPOCH_DATETIME = datetime.datetime(2016, 1, 1)
GUILDED_EPOCH_ISO8601 = GUILDED_EPOCH_DATETIME.isoformat() + 'Z'
GUILDED_EPOCH = int(GUILDED_EPOCH_DATETIME.timestamp())

valid_image_extensions = ['png', 'webp', 'jpg', 'jpeg', 'gif', 'jif', 'tif', 'tiff', 'apng', 'bmp', 'svg']
valid_video_extensions = ['mp4', 'mpeg', 'mpg', 'mov', 'avi', 'wmv', 'qt', 'webm']


def ISO8601(string: str):
    if string is None:
        return None

    try:
        return datetime.datetime.strptime(string, '%Y-%m-%dT%H:%M:%S.%fZ')
    except:
        try:
            return datetime.datetime.fromisoformat(string)
        except:
            pass
        raise TypeError(f'{string} is not a valid ISO8601 datetime.')


def hyperlink(link: str, *, title=None):
    """A helper function to make links clickable when sent into chat."""
    return f'[{title or link}]({link})'


def link(link: str, *, title=None):
    """Alias of :func:hyperlink."""
    return hyperlink(link, title=title)


def new_uuid():
    """Generate a new, compliant UUID."""
    return str(uuid1())


def find(predicate, sequence):
    for element in sequence:
        if predicate(element):
            return element
    return None


def get(item, **attributes):
    # global -> local
    _all = all
    attrget = attrgetter

    # Special case the single element call
    if len(attributes) == 1:
        k, v = attributes.popitem()
        pred = attrget(k.replace('__', '.'))
        for elem in item:
            if pred(elem) == v:
                return elem
        return None

    converted = [
        (attrget(attr.replace('__', '.')), value)
        for attr, value in attributes.items()
    ]

    for elem in item:
        if _all(pred(elem) == value for pred, value in converted):
            return elem
    return None


async def sleep_until(when, result=None):
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


def parse_hex_number(argument):
    arg = ''.join([i * 2 for i in argument]) if len(argument) == 3 else argument
    try:
        value = int(arg, base=16)
        if not (0 <= value <= 0xFFFFFF):
            raise ValueError(argument)
    except ValueError as e:
        raise ValueError(argument) from e
    else:
        return Colour(value=value)


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
