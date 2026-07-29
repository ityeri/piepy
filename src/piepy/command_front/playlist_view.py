from discord import Emoji
from discord.ui import LayoutView, Container, Section, TextDisplay, Thumbnail, Button

from piepy.player_manager import MusicElement
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
    def __init__(self, musics: list[MusicElement], current_music: MusicElement):
        super().__init__(timeout=None)

        self.musics: list[MusicElement] = musics
        self.current_music: MusicElement = current_music

        self.add_item(
            Container(
                TextDisplay('## 현재 재생목록'),
                *[
                    Section(
                        TextDisplay(
                            f'### [__*{music.title}*__]({music.url})' if music == self.current_music
                            else f'### [{music.title}]({music.url})'
                        ),
                        TextDisplay(
                            f'길이: **{to_natural_timecode(music.length)}**  **·**  **현재 재생중!**'
                            if music == self.current_music
                            else f'길이: **{to_natural_timecode(music.length)}**'
                        ),
                        accessory=Button(label='바로 재생'),
                    )
                    for music in self.musics
                ],
                accent_color=theme.OK_COLOR
            )
        )
