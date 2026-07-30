from discord import VoiceChannel
from discord.ext import commands

from .player import Player, PlayerStopEvent
from .player_controller import PlayerController


class PlayerManager:
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
        self._players: dict[int, Player] = dict() # guild id: Player

    async def _on_player_stop(self, player_stop_event: PlayerStopEvent):
        self._players.pop(player_stop_event.player.guild_id)

    async def ready_player(
            self,
            guild_id: int,
            voice_channel: VoiceChannel,
            *,
            is_loop: bool = False,
            is_random_order: bool = False
    ) -> PlayerController | None:
        if guild_id in self._players:
            return None

        player = Player(guild_id, self._on_player_stop)
        await player.ready(voice_channel, self.bot.loop, is_loop=is_loop, is_random_order=is_random_order)

        self._players[guild_id] = player

        return PlayerController(player)

    async def get_player_controller(self, guild_id: int) -> PlayerController | None:
        if guild_id in self._players:
            return PlayerController(self._players[guild_id])
        else:
            return None
