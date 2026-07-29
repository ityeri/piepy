import discord
from discord import InteractionResponse, Embed
from discord.ui import LayoutView, Container, Select, TextDisplay, ActionRow

from piepy.player_manager import MusicElement, PlayerManager, MusicRemovingResult
from piepy.utils import theme


class RemovingMusicSelectView(LayoutView):
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
            placeholder='지울 영상을 선택해 주세요',
            options=[
                *[
                    discord.SelectOption(label=music.title, value=music.id)
                    for music in self.musics
                ],
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
        target_music: MusicElement = next(filter(lambda m: m.id == value, self.musics))
        player_state = self.player_manager.get_player_state(self.guild_id)
        response: InteractionResponse = interaction.response

        if target_music not in player_state.musics:
            await response.send_message(
                embed=Embed(
                    title='MUSIC_NOT_FOUND',
                    description=f'해당 영상은 현재 재생목록에 없습니다!',
                    color=theme.ERROR_COLOR
                ).set_footer(text='/제거 명령어로 이 UI를 다시 띄워보세요')
            )
            return

        result = await self.player_manager.rm_music(self.guild_id, target_music)

        if result == MusicRemovingResult.PLAYER_NOT_FOUND:
            await response.send_message(
                embed=Embed(
                    title='BOT_DISCONNECTED',
                    description='뮤직봇 기능을 사용중이지 않습니다! `/재생` 명령어를 써보세요',
                    color=theme.ERROR_COLOR
                )
            )
        elif result == MusicRemovingResult.REMOVED:
            await response.send_message(
                embed=Embed(
                    title='REPLAYED',
                    description=f'**{target_music.title}** 영상을 재생목록에서 뺐습니다',
                    color=theme.OK_COLOR
                )
            )
        elif result == MusicRemovingResult.SKIPPED_AND_REMOVED:
            await response.send_message(
                embed=Embed(
                    title='SKIPPED_TO_TARGET',
                    description=f'**{target_music.title}** 영상을 건너뛴 후, 재생목록에서 뺐습니다',
                    color=theme.OK_COLOR
                )
            )
