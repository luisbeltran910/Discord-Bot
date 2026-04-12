# Global error handler for the commands
# Author: Luis Angel Beltran Sanchez
# Version: 1.0.0

import logging
import traceback

import discord
from discord import app_commands
from discord.ext import commands

from core.errors import BotError

log = logging.getLogger(__name__)

class ErrorHandler(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        bot.tree.on_error = self.on_app_command_error

        @commands.Cog.listener()
        async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
            original = getattr(error, "original", error)
            await self._handle(ctx, original, is_interaction=False)

        async def on_app_command_error(
                self,
                interaction: discord.Interaction,
                error: app_commands.AppCommandError,
        ):
            original = getattr(error, "original", error)
            await self.handle(interaction, original, is_interaction=True)

        async def _handle(self, ctx_or_interaction, error: Exception, is_interaction: bool):
            embed = discord.Embed(color=discord.Color.red())

            if isinstance(error, BotError):
                embed.description = error.user_message
                log.warning(f"BotError: {error.log_message}")

            elif isinstance(error, commands.CheckFailure):
                embed.description = str(error) or "❌ No tienes permiso para usar este comando."

            elif isinstance(error, commands.MissingRequiredArgument):
                embed.description = f"❌ Argumento faltante: `{error.param.name}`"

            elif isinstance(error, commands.BadArgument):
                embed.description = f"❌ Argumento invalido - {error}"

            elif isinstance(error, commands.CommandNotFound):
                return
            
            else:
                log.error(
                    f"Error inesperado:\n{''.join(traceback.format_exception(type(error), error, error.__traceback__))}"
                )
                embed.description = "❌ Algo salio mal, el problema fue anotado."

            try:
                if is_interaction:
                    if ctx_or_interaction.response.is_done():
                        await ctx_or_interaction.followup.send(embed=embed, ephemeral=True)
                    else:
                        await ctx_or_interaction.response.send_message(embed=embed, ephemeral=True)
                else:
                    await ctx_or_interaction.send(embed=embed)
            except discord.HTTPException:
                pass

async def setup(bot: commands.Bot):
    await bot.add_cog(ErrorHandler(bot))