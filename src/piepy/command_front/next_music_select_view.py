import discord
from discord import InteractionResponse, Embed
from discord.ui import LayoutView, Container, Select, TextDisplay, ActionRow

from piepy.player_manager import MusicElement, PlayerController, StateValidationFailedReason
from piepy.utils import theme


class NextMusicSelectView(LayoutView):
    def __init__(
            self,
            title: str,
            player_controller: PlayerController
    ):
        super().__init__(timeout=60)

        self.controller: PlayerController = player_controller

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

        music_id = interaction.data['values'][0]
        if music_id == 'next':
            target_music: MusicElement | None = None
        else:
            target_music: MusicElement | None = next(filter(lambda m: m.id == music_id[1:], self.controller.musics))

            if target_music not in self.controller.musics:
                await response.send_message(
                    embed=Embed(
                        title='MUSIC_NOT_FOUND',
                        description=f'해당 영상은 현재 재생목록에 없습니다!',
                        color=theme.ERROR_COLOR
                    ).set_footer(text='/목록 명령어로 새 최신 재생목록을 띄워 보세요')
                )
                return

        result = self.controller.jump_to_music(target_music)

        if result == StateValidationFailedReason.ALREADY_STOPPED:
            await response.send_message(
                embed=Embed(
                    title='BOT_DISCONNECTED',
                    description='뮤직봇을 사용중이지 않거나 사용하신 임베드가 너무 오래전에 생겼습니다',
                    color=theme.ERROR_COLOR
                ).set_footer(text='/재생 명령어를 쓰거나 /다음 명령어로 새 임베드를 띄워보세요')
            )

        elif music_id == 'next':
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
