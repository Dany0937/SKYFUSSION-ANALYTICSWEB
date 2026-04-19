"""
Event Bus Module for Skyfusion Analytics - Geospatial Agent
==========================================================

Sistema de mensajería de eventos para el pipeline de datos geoespaciales.

Arquitectura:
- Modo Local (file-based): Funciona sin infraestructura externa
- Modo Redis: Para producción con infraestructura Redis
- Modo RabbitMQ: Para producción con RabbitMQ

El evento principal emitido es: IMAGENES_HISTORICAS_LISTAS
"""

import os
import json
import time
import uuid
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from threading import Lock
import traceback


class EventBackend(Enum):
    """Backend de mensajería disponible."""
    LOCAL = "local"
    REDIS = "redis"
    RABBITMQ = "rabbitmq"


@dataclass
class SkyfusionEvent:
    """Estructura estándar de evento para Skyfusion Analytics."""
    event_id: str
    event_type: str
    timestamp: str
    source: str
    version: str
    payload: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), default=str)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "SkyfusionEvent":
        return cls(**data)


class EventStore:
    """
    Almacenamiento local de eventos en sistema de archivos.
    
    Implementa un event store simple paramodo offline/local
    que mantiene un log de eventos en archivos JSON.
    """
    
    def __init__(self, storage_dir: str = "./data/events"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.lock = Lock()
        self._current_day = self._get_day_filename()
        self._event_file = self.storage_dir / self._current_day
        self._initialize_file()
    
    def _get_day_filename(self) -> str:
        return f"events_{datetime.now().strftime('%Y%m%d')}.jsonl"
    
    def _initialize_file(self) -> None:
        if not self._event_file.exists():
            self._event_file.write_text("")
    
    def _check_day_change(self) -> None:
        current_day = self._get_day_filename()
        if current_day != self._current_day:
            self._current_day = current_day
            self._event_file = self.storage_dir / self._current_day
            self._initialize_file()
    
    def append(self, event: SkyfusionEvent) -> None:
        """Agrega un evento al log."""
        with self.lock:
            self._check_day_change()
            with open(self._event_file, 'a') as f:
                f.write(event.to_json() + '\n')
    
    def get_events(
        self,
        event_type: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> List[SkyfusionEvent]:
        """Recupera eventos del almacenamiento."""
        events = []
        
        if since:
            since_str = since.strftime('%Y%m%d')
        else:
            since_str = None
        
        for event_file in sorted(self.storage_dir.glob("events_*.jsonl")):
            if since_str and event_file.stem < f"events_{since_str}":
                continue
                
            with open(event_file, 'r') as f:
                for line in f:
                    if line.strip():
                        try:
                            data = json.loads(line)
                            if event_type and data.get('event_type') != event_type:
                                continue
                            events.append(SkyfusionEvent.from_dict(data))
                        except:
                            continue
        
        return events[-limit:]
    
    def get_last_event(self, event_type: Optional[str] = None) -> Optional[SkyfusionEvent]:
        """Obtiene el último evento de un tipo."""
        events = self.get_events(event_type=event_type, limit=1)
        return events[0] if events else None


class LocalEventBus:
    """
    Bus de eventos local (file-based).
    
    Implementa pub/sub básico usando archivos para notificación.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.subscribers: Dict[str, List[Callable]] = {}
        self.event_store = EventStore(
            storage_dir=self.config.get('storage_dir', './data/events')
        )
        self.logger = logging.getLogger(__name__)
    
    def emit(self, event: SkyfusionEvent) -> bool:
        """
        Emite un evento al bus local.
        
        Args:
            event: Evento a emitir
            
        Returns:
            True si se emitió exitosamente
        """
        try:
            self.event_store.append(event)
            
            if event.event_type in self.subscribers:
                for callback in self.subscribers[event.event_type]:
                    try:
                        callback(event)
                    except Exception as e:
                        self.logger.error(f"Error en subscriber: {e}")
            
            self.logger.info(
                f"Evento emitido: {event.event_type} (ID: {event.event_id})"
            )
            return True
            
        except Exception as e:
            self.logger.error(f"Error emitiendo evento: {e}")
            return False
    
    def subscribe(self, event_type: str, callback: Callable) -> Callable:
        """
        Suscribe un callback a un tipo de evento.
        
        Args:
            event_type: Tipo de evento
            callback: Función a llamar cuando se emita el evento
            
        Returns:
            Función para desuscribirse
        """
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)
        
        def unsubscribe():
            if event_type in self.subscribers:
                self.subscribers[event_type].remove(callback)
        
        return unsubscribe


class RedisEventBus:
    """
    Bus de eventos usando Redis Pub/Sub.
    
    Requiere infraestructura Redis disponible.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.redis_client = None
        self.channel = self.config.get('channel', 'skyfusion:events')
        self.logger = logging.getLogger(__name__)
        self._local_store = EventStore()
        self._connect()
    
    def _connect(self) -> bool:
        """Conecta a Redis."""
        try:
            import redis
            self.redis_client = redis.Redis(
                host=self.config.get('host', 'localhost'),
                port=self.config.get('port', 6379),
                db=self.config.get('db', 0),
                decode_responses=True,
                socket_connect_timeout=5
            )
            self.redis_client.ping()
            self.logger.info("Conectado a Redis")
            return True
        except Exception as e:
            self.logger.warning(f"No se pudo conectar a Redis: {e}")
            self.redis_client = None
            return False
    
    def emit(self, event: SkyfusionEvent) -> bool:
        """Emite evento a Redis o guarda localmente."""
        self._local_store.append(event)
        
        if self.redis_client:
            try:
                self.redis_client.publish(self.channel, event.to_json())
                self.logger.info(
                    f"Evento publicado en Redis: {event.event_type}"
                )
                return True
            except Exception as e:
                self.logger.error(f"Error publicando en Redis: {e}")
        
        return False
    
    def subscribe(self, event_type: str, callback: Callable) -> Callable:
        """Suscribe a eventos (requiere setup adicional de subscriber)."""
        def unsubscribe():
            pass
        return unsubscribe


class RabbitMQEventBus:
    """
    Bus de eventos usando RabbitMQ.
    
    Requiere infraestructura RabbitMQ disponible.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.connection = None
        self.channel = None
        self.logger = logging.getLogger(__name__)
        self._local_store = EventStore()
        self._connect()
    
    def _connect(self) -> bool:
        """Conecta a RabbitMQ."""
        try:
            import pika
            credentials = pika.PlainCredentials(
                self.config.get('user', 'guest'),
                self.config.get('password', 'guest')
            )
            parameters = pika.ConnectionParameters(
                host=self.config.get('host', 'localhost'),
                port=self.config.get('port', 5672),
                credentials=credentials,
                connection_attempts=3,
                retry_delay=1
            )
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            self.channel.exchange_declare(
                exchange='skyfusion_events',
                exchange_type='topic',
                durable=True
            )
            self.logger.info("Conectado a RabbitMQ")
            return True
        except Exception as e:
            self.logger.warning(f"No se pudo conectar a RabbitMQ: {e}")
            return False
    
    def emit(self, event: SkyfusionEvent) -> bool:
        """Emite evento a RabbitMQ o guarda localmente."""
        self._local_store.append(event)
        
        if self.channel:
            try:
                self.channel.basic_publish(
                    exchange='skyfusion_events',
                    routing_key=event.event_type,
                    body=event.to_json(),
                    properties=pika.BasicProperties(
                        delivery_mode=2,
                        content_type='application/json'
                    )
                )
                self.logger.info(
                    f"Evento publicado en RabbitMQ: {event.event_type}"
                )
                return True
            except Exception as e:
                self.logger.error(f"Error publicando en RabbitMQ: {e}")
        
        return False
    
    def subscribe(self, event_type: str, callback: Callable) -> Callable:
        """Suscribe a eventos (requiere setup adicional de subscriber)."""
        def unsubscribe():
            pass
        return unsubscribe


class GeoEventEmitter:
    """
    Emisor de eventos geoespaciales para el Geospatial Agent.
    
    Detecta automáticamente el backend disponible y emite
    el evento IMAGENES_HISTORICAS_LISTAS.
    """
    
    EVENT_TYPE_IMAGENES_HISTORICAS_LISTAS = "IMAGENES_HISTORICAS_LISTAS"
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.source = "geospatial_agent"
        self.version = "1.0.0"
        self.logger = logging.getLogger(__name__)
        
        self._bus = self._create_bus()
    
    def _create_bus(self):
        """Crea el bus de eventos según configuración."""
        backend = self.config.get('backend', 'local')
        
        if backend == 'redis':
            return RedisEventBus(self.config.get('redis', {}))
        elif backend == 'rabbitmq':
            return RabbitMQEventBus(self.config.get('rabbitmq', {}))
        else:
            return LocalEventBus(self.config.get('local', {}))
    
    def emit_historical_images_ready(
        self,
        date_range: Tuple[str, str],
        collections_used: List[str],
        image_count: int,
        cloud_filter_applied: bool = True,
        max_cloud_percent: float = 15.0,
        basin_info: Optional[Dict] = None,
        processing_metrics: Optional[Dict] = None
    ) -> bool:
        """
        Emite el evento IMAGENES_HISTORICAS_LISTAS.
        
        Args:
            date_range: Tupla (start_date, end_date)
            collections_used: Lista de colecciones GEE utilizadas
            image_count: Número de imágenes encontradas
            cloud_filter_applied: Si se aplicó filtro de nubosidad
            max_cloud_percent: Porcentaje máximo de nubosidad
            basin_info: Información de la cuenca procesada
            processing_metrics: Métricas adicionales de procesamiento
            
        Returns:
            True si el evento se emitió exitosamente
        """
        payload = {
            "dataAvailability": {
                "dateRange": {
                    "start": date_range[0],
                    "end": date_range[1]
                },
                "collectionsUsed": collections_used,
                "imageCount": image_count
            },
            "processingConfig": {
                "cloudFilterApplied": cloud_filter_applied,
                "maxCloudPercent": max_cloud_percent
            },
            "basin": basin_info or {
                "id": "combeima_basin",
                "name": "Cuenca Alta Río Combeima",
                "location": "Ibagué, Tolima, Colombia",
                "areaHa": 12450.75,
                "bbox": [-75.257, 4.433, -75.142, 4.529]
            },
            "processingMetrics": processing_metrics or {}
        }
        
        event = SkyfusionEvent(
            event_id=str(uuid.uuid4()),
            event_type=self.EVENT_TYPE_IMAGENES_HISTORICAS_LISTAS,
            timestamp=datetime.now().isoformat(),
            source=self.source,
            version=self.version,
            payload=payload,
            metadata={
                "agent": "geospatial",
                "pipeline": "data_ingestion",
                "complejidad": "historico_completo" if image_count > 100 else "muestra"
            }
        )
        
        self.logger.info(
            f"Emitiendo evento {self.EVENT_TYPE_IMAGENES_HISTORICAS_LISTAS}: "
            f"{image_count} imágenes de {date_range[0]} a {date_range[1]}"
        )
        
        return self._bus.emit(event)
    
    def emit_image_processed(
        self,
        image_id: str,
        collection: str,
        date: str,
        cloud_percent: float,
        bands_info: Optional[Dict] = None
    ) -> bool:
        """
        Emite evento cuando una imagen individual es procesada.
        
        Args:
            image_id: ID de la imagen en GEE
            collection: Nombre de la colección
            date: Fecha de adquisición
            cloud_percent: Porcentaje de nubosidad
            bands_info: Información de bandas disponibles
            
        Returns:
            True si el evento se emitió exitosamente
        """
        payload = {
            "imageId": image_id,
            "collection": collection,
            "date": date,
            "cloudCover": cloud_percent,
            "bands": bands_info or {}
        }
        
        event = SkyfusionEvent(
            event_id=str(uuid.uuid4()),
            event_type="IMAGEN_INDIVIDUAL_PROCESADA",
            timestamp=datetime.now().isoformat(),
            source=self.source,
            version=self.version,
            payload=payload
        )
        
        return self._bus.emit(event)
    
    def emit_error(
        self,
        error_type: str,
        error_message: str,
        context: Optional[Dict] = None
    ) -> bool:
        """
        Emite evento de error.
        
        Args:
            error_type: Tipo de error
            error_message: Mensaje de error
            context: Contexto adicional
            
        Returns:
            True si el evento se emitió exitosamente
        """
        payload = {
            "errorType": error_type,
            "message": error_message,
            "context": context or {},
            "traceback": traceback.format_exc()
        }
        
        event = SkyfusionEvent(
            event_id=str(uuid.uuid4()),
            event_type="GEOSPATIAL_AGENT_ERROR",
            timestamp=datetime.now().isoformat(),
            source=self.source,
            version=self.version,
            payload=payload,
            metadata={"severity": "error"}
        )
        
        self.logger.error(f"Error en Geospatial Agent: {error_message}")
        return self._bus.emit(event)
    
    def subscribe(self, event_type: str, callback: Callable) -> Callable:
        """Suscribe un callback a un tipo de evento."""
        return self._bus.subscribe(event_type, callback)
    
    def get_last_event(
        self,
        event_type: Optional[str] = None
    ) -> Optional[SkyfusionEvent]:
        """Obtiene el último evento de un tipo."""
        return self._bus.event_store.get_last_event(event_type)


def get_event_emitter(config: Optional[Dict] = None) -> GeoEventEmitter:
    """
    Factory function para crear un GeoEventEmitter.
    
    Lee configuración desde variables de entorno si no se provee config.
    """
    if config is None:
        config = {
            'backend': os.getenv('GEO_EVENT_BACKEND', 'local'),
            'redis': {
                'host': os.getenv('REDIS_HOST', 'localhost'),
                'port': int(os.getenv('REDIS_PORT', 6379)),
                'db': int(os.getenv('REDIS_DB', 0)),
                'channel': os.getenv('REDIS_CHANNEL', 'skyfusion:events')
            },
            'rabbitmq': {
                'host': os.getenv('RABBITMQ_HOST', 'localhost'),
                'port': int(os.getenv('RABBITMQ_PORT', 5672)),
                'user': os.getenv('RABBITMQ_USER', 'guest'),
                'password': os.getenv('RABBITMQ_PASSWORD', 'guest')
            },
            'local': {
                'storage_dir': os.getenv('EVENT_STORAGE_DIR', './data/events')
            }
        }
    
    return GeoEventEmitter(config)


if __name__ == "__main__":
    print("=" * 60)
    print("Skyfusion Analytics - GeoEventEmitter Test")
    print("=" * 60)
    
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] %(levelname)s: %(message)s'
    )
    
    emitter = get_event_emitter()
    
    print("\n📡 Probando emisión de evento...")
    
    result = emitter.emit_historical_images_ready(
        date_range=("1969-01-01", "2023-12-31"),
        collections_used=["LANDSAT/LM01/T1", "LANDSAT/LT05/C02/T1", "LANDSAT/LC08/C02/T1_L2"],
        image_count=1250,
        cloud_filter_applied=True,
        max_cloud_percent=15.0,
        processing_metrics={
            "yearsProcessed": 55,
            "yearsWithData": 48,
            "totalPixelsAnalyzed": 15000000
        }
    )
    
    if result:
        print("✅ Evento IMAGENES_HISTORICAS_LISTAS emitido exitosamente")
    else:
        print("⚠️ Evento guardado localmente (backend no disponible)")
    
    last_event = emitter.get_last_event(
        emitter.EVENT_TYPE_IMAGENES_HISTORICAS_LISTAS
    )
    
    if last_event:
        print(f"\n📋 Último evento:")
        print(json.dumps(last_event.to_dict(), indent=2, default=str))
