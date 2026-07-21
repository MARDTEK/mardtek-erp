from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Dict, List

logger = logging.getLogger(__name__)

EventHandler = Callable[..., Awaitable[None]]


@dataclass
class Event:
    name: str
    payload: Dict[str, Any]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    source_module: str = ""


class EventBus:
    """Simple in-process pub/sub event bus for module decoupling.

    Modules emit events (e.g. ``NonConformityOpened``, ``LeadWon``) and
    other modules subscribe to react without direct coupling.
    """

    def __init__(self) -> None:
        self._handlers: Dict[str, List[EventHandler]] = {}
        self._history: List[Event] = []

    def subscribe(self, event_name: str, handler: EventHandler) -> None:
        if event_name not in self._handlers:
            self._handlers[event_name] = []
        self._handlers[event_name].append(handler)
        logger.debug("Handler '%s' subscribed to '%s'", handler.__name__, event_name)

    def unsubscribe(self, event_name: str, handler: EventHandler) -> None:
        if event_name in self._handlers:
            self._handlers[event_name] = [h for h in self._handlers[event_name] if h is not handler]

    async def emit(self, event: Event) -> None:
        self._history.append(event)
        handlers = self._handlers.get(event.name, [])
        if not handlers:
            logger.debug("Event '%s' emitted with no subscribers", event.name)
            return
        logger.info("Emitting '%s' to %d handler(s)", event.name, len(handlers))
        results = await asyncio.gather(
            *[handler(event) for handler in handlers],
            return_exceptions=True,
        )
        for handler, result in zip(handlers, results):
            if isinstance(result, Exception):
                logger.error(
                    "Handler '%s' failed on event '%s': %s",
                    handler.__name__,
                    event.name,
                    result,
                )

    def get_history(self, limit: int = 50) -> List[Event]:
        return self._history[-limit:]


event_bus = EventBus()
