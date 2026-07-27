import discord
from dependency_injector import containers
from dependency_injector.providers import Object, Singleton
from discord.ext import commands

from piepy import config


class RootContainer(containers.DeclarativeContainer):
    bot: Object[commands.Bot] = \
        Object(commands.Bot(command_prefix='/', intents=discord.Intents.all()))

    config: Singleton[config.Config] = \
        Singleton(config.get_config_from_env)
