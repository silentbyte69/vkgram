"""
VKgram - Modern async VK bot library
High-performance Python library for building VK.com bots
Inspired by aiogram, optimized for VK API
"""

__version__ = "0.1.0"
__author__ = "silentbyte69"
__description__ = "Modern async VK bot library inspired by aiogram"

# Core bot
from .bot import VKgramBot

# Handlers
from .handlers import message_handler, event_handler

# Keyboards
from .keyboard import Keyboard, Button, ButtonColor

# Types
from .types import Message, Update

# Filters
from .filters import command, text, chat_type, user, content_type

# Main exports
__all__ = [
    'VKgramBot',
    'message_handler',
    'event_handler', 
    'Keyboard',
    'Button',
    'ButtonColor',
    'Message', 
    'Update',
    'command',
    'text',
    'chat_type',
    'user',
    'content_type',
]
