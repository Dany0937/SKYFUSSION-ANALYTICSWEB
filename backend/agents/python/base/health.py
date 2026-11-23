from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class HealthStatus:
    agent: str
    status: str
    uptime: float
    last_event: str | None = None
    memory_mb: float = 0.0
    cpu_percent: float = 0.0
    error_count: int = 0
    details: dict[str, Any] | None = None


class HealthCheck:
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.start_time = datetime.utcnow()
        self.last_event_time: datetime | None = None
        self.error_count = 0
        self.details: dict[str, Any] = {}

    def record_event(self, event_type: str):
        self.last_event_time = datetime.utcnow()

    def record_error(self):
        self.error_count += 1

    def get_status(self) -> HealthStatus:
        import os
        import psutil

        process = psutil.Process(os.getpid())
        uptime_seconds = (datetime.utcnow() - self.start_time).total_seconds()

        return HealthStatus(
            agent=self.agent_name,
            status='healthy' if self.error_count < 10 else 'degraded',
            uptime=round(uptime_seconds, 2),
            last_event=self.last_event_time.isoformat() + 'Z' if self.last_event_time else None,
            memory_mb=round(process.memory_info().rss / 1024 / 1024, 2),
            cpu_percent=process.cpu_percent(interval=0.1),
            error_count=self.error_count,
            details=self.details,
        )

    def to_dict(self) -> dict:
        status = self.get_status()
        return {
            'agent': status.agent,
            'status': status.status,
            'uptime': status.uptime,
            'last_event': status.last_event,
            'memory_mb': status.memory_mb,
            'cpu_percent': status.cpu_percent,
            'error_count': status.error_count,
            'details': status.details,
        }
