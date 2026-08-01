import discord
from discord import InteractionResponse, Embed
from discord.ui import Container, Select, TextDisplay, ActionRow

from piepy.player_manager import MusicElement, PlayerController
from piepy.utils import theme
from .player_context_view import PlayerContextView


class NextMusicSelectView(PlayerContextView):
    def __init__(self, title: str, player_controller: PlayerController):
        super().__init__(player_controller, timeout=60)

        select = Select(
            placeholder='영상을 선택해 주세요',
            options=[
                *[
                    discord.SelectOption(label=music.title, value='#' + music.id)
                    for music in self.controller.musics
                ],
                discord.SelectOption(
                    label='▶️ 다음 영상으로 건너뛰기',
                    description='다음 순서의 영상으로 건너 뜁니다. 무작위 순서 모드라면, 무작위 영상으로 건너 뜁니다',
                    value='next'
                )
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

        if not await self.validate_player_context(interaction, '/다음'):
            return

        music_id = interaction.data['values'][0]
        if music_id == 'next':
            target_music: MusicElement | None = None
        else:
            target_music = await self.get_music_by_id(interaction, music_id[1:], '/다음')
            if target_music is None:
                return

        self.controller.jump_to_music(target_music)

        if music_id == 'next':
            await response.send_message(
                embed=Embed(
                    title='SKIPPED_TO_NEXT',
                    description='바로 다음 영상을 재생합니다!',
                    color=theme.OK_COLOR
                )
            )
        elif target_music == self.controller.current_music:
            await response.send_message(
                embed=Embed(
                    title='REPLAYED',
                    description=f'**{target_music.title}** 영상을 다시 재생합니다!',
                    color=theme.OK_COLOR
                )
            )
        else:
            await response.send_message(
                embed=Embed(
                    title='SKIPPED_TO_TARGET',
                    description=f'**{target_music.title}** 영상으로 건너 뛰었습니다!',
                    color=theme.OK_COLOR
                )
            )
