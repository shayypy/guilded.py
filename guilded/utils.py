from operator import attrgetter
from uuid import uuid1
import datetime
import asyncio
import re

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
            return datetime.datetime.strptime(string, '%Y-%m-%dT%H:%M:%SZ')
        except:
            pass
        raise TypeError(f'{string} is not a valid ISO8601 datetime.')

def hyperlink(link: str, *, title=None):
    '''A helper function to make links clickable when sent into chat.'''
    return f'[{title or link}]({link})'

def link(link: str, *, title=None):
    '''Alias of :func:hyperlink.'''
    return hyperlink(link, title=title)

def new_uuid():
    '''Generate a new, compliant UUID.'''
    return str(uuid1())

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
