import os

from discord import PCMVolumeTransformer, FFmpegPCMAudio


class Music:
    def __init__(self, music_id: str, title: str, url: str, title_image_url: str, length: float, file_path: str):
        self.music_id: str = music_id
        self.title: str = title
        self.url: str = url
        self.title_image_url: str = title_image_url
        self.length: float = length
        self.file_path: str = file_path

        self.source: PCMVolumeTransformer | None = None

    def ready(self):
        if self.source: self.source.cleanup()

        self.source = PCMVolumeTransformer(
            FFmpegPCMAudio(
                self.file_path,
                options=(
                        '-af "loudnorm=I=-16:TP=-1.5:LRA=11" ' # 라우 머시기 정규화
                        # "-f s16le -ar 48000 -ac 2 " # 샘플링 레이트 명시 인데 짜피 이 옵션이 FFmpegPCMAudio 기본이라네
                )
            )
        )

    def cleanup(self):
        if self.source:
            self.source.cleanup()
        os.remove(self.file_path)

    def set_volume(self, volume: float):
        self.source.volume = volume