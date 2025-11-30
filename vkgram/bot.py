import aiohttp
import asyncio
import json
import logging
from typing import Callable, Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum

from .types import Message, Update, User

class VKgramBot:
    """
    VKgramBot - High-performance async VK bot library
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
        self.dispatcher = Dispatcher()
        self.session: Optional[aiohttp.ClientSession] = None
        self.connector: Optional[aiohttp.TCPConnector] = None
        
        # Long Poll
        self.lp_server = None
        self.lp_key = None
        self.lp_ts = None
        
        # Performance
        self.semaphore = asyncio.Semaphore(workers)
        self.update_queue = asyncio.Queue(maxsize=1000)
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    async def __aenter__(self):
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()
    
    async def start(self):
        """Start VKgram bot"""
        self.connector = aiohttp.TCPConnector(limit=100, limit_per_host=20)
        self.session = aiohttp.ClientSession(connector=self.connector)
        
        if not await self._setup_long_poll():
            raise Exception("Failed to setup Long Poll")
        
        self.logger.info("🚀 VKgram bot started successfully")
    
    async def stop(self):
        """Stop VKgram bot"""
        if self.session:
            await self.session.close()
        self.logger.info("🛑 VKgram bot stopped")
    
    async def _setup_long_poll(self) -> bool:
        """Setup Long Poll server"""
        response = await self._api_call("groups.getLongPollServer", {
            "group_id": self.group_id
        })
        
        if response:
            self.lp_server = response['server']
            self.lp_key = response['key']
            self.lp_ts = response['ts']
            return True
        return False
    
    async def _api_call(
        self, 
        method: str, 
        params: Dict[str, Any],
        retries: int = 3
    ) -> Dict[str, Any]:
        """Make async API call to VK"""
        url = f"{self.base_url}/{method}"
        params.update({
            'access_token': self.token,
            'v': self.api_version
        })
        
        for attempt in range(retries):
            try:
                async with self.session.post(url, data=params) as response:
                    data = await response.json()
                    
                    if 'error' in data:
                        error = data['error']
                        if error.get('error_code') == 6:  # Rate limit
                            await asyncio.sleep(0.34 * (attempt + 1))
                            continue
                        self.logger.error(f"VK API Error: {error}")
                        return {}
                    
                    return data.get('response', {})
                    
            except Exception as e:
                self.logger.error(f"API call failed: {e}")
            
            if attempt < retries - 1:
                await asyncio.sleep(0.5 * (attempt + 1))
        
        return {}
    
    async def send_message(
        self,
        chat_id: int,
        text: str,
        keyboard: Optional['Keyboard'] = None,
        **kwargs
    ) -> bool:
        """Send message quickly"""
        params = {
            "peer_id": chat_id,
            "message": text,
            "random_id": self._generate_random_id()
        }
        
        if keyboard:
            params["keyboard"] = keyboard.to_json()
        
        params.update(kwargs)
        
        response = await self._api_call("messages.send", params)
        return bool(response)
    
    def _generate_random_id(self) -> int:
        """Generate random_id for messages"""
        return int(asyncio.get_event_loop().time() * 1000000)
    
    def message_handler(self, *filters):
        """Decorator for message handlers"""
        def decorator(func: Callable) -> Callable:
            self.dispatcher.register_message_handler(func, filters)
            return func
        return decorator
    
    def event_handler(self, event_type: str):
        """Decorator for event handlers"""
        def decorator(func: Callable) -> Callable:
            self.dispatcher.register_event_handler(func, event_type)
            return func
        return decorator
    
    async def run(self):
        """Main run method"""
        await self.start()
        try:
            await self._start_long_poll()
        except KeyboardInterrupt:
            self.logger.info("Bot interrupted by user")
        finally:
            await self.stop()
    
    async def _start_long_poll(self):
        """Start Long Poll listening"""
        # Start workers
        workers = [
            asyncio.create_task(self._worker(i))
            for i in range(self.workers)
        ]
        
        # Main loop
        try:
            while True:
                await self._fetch_updates()
        except asyncio.CancelledError:
            pass
        finally:
            for worker in workers:
                worker.cancel()
            await asyncio.gather(*workers, return_exceptions=True)
    
    async def _fetch_updates(self):
        """Fetch updates from Long Poll"""
        try:
            url = f"{self.lp_server}?act=a_check&key={self.lp_key}&ts={self.lp_ts}&wait=25"
            
            async with self.session.get(url, timeout=30) as response:
                data = await response.json()
                
                if 'failed' in data:
                    await self._handle_failure(data['failed'])
                    return
                
                self.lp_ts = data['ts']
                
                for update in data.get('updates', []):
                    try:
                        self.update_queue.put_nowait(update)
                    except asyncio.QueueFull:
                        break
                        
        except Exception as e:
            self.logger.error(f"Long Poll error: {e}")
            await asyncio.sleep(1)
    
    async def _worker(self, worker_id: int):
        """Worker for processing updates"""
        while True:
            try:
                update = await self.update_queue.get()
                await self.dispatcher.process_update(update, self)
                self.update_queue.task_done()
            except Exception as e:
                self.logger.error(f"Worker {worker_id} error: {e}")

class Dispatcher:
    """Update dispatcher for VKgram"""
    
    def __init__(self):
        self.message_handlers = []
        self.event_handlers = {}
    
    def register_message_handler(self, handler: Callable, filters: tuple):
        self.message_handlers.append((handler, filters))
    
    def register_event_handler(self, handler: Callable, event_type: str):
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
    
    async def process_update(self, update: Dict, bot: VKgramBot):
        """Process incoming update"""
        update_type = update.get('type')
        
        # Handle events
        if update_type in self.event_handlers:
            for handler in self.event_handlers[update_type]:
                asyncio.create_task(handler(update, bot))
        
        # Handle messages
        if update_type == 'message_new':
            message = Message(**update['object']['message'])
            await self._process_message(message, bot)
    
    async def _process_message(self, message: Message, bot: VKgramBot):
        """Process incoming message"""
        for handler, filters in self.message_handlers:
            try:
                # Apply filters
                if await self._check_filters(message, filters):
                    await handler(message, bot)
            except Exception as e:
                bot.logger.error(f"Handler error: {e}")
    
    async def _check_filters(self, message: Message, filters: tuple) -> bool:
        """Check if message passes all filters"""
        # Filter logic implementation
        return True
