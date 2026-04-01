# Logger for the discord bot
# Author: Luis Angel Beltran Sanchez
# Version: 1.0.0


import logging
import sys
from pathlib import Path

def setup_logging(level: int = logging.INFO) -> None:
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    fmt = logging.Formatter(
        fmt="%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(fmt)

    file_handler = logging.FileHandler("logs/bot.log", mode="a", encoding="utf-8")
    file_handler.setFormatter(fmt)

    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(stream_handler)
    root.addHandler(file_handler)

    logging.getLogger("discord.gateway").setLevel(logging.WARNING)
    logging.getLogger("discord.http").setLevel(logging.WARNING)