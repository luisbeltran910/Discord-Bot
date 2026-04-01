# Resolver will handle our music requests messages and source
# Author: Luis Angel Beltran Sanchez
# Version: 1.0.0

from __future__ import annotations

import asyncio
import logging
import re
from typing import TYPE_CHECKING

import discord
import yt_dlp

from core.errors import SpotifyError, TrackError

if TYPE_CHECKING:
    from core.config import Config
    from cogs.music.song import Song

log = logging.getLogger(__name__)

# Our yt-dlp config stuff
_BASE_OPTIONS = {
    "format": "bestaudio/best",
    "quiet": True,
    "no_warnings": True,
    "default_search": "ytsearch",
    "source_address": "0.0.0.0",
}

YTDL_SINGLE = yt_dlp.YoutubeDL({**_BASE_OPTIONS, "noplaylist": True})
YTDL_PLAYLIST = yt_dlp.YoutubeDL({**_BASE_OPTIONS, "noplaylist": False, "extract_flat": True})

FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn",
}

# Some URL patterns for the bot
_SPOTIFY_TRACK = re.compile(r"open\.spotify\.com/track/([A-Za-z0-9]+)")
_SPOTIFY_PLAYLIST = re.compile(r"open\.spotify\.com/playlist/([A-Za-z0-9]+)")
_YT_PLAYLIST = re.compile(r"youtube\.com/playlist\?list=")

# Our whole audio source or where we make it
def make_audio_source(stream_url: str, volume: float = 0.5) -> discord.PCMVolumeTransformer:
    raw = discord.FFmpegPCMAudio(stream_url, **FFMPEG_OPTIONS)
    return discord.PCMVolumeTransformer(raw, volume=volume)
