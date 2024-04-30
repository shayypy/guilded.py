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
from typing import Any, Dict, Optional, Union

from .asset import AssetMixin, url_with_signature
from .enums import try_enum, FileType, MediaType
from . import utils


__all__ = (
    'Attachment',
    'File',
)


class File:
    """Wraps files pre- and mid-upload.

    .. container:: operations

        .. describe:: bytes(x)

            Returns the bytes of the underlying file.

    Parameters
    -----------
    fp: Union[:class:`os.PathLike`, :class:`io.BufferedIOBase`]
        The file to upload.
        If passing a file with ``open``, the file should be opened in ``rb`` mode.
    filename: Optional[:class:`str`]
        The name of this file.
    file_type: :class:`FileType`
        The file's file type.
        If this could not be detected by the library, defaults to :attr:`FileType.image`. 

    Attributes
    -----------
    fp: Union[:class:`os.PathLike`, :class:`io.BufferedIOBase`]
        The file ready to be uploaded to Guilded.
    filename: Optional[:class:`str`]
        The name of the file.
    type: Optional[:class:`MediaType`]
        The file's media type.
        This correlates to what the file is being uploaded for (e.g., an avatar) rather than the type of file that it is (e.g., an image).
        This will usually be set by the library before uploading.
    file_type: :class:`FileType`
        The file's file type.
    url: Optional[:class:`str`]
        The URL to the file on Guilded's CDN after being uploaded by the library.
    """

    __slots__ = (
        '_state',
        'fp',
        'filename',
        'type',
        'file_type',
        'url',
        '_owner',
        '_original_pos',
        '_closer',
    )

    def __init__(
        self,
        fp: Union[str, bytes, io.BufferedIOBase],
        filename: Optional[str] = None,
        *,
        file_type: FileType = None,
    ):
        self.type: Optional[MediaType] = None
        self.url: Optional[str] = None
        self.filename: Optional[str] = filename
        self.file_type: FileType

        if isinstance(fp, io.IOBase):
            if not (fp.seekable() and fp.readable()):
                raise ValueError(f'File buffer {fp!r} must be seekable and readable')

            self.fp: io.BufferedIOBase = fp
            self._owner = False
            self._original_pos = fp.tell()
            self.file_type = file_type

            _fp_name: Optional[str] = getattr(fp, 'name', None)

            if _fp_name is None and filename is None and file_type is None:
                # We cannot upload a file without knowing what type of file it is, which makes things more complicated when dealing with raw file data.
                # We assume an image type here just because it is probably the most common.
                # I decided to do this instead of raising an error for now in order to maintain compatibility with discord.py.
                self.file_type = FileType.image

            if _fp_name is None and filename is None:
                if self.file_type is FileType.image:
                    self.filename = 'untitled.png'
                elif self.file_type is FileType.video:
                    self.filename = 'untitled.mp4'

            self.fp.name = getattr(self.fp, 'name', self.filename)

        else:
            self.fp = open(fp, 'rb')
            self._owner = True
            self._original_pos = 0

            if file_type is None:
                fn = filename or ''
                if filename is None and isinstance(fp, str):
                    _, fn = os.path.split(fp)
                try:
                    extension = fn.split('.')[-1].lower()
                except IndexError:
                    # The file has no extension
                    raise ValueError('filename must be specified or file must have an extension if file_type is not specified.')
                else:
                    if extension in utils.valid_image_extensions:
                        self.file_type = FileType.image
                    elif extension in utils.valid_video_extensions:
                        self.file_type = FileType.video
                    else:
                        raise TypeError('Invalid file type. Consider passing file_type to manually tell Guilded what type of file this is.')

            else:
                self.file_type = file_type

        self._closer = self.fp.close
        self.fp.close = lambda: None

        if self.file_type is None:
            # Fallback just so that None isn't sent. This may potentially lead to confusing behavior.
            self.file_type = FileType.image

    def __repr__(self) -> str:
        return f'<File type={self.type}>'

    def __bytes__(self) -> bytes:
        return self.fp.read()

    @property
    def content_type(self) -> Optional[str]:
        # This exists for uploading files with webhooks
        if self.file_type is FileType.image:
            return 'image/png'
        elif self.file_type is FileType.video:
            return 'video/mp4'
        return None

    def set_media_type(self, media_type: MediaType):
        """Manually set this file's media type."""
        self.type = media_type
        return self

    def set_file_type(self, file_type: FileType):
        """Manually set this file's file type."""
        self.file_type = file_type
        return self

    def reset(self, *, seek: Union[int, bool] = True) -> None:
        # https://github.com/Rapptz/discord.py/blob/5c14149873368060c0b86c95914753ab7b283097/discord/file.py#L134-L141
        if seek:
            self.fp.seek(self._original_pos)

    def close(self) -> None:
        self.fp.close = self._closer
        if self._owner:
            self._closer()

    async def _upload(self, state):
        if self.file_type in {FileType.image, FileType.video}:
            coro = state.upload_media
        else:
            coro = state.upload_file

        data = await coro(self)
        url = data.get('url')
        self.url = url
        return self


