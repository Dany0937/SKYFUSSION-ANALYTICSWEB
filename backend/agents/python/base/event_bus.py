import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Event:
    type: str
    payload: dict[str, Any]
    source: str = ''
    timestamp: str = ''
    correlation_id: str = ''


class EventBusClient:
    def __init__(self, config: dict):
        self.config = config
        self._backend = config.get('backend', 'eventemitter')
        self._connection = None
        self._subscriptions: dict[str, list] = {}

    async def connect(self):
        if self._backend == 'rabbitmq':
            import aio_pika
            self._connection = await aio_pika.connect_robust(
                host=self.config.get('host', 'localhost'),
                port=self.config.get('port', 5672),
                login=self.config.get('user', 'guest'),
                password=self.config.get('password', 'guest'),
            )
        else:
            self._connection = {'type': 'local'}
        import logging
        logging.getLogger(__name__).info(f'EventBus connected (backend={self._backend})')

    async def disconnect(self):
        if self._backend == 'rabbitmq' and self._connection:
            await self._connection.close()
        self._connection = None

    async def publish(self, event_type: str, payload: dict):
        event = Event(
            type=event_type,
            payload=payload,
            source=self.config.get('service_name', 'unknown'),
            timestamp=__import__('datetime').datetime.utcnow().isoformat() + 'Z',
        )
        if self._backend == 'rabbitmq':
            import aio_pika
            channel = await self._connection.channel()
            await channel.default_exchange.publish(
                aio_pika.Message(body=json.dumps({
                    'type': event.type,
                    'payload': event.payload,
                    'source': event.source,
                    'timestamp': event.timestamp,
                }).encode()),
                routing_key=event_type,
            )
        else:
            for handler in self._subscriptions.get(event_type, []):
                await handler(event)

    async def subscribe(self, event_type: str, handler):
        if self._backend == 'rabbitmq':
            import aio_pika
            channel = await self._connection.channel()
            queue = await channel.declare_queue(event_type, durable=True)
            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    async with message.process():
                        data = json.loads(message.body)
                        await handler(Event(**data))
        else:
            if event_type not in self._subscriptions:
                self._subscriptions[event_type] = []
            self._subscriptions[event_type].append(handler)

    async def wait_for(self, event_type: str, timeout: int = 30) -> Event:
        import asyncio
        future = asyncio.get_event_loop().create_future()

        async def waiter(event: Event):
            if not future.done():
                future.set_result(event)

        await self.subscribe(event_type, waiter)
        try:
            return await asyncio.wait_for(future, timeout=timeout)
        except asyncio.TimeoutError:
            raise TimeoutError(f'Timeout waiting for {event_type}')
