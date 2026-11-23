from abc import ABC, abstractmethod
from typing import Any, Callable
from .event_bus import EventBusClient, Event
from .logger import get_logger


class BaseAgent(ABC):
    def __init__(self, name: str, config: dict):
        self.name = name
        self.config = config
        self._status = 'idle'
        self._event_bus = EventBusClient(config.get('rabbitmq', {}))
        self.logger = get_logger(name)
        self._handlers: dict[str, list[Callable]] = {}
        self._input_event: str | None = None

    @property
    def status(self) -> str:
        return self._status

    @status.setter
    def status(self, value: str):
        self._status = value
        self.logger.info(f'Status changed to: {value}')

    async def initialize(self) -> 'BaseAgent':
        await self._event_bus.connect()
        self.status = 'ready'
        self.logger.info(f'{self.name} initialized')
        return self

    async def start(self):
        if not self._input_event:
            raise ValueError(f'{self.name}: _input_event not set')
        self.status = 'processing'
        await self._event_bus.subscribe(self._input_event, self._handle_wrapper)

    async def _handle_wrapper(self, event: Event):
        self.logger.info(f'Received event: {event.type}', extra={'payload': event.payload})
        self.status = 'processing'
        try:
            await self.handle_event(event)
        except Exception as e:
            self.logger.error(f'Error handling event: {e}', exc_info=True)
            await self.emit(f'{self.name}:error', {'error': str(e), 'original_event': event.type})
        finally:
            self.status = 'ready'

    @abstractmethod
    async def handle_event(self, event: Event):
        pass

    async def emit(self, event_type: str, payload: dict):
        await self._event_bus.publish(event_type, {'agent': self.name, **payload})

    def on(self, event: str, handler: Callable):
        if event not in self._handlers:
            self._handlers[event] = []
        self._handlers[event].append(handler)

    async def _emit_local(self, event: str, data: Any):
        for handler in self._handlers.get(event, []):
            await handler(data)

    async def shutdown(self):
        self.status = 'shutdown'
        await self._event_bus.disconnect()
        self.logger.info(f'{self.name} shutdown complete')

    def get_status(self) -> dict:
        return {
            'name': self.name,
            'status': self.status,
            'config': {k: v for k, v in self.config.items() if k != 'secrets'},
        }
