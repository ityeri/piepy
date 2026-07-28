from abc import ABC, abstractmethod
from typing import override, final

from discord import FFmpegPCMAudio, AudioSource


class MusicElement(ABC):
    def __init__(self, id: str, title: str, url: str, title_image_url: str, length: float):
        self.id: str = id
        self.title: str = title
        self.url: str = url
        self.title_image_url: str = title_image_url
        self.length: float = length

        self.source: AudioSource | None = None

        self.is_ready: bool = False
        self.is_used: bool = False

    def __hash__(self):
        return hash(self.id)
    def __eq__(self, other):
        if isinstance(other, MusicElement):
            return self.id == other.id
        else:
            return False

    @final
    async def ready(self):
        if self.is_used:
            raise RuntimeError("Music cannot be reused")

        await self._ready()
        self.is_ready = True
        self.is_used = True

    @final
    async def cleanup(self):
        if not self.is_ready:
            raise RuntimeError("Music is not ready")

        await self._cleanup()
        self.is_ready = False

    @abstractmethod
    async def _ready(self) -> None: ...
    @abstractmethod
    async def _cleanup(self) -> None: ...


class UrlStreamMusicElement(MusicElement): # 지금 무료체험하세요
    def __init__(self, id: str, title: str, url: str, title_image_url: str, length: float, stream_url: str):
        super().__init__(id, title, url, title_image_url, length)

        self.stream_url: str = stream_url

    @override
    async def _ready(self) -> None:
        self.source = FFmpegPCMAudio(
            self.stream_url,
            before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', # Reconnect setting
            options='-af loudnorm=I=-16:TP=-1.5:LRA=11' # Loudness normalization
        )

    @override
    async def _cleanup(self) -> None:
        if self.source:
            self.source.cleanup()
