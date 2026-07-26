import random
from enum import Enum, auto

from .music import Music


class LoopMode(Enum):
    ONCE_IN_ORDER = auto()
    ONCE_IN_RANDOM = auto()
    LOOP_IN_ORDER = auto()
    LOOP_IN_RANDOM = auto()


class MusicLoopManager:
    def __init__(self, initial_mode: LoopMode):
        self._musics: list[Music] = list()
        self.current_index: int | None = None
        self.next_index: int | None = None
        self.loop_mode: LoopMode = initial_mode
        self.tried_musics: set[Music] = set()

    @property
    def current_music(self) -> Music | None:
        try:
            return self._musics[self.current_index]
        except IndexError:
            return None

    @property
    def next_music(self) -> Music | None:
        if self.next_index is None: return None
        try:
            return self._musics[self.next_index]
        except IndexError:
            return None

    @next_music.setter
    def next_music(self, music: Music):
        self.next_index = self._musics.index(music)


    def get_all_musics(self) -> list[Music]:
        return list(self._musics)
    def get_all_music_ids(self) -> list[str]:
        return [music.music_id for music in self._musics]

    def get_music(self, index: int) -> Music:
        if index < 0: raise IndexError()
        return self._musics[index]
    def get_music_by_id(self, music_id: str) -> Music | None:
        try:
            return next(filter(lambda x: x.music_id == music_id, self._musics))
        except StopIteration:
            return None


    def has_next(self) -> bool:

        if self.next_index is None:
            return False

        if self.loop_mode == LoopMode.ONCE_IN_ORDER:
            if self.next_index < len(self._musics):
                return True
            else:
                return False

        elif self.loop_mode == LoopMode.ONCE_IN_RANDOM:
            if len(self._musics) <= len(self.tried_musics):
                return False
            else:
                return True

        elif self.loop_mode == LoopMode.LOOP_IN_ORDER:
            return True

        elif self.loop_mode == LoopMode.LOOP_IN_RANDOM:
            return True

        return False

    def next(self) -> Music:
        self.current_index = self.next_index
        music = self.next_music
        self.tried_musics.add(music)
        self.update_next_index()

        return music

    def update_next_index(self):
        if self.loop_mode == LoopMode.ONCE_IN_ORDER:
            self.next_index = self.current_index + 1

        elif self.loop_mode == LoopMode.ONCE_IN_RANDOM:

            if len(self._musics) <= len(self.tried_musics):
                self.next_index = None

            else:
                self.next_index = random.randrange(0, len(self._musics))
                while self.next_music in self.tried_musics:
                    self.next_index = random.randrange(0, len(self._musics))

        elif self.loop_mode == LoopMode.LOOP_IN_ORDER:
            self.next_index = self.current_index + 1

            if self.next_index == len(self._musics):
                self.next_index = 0

        elif self.loop_mode == LoopMode.LOOP_IN_RANDOM:
            if len(self._musics) <= len(self.tried_musics):
                self.tried_musics.clear()

            self.next_index = random.randrange(0, len(self._musics))
            while self.next_music in self.tried_musics:
                self.next_index = random.randrange(0, len(self._musics))


    def reset_loop(self):
        self.tried_musics.clear()

    def clear_all(self):
        self.reset_loop()
        for music in self.get_all_musics():
            self.rm(music)
        self.current_index = None
        self.next_index = None


    def add(self, music: Music):
        self._musics.append(music)

    def rm(self, music: Music, cleanup: bool=True):
        self._musics.remove(music)

        if music in self.tried_musics:
            self.tried_musics.remove(music)

        if cleanup:
            music.cleanup()