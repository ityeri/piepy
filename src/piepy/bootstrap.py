import asyncio
import logging

import reger
from discord.ext import commands

from piepy.root_container import RootContainer


class Bootstrapper:
    def __init__(self, root_container: RootContainer):
        self.root_container: RootContainer = root_container
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.bot: commands.Bot = root_container.bot()

    def run(self):
        asyncio.run(self.arun())

    async def arun(self):
        print('Bootstrapper: Setup logging...')
        self.setup_logging()
        self.logger.info('If you can see it, logging setup is complete')

        self.bot.add_listener(self.on_ready)

        self.logger.info('Loading MusicCommandCog...')
        cog = self.root_container.music_command_cog()
        await self.bot.add_cog(cog)
        self.logger.info('MusicCommandCog loading is done')

        self.logger.info('Starting PlayerGc...')
        player_gc = self.root_container.player_gc()
        asyncio.create_task(player_gc.run())
        self.logger.info('PlayerGc has started')

        self.logger.info('Starting bot...')
        config = self.root_container.config()
        bot_task = asyncio.create_task(self.bot.start(token=config.bot_token))
        self.logger.info('Bot has started')

        self.logger.info('Bootstrapping is complete! now you just waiting for actual log with delicious ramyeon')

        await bot_task

    async def on_ready(self):
        self.logger.info('Bot is now ready!')
        self.logger.info(f'Logged in as {self.bot.user.name}')
        self.logger.info('Timings Reset')

        self.logger.info('Command syncing... (This may take a moment!)')
        await self.bot.tree.sync()
        self.logger.info('Command syncing has done')

    def setup_logging(self):
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)

        # TODO this looks bad log saving system
        file_handler = logging.FileHandler(filename='latest.log', encoding='utf-8', mode='w')
        file_handler.setFormatter(reger.ColourFormatter())

        root_logger.addHandler(file_handler)

        reger.setup_logging()
