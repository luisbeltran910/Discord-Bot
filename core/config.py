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
    prefir: str = "!"
    