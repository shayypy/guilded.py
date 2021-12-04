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

import datetime

from . import utils
from .colour import Colour


class _EmptyEmbed:
    def __bool__(self): return False
    def __repr__(self): return 'Embed.Empty'
    def __len__(self): return 0

EmptyEmbed = _EmptyEmbed()

class EmbedProxy:
    def __init__(self, layer):
        self.__dict__.update(layer)

    def __len__(self):
        return len(self.__dict__)

    def __repr__(self):
        return 'EmbedProxy(%s)' % ', '.join(['%s=%r' % (k, v) for k, v in self.__dict__.items() if not k.startswith('_')])

    def __getattr__(self, attr):
        return EmptyEmbed

class Embed:
    """Represents a Guilded embed.

    .. container:: operations

        .. describe:: len(x)

            Returns the total size of the embed.
            Useful for checking if it's within the 6000 character limit.

    Certain properties return an ``EmbedProxy``, a type
    that acts similar to a regular :class:`dict` except using dotted access,
    e.g. ``embed.author.icon_url``. If the attribute
    is invalid or empty, then a special sentinel value is returned,
    :attr:`Embed.Empty`.

    For ease of use, all parameters that expect a :class:`str` are implicitly
    casted to :class:`str` for you.

    Attributes
    -----------
    title: :class:`str`
        The title of the embed.
        This can be set during initialisation.
    type: :class:`str`
        The type of embed. Usually "rich".
        This can be set during initialisation.
    description: :class:`str`
        The description of the embed.
        This can be set during initialisation.
    url: :class:`str`
        The URL of the embed.
        This can be set during initialisation.
    timestamp: :class:`datetime.datetime`
        The timestamp of the embed content. This could be a naive or aware datetime.
    colour: Union[:class:`Colour`, :class:`int`]
        The colour code of the embed. Aliased to ``color`` as well.
        This can be set during initialisation.
    Empty
        A special sentinel value used by ``EmbedProxy`` and this class
        to denote that the value or attribute is empty.
    """

    __slots__ = ('title', 'url', 'type', '_timestamp', '_colour', '_footer',
                 '_image', '_thumbnail', '_video', '_provider', '_author',
                 '_fields', 'description')

    Empty = EmptyEmbed

    def __init__(self, **kwargs):
        # swap the colour/color aliases
        try:
            colour = kwargs['colour']
        except KeyError:
            colour = kwargs.get('color', EmptyEmbed)

        self.colour = colour
        self.title = kwargs.get('title', EmptyEmbed)
        self.type = kwargs.get('type', 'rich')
        self.url = kwargs.get('url', EmptyEmbed)
        self.description = kwargs.get('description', EmptyEmbed)

        if self.title is not EmptyEmbed:
            self.title = str(self.title)

        if self.description is not EmptyEmbed:
            self.description = str(self.description)

        if self.url is not EmptyEmbed:
            self.url = str(self.url)

        try:
            timestamp = kwargs['timestamp']
        except KeyError:
            pass
        else:
            self.timestamp = timestamp

    @classmethod
    def from_dict(cls, data):
        """Converts a :class:`dict` to a :class:`Embed`, provided it is in the
        format that Guilded expects it to be in.

        This format is identical to Discord's format for embeds, but you can
        find `documentation about it here <https://guildedapi.com/resources/
        channel#embed-object>`_ anyway.

        Parameters
        -----------
        data: :class:`dict`
            The dictionary to convert into an embed.
        """
        # we are bypassing __init__ here since it doesn't apply here
        self = cls.__new__(cls)

        # fill in the basic fields

        self.title = data.get('title', EmptyEmbed)
        self.type = data.get('type', EmptyEmbed)
        self.description = data.get('description', EmptyEmbed)
        self.url = data.get('url', EmptyEmbed)

        if self.title is not EmptyEmbed:
            self.title = str(self.title)

        if self.description is not EmptyEmbed:
            self.description = str(self.description)

        if self.url is not EmptyEmbed:
            self.url = str(self.url)

        # try to fill in the more rich fields

        try:
            self._colour = Colour(value=data['color'])
        except (KeyError, TypeError):
            pass

        try:
            self._timestamp = utils.ISO8601(data['timestamp'])
        except KeyError:
            pass

        for attr in ('thumbnail', 'video', 'provider', 'author', 'fields', 'image', 'footer'):
            try:
                value = data[attr]
            except KeyError:
                continue
            else:
                setattr(self, '_' + attr, value)

        return self

    @classmethod
    def from_unfurl_dict(cls, data):
        """Similar to :meth:`Embed.from_dict`, but for embed data returned by
        the `Get Embed for URL <https://guildedapi.com/resources/channel#get-
        embed-for-url>`_ endpoint.

        You probably won't have to use this yourself.
        """
        data['type'] = 'link'
        try:
            data['title'] = data.pop('ogTitle')
        except KeyError:
            pass

        try:
            data['description'] = data.pop('ogDescription')
        except KeyError:
            pass

        try:
            data['url'] = data.pop('ogUrl')
        except KeyError:
            pass

        try:
            data['provider'] = data.pop('ogSiteName')
        except KeyError:
            pass

        try:
            data['thumbnail'] = {}
            data['thumbnail']['url'] = data.pop('ogImage')['url']
        except KeyError:
            del data['thumbnail']

        try:
            data['video'] = {}
            data['video']['url'] = data.pop('ogVideo')['url']
        except KeyError:
            del data['video']

        return Embed.from_dict(data)

    def copy(self):
        """Returns a shallow copy of the embed."""
        return Embed.from_dict(self.to_dict())

    def __len__(self):
        total = len(self.title) + len(self.description)
        for field in getattr(self, '_fields', []):
            total += len(field['name']) + len(field['value'])

        try:
            footer = self._footer
        except AttributeError:
            pass
        else:
            total += len(footer['text'])

        try:
            author = self._author
        except AttributeError:
            pass
        else:
            total += len(author['name'])

        return total

    @property
    def colour(self):
        return getattr(self, '_colour', EmptyEmbed)

    @colour.setter
    def colour(self, value):
        if isinstance(value, (Colour, _EmptyEmbed)):
            self._colour = value
        elif isinstance(value, int):
            self._colour = Colour(value=value)
        else:
            raise TypeError('Expected guilded.Colour, int, or Embed.Empty but received %s instead.' % value.__class__.__name__)

    color = colour

    @property
    def timestamp(self):
        return getattr(self, '_timestamp', EmptyEmbed)

    @timestamp.setter
    def timestamp(self, value):
        if isinstance(value, (datetime.datetime, _EmptyEmbed)):
            self._timestamp = value
        else:
            raise TypeError("Expected datetime.datetime or Embed.Empty received %s instead" % value.__class__.__name__)

    @property
    def footer(self):
        """Union[:class:`EmbedProxy`, :attr:`Empty`]: Returns an ``EmbedProxy`` denoting the footer contents.
        See :meth:`set_footer` for possible values you can access.
        If the attribute has no value then :attr:`Empty` is returned.
        """
        return EmbedProxy(getattr(self, '_footer', {}))

    def set_footer(self, *, text=EmptyEmbed, icon_url=EmptyEmbed):
        """Sets the footer for the embed content.
        This function returns the class instance to allow for fluent-style
        chaining.
        Parameters
        -----------
        text: :class:`str`
            The footer text.
        icon_url: :class:`str`
            The URL of the footer icon. Only HTTP(S) is supported.
        """

        self._footer = {}
        if text is not EmptyEmbed:
            self._footer['text'] = str(text)

        if icon_url is not EmptyEmbed:
            self._footer['iconUrl'] = str(icon_url)

        return self

    @property
    def image(self):
        """Union[:class:`EmbedProxy`, :attr:`Empty`]: Returns an ``EmbedProxy`` denoting the image contents.
        Possible attributes you can access are:
        - ``url``
        - ``proxy_url``
        - ``width``
        - ``height``
        If the attribute has no value then :attr:`Empty` is returned.
        """
        return EmbedProxy(getattr(self, '_image', {}))

    def set_image(self, *, url):
        """Sets the image for the embed content.
        This function returns the class instance to allow for fluent-style
        chaining.

        Parameters
        -----------
        url: :class:`str`
            The source URL for the image. Only HTTP(S) or an
            ``attachment://`` is supported.
        """

        if url is EmptyEmbed:
            try:
                del self._image
            except AttributeError:
                pass
        else:
            self._image = {
                'url': str(url)
            }

        return self

    @property
    def thumbnail(self):
        """Union[:class:`EmbedProxy`, :attr:`Empty`]: Returns an ``EmbedProxy`` denoting the thumbnail contents.
        Possible attributes you can access are:
        - ``url``
        - ``proxy_url``
        - ``width``
        - ``height``
        If the attribute has no value then :attr:`Empty` is returned.
        """
        return EmbedProxy(getattr(self, '_thumbnail', {}))

    def set_thumbnail(self, *, url):
        """Sets the thumbnail for the embed content.
        This function returns the class instance to allow for fluent-style
        chaining.

        Parameters
        -----------
        url: :class:`str`
            The source URL for the thumbnail. Only HTTP(S) or an
            ``attachment://`` is supported.
        """

        if url is EmptyEmbed:
            try:
                del self._thumbnail
            except AttributeError:
                pass
        else:
            self._thumbnail = {
                'url': str(url)
            }

        return self

    @property
    def video(self):
        """Union[:class:`EmbedProxy`, :attr:`Empty`]: Returns an ``EmbedProxy`` denoting the video contents.
        Possible attributes include:
        - ``url`` for the video URL.
        - ``height`` for the video height.
        - ``width`` for the video width.
        If the attribute has no value then :attr:`Empty` is returned.
        """
        return EmbedProxy(getattr(self, '_video', {}))

    @property
    def provider(self):
        """Union[:class:`EmbedProxy`, :attr:`Empty`]: Returns an ``EmbedProxy`` denoting the provider contents.
        The only attributes that might be accessed are ``name`` and ``url``.
        If the attribute has no value then :attr:`Empty` is returned.
        """
        return EmbedProxy(getattr(self, '_provider', {}))

    @property
    def author(self):
        """Union[:class:`EmbedProxy`, :attr:`Empty`]: Returns an ``EmbedProxy`` denoting the author contents.
        See :meth:`set_author` for possible values you can access.
        If the attribute has no value then :attr:`Empty` is returned.
        """
        return EmbedProxy(getattr(self, '_author', {}))

    def set_author(self, *, name, url=EmptyEmbed, icon_url=EmptyEmbed):
        """Sets the author for the embed content.
        This function returns the class instance to allow for fluent-style
        chaining.

        Parameters
        -----------
        name: :class:`str`
            The name of the author.
        url: :class:`str`
            The URL for the author.
        icon_url: :class:`str`
            The URL of the author icon. Only HTTP(S) is supported.
        """

        self._author = {
            'name': str(name)
        }

        if url is not EmptyEmbed:
            self._author['url'] = str(url)

        if icon_url is not EmptyEmbed:
            self._author['iconUrl'] = str(icon_url)

        return self

    def remove_author(self):
        """Clears embed's author information.
        This function returns the class instance to allow for fluent-style
        chaining.
        """
        try:
            del self._author
        except AttributeError:
            pass

        return self

    @property
    def fields(self):
        """Union[List[:class:`EmbedProxy`], :attr:`Empty`]: Returns a
        :class:`list` of ``EmbedProxy`` denoting the field contents.
        See :meth:`add_field` for possible values you can access.
        If the attribute has no value then :attr:`Empty` is returned.
        """
        return [EmbedProxy(d) for d in getattr(self, '_fields', [])]

    def add_field(self, *, name, value, inline=True):
        """Adds a field to the embed object.
        This function returns the class instance to allow for fluent-style
        chaining.

        Parameters
        -----------
        name: :class:`str`
            The name of the field.
        value: :class:`str`
            The value of the field.
        inline: :class:`bool`
            Whether the field should be displayed inline.
        """

        field = {
            'inline': inline,
            'name': str(name),
            'value': str(value)
        }

        try:
            self._fields.append(field)
        except AttributeError:
            self._fields = [field]

        return self

    def insert_field_at(self, index, *, name, value, inline=True):
        """Inserts a field before a specified index to the embed.
        This function returns the class instance to allow for fluent-style
        chaining.

        Parameters
        -----------
        index: :class:`int`
            The index of where to insert the field.
        name: :class:`str`
            The name of the field.
        value: :class:`str`
            The value of the field.
        inline: :class:`bool`
            Whether the field should be displayed inline.
        """

        field = {
            'inline': inline,
            'name': str(name),
            'value': str(value)
        }

        try:
            self._fields.insert(index, field)
        except AttributeError:
            self._fields = [field]

        return self

    def clear_fields(self):
        """Removes all fields from this embed."""
        try:
            self._fields.clear()
        except AttributeError:
            self._fields = []

    def remove_field(self, index):
        """Removes a field at a specified index.
        If the index is invalid or out of bounds then the error is
        silently swallowed.

        .. note::
            When deleting a field by index, the index of the other fields
            shift to fill the gap just like a regular list.

        Parameters
        -----------
        index: :class:`int`
            The index of the field to remove.
        """
        try:
            del self._fields[index]
        except (AttributeError, IndexError):
            pass

    def set_field_at(self, index, *, name, value, inline=True):
        """Modifies a field to the embed object.
        The index must point to a valid pre-existing field.
        This function returns the class instance to allow for fluent-style
        chaining.

        Parameters
        -----------
        index: :class:`int`
            The index of the field to modify.
        name: :class:`str`
            The name of the field.
        value: :class:`str`
            The value of the field.
        inline: :class:`bool`
            Whether the field should be displayed inline.

        Raises
        -------
        IndexError
            An invalid index was provided.
        """

        try:
            field = self._fields[index]
        except (TypeError, IndexError, AttributeError):
            raise IndexError('field index out of range')

        field['name'] = str(name)
        field['value'] = str(value)
        field['inline'] = inline
        return self

    def to_dict(self):
        """Converts this embed object into a dict.

        .. note::
            The resulting dict will be more or less identical to Discord's
            format for embeds, with the exception that an ``iconUrl`` key is
            used in place of ``icon_url``\s. This is because ``icon_url``\s do
            not display on Desktop clients.
        """
        # add in the raw data into the dict
        result = {
            key[1:]: getattr(self, key)
            for key in self.__slots__
            if key[0] == '_' and hasattr(self, key)
        }

        # deal with basic convenience wrappers

        try:
            colour = result.pop('colour')
        except KeyError:
            pass
        else:
            if colour:
                result['color'] = colour.value

        try:
            timestamp = result.pop('timestamp')
        except KeyError:
            pass
        else:
            if timestamp:
                if timestamp.tzinfo:
                    result['timestamp'] = timestamp.astimezone(tz=datetime.timezone.utc).isoformat()
                else:
                    result['timestamp'] = timestamp.replace(tzinfo=datetime.timezone.utc).isoformat()

        # add in the non raw attribute ones
        if self.type:
            result['type'] = self.type

        if self.description:
            result['description'] = self.description

        if self.url:
            result['url'] = self.url

        if self.title:
            result['title'] = self.title

        return result
