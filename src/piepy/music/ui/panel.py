from typing import Callable, Awaitable

import discord
from discord import ButtonStyle
from discord import Interaction, InteractionResponse
from discord.ext import commands

from piepy.utils import theme
from ..core.guild_music_manager import GuildMusicManager, GuildManagerEvent
from ..core.guild_music_manager import StopReason
from .loop_mode_ui import LoopModeSelect
from .music_select_ui import MusicSelect
from ..utils import parse_time


class PanelView(discord.ui.View):  # TODO 1238114213256237097
    def __init__(self, guild_manager: GuildMusicManager, message: discord.Message):
        super().__init__()
        self.guild_manager: GuildMusicManager = guild_manager
        self.message: discord.Message = message

        self.add_item(MusicSelect(self.guild_manager, False, row=0))
        self.add_item(LoopModeSelect(self.guild_manager, False, row=1))

        previous_button = discord.ui.Button(label="⏮", row=2, style=ButtonStyle.green)
        previous_button.callback = self.on_previous

        next_button = discord.ui.Button(label="⏭", row=2, style=ButtonStyle.green)
        next_button.callback = self.on_next

        stop_button = discord.ui.Button(label="⏹", row=2, style=ButtonStyle.red)
        stop_button.callback = self.on_stop

        self.add_item(previous_button)
        self.add_item(next_button)
        self.add_item(stop_button)

    async def on_previous(self, interaction: Interaction):
        current_music_index = self.guild_manager.get_all_musics() \
            .index(self.guild_manager.current_music)

        try:
            previous_music = self.guild_manager.get_all_musics()[current_music_index - 1]
        except IndexError:
            previous_music = None

        self.guild_manager.skip_to(previous_music)

        res: InteractionResponse = interaction.response
        await res.defer(ephemeral=True)

    async def on_next(self, interaction: Interaction):
        current_music_index = self.guild_manager.get_all_musics() \
            .index(self.guild_manager.current_music)

        try:
            previous_music = self.guild_manager.get_all_musics()[current_music_index + 1]
        except IndexError:
            previous_music = None

        self.guild_manager.skip_to(previous_music)

        res: InteractionResponse = interaction.response
        await res.defer(ephemeral=True)

    async def on_stop(self, interaction: Interaction):
        await self.guild_manager.stop(StopReason.USER_CONTROL)

        res: InteractionResponse = interaction.response
        await res.defer(ephemeral=True)


class Panel:
    def __init__(self, bot: commands.Bot, guild: GuildMusicManager, message: discord.Message):
        self.bot: commands.Bot = bot
        self.guild_manager: GuildMusicManager = guild
        self.message: discord.Message = message
        self.panel_delete_handler: PanelDeleteHandler | None = None
        # 패널 삭제는 guild_manager.listeners 로 감지는 되지만
        # 상위인 panel_manager 쪽에서 추가로 해야하는 작업이 있기에 panel_manager 로 부터 특수하게 받음

        self.bot.add_listener(self.on_message_delete)
        self.guild_manager.listeners.add_listener(GuildManagerEvent.END, self.on_play_end)
        self.guild_manager.listeners.add_listener(GuildManagerEvent.LOOP_SWITCH, self.update_wrapper)
        self.guild_manager.listeners.add_listener(GuildManagerEvent.LOOP_MODE_CHANGE, self.update_wrapper)
        self.guild_manager.listeners.add_listener(GuildManagerEvent.PLAYLIST_MODIFY, self.update_wrapper)


    async def update(self):
        current_music = self.guild_manager.current_music
        embed = discord.Embed(
            title=f"현재 재생중:",
            description=current_music.title,
            url=current_music.url,
            color=theme.OK_COLOR
        )
        embed.set_image(url=current_music.title_image_url)
        embed.add_field(name="길이", value=parse_time(current_music.length))
        embed.add_field(name="순번", value=self.guild_manager.current_music_index + 1)
        embed.add_field(name="현재 반복 모드", value=self.guild_manager.loop_mode)

        view = PanelView(self.guild_manager, self.message)

        await self.message.edit(
            content="",
            embed=embed,
            view=view
        )

    async def update_wrapper(self, *args, **kwargs):
        await self.update()

    async def on_play_end(self, guild_manager: GuildMusicManager, stopped_reason: StopReason):
        await self.delete()

    async def on_message_delete(self, message: discord.Message):
        if message == self.message:
            self.guild_manager.listeners.rm_listener(self.on_play_end)
            self.guild_manager.listeners.rm_listener(self.update_wrapper)
            if self.panel_delete_handler is not None:
                await self.panel_delete_handler(self)

    async def delete(self):
        await self.message.delete()


PanelDeleteHandler = Callable[[Panel], Awaitable]