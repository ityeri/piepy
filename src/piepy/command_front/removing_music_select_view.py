import discord
from discord import InteractionResponse, Embed
from discord.ui import LayoutView, Container, Select, TextDisplay, ActionRow

from piepy.player_manager import MusicElement, MusicRemovingResult, PlayerController, PlayerStatus
from piepy.utils import theme


class RemovingMusicSelectView(LayoutView):
    def __init__(
            self,
            title: str,
            player_controller: PlayerController
    ):
        super().__init__(timeout=60)

        self.controller: PlayerController = player_controller

        select = Select(
            placeholder='지울 영상을 선택해 주세요',
            options=[
                *[
                    discord.SelectOption(label=music.title, value=music.id)
                    for music in self.controller.musics
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
        response: InteractionResponse = interaction.response

        if self.controller.status != PlayerStatus.ACTIVE:
            await response.send_message(
                embed=Embed(
                    title='BOT_DISCONNECTED',
                    description='뮤직봇을 사용중이지 않거나 사용하신 임베드가 너무 오래전에 생겼습니다',
                    color=theme.ERROR_COLOR
                ).set_footer(text='/재생 명령어를 쓰거나 /제거 명령어로 새 임베드를 띄워보세요')
            )
            return

        music_id = interaction.data['values'][0]
        target_music: MusicElement = next(filter(lambda m: m.id == music_id, self.controller.musics))

        if target_music not in self.controller.musics:
            await response.send_message(
                embed=Embed(
                    title='MUSIC_NOT_FOUND',
                    description=f'해당 영상은 현재 재생목록에 없습니다!',
                    color=theme.ERROR_COLOR
                ).set_footer(text='/제거 명령어로 이 UI를 다시 띄워보세요')
            )
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
