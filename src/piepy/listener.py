from collections.abc import Callable
from enum import Enum
from typing import TypeVar, Generic, Awaitable

Listener = Callable[..., None]

class EventEnum(Enum):
    def __init__(self, listener_type: type[Listener]):
        self.listener_type = listener_type

T = TypeVar("T", bound=EventEnum)

class ListenerManager(Generic[T]):
    def __init__(self):
        self._listener_map: dict[T, set[Listener]] = dict()

    def add_listener(self, event_type: T, listener: Listener):
        if event_type in self._listener_map:
            self._listener_map[event_type].add(listener)
        else:
            self._listener_map[event_type] = {listener}

    def rm_listener(self, listener: Listener):
        is_removed = False
        for listeners in self._listener_map.values():
            try:
                listeners.remove(listener)
                is_removed = True
            except KeyError: pass

        if not is_removed:
            raise ValueError("해당 리스너를 하나도 찾을수 없습니다")

    def dispatch_event(self, event_type: T, *args, **kwargs):
        if event_type in self._listener_map:
            for listener in self._listener_map[event_type]:
                listener(*args, **kwargs)

    def all_listeners(self) -> list[tuple[T, Listener]]:
        all_listeners = list()

        for event_type, listeners in self._listener_map.items():
            for listener in listeners:
                all_listeners.append((event_type, listener))

        return all_listeners