import os
import yaml
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Config:
    agents: dict = field(default_factory=dict)
    rabbitmq: dict = field(default_factory=lambda: {
        'host': 'localhost',
        'port': 5672,
        'user': 'guest',
        'password': 'guest',
        'backend': 'eventemitter',
    })
    storage: dict = field(default_factory=lambda: {
        'blob_container': 'skyfusion-data',
        'connection_string': '',
    })
    logging: dict = field(default_factory=lambda: {
        'level': 'INFO',
        'format': 'json',
    })
    monitoring: dict = field(default_factory=lambda: {
        'prometheus_port': 8000,
        'health_port': 8080,
    })

    @classmethod
    def from_dict(cls, data: dict) -> 'Config':
        config = cls()
        for key, value in data.items():
            if hasattr(config, key) and isinstance(getattr(config, key), dict):
                merged = {**getattr(config, key), **(value or {})}
                setattr(config, key, merged)
            elif key in config.__annotations__:
                setattr(config, key, value)
        return config


def load_config(path: str | None = None) -> Config:
    paths = [
        path,
        'config/agents.yaml',
        '../config/agents.yaml',
        '/etc/skyfusion/agents.yaml',
        os.environ.get('AGENTS_CONFIG_PATH'),
    ]

    config_data: dict[str, Any] = {}

    for config_path in paths:
        if config_path and os.path.exists(config_path):
            with open(config_path) as f:
                data = yaml.safe_load(f) or {}
                deep_merge(config_data, data)
            break

    env_overrides = {
        k.lower().replace('agent_', '').replace('__', '.'): v
        for k, v in os.environ.items()
        if k.startswith('AGENT_')
    }
    for key, value in env_overrides.items():
        parts = key.split('.')
        target = config_data
        for part in parts[:-1]:
            target = target.setdefault(part, {})
        target[parts[-1]] = value

    return Config.from_dict(config_data.get('agents', config_data))


def deep_merge(base: dict, override: dict):
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            deep_merge(base[key], value)
        else:
            base[key] = value
