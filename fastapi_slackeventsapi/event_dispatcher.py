import asyncio
import aiojobs
from typing import Dict, Callable, Any, Awaitable, List, Tuple


class EventDispatcher:
    __events: Dict[str, List[Callable[[Any], Awaitable[Any]]]]

    def __init__(self, timeout: float = 5.0):
        self.__timeout = timeout
        self.__events = {}

    def __contains__(self, event_name):
        return event_name in self.__events

    def items(self) -> Tuple[str]:
        return tuple(
            self.__events.keys()
        )

    def add(self, event_name: str, handler: Callable[[Any], Awaitable[Any]]):
        if event_name in self.__events:
            self.__events[event_name].append(handler)
        else:
            self.__events[event_name] = [handler]

    async def dispatch(self, event_name: str, event_data: Any):
        if event_name in self.__events:
            time_counter = 0.0
            scheduler = await aiojobs.create_scheduler()
            for handler in self.__events[event_name]:
                await scheduler.spawn(handler(event_data))
            while not scheduler.closed:
                if time_counter >= self.__timeout or scheduler.active_count == 0:
                    await scheduler.close()
                await asyncio.sleep(0.1)
                time_counter += 0.1
