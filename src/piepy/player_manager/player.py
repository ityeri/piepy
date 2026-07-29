import asyncio
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

@dataclass(frozen=False)
class PlayerState:
    guild_id: int
    status: PlayerStatus
    musics: list[MusicElement]

    current_music: MusicElement | None
    next_music: MusicElement | None

    is_loop: bool
    is_random_order: bool

    current_channel: VoiceChannel | None


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

        self._step_waiters: list[asyncio.Future[None]] = []

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
    def musics(self) -> list[MusicElement] | None:
        if self._order_manager is not None:
            return self._order_manager.elements
        else:
            return None
    @property
    def current_music(self) -> MusicElement | None:
        if self._order_manager is not None:
            return self._order_manager.current_element
        else:
            return None
    @property
    def next_music(self) -> MusicElement | None:
        if self._order_manager is not None:
            return self._order_manager.next_element
        else:
            return None

    @property
    def is_loop(self) -> bool: return self._order_manager.is_loop
    @property
    def is_random_order(self) -> bool: return self._order_manager.is_random_order

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

    def _notify_step_waiters(self) -> None:
        waiters, self._step_waiters = self._step_waiters, []
        for future in waiters:
            if not future.done():
                future.set_result(None)

    async def _single_play_step(self, e: Exception | None = None):
        if self.status in [PlayerStatus.STOPPING, PlayerStatus.DONE]:
            self._notify_step_waiters()
            return

        if self.voice_client.source:
            self.voice_client.source.cleanup()

        self._order_manager = self._order_manager.step()
        current_music = self._order_manager.current_element

        if current_music is None:
            await self.voice_client.channel.send("다틈 ㅃ")
            self._notify_step_waiters()
            return # TODO Here needs some play end processing

        self._play_wrap(await current_music.create_source())
        self._notify_step_waiters()

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
        self._order_manager = self._order_manager\
            .change_order_mode(is_loop, is_random_order)\
            .update_next_element()

    def subscribe_next_step(self) -> asyncio.Future[None]:
        future: asyncio.Future[None] = self.running_loop.create_future()
        self._step_waiters.append(future)
        return future

    def to_player_state(self) -> PlayerState:
        return PlayerState(
            guild_id=self.guild_id,
            status=self.status,
            musics=list(self.musics),

            current_music=self.current_music,
            next_music=self.next_music,

            is_loop=self.is_loop,
            is_random_order=self.is_random_order,

            current_channel=self.voice_client.channel
        )
