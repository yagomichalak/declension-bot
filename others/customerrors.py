import discord
from discord.ext import commands

class NotInWhitelist(commands.CheckFailure):
    pass


class DailyCommandsLimit(commands.CheckFailure):
    def __init__(self, limit: int) -> None:
        self.limit = limit
