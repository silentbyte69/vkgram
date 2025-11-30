from typing import Union, Any, List, Pattern
import re
from abc import ABC, abstractmethod
from .types import Message, Update

class Filter(ABC):
    """Abstract base class for all filters"""
    
    @abstractmethod
    async def check(self, update: Union[Message, Update], bot: Any) -> bool:
        """Check if update passes the filter"""
        pass

class CommandFilter(Filter):
    """Filter for bot commands"""
    
    def __init__(self, commands: Union[str, List[str]]):
        self.commands = [commands] if isinstance(commands, str) else commands
    
    async def check(self, update: Union[Message, Update], bot: Any) -> bool:
        if not isinstance(update, Message):
            return False
        
        text = update.text or ""
        if not text.startswith('/'):
            return False
        
        command = text.split()[0][1:].lower()  # Remove '/' and get first word
        return command in [cmd.lower() for cmd in self.commands]

class TextFilter(Filter):
    """Filter for message text"""
    
    def __init__(self, text: Union[str, List[str], Pattern], ignore_case: bool = True):
        self.text = text
        self.ignore_case = ignore_case
    
    async def check(self, update: Union[Message, Update], bot: Any) -> bool:
        if not isinstance(update, Message):
            return False
        
        message_text = update.text or ""
        
        if isinstance(self.text, Pattern):
            return bool(self.text.search(message_text))
        
        texts = [self.text] if isinstance(self.text, str) else self.text
        
        if self.ignore_case:
            message_text = message_text.lower()
            texts = [text.lower() for text in texts]
        
        return any(text in message_text for text in texts)

class StateFilter(Filter):
    """Filter for user state"""
    
    def __init__(self, state: Union[str, List[str]]):
        self.states = [state] if isinstance(state, str) else state
    
    async def check(self, update: Union[Message, Update], bot: Any) -> bool:
        # This would work with a state manager
        # For now, it's a placeholder implementation
        return True

class ChatTypeFilter(Filter):
    """Filter for chat type (private, group, etc.)"""
    
    def __init__(self, chat_type: str):
        self.chat_type = chat_type
    
    async def check(self, update: Union[Message, Update], bot: Any) -> bool:
        if not isinstance(update, Message):
            return False
        
        if self.chat_type == "private":
            return update.peer_id == update.from_id
        elif self.chat_type == "group":
            return update.peer_id != update.from_id
        return False

class UserFilter(Filter):
    """Filter for specific users"""
    
    def __init__(self, user_ids: Union[int, List[int]]):
        self.user_ids = [user_ids] if isinstance(user_ids, int) else user_ids
    
    async def check(self, update: Union[Message, Update], bot: Any) -> bool:
        if isinstance(update, Message):
            return update.from_id in self.user_ids
        return False

class ContentTypeFilter(Filter):
    """Filter for message content type"""
    
    def __init__(self, content_type: str):
        self.content_type = content_type
    
    async def check(self, update: Union[Message, Update], bot: Any) -> bool:
        if not isinstance(update, Message):
            return False
        
        if self.content_type == "text":
            return bool(update.text and update.text.strip())
        elif self.content_type == "attachment":
            return bool(update.attachments)
        elif self.content_type == "sticker":
            return any(att.get('type') == 'sticker' for att in update.attachments)
        elif self.content_type == "photo":
            return any(att.get('type') == 'photo' for att in update.attachments)
        
        return False

# Filter combinations
class AndFilter(Filter):
    """Logical AND for filters"""
    
    def __init__(self, *filters: Filter):
        self.filters = filters
    
    async def check(self, update: Union[Message, Update], bot: Any) -> bool:
        return all(await filter_obj.check(update, bot) for filter_obj in self.filters)

class OrFilter(Filter):
    """Logical OR for filters"""
    
    def __init__(self, *filters: Filter):
        self.filters = filters
    
    async def check(self, update: Union[Message, Update], bot: Any) -> bool:
        return any(await filter_obj.check(update, bot) for filter_obj in self.filters)

class NotFilter(Filter):
    """Logical NOT for filter"""
    
    def __init__(self, filter_obj: Filter):
        self.filter = filter_obj
    
    async def check(self, update: Union[Message, Update], bot: Any) -> bool:
        return not await self.filter.check(update, bot)

# Convenience functions
def command(commands: Union[str, List[str]]) -> CommandFilter:
    return CommandFilter(commands)

def text(text_pattern: Union[str, List[str], Pattern]) -> TextFilter:
    return TextFilter(text_pattern)

def state(state_value: Union[str, List[str]]) -> StateFilter:
    return StateFilter(state_value)

def chat_type(chat_type: str) -> ChatTypeFilter:
    return ChatTypeFilter(chat_type)

def user(user_ids: Union[int, List[int]]) -> UserFilter:
    return UserFilter(user_ids)

def content_type(content_type: str) -> ContentTypeFilter:
    return ContentTypeFilter(content_type)
