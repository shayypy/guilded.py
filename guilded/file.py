import io
from enum import Enum
from typing import Union

from . import utils


class MediaType(Enum):
    attachment = 'ContentMedia'
    content_media = 'ContentMedia'
    emoji = 'CustomReaction'
    profile_banner = 'UserBanner'
    banner = 'UserBanner'
    avatar = 'UserAvatar'
    profile_avatar = 'UserAvatar'
    team_icon = 'TeamAvatar'
    team_avatar = 'TeamAvatar'
    team_banner = 'TeamBanner'
    group_icon = 'GroupAvatar'
    group_avatar = 'GroupAvatar'
    group_banner = 'GroupBanner'

    def __str__(self):
        return self.value

    def __repr__(self):
        return f'<MediaType name={self.name} value={self.value}>'

class FileType(Enum):
    image = 'image'
    video = 'video'

    def __str__(self):
        return self.value

    def __repr__(self):
        return f'<FileType name={self.name} value={self.value}>'

class File:
    def __init__(self, fp: Union[str, io.BufferedIOBase], *, filename=None, file_type: FileType = None):
        '''A class that wraps basic media pre-and-mid-upload. Non-image/video filetypes are not supported by Guilded.'''
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
            elif isinstance(fp, bytes):
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
        self.type = media_type
        return self

    def set_file_type(self, file_type):
        self.file_type = file_type
        return self

    async def _upload(self, state):
        response = await state.upload_file(self)
        url = response.get('url')
        self.url = url
        return self
