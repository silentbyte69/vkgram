"""
VKgram - Modern async VK bot library
High-performance Python library for building VK.com bots
Inspired by aiogram, optimized for VK
"""

from .bot import VKgramBot
from .handlers import MessageHandler, EventHandler
from .keyboard import Keyboard, Button, ButtonColor
from .types import Message, Update, User
from .filters import CommandFilter, TextFilter, StateFilter

__version__ = "1.0.0"
__author__ = "VKgram Team"

__all__ = [
    'VKgramBot',
    'MessageHandler', 
    'EventHandler',
    'Keyboard', 'Button', 'ButtonColor',
    'Message', 'Update', 'User',
    'CommandFilter', 'TextFilter', 'StateFilter'
]