class Attachment(AssetMixin):
    """An uploaded attachment in a message, announcement, document, or any
    other place you can upload files inline with content.

    Attributes
    -----------
    url: :class:`str`
        The URL to the file.

        .. versionchanged: 1.13
            May now be a tenor.com or giphy.com URL in the
            case of GIF picker "attachments".

    file_type: Optional[:class:`FileType`]
        The type of file.
    caption: Optional[:class:`str`]
        The attachment's caption.
    size: Optional[:class:`int`]
        The attachment's size in bytes.
    height: Optional[:class:`int`]
        The attachment's height in pixels.
    width: Optional[:class:`int`]
        The attachment's width in pixels.
    """

    __slots__ = (
        '_state',
        'file_type',
        'type',
        'url',
        'width',
        'height',
        'caption',
        'size',
        '_filename',
    )

    def __init__(self, *, state, data: Dict[str, Any], **extra):
        self._state = state
        self.file_type: FileType = try_enum(FileType, data.get('type'))
        self.type: MediaType = extra.get('type') or MediaType.content_media_generic_files
        self.caption: Optional[str] = data.get('caption')

        inner_data: Dict[str, Any] = data.get('data', {})
        self.size: Optional[int] = inner_data.get('fileSizeBytes')
        self._filename: Optional[str] = inner_data.get('name')

        self.url: str = data.get('url') or inner_data.get('src')
        if not state.cdn_qs_expired:
            # Avoid the signing dance if possible. This makes it possible for
            # users to use URLs straight from the library without having to
            # read (and thus sign) them first.
            self.url = url_with_signature(self.url, state.cdn_qs)

        self.width: Optional[int] = None
        self.height: Optional[int] = None

        # I also considered re.findall with `(?:\?|&)(?:(w)=(?P<width>\d+)|(h)=(?P<height>\d+))`
        # but I thought it was too clunky.
        height_match: Optional[re.Match] = re.search(r'(?:\?|&)h=(?P<value>\d+)', self.url)
        width_match: Optional[re.Match] = re.search(r'(?:\?|&)w=(?P<value>\d+)', self.url)
        if width_match:
            self.width = int(width_match.group('value'))
        if height_match:
            self.height = int(height_match.group('value'))

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
                            else:
                                pass
                        caption += to_mark.format(
                            unmarked_content=str(leaf['text'])
                        )

                self.caption = caption

    def __repr__(self) -> str:
        return f'<Attachment filename={self.filename!r} url={self.url!r}>'

    def __str__(self) -> str:
        return self.url

    @property
    def filename(self) -> str:
        """:class:`str`: The file's name."""
        if not self._filename:
            try:
                # Remove the leading host & path details and trailing query parameters
                return str(self.url).split('/')[-1].split('?')[0]
            except IndexError:
                return ''

        return self._filename

    @property
    def description(self) -> Optional[str]:
        """Optional[:class:`str`]: |dpyattr|

        This is an alias of :attr:`.caption`.

        The attachment's caption.
        """
        return self.caption

    async def to_file(self) -> File:
        """|coro|

        Converts the attachment to an uploadable :class:`File` instance.

        Returns
        --------
        :class:`File`
            The attachment as a :class:`File`.
        """

        data = io.BytesIO(await self.read())
        file = File(data, filename=self.filename, file_type=self.file_type)
        file.set_media_type(self.type)
        return file
