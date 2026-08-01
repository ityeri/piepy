import logging
from typing import Callable, Awaitable

from discord import VoiceChannel
from discord.ext import commands

from .player import Player, PlayerStopEvent, PlayerStopReason
from .player_controller import PlayerController

_logger = logging.getLogger(__name__)


class PlayerManager:
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
        self._players: dict[int, Player] = dict() # guild id: Player

    async def ready_player(
            self,
            guild_id: int,
            voice_channel: VoiceChannel,
            *,
            stop_callback: Callable[[PlayerController, PlayerStopReason], Awaitable] = lambda c: None,
            is_loop: bool = False,
            is_random_order: bool = False
    ) -> PlayerController | None:
        if guild_id in self._players:
            return None

        async def on_player_stop(event: PlayerStopEvent):
            try:
                await stop_callback(PlayerController(event.player), event.reason)
            except Exception:
                _logger.error(
                    f'stop_callback raised an exception for guild {event.player.guild_id}',
                    exc_info=True
                )

            self._players.pop(event.player.guild_id)

        player = Player(self.bot, guild_id, on_player_stop)
        await player.ready(voice_channel, self.bot.loop, is_loop=is_loop, is_random_order=is_random_order)

        self._players[guild_id] = player

        return PlayerController(player)

    def get_player_controller(self, guild_id: int) -> PlayerController | None:
        if guild_id in self._players:
            return PlayerController(self._players[guild_id])
        else:
            return None

    def get_all_player_controller(self) -> dict[int, PlayerController]:
        return {id: PlayerController(player) for id, player in self._players.items()}
