import aiohttp
import asyncio
import json
import logging
from typing import Callable, Dict, List, Any, Optional, Union

from .handlers import HandlerManager, MessageHandler, EventHandler, message_handler, event_handler
from .filters import Filter, CommandFilter, TextFilter
from .types import Message, Update
from .keyboard import Keyboard, Button, ButtonColor
from .utils import rate_limiter, api_utils, logger as util_logger

class VKgramBot:
    """
    VKgramBot - Complete async VK bot library
    """
    
    def __init__(
        self, 
        token: str,
        group_id: int,
        api_version: str = "5.199",
        workers: int = 10,
        parse_mode: str = "HTML"
    ):
        self.token = token
        self.group_id = group_id
        self.api_version = api_version
        self.workers = workers
        self.parse_mode = parse_mode
        
        self.base_url = "https://api.vk.com/method"
        
        # Core components
        self.handler_manager = HandlerManager()
        self.session: Optional[aiohttp.ClientSession] = None
        self.connector: Optional[aiohttp.TCPConnector] = None
        
        # Long Poll
        self.lp_server = None
        self.lp_key = None
        self.lp_ts = None
        
        # Performance
        self.semaphore = asyncio.Semaphore(workers)
        self.update_queue = asyncio.Queue(maxsize=1000)
        
        # Auto-register handlers from decorators
        self._auto_handlers = []
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def message_handler(self, *filters: Filter):
        """Decorator for message handlers"""
        def decorator(func: Callable) -> Callable:
            handler = MessageHandler(func, list(filters))
            self._auto_handlers.append(('message', handler))
            return func
        return decorator
    
    def event_handler(self, event_type: str, *filters: Filter):
        """Decorator for event handlers"""
        def decorator(func: Callable) -> Callable:
            handler = EventHandler(event_type, func, list(filters))
            self._auto_handlers.append(('event', handler))
            return func
        return decorator
    
    async def start(self):
        """Start VKgram bot"""
        self.connector = aiohttp.TCPConnector(limit=100, limit_per_host=20)
        self.session = aiohttp.ClientSession(connector=self.connector)
        
        # Register auto-handlers
        for handler_type, handler in self._auto_handlers:
            if handler_type == 'message':
                self.handler_manager.register_message_handler(handler)
            elif handler_type == 'event':
                self.handler_manager.register_event_handler(handler)
        
        if not await self._setup_long_poll():
            raise Exception("Failed to setup Long Poll")
        
        self.logger.info("🚀 VKgram bot started successfully")
    
    # ... (rest of the bot implementation remains similar but uses handler_manager)
    
    async def _process_update(self, update: Dict[str, Any]):
        """Process single update"""
        util_logger.log_update(update)
        
        update_type = update.get('type')
        
        if update_type == 'message_new':
            message_data = update['object']['message']
            message = Message(
                id=message_data['id'],
                from_id=message_data['from_id'],
                peer_id=message_data['peer_id'],
                text=message_data.get('text', ''),
                date=message_data['date'],
                attachments=message_data.get('attachments', []),
                payload=message_data.get('payload')
            )
            await self.handler_manager.process_message(message, self)
        
        else:
            update_obj = Update(
                type=update_type,
                object=update.get('object', {}),
                group_id=update.get('group_id', 0),
                event_id=update.get('event_id', '')
            )
            await self.handler_manager.process_event(update_obj, self)
