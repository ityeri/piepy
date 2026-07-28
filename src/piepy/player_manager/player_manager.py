from enum import Enum, auto

from discord import VoiceChannel
from discord.ext import commands

from .music_element import MusicElement
from .player import Player, PlayerStopEvent


class MusicAddResult(Enum):
    is_success: bool

    def __new__(cls, value, is_success: bool):
        obj = object.__new__(cls)
        obj._value_ = value
        return obj

    def __init__(self, value, is_success: bool):
        self.is_success = is_success

    CREATED_AND_ADDED = (auto(), True)
    ADDED = (auto(), True)
    DUPLICATED = (auto(), False)

class StopResult(Enum):
    is_success: bool

    def __new__(cls, value, is_success: bool):
        obj = object.__new__(cls)
        obj._value_ = value
        return obj

    def __init__(self, value, is_success: bool):
        self.is_success = is_success

    PLAYER_NOT_FOUND = (auto(), False)
    STOPPED = (auto(), True)

class MusicRemoveResult(Enum):
    is_success: bool

    def __new__(cls, value, is_success: bool):
        obj = object.__new__(cls)
        obj._value_ = value
        return obj

    def __init__(self, value, is_success: bool):
        self.is_success = is_success

    PLAYER_NOT_FOUND = (auto(), False)
    REMOVED = (auto(), True)
    SKIPPED_AND_REMOVED = (auto(), True)


class PlayerManager:
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
        self._players: dict[int, Player] = dict() # guild id: Player

    def _get_player(self, guild_id: int) -> Player | None:
        try:
            return self._players[guild_id]
        except KeyError:
            return None

    def _create_player(self, guild_id: int) -> Player:
        if guild_id in self._players:
            raise RuntimeError(f'Player for given guild_id is already exists (id: {guild_id})')

        created_player = Player(guild_id, on_stop=self._on_player_stop)
        self._players[guild_id] = created_player

        return created_player

    async def _on_player_stop(self, player_stop_event: PlayerStopEvent):
        self._players.pop(player_stop_event.player.guild_id)

    async def play_or_add(self, guild_id: int, voice_channel: VoiceChannel, music_element: MusicElement) -> MusicAddResult:
        is_created = False

        player = self._get_player(guild_id)
        if player is None:
            player = self._create_player(guild_id)

            await player.ready(voice_channel, self.bot.loop, is_loop=True, is_random_order=False)

            is_created = True

        if music_element in player.musics:
            return MusicAddResult.DUPLICATED

        player.add_last(music_element)

        if is_created:
            player.start()

        return MusicAddResult.CREATED_AND_ADDED if is_created else MusicAddResult.ADDED

    async def stop(self, guild_id: int) -> StopResult:
        player = self._get_player(guild_id)
        if player is None:
            return StopResult.PLAYER_NOT_FOUND

        await player.stop()

        return StopResult.STOPPED

    def rm(self, guild_id: int, music_element: MusicElement) -> MusicRemoveResult:
        player = self._get_player(guild_id)
        if player is None:
            return MusicRemoveResult.PLAYER_NOT_FOUND

        skipped = False

        if music_element == player.current_music:
            player.skip()
            skipped = True

        player.rm(music_element)

        if skipped:
            return MusicRemoveResult.SKIPPED_AND_REMOVED
        else:
            return MusicRemoveResult.REMOVED
