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
from enum import Enum
from typing import Union

from . import utils


class MediaType(Enum):
    """Represents a file/attachment's media type in Guilded."""
    attachment = 'ContentMedia'
    content_media = 'ContentMedia'
    emoji = 'CustomReaction'
    custom_reaction = 'CustomReaction'
    avatar = 'UserAvatar'
    user_avatar = 'UserAvatar'
    profile_avatar = 'UserAvatar'
    banner = 'UserBanner'
    user_banner = 'UserBanner'
    profile_banner = 'UserBanner'
    team_icon = 'TeamAvatar'
    team_avatar = 'TeamAvatar'
    team_banner = 'TeamBanner'
    group_icon = 'GroupAvatar'
    group_avatar = 'GroupAvatar'
    group_banner = 'GroupBanner'
    embed_image = 'ExternalOGEmbedImage'
    media_channel_upload = 'MediaChannelUpload'

    def __str__(self):
        return self.value

    def __repr__(self):
        return f'<MediaType name={self.name} value={self.value}>'

class FileType(Enum):
    """Represents a type of file in Guilded. In the case of uploading
    files, this usually does not have to be set manually, but if the
    library fails to detect the type of file from its extension, you
    can pass this into :class:`File`\'s ``file_type`` keyword argument.
    """
    image = 'image'
    video = 'video'

    def __str__(self):
        return self.value

    def __repr__(self):
        return f'<FileType name={self.name} value={self.value}>'

class File:
    """Wraps media pre-and-mid-upload.

    .. warning::
        Non-image/video filetypes are not supported by Guilded.

    Parameters
    ------------
    fp: Union[:class:`str`, :class:`io.BufferedIOBase`]
        The file to upload. If passing a file with ``open``, the file
        should be opened in ``rb`` mode.
    filename: Optional[:class:`str`]
        The name of this file. Not required unless also using the
        ``attachment://`` URI in an accompanying embed.
    file_type: :class:`FileType`
        The type of file (image, video). It this could not be detected by
        the library, defaults to :attr:`FileType.image`. 

    Attributes
    ------------
    fp: Union[:class:`str`, :class:`io.BufferedIOBase`]
        The file to upload.
    filename: Optional[:class:`str`]
        The name of this file.
    type: Optional[:class:`MediaType`]
        The file's media type (attachment, emoji, ...).
    file_type: :class:`FileType`
        The type of file (image, video).
    url: Optional[:class:`str`]
        The URL to the file on Guilded's CDN after being uploaded by the
        library.
    """
    def __init__(self, fp: Union[str, io.BufferedIOBase], *, filename=None, file_type: FileType = None):
        self.fp = fp
        self.type = None
        self.url = None
        self.filename = filename

        if type(fp) == str:
            self._bytes = open(fp, 'rb')
            self.filename = filename or fp
            if file_type is None:
                try:
                    extension = self.fp.split('.')[-1]
                except IndexError:
                    # file has no extension
                    raise ValueError('File must have an extension if file_type is not specified.')
                else:
                    if extension in utils.valid_image_extensions:
                        self.file_type = 'image'
                    elif extension in utils.valid_video_extensions:
                        self.file_type = 'video'
                    else:
                        raise TypeError('Invalid file type. Consider passing file_type to manually tell Guilded what type of file this is.')

            else:
                self.file_type = file_type

        else:
            if isinstance(fp, io.BytesIO):
                fp.seek(0)
                self._bytes = fp.read()
            elif isinstance(fp, (bytes, io.BufferedReader)):
                self._bytes = fp
            else:
                self._bytes = None
            self.file_type = file_type

        if self.file_type is None:
            # fallback in case the checker fails, just so null isn't sent
            self.file_type = FileType.image

    def __repr__(self):
        return f'<File type={self.type}>'

    def __bytes__(self):
        return self._bytes

    def set_media_type(self, media_type):
        """Manually set this file's media type."""
        self.type = media_type
        return self

    def set_file_type(self, file_type):
        """Manually set this file's file type."""
        self.file_type = file_type
        return self

    async def _upload(self, state):
        response = await state.upload_file(self)
        url = response.get('url')
        self.url = url
        return self

class Attachment:
    """An uploaded attachment in a message, announcement, document, or any
    other place you can upload files inline with content.

    Attributes
    ------------
    url: :class:`str`
        The URL to the file on Guilded's CDN.
    type: :class:`MediaType`
        The file's media type (should only ever be :attr:`MediaType.attachment`).
    filename: Optional[:class:`str`]
        The file's name (``{hash}-{Size}.{extension}``). Automatically parsed
        from :attr:`.url`, so this will be ``None`` if :attr:`.url` is also
        ``None``.
    file_type: Optional[:class:`FileType`]
        The type of file (image, video).
    caption: Optional[:class:`str`]
        The attachment's caption. This probably won't be present in message
        attachments.
    """
    def __init__(self, *, state, data, **extra):
        self._state = state
        self.file_type = getattr(FileType, data.get('type'), None)
        self.type = extra.get('type') or MediaType.attachment
        self.url = data.get('data', {}).get('src')
        if data.get('nodes'):
            node = data['nodes'][0] or {}
            if node.get('type') == 'image-caption-line':
                caption = ''
                for leaf in node.get('leaves', []):
                    if not leaf.get('marks'):
                        caption += leaf['text']
                    else:
                        to_mark = '{unmarked_content}'
                        for mark in leaf['marks']:
                            if mark['type'] == 'bold':
                                to_mark = '**' + to_mark + '**'
                            elif mark['type'] == 'italic':
                                to_mark = '*' + to_mark + '*'
                            elif mark['type'] == 'underline':
                                to_mark = '__' + to_mark + '__'
                            elif mark['type'] == 'strikethrough':
                                to_mark = '~~' + to_mark + '~~'
                            elif mark['type'] == 'spoiler':
                                to_mark = '||' + to_mark + '||'
                        caption += to_mark.format(
                            unmarked_content=str(leaf['text'])
                        )

                self.caption = caption
            else:
                self.caption = None

    @property
    def filename(self):
        try:
            return str(self.url).split('/')[-1]
        except IndexError:
            # self.url is probably None
            return None

    async def read(self):
        """|coro|

        Returns
        ---------
        :class:`bytes`
        """
        return await self._state.read_filelike_data(self)

    async def to_file(self):
        """|coro|

        Converts the attachment to an uploadable :class:`File` instance.

        Returns
        ---------
        :class:`File`
        """
        data = await self.read()
        return File(data, filename=self.filename, file_type=self.file_type)
