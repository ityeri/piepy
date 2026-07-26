from collections.abc import Callable
from enum import Enum
from typing import TypeVar, Generic, Awaitable

AsyncListener = Callable[..., Awaitable[None]]

class AsyncEventEnum(Enum):
    def __init__(self, listener_type: type[AsyncListener]):
        self.listener_type = listener_type

T = TypeVar("T", bound=AsyncEventEnum)

class AsyncListenerManager(Generic[T]):
    def __init__(self):
        self._listener_map: dict[T, set[AsyncListener]] = dict()

    def add_listener(self, event_type: T, listener: AsyncListener):
        if event_type in self._listener_map:
            self._listener_map[event_type].add(listener)
        else:
            self._listener_map[event_type] = {listener}

    def rm_listener(self, listener: AsyncListener):
        is_removed = False
        for listeners in self._listener_map.values():
            try:
                listeners.remove(listener)
                is_removed = True
            except KeyError: pass

        if not is_removed:
            raise ValueError("해당 리스너를 하나도 찾을수 없습니다")

    async def dispatch_event(self, event_type: T, *args, **kwargs):
        if event_type in self._listener_map:
            for listener in list(self._listener_map[event_type]):
                await listener(*args, **kwargs)

    def all_listeners(self) -> list[tuple[T, AsyncListener]]:
        all_listeners = list()

        for event_type, listeners in self._listener_map.items():
            for listener in listeners:
                all_listeners.append((event_type, listener))

        return all_listeners