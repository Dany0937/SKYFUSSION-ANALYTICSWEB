from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any


@dataclass
class SceneMetadata:
    scene_id: str
    collection: str
    satellite: str
    date: datetime
    cloud_pct: float
    bounds: dict
    bands: list[str]
    scale: int
    crs: str
    resolution_m: float
    blob_url: str
    checksum: str
    ingested_at: str = ''


class MetadataOrganizer:
    def __init__(self):
        self._scenes: dict[str, SceneMetadata] = {}

    def register_scene(self, scene: SceneMetadata):
        scene.ingested_at = datetime.utcnow().isoformat() + 'Z'
        self._scenes[scene.scene_id] = scene

    def get_scene(self, scene_id: str) -> SceneMetadata | None:
        return self._scenes.get(scene_id)

    def query(
        self,
        collection: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        max_cloud: float | None = None,
    ) -> list[SceneMetadata]:
        results = list(self._scenes.values())

        if collection:
            results = [s for s in results if s.collection == collection]
        if start_date:
            sd = datetime.fromisoformat(start_date)
            results = [s for s in results if s.date >= sd]
        if end_date:
            ed = datetime.fromisoformat(end_date)
            results = [s for s in results if s.date <= ed]
        if max_cloud is not None:
            results = [s for s in results if s.cloud_pct <= max_cloud]

        return sorted(results, key=lambda s: s.date, reverse=True)

    def to_dict(self, scene_id: str) -> dict | None:
        scene = self._scenes.get(scene_id)
        return asdict(scene) if scene else None

    def summary(self) -> dict:
        return {
            'total_scenes': len(self._scenes),
            'collections': list(set(s.collection for s in self._scenes.values())),
            'date_range': {
                'earliest': min((s.date for s in self._scenes.values()), default=None),
                'latest': max((s.date for s in self._scenes.values()), default=None),
            },
        }
