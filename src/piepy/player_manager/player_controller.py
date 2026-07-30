import asyncio
from enum import Enum, auto
from typing import Final
from uuid import UUID

from discord import VoiceChannel

from .music_element import MusicElement
from .player import Player
from .player import PlayerStatus


class _OperationResult(Enum):
    def __new__(cls, value, is_success: bool):
        obj = object.__new__(cls)
        obj._value_ = value
        return obj

    def __init__(self, value, is_success: bool):
        self.is_success = is_success

class StateValidationFailedReason(_OperationResult):
    NOT_YET_ACTIVE = (auto(), False)
    ALREADY_STOPPED = (auto(), False)

class MusicAddingResult(_OperationResult):
    ADDED = (auto(), True)
    DUPLICATED = (auto(), False)

class MusicRemovingResult(_OperationResult):
    REMOVED = (auto(), True)
    SKIPPED_AND_REMOVED = (auto(), True)


class PlayerController:
    """
    This class can be creatable only in the player_manager package domain
    """
    def __init__(self, player: Player):
        if player.status == PlayerStatus.BEFORE_READY:
            raise RuntimeError('Could not create PlayerController. Player status should not be a BEFORE_READY')

        self._player: Final[Player] = player
        self.session_id: Final[UUID] = self._player.session_id
        self.guild_id: Final[int] = self._player.guild_id

    @property
    def status(self) -> PlayerStatus: return self._player.status
    @property
    def musics(self) -> list[MusicElement]: return self._player.musics

    @property
    def current_music(self) -> MusicElement | None: return self._player.current_music
    @property
    def next_music(self) -> MusicElement | None: return self._player.next_music

    @property
    def is_loop(self) -> bool: return self._player.is_loop
    @property
    def is_random_order(self) -> bool: return self._player.is_random_order

    @property
    def current_channel(self) -> VoiceChannel | None:
        if self._player.voice_client is not None:
            return self._player.voice_client.channel
        else:
            return None

    @property
    def is_active(self) -> bool: return self._player.status == PlayerStatus.ACTIVE

    def _validate_status(self) -> StateValidationFailedReason | None:
        if self.status == PlayerStatus.DONE:
            return StateValidationFailedReason.ALREADY_STOPPED
        elif self.status != PlayerStatus.ACTIVE:
            return StateValidationFailedReason.NOT_YET_ACTIVE
        else:
            return None

    def start(self) -> bool:
        try:
            self._player.start()
            return True
        except RuntimeError:
            return False

    async def add_music(self, music: MusicElement) -> MusicAddingResult | StateValidationFailedReason:
        if music in self._player.musics:
            return MusicAddingResult.DUPLICATED
        else:
            self._player.add_last(music)
            return MusicAddingResult.ADDED

    async def stop(self) -> StateValidationFailedReason | None:
        if (result := self._validate_status()) is not None:
            return result

        await self._player.stop()
        return None

    async def rm_music(self, music: MusicElement) -> MusicRemovingResult | StateValidationFailedReason:
        if (result := self._validate_status()) is not None:
            return result

        skipped = False

        if music == self.current_music:
            future = self._player.subscribe_next_step()
            self._player.jump_to(None)
            await asyncio.wait_for(future, timeout=None)
            skipped = True

        self._player.rm(music)

        if skipped:
            return MusicRemovingResult.SKIPPED_AND_REMOVED
        else:
            return MusicRemovingResult.REMOVED

    def jump_to_music(self, music: MusicElement | None) -> StateValidationFailedReason | None:
        if (result := self._validate_status()) is not None:
            return result

        self._player.jump_to(music)
        return None

    def change_order_mode(self, is_loop: bool, is_random_order: bool) -> StateValidationFailedReason | None:
        if (result := self._validate_status()) is not None:
            return result

        self._player.change_order_mode(is_loop, is_random_order)
        return None
