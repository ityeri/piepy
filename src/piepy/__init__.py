from piepy import listener
from piepy import async_listener
from piepy import utils
from piepy import music

from piepy.root_container import RootContainer
from piepy.bootstrap import Bootstrapper
from piepy import config


def main():
    container = RootContainer()
    bootstrapper = Bootstrapper(container)

    bootstrapper.run()


__all__ = [
    'listener',
    'async_listener',
    'utils',
    'music',

    'RootContainer',
    'Bootstrapper',
    'config',

    'main'
]
