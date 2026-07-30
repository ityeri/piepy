import discord
from discord import Embed
from discord import InteractionResponse
from discord.ui import LayoutView, Container, Section, TextDisplay, Button

from piepy.player_manager import MusicElement, PlayerController, PlayerStatus
from piepy.utils import theme


def to_natural_timecode(
        time_sec: float,
        hour_suffix: str = ':',
        min_suffix: str = ':',
        sec_suffix: str = '',
        sep: str = ''
) -> str:
    hour = time_sec // 3600
    time_sec %= 3600

    mins = time_sec // 60
    time_sec %= 60

    sec = int(time_sec)

    output = str(sec) + sec_suffix

    if 0 < mins:
        output = str(mins) + min_suffix + sep + output

    if 0 < hour:
        output = str(hour) + hour_suffix + sep + output

    return output


class PlaylistView(LayoutView):
    def __init__(
            self,
            title: str,
            player_controller: PlayerController
    ):
        super().__init__(timeout=None)

        self.controller: PlayerController = player_controller

        self.add_item(
            Container(
                TextDisplay(f'## {title}'),
                *[
                    self.create_music_section(music)
                    for music in self.controller.musics
                ],
                accent_color=theme.OK_COLOR
            )
        )

    def create_music_section(self, music: MusicElement) -> Section:
        button = Button(label='바로 재생', custom_id=music.id)
        button.callback = self.play_button

        return Section(
            TextDisplay(
                f'### [__*{music.title}*__]({music.url})' if music == self.controller.current_music
                else f'### [{music.title}]({music.url})'
            ),
            TextDisplay(
                f'길이: **{to_natural_timecode(music.length)}**  **·**  **현재 재생중!**'
                if music == self.controller.current_music
                else f'길이: **{to_natural_timecode(music.length)}**'
            ),
            accessory=button,
        )

    async def play_button(self, interaction: discord.Interaction):
        response: InteractionResponse = interaction.response

        if self.controller.status != PlayerStatus.ACTIVE:
            await response.send_message(
                embed=Embed(
                    title='BOT_DISCONNECTED',
                    description='뮤직봇을 사용중이지 않거나 사용하신 임베드가 너무 오래전에 생겼습니다',
                    color=theme.ERROR_COLOR
                ).set_footer(text='/재생 명령어를 쓰거나 /목록 명령어로 새 재생목록을 띄워보세요')
            )
            return

        music_id = interaction.data['custom_id']
        target_music: MusicElement = next(filter(lambda m: m.id == music_id, self.controller.musics))

        if target_music not in self.controller.musics:
            await response.send_message(
                embed=Embed(
                    title='MUSIC_NOT_FOUND',
                    description=f'해당 영상은 현재 재생목록에 없습니다!',
                    color=theme.ERROR_COLOR
                ).set_footer(text='/목록 명령어로 새 최신 재생목록을 띄워 보세요')
            )
            return

        self.controller.jump_to_music(target_music)

        if target_music == self.controller.current_music:
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
