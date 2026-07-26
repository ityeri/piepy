import discord.ui
from discord import Embed
from discord.interactions import InteractionResponse

from piepy.utils import theme
from ..core.guild_music_manager import GuildMusicManager


class MusicSelect(discord.ui.Select):
    def __init__(
            self,
            guild_manager: GuildMusicManager,
            do_response: bool,
            **kwargs
    ):
        self.guild_manager: GuildMusicManager = guild_manager
        self.display_response: bool = do_response

        options = [
            discord.SelectOption(label=music.title, value=music.music_id)
            for music in self.guild_manager.get_all_musics()
        ]
        super().__init__(
            placeholder="무엇을 재생할지 선택해 주세요",
            min_values=1, max_values=1, options=options,
            **kwargs
        )

    async def callback(self, interaction: discord.Interaction):
        value = self.values[0]
        previous_music = self.guild_manager.current_music
        next_music = self.guild_manager.get_music_by_id(value)
        res: InteractionResponse = interaction.response

        self.guild_manager.skip_to(next_music)

        if self.display_response:
            if next_music == previous_music:
                await res.send_message(embed=Embed(
                    title=f"\"**{next_music.title}**\" 영상을 다시 재생합니다", color=theme.OK_COLOR
                ))
            else:
                await res.send_message(embed=Embed(
                    title=f"**{next_music.title}** (으)로 건너 뛰었습니다", color=theme.OK_COLOR
                ))
        else:
            await res.defer(ephemeral=True)