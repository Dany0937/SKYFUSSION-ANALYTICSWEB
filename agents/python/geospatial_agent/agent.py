import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from agents.python.base import BaseAgent, Event, get_logger

logger = get_logger('geospatial_agent')


class GeospatialAgent(BaseAgent):
    def __init__(self, config: dict):
        super().__init__('GeospatialAgent', config)
        self._input_event = 'analysis:requested'
        self._executor = ThreadPoolExecutor(max_workers=config.get('download_workers', 4))
        self._gee_client = None
        self._blob_client = None
        self._collections = config.get('collections', [
            {'id': 'S2', 'name': 'COPERNICUS/S2_HARMONIZED', 'bands': ['B2', 'B3', 'B4', 'B8', 'B11', 'B12', 'QA60'], 'scale': 10},
            {'id': 'L8', 'name': 'LANDSAT/LC08/C02/T1_L2', 'bands': ['SR_B2', 'SR_B3', 'SR_B4', 'SR_B5', 'SR_B6', 'SR_B7', 'QA_PIXEL'], 'scale': 30},
        })
        self._cloud_filter = config.get('cloud_filter', 20)
        self._max_scenes = config.get('max_scenes_per_request', 50)
        self._blob_container = config.get('blob_container', 'satellite-imagery')

    async def initialize(self) -> 'GeospatialAgent':
        await super().initialize()
        self._gee_client = await self._init_gee()
        self._blob_client = await self._init_blob_storage()
        logger.info('GeospatialAgent ready with GEE + Blob Storage')
        return self

    async def _init_gee(self):
        try:
            import ee
            ee.Initialize(
                project=self.config.get('gee_project', 'skyfusion-analytics'),
                credentials=ee.ServiceAccountCredentials(
                    self.config.get('gee_service_account', ''),
                    self.config.get('gee_key_path', ''),
                )
            )
            logger.info('GEE initialized')
            return ee
        except Exception as e:
            logger.warning(f'GEE init failed (dev mode): {e}')
            return None

    async def _init_blob_storage(self):
        try:
            from google.cloud import storage
            client = storage.Client.from_service_account_json(
                self.config.get('gee_key_path', '')
            )
            logger.info('Blob Storage initialized')
            return client
        except Exception as e:
            logger.warning(f'Blob Storage init failed (dev mode): {e}')
            return None

    async def handle_event(self, event: Event):
        payload = event.payload
        geometry = payload.get('geometry')
        start_date = payload.get('start_date')
        end_date = payload.get('end_date')
        collections = payload.get('collections', [c['id'] for c in self._collections])
        request_id = payload.get('request_id', '')

        if not all([geometry, start_date, end_date]):
            raise ValueError('Missing required fields: geometry, start_date, end_date')

        scenes = await self._query_and_download(
            geometry=geometry,
            start_date=start_date,
            end_date=end_date,
            collections=collections,
            request_id=request_id,
        )

        await self.emit('data:ingested', {
            'request_id': request_id,
            'scenes': scenes,
            'count': len(scenes),
            'collections': collections,
        })
        logger.info(f'Ingested {len(scenes)} scenes for request {request_id}')

    async def _query_and_download(
        self, geometry: dict, start_date: str, end_date: str,
        collections: list[str], request_id: str,
    ) -> list[dict]:
        if not self._gee_client:
            return self._mock_scenes(geometry, start_date, end_date, collections, request_id)

        loop = asyncio.get_event_loop()
        all_scenes = []

        for col_id in collections:
            col_config = next((c for c in self._collections if c['id'] == col_id), None)
            if not col_config:
                continue

            scenes = await loop.run_in_executor(
                self._executor,
                self._query_collection,
                col_config, geometry, start_date, end_date,
            )
            all_scenes.extend(scenes)

        return all_scenes[:self._max_scenes]

    def _query_collection(
        self, col_config: dict, geometry: dict,
        start_date: str, end_date: str,
    ) -> list[dict]:
        ee = self._gee_client
        aoi = ee.Geometry.Polygon(geometry.get('coordinates', [[]]))

        collection = (
            ee.ImageCollection(col_config['name'])
            .filterDate(start_date, end_date)
            .filterBounds(aoi)
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', self._cloud_filter))
        )

        size = collection.size().getInfo()
        images = collection.toList(size).getInfo()

        scenes = []
        for img in images:
            props = img.get('properties', {})
            scene = {
                'scene_id': img.get('id', ''),
                'collection': col_config['id'],
                'date': props.get('system:time_start', ''),
                'cloud_pct': props.get('CLOUDY_PIXEL_PERCENTAGE', 0),
                'bounds': img.get('geometry', {}),
                'bands': col_config['bands'],
                'scale': col_config['scale'],
                'blob_url': self._upload_to_blob(img),
            }
            scenes.append(scene)

        return scenes

    def _mock_scenes(
        self, geometry: dict, start_date: str, end_date: str,
        collections: list[str], request_id: str,
    ) -> list[dict]:
        from datetime import datetime, timedelta
        import random

        scenes = []
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
        delta = (end - start).days

        for i, col_id in enumerate(collections[:3]):
            num_scenes = max(1, delta // (5 if col_id == 'S2' else 16))
            for j in range(min(num_scenes, 5)):
                scene_date = start + timedelta(days=j * (delta // max(num_scenes, 1)))
                scenes.append({
                    'scene_id': f'{col_id}_{request_id}_{i}_{j}',
                    'collection': col_id,
                    'date': scene_date.isoformat(),
                    'cloud_pct': round(random.uniform(0, 30), 1),
                    'bounds': geometry,
                    'bands': ['B4', 'B3', 'B2', 'B8'],
                    'scale': 10 if col_id == 'S2' else 30,
                    'blob_url': f'https://storage.example.com/{self._blob_container}/{col_id}/{scene_date.strftime("%Y/%m/%d")}/scene_{j}.tif',
                })

        return scenes

    def _upload_to_blob(self, image) -> str:
        return f'https://storage.example.com/{self._blob_container}/mock_{image.get("id", "unknown")}.tif'

    async def shutdown(self):
        self._executor.shutdown(wait=True)
        await super().shutdown()
