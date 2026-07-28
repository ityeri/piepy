from asyncio import AbstractEventLoop
from collections.abc import Awaitable
from dataclasses import dataclass
from enum import Enum, auto
from typing import Callable

from discord import VoiceChannel, VoiceClient, AudioSource

from .music_element import MusicElement
from .order_manager import OrderManager


class PlayerStatus(Enum):
    BEFORE_READY = auto()
    READY = auto()
    ACTIVE = auto()
    STOPPING = auto()
    DONE = auto()

@dataclass(frozen=True)
class PlayerStopEvent:
    player: Player

    type LISTENER_TYPE = Callable[[PlayerStopEvent], Awaitable]


class MusicInPlayingError(Exception): ...


#
class Player:
    """
    """
    def __init__(self, guild_id: int, on_stop: PlayerStopEvent.LISTENER_TYPE):
        self.guild_id: int = guild_id
        self.status: PlayerStatus = PlayerStatus.BEFORE_READY
        self.on_stop: PlayerStopEvent.LISTENER_TYPE = on_stop

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
        self._order_manager = OrderManager.create(
            list(),
            None, None,
            is_loop=is_loop, is_random_order=is_random_order
        )

        self.status = PlayerStatus.READY

    @property
    def musics(self) -> list[MusicElement]:
        return self._order_manager.elements
    @property
    def current_music(self) -> MusicElement | None:
        return self._order_manager.current_element

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
        if self.status in [PlayerStatus.STOPPING, PlayerStatus.DONE]:
            return

        if self.voice_client.source:
            self.voice_client.source.cleanup()

        self._order_manager = self._order_manager.step()
        current_music = self._order_manager.current_element

        if current_music is None:
            await self.voice_client.channel.send("다틈 ㅃ")
            return # TODO Here needs some play end processing

        self._play_wrap(await current_music.create_source())


    async def stop(self):
        if self.status != PlayerStatus.ACTIVE:
            raise RuntimeError('Cannot stop. Player status is not ACTIVE')

        self.status = PlayerStatus.STOPPING

        self.voice_client.stop()
        await self.voice_client.disconnect()

        self.status = PlayerStatus.DONE

        await self.on_stop(PlayerStopEvent(self))

    def add_last(self, music: MusicElement):
        self._order_manager = self._order_manager.add_last(music).update_next_element()

    def rm(self, music: MusicElement):
        if music not in self._order_manager.elements:
            raise ValueError('Cannot remove. Given music element does not exists')
        if music == self._order_manager.current_element:
            raise MusicInPlayingError('Cannot remove. Given music is currently playing')

        self._order_manager = self._order_manager.rm(music)

    def jump_to(self, music: MusicElement | None):
        if music is not None:
            if music not in self._order_manager.elements:
                raise ValueError('Cannot jump. Given music element does not exists')

            self._order_manager = self._order_manager.set_next(music)

        self.voice_client.stop()

    def change_order_mode(self, is_loop: bool, is_random_order: bool):
        self._order_manager.change_order_mode(is_loop, is_random_order)
