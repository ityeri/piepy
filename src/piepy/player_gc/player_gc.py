import asyncio
from asyncio import AbstractEventLoop, Task

from piepy.player_manager import PlayerManager


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
                        await controller.stop()

            await asyncio.sleep(self.interval)
