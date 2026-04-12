# Join and leave handler
# Author: Luis Angel Beltran Sanchez
# Version: 1.0.0

import logging
from datetime import datetime, timezone

import discord
from discord.ext import commands

log = logging.getLogger(__name__)

class JoinLeave(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config = bot.config

    @commands.Cog.listener()
    async def on_member_Join(self, member: discord.Member):
        channel = discord.utils.get(
            member.guild.text_channels,
            name=self.config.welcome_channel,
        )
        if channel is None:
            log.warning(f"Canal de bienvenida #{self.config.welcome_channel} no encontrado en {member.guild.name}")
            return
        
        embed = discord.Embed(
            title=f"👋 Bienvenid@, {member.display_name}!",
            description=(
                f"Hey {member.mention}, Entra para pasar el rato!\n\n"
            ),
            color=discord.Color.green(),
            timestamp=datetime.now(timezone.utc),
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"ID: {member.id}")
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        channel = discord.utils.get(
            member.guild.text_channels,
            name=self.config.goodbye_channel,
        )
        if channel is None:
            return
        
        embed = discord.Embed(
            title=f"👋 Adios, {member.display_name}",
            description=f"**{member.name}** fue bueno duro mientras duro supongo.",
            color=discord.Color.orange(),
            timestamp=datetime.now(timezone.utc),
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"ID: {member.id}")
        await channel.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(JoinLeave(bot))