# Main file for my discord bot
# Author: Luis Angel Beltran Sanchez
# Version: 1.0.0

import asyncio
import logging

from core.bot import MusicBot
from core.config import load_config
from core.logger import setup_logging

async def main() -> None:
    setup_logging(level=logging.INFO)
    log = logging.getLogger(__name__)

    try:
        config = load_config()
    except EnvironmentError as e:
        log.critical(str(e))
        return

    bot = MusicBot(config)

    async with bot:
        log.info(f"Token starts with: {config.discord_token[:10]}")
        await bot.start(config.discord_token)

if __name__ == "__main__":
    asyncio.run(main())