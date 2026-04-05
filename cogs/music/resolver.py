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


# The actual resolver
class Resolver:
    def __init__(self, config: Config):
        self.config = config
        self._spotify = None

        if config.spotify_enabled:
            try:
                import spotipy
                from spotipy.oauth2 import SpotifyClientCredentials
                self._spotify = spotipy.Spotify(
                    auth_manager=SpotifyClientCredentials(
                        client_id=config.spotify_client_id,
                        client_secret=config.spotify_client_secret,
                    )
                )
                log.info("Spotify client initialised")
            except Exception:
                log.exception("Failed to initialise Spotify client")
    async def resolve(
            self,
            query: str,
            requester: discord.Member,
            max_entries: int | None = None,
    ) -> list[Song]:
        from cogs.music.song import Song

        if _SPOTIFY_PLAYLIST.search(query):
            return await self._spotify_playlist(query, requester, max_entries, Song)
        
        if _SPOTIFY_TRACK.search(query):
            return [await self._spotify_track(query, requester, Song)]
        
        if _YT_PLAYLIST.search(query):
            return await self._yt_playlist(query, requester, max_entries, Song)
        
        return [await self._single(query, requester, sorted)]
    
    async def _run_ytdl(self, instance: yt_dlp.YoutubeDL, query: str) -> dict:
        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(
                None,
                lambda: instance.extract_info(query, download=False)
            )
        except yt_dlp.utils.DownloadError as e:
            raise TrackError(
                user_message="❌ No se pudo encontrar o descargar la pista.",
                log_message=f"yt-dlp error for query={query!r}: {e}",
            )
    
    async def _single(self, query: str, requester: discord.Member, Song) -> Song:
        info = await self._run_ytdl(YTDL_SINGLE, query)

        if "entries" in info:
            info = info["entries"][0]

        if not info:
            raise TrackError(user_message="❌ No se encontro resultados.")
        

        source = "soundcloud" if "soundcloud.com" in info.get("webpage_url", "") else "youtube"

        return Song(
            stream_url=info["url"],
            page_url=info.get("webpage_url", info.get("url", "")),
            title=info.get("title", "Unknown"),
            duration=info.get("duration", 0),
            requester=requester,
            thumbnail=info.get("thumbnail"),
            source=source,
        )
    
    async def _yt_playlist(
            self,
            url: str,
            requester: discord.Member,
            max_entries: int | None,
            Song,
    ) -> list[Song]:
        info = await self._run_ytdl(YTDL_PLAYLIST, url)

        if not info or "entrties" not in info:
            raise TrackError(user_message="❌ No se pudo cargar el playlist.")
        
        entries = info["entries"]
        if max_entries:
            entries = entries[:max_entries]

        songs = []
        for entry in entries:
            if not entry:
                continue
            songs.append(Song(
                stream_url=f"https://www.youtube.com/watch?v={entry.get('id', '')}",
                page_url=f"https://www.youtube.com/watch?v={entry.get('id', '')}",
                title=entry.get("title", "Unknown"),
                duration=entry.get("duration", 0),
                requester=requester,
                thumbnail=entry.get("thumbnail"),
                source="youtube",
            ))

        if not songs:
            raise TrackError(user_message="❌ El playlist estaba vacio.")
        
        return songs
    
    async def _spotify_track(self, url: str, requester: discord.Member, Song) -> Song:
        if not self._spotify:
            raise SpotifyError(
                user_message="❌ Spotify todavia no ha sido configurado. Agregalos en el archivo .env!"
            )
        
        track_id = _SPOTIFY_TRACK.search(url).group(1)
        loop = asyncio.get_event_loop()

        try:
            track = await loop.run_in_executor(None, lambda: self._spotify.track(track_id))
        except Exception as e:
            raise SpotifyError(
                user_message="❌ No se pudo obtener la pista de spotify.",
                log_message=f"Spotify API error: {e}",
            )
        
        artist = track["artists"][0]["name"]
        title= track["name"]
        thumbnail = track["album"]["images"][0]["url"] if track["album"]["images"] else None
        duration_ms = track.get("duration_ms", 0)

        song = await self._single(f"ytsearch: {artist} - {title} audio", requester, Song)

        return Song(
            stream_url=song.stream_url,
            page_url=song.page_url,
            title=f"{artist} - {title}",
            duration_ms=duration_ms // 1000,
            requester=requester,
            thumbnail=thumbnail or song.thumbnail,
            source="spotify->yt",
        )

    async def _spotify_playlist(
        self,
        url: str,
        requester: discord.Member,
        max_entries: int | None,
        Song,
    ) -> list[Song]:
        if not self._spotify:
            raise SpotifyError(user_message="❌ Spotify no esta configurado.")
        
        playlist_id = _SPOTIFY_PLAYLIST.search(url).group(1)
        loop = asyncio.get_event_loop()

        try:
            result = await loop.run_in_executor(
                None,
                lambda: self._spotify.playlist_tracks(playlist_id, limit=max_entries or 50)
            )
        
        songs = []
        for item in result.get("items", []):
            track = item.get("track")
            if not track:
                continue
            artist = track["artists"][0]["name"]
            title = track["name"]
            thumbnail = track["album"]["images"][0]["url"] if track ["album"]["images"] else None
            duration_ms = track.get("duration_ms", 0)

            songs.append(Song(
                stream_url=f"ytsearch:{artist} - {title} audio",
                page_url=f"https://open.spotify.com/track/{track.get('id', '')}",
                title=f"{artist} - {title}",
                duration=duration_ms // 1000,
                requester=requester,
                thumbnail=thumbnail,
                source="spotify->yt",
            ))

        return songs