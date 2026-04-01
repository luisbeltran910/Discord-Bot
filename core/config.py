# Config for the core of my project for the discord bot
# Author: Luis Angel Beltran Sanchez
# Version: 1.0.0

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

def _require(key: str) -> str:
    value = os.getenv(key, "").strip()
    if not value:
        raise EnvironmentError(
            f"Missing required env variable: {key}\n"
            f"Check your .env file"
        )
    return value

def _optional(key: str, default: str = "") -> str:
    return os.getenv(key, default).strip()

@dataclass(frozen=True)
class Config:
    discord_token: str
    prefix: str = "!"
    spotify_client_id: str = ""
    spotify_client_secret: str = ""
    default_volume: float = 0.5
    max_queue_size: int = 200
    inactivity_timeout: int = 300
    max_playlist_size: int = 50
    welcome_channel: str = "general"
    goodbye_channel: str = "general"

    @property
    def spotify_enabled(self) -> bool:
        return bool(self.spotify_client_id and self.spotify_client_secret)
    
def load_config() -> Config:
    return Config(
        discord_token=_require("DISCORD_TOKEN"),
        prefix=_optional("PREFIX", "!"),
        spotify_client_id=_optional("SPOTIFY_CLIENT_ID"),
        spotify_client_secret=_optional("SPOTIFY_CLIENT_SECRET"),
        default_volume=float(_optional("DEFAULT_VOLUME", "0.5")),
        max_queue_size=int(_optional("MAX_QUEUE_SIZE", "200")),
        inactivity_timeout=int(_optional("INACTIVITY_TIMEOUT", "300")),
        max_playlist_size=int(_optional("MAX_PLAYLIST_SIZE", "50")),
        welcome_channel=_optional("WELCOME_CHANNEL", "general"),
        goodbye_channel=_optional("GOODBYE_CHANNEL", "general"),
    )