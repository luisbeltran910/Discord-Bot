# Songs model part of the actual music bot
# Author: Luis Angel Beltran Sanchez
# Version: 1.0.0

from __future__ import annotations
import discord

class Song:
    __slots__ = ("stream_url", "page_url", "title", "duration", "requester", "thumbnail", "source")

    def __init__(
        self,
        *,
        stream_url: str,
        page_url: str,
        title: str,
        duration: int,
        requester: discord.Member,
        thumbnail: str | None = None,
        source: str = "unknown",
    ):
        self.stream_url = stream_url
        self.page_url = page_url
        self.title = title
        self.duration = duration
        self.requester = requester
        self.thumbnail = thumbnail
        self.source = source
        
    @property
    def duration_str(self) -> str:
        total = int(self.duration)
        hours, remainder = divmod(total, 3600)
        mins, secs = divmod(remainder, 60)
        if hours:
            return f"{hours}:{mins:02d}:{secs:02d}"
        return f"{mins}:{secs:02d}"
    
    def to_embed(self, title: str = "Now Playing") -> discord.Embed:
        embed = discord.Embed(
            title=title,
            description=f"**[{self.title}]({self.page_url})**",
            color=discord.Color.blurple(),
        )
        embed.add_field(name="Duration", value=self.duration_str, inline=True)
        embed.add_field(name="Source", value=self.source.title(), inline=True)
        embed.add_field(name="Requested by", value=self.requester.mention, inline=True)
        if self.thumbnail:
            embed.set_thumbnail(url=self.thumbnail)
        return embed
    
    def __repr__(self) -> str:
        return f"<Song title={self.title!r} duration={self.duration_str}>"