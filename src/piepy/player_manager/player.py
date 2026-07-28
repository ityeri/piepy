from asyncio import AbstractEventLoop
from enum import Enum, auto

from discord import VoiceChannel, VoiceClient, AudioSource

from .music_element import MusicElement
from .order_manager import OrderManager


class PlayerStatus(Enum):
    BEFORE_READY = auto()
    READY = auto()
    ACTIVE = auto()
    DONE = auto()


# TODO move_to, ... stop logic
class Player:
    """
    """
    def __init__(self, guild_id: int):
        self.guild_id: int = guild_id
        self.status: PlayerStatus = PlayerStatus.BEFORE_READY

        self.voice_client: VoiceClient | None = None
        self.running_loop: AbstractEventLoop | None = None
        self._order_manager: OrderManager[MusicElement] | None = None

    async def ready(
            self,
            start_channel: VoiceChannel,
            running_loop: AbstractEventLoop,
            *,
            is_loop: bool,
            is_random_order: bool
    ):
        if self.status != PlayerStatus.BEFORE_READY:
            raise RuntimeError('Cannot ready. Player status is not BEFORE_READY')

        self.running_loop = running_loop
        self.voice_client = await start_channel.connect()
        self._order_manager = OrderManager.create(list(), None, is_loop, is_random_order)

        self.status = PlayerStatus.READY

    @property
    def musics(self) -> list[MusicElement]:
        return self._order_manager.elements

    def start(self):
        if self.status != PlayerStatus.READY:
            raise RuntimeError('Cannot start. Player status is not READY')

        self.running_loop.create_task(self._single_play_step())

        self.status = PlayerStatus.ACTIVE

    def _play_wrap(self, source: AudioSource):
        self.voice_client.play(
            source,
            after=lambda e: self.running_loop.create_task(self._single_play_step(e))
        )

    async def _single_play_step(self, e: Exception | None = None):
        self._order_manager = self._order_manager.step()
        current_music = self._order_manager.current_element

        if current_music is None:
            await self.voice_client.channel.send("다틈 ㅃ")
            return # TODO Here needs some play end processing

        if not current_music.is_ready:
            await current_music.ready()

        self._play_wrap(current_music.source)

    def add_last(self, music: MusicElement):
        self._order_manager = self._order_manager.add_last(music)
