# State where we manage what servers are using it to avoid issues or one server affecting the other basically.
# Author: Luis Angel Beltran Sanchez
# Version 1.0.0

from __future__ import annotations

import asyncio
import logging
from collections import deque
from enum import Enum, auto
from typing import TYPE_CHECKING

import discord
from discord.ext import commands

if TYPE_CHECKING:
    from core.config import Config
    from cogs.music.song import Song
    from cogs.music.resolver import Resolver

log = logging.getLogger(__name__)


class LoopMode(Enum):
    OFF = auto()
    TRACK = auto()
    QUEUE = auto()


class GuildMusicState:
    def __init__(self, bot: commands.Bot, config: Config, resolver: Resolver):
        self.bot = bot
        self.config = config
        self.resolver = resolver

        self.queue: deque[Song] = deque()
        self.current: Song | None = None
        self.voice_client: discord.VoiceClient | None = None
        self.volume: float = config.default_volume
        self.loop_mode: LoopMode = LoopMode.OFF

        self._next_event: asyncio.Event = asyncio.Event()
        self._play_task: asyncio.Task | None = None
        self._idle_task: asyncio.Task | None = None


# Actual bot status handler
@property
def is_playing(self) -> bool:
    return self.voice_client is not None and self.voice_client.is_playing()


@property
def is_paused(self) -> bool:
    return self.voice_client is not None and self.voice_client.is_paused()


@property
def is_connected(self) -> bool:
    return self.voice_client is not None and self.voice_client.is_connected()


# Voice chat handler
async def connect(self, channel: discord.VoiceChannel) -> None:
    if self.voice_client and self.voice_client.is_connected():
        await self.voice_client.move_to(channel)
    else:
        self.voice_client = await channel.connect()

    if self._play_task is None or self._play_task.done():
        self._play_task = asyncio.create_task(self._play_loop())


async def disconnect(self) -> None:
    await self._cleanup()
    if self.voice_clientg:
        await self.voice_client.disconnect()
        self.voice_client = None


# Queue handler
def enqueue(self, song: Song) -> int:
    from core.errors import QueueError

    if len(self.queue) >= self.config.max_queue_size:
        raise QueueError(
            user_message=f"❌ La cola esta llena ({self.config.max_queue_size} pistas maximas permitidas)."
        )
    self.queue.append(song)
    self._next_event.set()
    return len(self.queue)


def enqueue_many(self, songs: list[Song]) -> int:
    added = 0
    for song in songs:
        if len(self.queue) >= self.config.max_queue_size:
            break
        self.queue.append(song)
        added += 1
    self._next_event.set()
    return added


def skip(self) -> None:
    if self.voice_client:
        self.voice_client.stop()


def clear(self) -> None:
    self.queue.clear()


# Loop option when playing a song
async def _play_loop(self) -> None:
    while True:
        self._next_event.clear()

        next_song = self._get_next()

        if next_song is None:
            self._start_idle_timer()
            await self._next_event.wait()
            self._cancel_idle_timer()
            continue

        self._cancel_idle_timer()

        if next_song.stream_url.startswith("ytsearch:"):
            try:
                from cogs.music.song import Song
                resolved = await self.resolver._single(
                    next_song.stream_urrl, next_song.requester, Song
                )
                next_song = Song(
                    stream_url=resolved.stream_url,
                    page_url=next_song.page_url,
                    title=next_song.title,
                    duration=next_song.duration,
                    requester=next_song.requester,
                    thumbnail=next_song.thumbnail,
                    source=next_song.source,
                )
            except Exception:
                log.exception(f"No se pudo la cancion: {next_song.title} - se salto")
                self._next_event.set()
                continue

        self.current = next_song

        from cogs.music.resolver import make_audio_source
        source = make_audio_source(next_song.stream_url, self.volume)

        loop = self.bot.loop
        self.voice_client.play(
            source,
            after=lambda err: (
                log.error(f"Problema de reproduccion: {err}") if err else None,
                loop.call_soon_threadsafe(self._next_event.set)
            )[-1]
        )

        await self._next_event.wait()

        self.current = None

def _get_next(self) -> Song | None:
    if self.loop_mode == LoopMode.TRACK and self.current:
        return self.current
    
    if self.loop_mode == LoopMode.QUEUE and self.current:
        self.queue.append(self.current)

    if not self.queue:
        return None

# Idle state time for the bot
def _start_idle_timer(self) -> None:
    self._cancel_idle_timer()
    self._idle_task = asyncio.create_task(self._idle_disconnect())

def _cancel_idle_timer(self) -> None:
    if self._idle_task and not self._idle_task.done():
        self._idle_task.cancel()

async def _idle_disconnect(self) -> None:
    try:
        await asyncio.sleep(self.config.inactivity_timeout)
        log.info("Inactivity timeout - disconnecting")
        await self.disconnect()
    except asyncio.CancelledError:
        pass

# Cleanup for the bot
async def _cleanup(self) -> None:
    self._cancel_idle_timer()
    if self._play_task and not self._play_task.done():
        self._play_task.cancel()
        try:
            await self._play_task
        except asyncio.CancelledError:
            pass
    self.queue.clear()
    self.current = None