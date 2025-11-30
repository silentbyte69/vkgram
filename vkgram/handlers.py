from typing import Callable, Dict, Any, Optional, Union, List
from .types import Message, Update
from .filters import Filter, CommandFilter, TextFilter, StateFilter

class Handler:
    """Base handler class"""
    
    def __init__(self, callback: Callable, filters: Optional[List[Filter]] = None):
        self.callback = callback
        self.filters = filters or []
    
    async def check(self, update: Union[Message, Update], bot: Any) -> bool:
        """Check if handler should process the update"""
        for filter_obj in self.filters:
            if not await filter_obj.check(update, bot):
                return False
        return True

class MessageHandler(Handler):
    """Handler for message events"""
    
    def __init__(self, callback: Callable, filters: Optional[List[Filter]] = None):
        super().__init__(callback, filters)
    
    async def handle(self, message: Message, bot: Any):
        """Handle message"""
        if await self.check(message, bot):
            return await self.callback(message, bot)

class EventHandler(Handler):
    """Handler for other VK events"""
    
    def __init__(self, event_type: str, callback: Callable, filters: Optional[List[Filter]] = None):
        super().__init__(callback, filters)
        self.event_type = event_type
    
    async def handle(self, update: Update, bot: Any):
        """Handle event"""
        if update.type == self.event_type and await self.check(update, bot):
            return await self.callback(update, bot)

class HandlerManager:
    """Manager for all handlers"""
    
    def __init__(self):
        self.message_handlers: List[MessageHandler] = []
        self.event_handlers: List[EventHandler] = []
    
    def register_message_handler(self, handler: MessageHandler):
        """Register message handler"""
        self.message_handlers.append(handler)
    
    def register_event_handler(self, handler: EventHandler):
        """Register event handler"""
        self.event_handlers.append(handler)
    
    async def process_message(self, message: Message, bot: Any):
        """Process message with all registered handlers"""
        for handler in self.message_handlers:
            await handler.handle(message, bot)
    
    async def process_event(self, update: Update, bot: Any):
        """Process event with all registered handlers"""
        for handler in self.event_handlers:
            await handler.handle(update, bot)

# Decorators for easy handler registration
def message_handler(*filters: Filter):
    """Decorator for message handlers"""
    def decorator(func: Callable) -> Callable:
        handler = MessageHandler(func, list(filters))
        # This will be registered when bot starts
        func._handler = handler
        return func
    return decorator

def event_handler(event_type: str, *filters: Filter):
    """Decorator for event handlers"""
    def decorator(func: Callable) -> Callable:
        handler = EventHandler(event_type, func, list(filters))
        func._handler = handler
        return func
    return decorator
