import discord
from discord import InteractionResponse, Embed
from discord.ui import Container, Select, TextDisplay, ActionRow

from piepy.player_manager import MusicRemovingResult, PlayerController
from piepy.utils import theme
from .player_context_view import PlayerContextView


class RemovingMusicSelectView(PlayerContextView):
    def __init__(self, title: str, player_controller: PlayerController):
        super().__init__(player_controller, timeout=60)

        select = Select(
            placeholder='지울 영상을 선택해 주세요',
            options=[
                discord.SelectOption(label=music.title, value=music.id)
                for music in self.controller.musics
            ],
        )
        select.callback = self.on_select

        self.add_item(
            Container(
                TextDisplay(f'### {title}'),
                ActionRow(select),
                accent_color=theme.OK_COLOR
            )
        )

    async def on_select(self, interaction: discord.Interaction):
        response: InteractionResponse = interaction.response

        if not await self.validate_player_context(interaction, '/제거'):
            return

        music_id = interaction.data['values'][0]
        target_music = await self.get_music_by_id(interaction, music_id, '/제거')
        if target_music is None:
            return

        result = await self.controller.rm_music(target_music)

        if result == MusicRemovingResult.REMOVED:
            await response.send_message(
                embed=Embed(
                    title='REMOVED',
                    description=f'**{target_music.title}** 영상을 재생목록에서 뺐습니다',
                    color=theme.OK_COLOR
                )
            )
        elif result == MusicRemovingResult.SKIPPED_AND_REMOVED:
            await response.send_message(
                embed=Embed(
                    title='JUMPED_AND_REMOVED',
                    description=f'**{target_music.title}** 영상을 건너뛴 후, 재생목록에서 뺐습니다',
                    color=theme.OK_COLOR
                )
            )
