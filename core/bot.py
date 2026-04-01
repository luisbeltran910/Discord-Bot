# Our bot stuff for the actual core part which will handle music, etc
# Author: Luis Angel Beltran Sanchez
# Version: 1.0.0

import logging
import discord
from discord.ext import commands
from core.config import Config

log = logging.getLogger(__name__)

EXTENSIONS = [
    "cogs.music.cog",
    "cogs.events.join_leave",
    "cogs.events.errors",
]

class MusicBot(commands.Bot):
    def __init__(self, config: Config):
        self.config = config

        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True

        super().__init__(
            command_prefix=commands.when_mentioned_or(config.prefix),
            intents=intents,
        )

    async def setup_hook(self) -> None:
        log.info("Loading extensions...")

        for ext in EXTENSIONS:
            try:
                await self.load_extension(ext)
                log.info(f" Enabled: {ext}")
            except Exception:
                log.exception(f" Disabled: {ext}")

            try:
                synced = await self.tree.sync()
                log.info(f"Synced {len(synced)} slash command(s)")
            except Exception:
                log.exception("Failed to sync slash commands")

    async def on_ready(self) -> None:
        log.info(f"Logged in as {self.user} (ID: {self.user.id})")
        log.info(f"Connected to {len(self.guilds)} server(s)")

        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.listening,
                name="/play"
        )
    )

    async def close(self) -> None:
        log.info("Shutting down...")
        await super().close()