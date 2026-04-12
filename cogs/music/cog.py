# Music commands for discord
# Author: Luis Angel Beltran Sanchez
# Version: 1.0.0

from __future__ import annotations

import logging
import random
from collections import deque
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from cogs.music.resolver import Resolver
from cogs.music.state import GuildMusicState, LoopMode
from core.errors import BotError, QueueError, VoiceError

log = logging.getLogger(__name__)

class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.resolver = Resolver(bot.config)
        self._states: dict[int, GuildMusicState] = {}
    
    def get_state(self, guild: discord.Guild) -> GuildMusicState:
        if guild.id not in self._states:
            self._states[guild.id] = GuildMusicState(self.bot, self.bot.config, self.resolver)
        return self._states[guild.id]

    async def _ensure_voice(self, ctx: commands.Context) -> GuildMusicState:
        if not ctx.author.voice:
            raise VoiceError(user_message="❌ tienes que estar en el canal primero.")
        state = self.get_state(ctx.guild)
        await state.connect(ctx.author.voice.channel)
        return state
    
    # /play command
    @commands.hybrid_command(name="play", aliases=["p"])
    @app_commands.describe(query="Nombre de una cancion, Link de YouTube, Spotify o Soundcloud")
    async def play(self, ctx: commands.Context, *, query: str):
        """Dale play a una cancion o agregalo a la cola."""
        await ctx.defer()

        state = await self._ensure_voice(ctx)
        songs = await self.resolver.resolve(
            query,
            ctx.author,
            max_entries=self.bot.config.max_playlist_size
        )

        if len(songs) == 1:
            pos = state.enqueue(songs[0])
            song = songs[0]
            title = "🎵 Reproduciendo Ahora" if not state.is_playing else "➕ Agregado a la cola"
            embed = song.to_embed(title=title)
            embed.add_field(name="Position", value=str(pos), inline=True)
            await ctx.send(embed=embed)
        else:
            added = state.enqueue_many(songs)
            embed = discord.Embed(
                title="📋 Playlist Agregado",
                description=f"En cola **{added}** pistas",
                color=discord.Color.blurple(),
            )
            embed.add_field(name="Primera pista", value=songs[0].title, inline=False)
            await ctx.send(embed=embed)
    
    # /playlist command
    @commands.hybrid_command(name="playlist", aliases=["pl"])
    @app_commands.describe(
        url="Link del playlist de YouTube o Spotify",
        limit="Maximo numero de pistas para agregar"
    )
    async def playlist(self, ctx: commands.Context, url: str, limit: Optional[int] = None):
        """Agrega toda una playlist a la cola."""
        await ctx.defer()

        state = await self._ensure_voice(ctx)
        max_entries = min(limit or self.bot.config.max_playlist_size, self.bot.config.max_playlist_size)
        songs = await self.resolver.resolve(url, ctx.author, max_entries=max_entries)

        if not songs:
            return await ctx.send("❌ No se pudo encontrar ninguna cancion en el playlist.")
        
        added = state.enqueue_many(songs)
        embed = discord.Embed(
            title="📋 Playlist Agregada",
            color=discord.Color.blurple(),
        )
        embed.add_field(name="Pistas agregas", value=str(added), inline=True)
        embed.add_field(name="Tamaño de la cola", value=str(len(state.queue)), inline=True)
        embed.add_field(name="Primera cancion", value=songs[0].title, inline=False)
        await ctx.send(embed=embed)
    
    # /skip command
    @commands.hybrid_command(name="skip", aliases=["s"])
    async def skip(self, ctx: commands.Context):
        """Salta la cancion actual."""
        state = self.get_state(ctx.guild)
        if not state.is_playing and not state.is_paused:
            raise QueueError(user_message="❌ No hay nada tocando ahorita.")
        state.skip()
        await ctx.send("⏭️ Saltado.")

    # /stop command
    @commands.hybrid_command(name="stop")
    async def stop(self, ctx: commands.Context):
        """Para la cola y me salgo"""
        state = self.get_state(ctx.guild)
        await state.disconnect()
        await ctx.send("⏹️ Detenido y desconectado.")
    
    # /pause command
    @commands.hybrid_command(name="pause")
    async def pause(self, ctx: commands.Context):
        """Continuar musica pausada"""
        state = self.get_state(ctx.guild)
        if not state.is_playing:
            raise QueueError(user_message="❌ La pista no esta pausada.")
        state.voice_client.pause()
        await ctx.send("⏸️ Pausando.")

    # /resume command
    @commands.hybrid_command(name="resume")
    async def resume(self, ctx: commands.Context):
        """Continuar tocando la pista."""
        state = self.get_state(ctx.guild)
        if not state.is_paused:
            raise QueueError(user_message=f"❌ La cola no esta pausada.")
        state.voice_client.resume()
        await ctx.send("▶️ Continuando.")
    
    # /nowplaying command
    @commands.hybrid_command(name="nowplaying", aliases=["np"])
    async def nowplaying(self, ctx: commands.Context):
        """Te muestra lo que esta tocando ahorita."""
        state = self.get_state(ctx.guild)
        if not state.current:
            raise QueueError(user_message="❌ No hay nada tocando ahorita.")
        await ctx.send(embed=state.current.to_embed())

    # /queue command
    @commands.hybrid_command(name="queue", aliases=["q"])
    @app_commands.describe(page="Numero de pagina (10 pistas por pagina)")
    async def queue(self, ctx: commands.Context, page: int = 1):
        """Muestra la cola actual."""
        state = self.get_state(ctx.guild)

        per_page = 10
        total = len(state.queue)
        max_pages = max(1, -(-total // per_page))
        page = max(1, min(page, max_pages))

        embed = discord.Embed(title="🎵 Cola", color = discord.Color.blurple())

        if state.current:
            loop_indicator = {
                LoopMode.OFF: "",
                LoopMode.TRACK: " 🔂",
                LoopMode.QUEUE: " 🔁",
            }[state.loop_mode]
            embed.add_field(
                name=f"Ahora tocando{loop_indicator}",
                value=f"**{state.current.title}** - {state.current.duration_str}",
                inline=False,
            )

        if total == 0:
            embed.add_field(name="Siguiente pista", value="La cola esta vacia", inline=False)
        else:
            queue_list = list(state.queue)
            start = (page - 1) * per_page
            items = queue_list[start:start + per_page]
            lines = [
                f"`{start + i + 1}.` {s.title} - {s.duration_str}"
                for i, s in enumerate(items)
            ]
            embed.add_field(
                name=f"Siguiente Pista (page {page}/{max_pages})",
                value="\n".join(lines),
                inline=False,
            )
            embed.set_footer(text=f"{total} pista(s) en la cola")

        await ctx.send(embed=embed)
    
    # /remove command
    @commands.hybrid_command(name="remove")
    @app_commands.describe(position="Posicion en la cola a eliminar")
    async def remove(self, ctx: commands.Context, position: int):
        """Elimina una pista de la cola por posicion."""
        state = self.get_state(ctx.guild)
        queue_list = list(state.queue)

        if not (1 <= position <= len(queue_list)):
            raise QueueError(user_message=f"❌ Posicion invalida. La cola tiene {len(queue_list)} pista(s).")
        
        removed = queue_list.pop(position - 1)
        state.queue = deque(queue_list)
        await ctx.send(f"🗑️ Eliminado **{removed.title}** de la posicion {position}.")

    # /loop command
    @commands.hybrid_command(name="loop")
    @app_commands.describe(mode="apagado = continua por el playlist | track = se repite la pista | cola = se repite todo")
    @app_commands.choices(mode=[
        app_commands.Choice(name="apagado", value="apagado"),
        app_commands.Choice(name="pista", value="pista"),
        app_commands.Choice(name="cola", value="cola"),
    ])
    async def loop(self, ctx: commands.Context, mode: str = "apagado"):
        """Elige el modo de repetir."""
        state = self.get_state(ctx.guild)
        mapping = {
            "apagado": LoopMode.OFF,
            "pista": LoopMode.TRACK,
            "cola": LoopMode.QUEUE,
        }
        if mode not in mapping:
            raise QueueError(user_message="❌ El modo al elegir debe ser `apagado`, `pista` o `cola`.")
        state.loop_mode = mapping[mode]
        labels = {
            "apagado": "⏹️ repetir apagado",
            "pista": "🔁 Repitiendo la pista actual",
            "cola": "🔁 Repitiendo la cola actual"
        }
        await ctx.send(labels[mode])

    # /volume command
    @commands.hybrid_command(name="volume", aliases=["vol"])
    @app_commands.describe(level="Volumen del 0 al 100")
    async def volume(self, ctx: commands.Context, level: int):
        """Selecciona el volumen actual"""
        if not 0 <= level <= 100:
            raise QueueError(user_message="❌ El volumen debe de ser entre 0 y 100.")
        state = self.get_state(ctx.guild)
        state.volume = level / 100
        if state.voice_client and state.voice_client.source:
            state.voice_client.source.volume = state.volume
        await ctx.send(f"🔊 Volumen en el nivel **{level}**%")

    # /shuffle command
    @commands.hybrid_command(name="shuffle")
    async def shuffle(self, ctx: commands.Context):
        """Modo aleatorio para la cola."""
        state = self.get_state(ctx.guild)
        if len(state.queue) < 2:
            raise QueueError(user_message="❌ Necesitas al menos 2 pistas para el modo aleatorio.")
        q = list(state.queue)
        random.shuffle(q)
        state.queue = deque(q)
        await ctx.send(f"🔀 Mezclando {len(q)} pistas.")

    # Auto-Disconnect for when everyone leaves the voice channel
    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ):
        if member.bot:
            return
        
        state = self._states.get(member.guild.id)
        if not state or not state.is_connected:
            return
        
        bot_channel = state.voice_client.channel
        if before.channel == bot_channel and after.channel != bot_channel:
            humans = [m for m in bot_channel.members if not m.bot]
            if not humans:
                log.info(f"Everyone left {bot_channel.name} - starting idle time")
                state._start_idle_timer()

async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))