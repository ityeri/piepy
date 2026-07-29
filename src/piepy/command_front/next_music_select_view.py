import discord
from discord import InteractionResponse, Embed
from discord.ui import LayoutView, Container, Select, TextDisplay, Section, Button, ActionRow

from piepy.player_manager import MusicElement, PlayerManager
from piepy.utils import theme


class NextMusicSelectView(LayoutView):
    def __init__(
            self,
            title: str,
            player_manager: PlayerManager,
            guild_id: int,
            musics: list[MusicElement]
    ):
        super().__init__(timeout=60)

        self.player_manager: PlayerManager = player_manager
        self.guild_id: int = guild_id
        self.musics: list[MusicElement] = musics

        select = Select(
            placeholder='영상을 선택해 주세요',
            options=[
                *[
                    discord.SelectOption(label=music.title, value='#' + music.id)
                    for music in self.musics
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
        value = interaction.data['values'][0]

        if value == 'next':
            target_music: MusicElement | None = None
        else:
            target_music: MusicElement | None = next(filter(lambda m: m.id == value[1:], self.musics))

        player_state = self.player_manager.get_player_state(self.guild_id)
        response: InteractionResponse = interaction.response

        if target_music not in player_state.musics:
            await response.send_message(
                embed=Embed(
                    title='MUSIC_NOT_FOUND',
                    description=f'해당 영상은 현재 재생목록에 없습니다!',
                    color=theme.ERROR_COLOR
                ).set_footer(text='/목록 명령어로 새 최신 재생목록을 띄워 보세요')
            )
            return

        is_success = self.player_manager.jump_to_music(self.guild_id, target_music)

        if not is_success:
            await response.send_message(
                embed=Embed(
                    title='BOT_DISCONNECTED',
                    description='뮤직봇 기능을 사용중이지 않습니다! `/재생` 명령어를 써보세요',
                    color=theme.ERROR_COLOR
                )
            )
            return

        player_state = self.player_manager.get_player_state(self.guild_id)

        if value == 'next':
            await response.send_message(
                embed=Embed(
                    title='SKIPPED_TO_NEXT',
                    description='바로 다음 영상을 재생합니다!',
                    color=theme.OK_COLOR
                )
            )
        elif target_music == player_state.current_music:
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
