from typing import Callable, Awaitable

from discord import VoiceChannel
from discord.ext import commands

from .player import Player, PlayerStopEvent, PlayerStopReason
from .player_controller import PlayerController


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
                ... # TODO logging

            self._players.pop(event.player.guild_id)

        player = Player(guild_id, on_player_stop)
        await player.ready(voice_channel, self.bot.loop, is_loop=is_loop, is_random_order=is_random_order)

        self._players[guild_id] = player

        return PlayerController(player)

    def get_player_controller(self, guild_id: int) -> PlayerController | None:
        if guild_id in self._players:
            return PlayerController(self._players[guild_id])
        else:
            return None
