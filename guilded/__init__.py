
__copyright__ = 'shay 2020-2021'
__version__ = '1.0.0a'

import logging

from .asset import Asset
from .channel import *
from .client import Client
from .errors import *
from . import abc, utils
from .user import *
from .message import Message
from .team import Team
from .emoji import Emoji
from .file import File
from .embed import Embed, EmptyEmbed, EmbedProxy
from .colour import Colour, Color
from .status import TransientStatus, Game
from .presence import Presence

logging.getLogger(__name__).addHandler(logging.NullHandler())
