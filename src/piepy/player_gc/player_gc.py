import asyncio
import logging
from asyncio import AbstractEventLoop, Task

from piepy.player_manager import PlayerManager

_logger = logging.getLogger(__name__)


class PlayerGc:
    def __init__(self, player_manager: PlayerManager, interval: float):
        self.player_manager: PlayerManager = player_manager
        self.interval: float = interval
        self._task: Task | None = None

    def start(self, running_loop: AbstractEventLoop):
        self._task = running_loop.create_task(self.run())

    async def run(self):
        while True:
            for controller in self.player_manager.get_all_player_controller().values():
                if controller.current_channel is not None and controller.is_active:
                    active_users = list(filter(lambda m: not m.bot, controller.current_channel.members))

                    if not active_users:
                        _logger.info(
                            f'Stopping idle player in guild={controller.guild_id} channel={controller.current_channel.name}'
                        )
                        await controller.stop()

            await asyncio.sleep(self.interval)
