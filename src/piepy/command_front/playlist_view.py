import discord
from discord import Embed
from discord import InteractionResponse
from discord.ui import Container, Section, TextDisplay, Button

from piepy.player_manager import MusicElement, PlayerController
from piepy.utils import theme
from .player_context_view import PlayerContextView


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

    output = (str(sec).zfill(2) if (0 < mins or 0 < hour) else str(sec)) + sec_suffix

    if 0 < mins:
        output = (str(int(mins)).zfill(2) if 0 < hour else str(int(mins))) + min_suffix + sep + output

    if 0 < hour:
        output = str(int(hour)) + hour_suffix + sep + output

    return output


class PlaylistView(PlayerContextView):
    def __init__(self, title: str, player_controller: PlayerController):
        super().__init__(player_controller, timeout=None)

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

        if not await self.validate_player_context(interaction, '/목록'):
            return

        music_id = interaction.data['custom_id']
        target_music = await self.get_music_by_id(interaction, music_id, '/목록')
        if target_music is None:
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
