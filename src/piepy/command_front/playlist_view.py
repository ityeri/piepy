import discord
from discord import InteractionResponse
from discord import Embed
from discord.ui import LayoutView, Container, Section, TextDisplay, Button

from piepy.player_manager import MusicElement, PlayerManager
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
            player_manager: PlayerManager,
            guild_id: int,
            musics: list[MusicElement],
            current_music: MusicElement
    ):
        super().__init__(timeout=None)

        self.player_manager: PlayerManager = player_manager
        self.guild_id: int = guild_id
        self.musics: list[MusicElement] = musics
        self.current_music: MusicElement = current_music

        self.add_item(
            Container(
                TextDisplay(f'## {title}'),
                *[
                    self.create_music_section(music)
                    for music in self.musics
                ],
                accent_color=theme.OK_COLOR
            )
        )

    def create_music_section(self, music: MusicElement) -> Section:
        button = Button(label='바로 재생', custom_id=music.id)
        button.callback = self.play_button

        return Section(
            TextDisplay(
                f'### [__*{music.title}*__]({music.url})' if music == self.current_music
                else f'### [{music.title}]({music.url})'
            ),
            TextDisplay(
                f'길이: **{to_natural_timecode(music.length)}**  **·**  **현재 재생중!**'
                if music == self.current_music
                else f'길이: **{to_natural_timecode(music.length)}**'
            ),
            accessory=button,
        )

    async def play_button(self, interaction: discord.Interaction):
        target_music: MusicElement = next(filter(lambda m: m.id == interaction.data['custom_id'], self.musics))

        is_success = self.player_manager.jump_to_music(self.guild_id, target_music)
        response: InteractionResponse = interaction.response

        if not is_success:
            await response.send_message(
                embed=Embed(
                    title='BOT_DISCONNECTED',
                    description='뮤직봇 기능을 사용중이지 않습니다! `/재생` 명령어를 써보세요',
                    color=theme.ERROR_COLOR
                )
            )
        else:
            if target_music == self.current_music:
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
