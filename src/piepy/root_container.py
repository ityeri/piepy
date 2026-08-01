import discord
from dependency_injector import containers
from dependency_injector.providers import Object, Singleton
from discord.ext import commands

from piepy import config
from piepy.command_front.music_command_cog import MusicCommandCog
from piepy.player_gc import PlayerGc
from piepy.player_manager import PlayerManager


class RootContainer(containers.DeclarativeContainer):
    bot: Object[commands.Bot] = \
        Object(commands.Bot(command_prefix='/', intents=discord.Intents.all()))

    config: Singleton[config.Config] = \
        Singleton(config.get_config_from_env)

    player_manager: Singleton[PlayerManager] = \
        Singleton(PlayerManager, bot=bot)

    player_gc: Singleton[PlayerGc] = \
        Singleton(PlayerGc, player_manager=player_manager, interval=60.0)

    music_command_cog: Singleton[MusicCommandCog] = \
        Singleton(MusicCommandCog, bot=bot, player_manager=player_manager)
