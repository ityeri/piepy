from piepy import command_front
from piepy import config
from piepy import player_gc
from piepy import player_manager
from piepy import youtube
from piepy.bootstrap import Bootstrapper
from piepy.root_container import RootContainer


def main():
    container = RootContainer()
    bootstrapper = Bootstrapper(container)

    bootstrapper.run()


__all__ = [
    'RootContainer',
    'Bootstrapper',
    'config',

    'player_manager',
    'player_gc',
    'command_front',
    'youtube',

    'main'
]
