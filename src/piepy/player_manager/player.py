import asyncio
import uuid
from asyncio import AbstractEventLoop
from collections.abc import Awaitable
from dataclasses import dataclass
from enum import Enum, auto
from typing import Callable, Final
from uuid import UUID

import discord
from discord import VoiceChannel, VoiceClient, AudioSource, Member, VoiceState
from discord.ext import commands

from .music_element import MusicElement
from .order_manager import OrderManager


class PlayerStatus(Enum):
    BEFORE_READY = auto()
    READY = auto()
    ACTIVE = auto()
    STOPPING = auto()
    DONE = auto()

class PlayerStopReason(Enum):
    BY_USER = auto()
    BY_SYSTEM = auto()
    END_OF_PLAY = auto()
    DISCONNECTED = auto()

@dataclass(frozen=True)
class PlayerStopEvent:
    player: Player
    reason: PlayerStopReason

    type Listener = Callable[[PlayerStopEvent], Awaitable]

class MusicInPlayingError(Exception): ...


class Player:
    """
    """
    def __init__(
            self,
            bot: commands.Bot,
            guild_id: int,
            on_stop: PlayerStopEvent.Listener,
            *,
            session_id: UUID | None = None
    ):
        self.guild_id: Final[int] = guild_id
        self.bot: commands.Bot = bot
        self.session_id: Final[UUID] = session_id if session_id is not None else uuid.uuid4()
        self.status: PlayerStatus = PlayerStatus.BEFORE_READY
        self.stop_callback: PlayerStopEvent.Listener = on_stop

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
        self.bot.add_listener(self.on_voice_state_update, 'on_voice_state_update')

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


    async def on_voice_state_update(self, member: Member, before: VoiceState, after: VoiceState):
        if (
                member == self.bot.user
                and before.channel is not None
                and after.channel is None
                and self.status == PlayerStatus.ACTIVE
        ):
            await self._stop(PlayerStopReason.DISCONNECTED)


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
            self._notify_step_waiters()
            await self._stop(PlayerStopReason.END_OF_PLAY)
            return

        self._play_wrap(await current_music.create_source())
        self._notify_step_waiters()


    async def stop(self):
        if self.status != PlayerStatus.ACTIVE:
            raise RuntimeError('Cannot stop. Player status is not ACTIVE')

        await self._stop(PlayerStopReason.BY_USER if is_by_user else PlayerStopReason.BY_SYSTEM)

    async def _stop(self, reason: PlayerStopReason):
        self.status = PlayerStatus.STOPPING

        await self.stop_callback(PlayerStopEvent(
            player=self,
            reason=reason
        ))

        self.bot.remove_listener(self.on_voice_state_update, 'on_voice_state_update')
        self.voice_client.stop()
        if self.voice_client.is_connected():
            await self.voice_client.disconnect()

        self.status = PlayerStatus.DONE


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
