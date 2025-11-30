import asyncio
import aiohttp
import json
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta

class RateLimiter:
    """Rate limiter for VK API calls"""
    
    def __init__(self, max_requests: int = 3, period: float = 1.0):
        self.max_requests = max_requests
        self.period = period
        self.requests = []
        self.lock = asyncio.Lock()
    
    async def acquire(self):
        """Acquire a rate limit slot"""
        async with self.lock:
            now = asyncio.get_event_loop().time()
            
            # Remove old requests
            self.requests = [req_time for req_time in self.requests 
                           if now - req_time < self.period]
            
            if len(self.requests) >= self.max_requests:
                # Wait until the oldest request expires
                wait_time = self.period - (now - self.requests[0])
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                self.requests.pop(0)
            
            self.requests.append(now)

class APIUtils:
    """Utility methods for VK API"""
    
    @staticmethod
    def prepare_attachments(attachments: List[Dict]) -> str:
        """Convert attachments to VK API format"""
        if not attachments:
            return ""
        
        result = []
        for attachment in attachments:
            if isinstance(attachment, dict):
                attach_type = attachment.get('type', '')
                owner_id = attachment.get('owner_id', '')
                media_id = attachment.get('id', '')
                access_key = attachment.get('access_key', '')
                
                if attach_type and owner_id and media_id:
                    attach_str = f"{attach_type}{owner_id}_{media_id}"
                    if access_key:
                        attach_str += f"_{access_key}"
                    result.append(attach_str)
        
        return ",".join(result)
    
    @staticmethod
    def parse_message_payload(payload: Optional[str]) -> Dict[str, Any]:
        """Parse message payload from JSON string"""
        if not payload:
            return {}
        
        try:
            return json.loads(payload)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    @staticmethod
    def build_payload(**kwargs) -> str:
        """Build payload JSON string"""
        return json.dumps(kwargs, ensure_ascii=False)

class KeyboardUtils:
    """Utilities for keyboard creation"""
    
    @staticmethod
    def quick_reply(*buttons: str, one_time: bool = True) -> 'Keyboard':
        """Create quick reply keyboard"""
        from .keyboard import Keyboard, Button, ButtonColor
        
        kb = Keyboard(one_time=one_time)
        for button_text in buttons:
            kb.add(Button(button_text, ButtonColor.PRIMARY))
        
        return kb
    
    @staticmethod
    def inline_grid(buttons: List[List[str]], colors: List['ButtonColor'] = None) -> 'Keyboard':
        """Create inline keyboard grid"""
        from .keyboard import Keyboard, Button, ButtonColor
        
        kb = Keyboard(inline=True)
        default_colors = [ButtonColor.PRIMARY, ButtonColor.SECONDARY, 
                         ButtonColor.POSITIVE, ButtonColor.NEGATIVE]
        
        colors = colors or default_colors
        
        for row in buttons:
            row_buttons = []
            for i, text in enumerate(row):
                color = colors[i % len(colors)]
                row_buttons.append(Button(text, color))
            kb.add(*row_buttons)
        
        return kb

class TextUtils:
    """Text formatting utilities"""
    
    @staticmethod
    def escape_markdown(text: str) -> str:
        """Escape Markdown characters"""
        escape_chars = r'_*[]()~`>#+-=|{}.!'
        for char in escape_chars:
            text = text.replace(char, f'\\{char}')
        return text
    
    @staticmethod
    def truncate_text(text: str, max_length: int = 4096, suffix: str = "...") -> str:
        """Truncate text to maximum length"""
        if len(text) <= max_length:
            return text
        
        return text[:max_length - len(suffix)] + suffix

class Cache:
    """Simple async cache implementation"""
    
    def __init__(self, default_ttl: int = 300):
        self._cache = {}
        self.default_ttl = default_ttl
        self._lock = asyncio.Lock()
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set cache value"""
        async with self._lock:
            expire_time = datetime.now() + timedelta(seconds=ttl or self.default_ttl)
            self._cache[key] = (value, expire_time)
    
    async def get(self, key: str, default: Any = None) -> Any:
        """Get cache value"""
        async with self._lock:
            if key not in self._cache:
                return default
            
            value, expire_time = self._cache[key]
            if datetime.now() > expire_time:
                del self._cache[key]
                return default
            
            return value
    
    async def delete(self, key: str):
        """Delete cache value"""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
    
    async def clear(self):
        """Clear all cache"""
        async with self._lock:
            self._cache.clear()

class Logger:
    """Enhanced logger for VKgram"""
    
    def __init__(self, name: str = "vkgram"):
        self.logger = logging.getLogger(name)
    
    def log_update(self, update: Dict[str, Any]):
        """Log incoming update"""
        update_type = update.get('type', 'unknown')
        
        if update_type == 'message_new':
            message = update.get('object', {}).get('message', {})
            self.logger.info(
                f"📨 Message from {message.get('from_id')}: "
                f"{message.get('text', '').strip() or '<no text>'}"
            )
        else:
            self.logger.debug(f"📢 Event: {update_type}")

# Global instances
rate_limiter = RateLimiter()
api_utils = APIUtils()
keyboard_utils = KeyboardUtils()
text_utils = TextUtils()
cache = Cache()
logger = Logger()
