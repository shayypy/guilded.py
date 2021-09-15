
__copyright__ = 'shay 2020-2021'
__version__ = '1.0.0a'

import logging

from . import abc, utils
from .asset import Asset
from .channel import ChannelType, ChatChannel, DMChannel, Thread
from .client import Client
from .colour import Color, Colour
from .embed import Embed, EmbedProxy, EmptyEmbed
from .emoji import Emoji
from .enums import *
from .errors import (
    BadRequest,
    ClientException,
    Forbidden,
    GuildedException,
    GuildedServerError,
    HTTPException,
    NotFound,
    TooManyRequests,
)
from .file import File, FileType, MediaType, Attachment
from .message import ChatMessage, Message, MessageMention, MentionType
from .presence import Presence
from .status import TransientStatus, Game
from .team import SocialInfo, Team, TeamTimezone
from .user import ClientUser, Device, Member, User

logging.getLogger(__name__).addHandler(logging.NullHandler())
