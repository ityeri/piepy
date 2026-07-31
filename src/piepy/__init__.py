from piepy import config
from piepy.bootstrap import Bootstrapper
from piepy.root_container import RootContainer

from piepy import player_manager
from piepy import player_gc
from piepy import command_front


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

    'main'
]
