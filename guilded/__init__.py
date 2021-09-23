
__copyright__ = 'shay 2020-present'
__version__ = '1.0.0a'

import logging

from . import abc, utils
from .asset import Asset
from .channel import ChannelType, ChatChannel, DMChannel, Thread, VoiceChannel
from .client import Client
from .colour import Color, Colour
from .embed import Embed, EmbedProxy, EmptyEmbed
from .emoji import DiscordEmoji, Emoji
from .enums import *
from .errors import *
from .file import Attachment, File, FileType, MediaType
from .group import Group
from .message import ChatMessage, Mention, MentionType, Message, MessageMention
from .presence import Presence
from .status import TransientStatus, Game
from .team import Guild, SocialInfo, Team, TeamTimezone
from .user import ClientUser, Device, Member, User

logging.getLogger(__name__).addHandler(logging.NullHandler())
