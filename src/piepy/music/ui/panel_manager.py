import discord
from discord.ext import commands

from ..core.guild_music_manager import GuildMusicManager
from .panel import Panel


class PanelManager:
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
        self._panel_group: dict[discord.Guild, list[Panel]] = dict()

    async def new_panel(self, guild_manager: GuildMusicManager, message: discord.Message) -> Panel:
        panel = Panel(self.bot, guild_manager, message)
        panel.panel_delete_handler = self.on_panel_delete
        self.get_panel_group(guild_manager.guild).append(panel)
        await panel.update()
        return panel

    def get_panel_group(self, guild: discord.Guild, auto: bool = True) -> list[Panel]:
        try:
            return self._panel_group[guild]
        except KeyError as e:
            if not auto: raise e

            self._panel_group[guild] = list()
            return self._panel_group[guild]

    async def on_panel_delete(self, panel: Panel):
        self.get_panel_group(panel.guild_manager.guild).remove(panel)