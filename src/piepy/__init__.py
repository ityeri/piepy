from piepy import config
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

    'main'
]
