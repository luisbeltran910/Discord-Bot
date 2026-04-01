# Error messages or handler for the bot
# Author: Luis Angel Beltran Sanchez
# Version: 1.0.0

class BotError(Exception):
    def __init__(self, user_message: str, log_message: str = ""):
        self.user_message = user_message
        self.log_message = log_message or user_message
        super().__init__(self.log_message)

class VoiceError(BotError):
    pass

class TrackError(BotError):
    pass

class QueueError(BotError):
    pass

class SpotifyError(BotError):
    pass