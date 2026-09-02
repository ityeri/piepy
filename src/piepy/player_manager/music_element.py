import os
from abc import ABC, abstractmethod
from typing import override

from discord import FFmpegPCMAudio, AudioSource


class MusicElement(ABC):
    def __init__(self, id: str, title: str, url: str, title_image_url: str, length: float):
        self.id: str = id
        self.title: str = title
        self.url: str = url
        self.title_image_url: str = title_image_url
        self.length: float = length

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if isinstance(other, MusicElement):
            return self.id == other.id
        else:
            return False

    @abstractmethod
    async def create_source(self) -> AudioSource:
        ...

    async def cleanup(self):
        pass


class UrlStreamMusicElement(MusicElement):  # 지금 무료체험하세요
    def __init__(self, id: str, title: str, url: str, title_image_url: str, length: float, stream_url: str):
        super().__init__(id, title, url, title_image_url, length)
        self.stream_url: str = stream_url

    @override
    async def create_source(self) -> AudioSource:
        # TODO Long-period test needed. This may causes an unexpected stream disconnecting for given stream_url
        return FFmpegPCMAudio(
            self.stream_url,
            before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',  # Stream reconnect setting
            options='-af loudnorm=I=-16:TP=-1.5:LRA=11',  # Loudness normalization
            stderr=open(os.devnull, 'wb')
        )


class LocalFileMusicElement(MusicElement):
    def __init__(
            self,
            id: str,
            title: str,
            url: str,
            title_image_url: str,
            length: float,
            file_path: str,
            *,
            auto_file_delete: bool = False
    ):
        super().__init__(id, title, url, title_image_url, length)
        self.file_path: str = file_path
        self.auto_file_delete: bool = auto_file_delete

    @override
    async def create_source(self) -> AudioSource:
        return FFmpegPCMAudio(
            self.file_path,
            options='-af loudnorm=I=-16:TP=-1.5:LRA=11',  # Loudness normalization
            stderr=open(os.devnull, 'wb')
        )

    @override
    async def cleanup(self):
        if self.auto_file_delete:
            self.auto_file_delete = False
            os.remove(self.file_path)
