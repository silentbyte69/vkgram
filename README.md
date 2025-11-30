# VKgram

Modern async VK bot library inspired by aiogram

## Features

- 🚀 **Fully asynchronous** - Built on asyncio for maximum performance
- ⚡ **High-performance** - Handles thousands of messages per second
- 🎯 **aiogram-like API** - Familiar interface for Telegram bot developers
- 🔧 **Powerful filters** - Flexible message filtering system
- ⌨️ **Easy keyboards** - Simple keyboard builder
- 📊 **Rate limiting** - Built-in rate limit handling
- 🛠 **Extensible** - Middleware support and custom handlers

## Installation

```bash
pip install vkgram
```

# Quick Start

```python
import asyncio
from vkgram import VKgramBot
from vkgram.filters import command

bot = VKgramBot(token="YOUR_TOKEN", group_id=YOUR_GROUP_ID)

@bot.message_handler(command("start"))
async def start_handler(message, bot):
    await bot.send_message(message.chat_id, "Hello from VKgram! 🚀")

async def main():
    async with bot:
        await bot.run()

if __name__ == "__main__":
    asyncio.run(main())
```

# License

MIT License
