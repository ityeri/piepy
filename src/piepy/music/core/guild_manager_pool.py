import discord
from discord.ext import commands

from piepy.listener import ListenerManager
from .guild_music_manager import GuildMusicManager, GuildManagerEvent


class GuildManagerPool:
    def __init__(self, bot: commands.Bot):
        self._guilds: dict[discord.Guild, GuildMusicManager] = dict()
        self.bot: commands.Bot = bot
        self.listeners: ListenerManager[GuildManagerEvent] = ListenerManager()

    def get_guild(self, guild: discord.Guild, auto: bool = True) -> GuildMusicManager:
        try:
            return self._guilds[guild]
        except KeyError as e:
            if not auto: raise e

            guild_manager = GuildMusicManager(self.bot, guild)
            for event_type, listener in self.listeners.all_listeners():
                guild_manager.listeners.add_listener(event_type, listener)

            self._guilds[guild] = guild_manager

            return guild_manager

    def all_guilds(self) -> list[GuildMusicManager]:
        return self._guilds.values()