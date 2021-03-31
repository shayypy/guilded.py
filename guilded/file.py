from typing import Union
from enum import Enum
import io

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
    def __init__(self, fp: Union[str, io.BufferedIOBase], *, file_type: FileType = None):
        '''A class that wraps basic media pre-and-mid-upload. Non-image/video filetypes are not supported by Guilded.'''
        self.fp = fp
        self.type = None
        self.url = None

        if type(fp) == str:
            self._bytes = open(fp, 'rb')
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
            self._bytes = fp
            self.file_type = file_type

    def __repr__(self):
        return f'<File type={self.type}>'

    def __bytes__(self):
        return self._bytes

    async def _upload(self, state):
        response = await state.upload_file(self)
        url = response.get('url')
        self.url = url
        return url
