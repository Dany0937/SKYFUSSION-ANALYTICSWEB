import numpy as np
from agents.python.base import BaseAgent, Event, get_logger

logger = get_logger('vision_agent')


class VisionAgent(BaseAgent):
    def __init__(self, config: dict):
        super().__init__('VisionAgent', config)
        self._input_event = 'data:ingested'
        self._indices_to_calculate = config.get('indices', ['NDVI', 'NDWI', 'EVI'])
        self._ndvi_threshold = config.get('ndvi_threshold', 0.3)
        self._ndwi_threshold = config.get('ndwi_threshold', 0.0)
        self._water_segmentator = None
        self._vegetation_segmentator = None

    async def initialize(self) -> 'VisionAgent':
        await super().initialize()
        from .processors.segmentation import WaterBodySegmentator, VegetationSegmentator
        self._water_segmentator = WaterBodySegmentator({
            'ndwi_threshold': self._ndwi_threshold,
        })
        self._vegetation_segmentator = VegetationSegmentator({
            'ndvi_threshold': self._ndvi_threshold,
        })
        logger.info(f'VisionAgent ready (indices: {self._indices_to_calculate})')
        return self

    async def handle_event(self, event: Event):
        scenes = event.payload.get('scenes', [])
        request_id = event.payload.get('request_id', '')

        logger.info(f'Processing {len(scenes)} scenes for request {request_id}')
        results = []

        for scene in scenes:
            result = await self._process_scene(scene)
            results.append(result)

        await self.emit('analysis:completed', {
            'request_id': request_id,
            'results': results,
            'count': len(results),
        })

    async def _process_scene(self, scene: dict) -> dict:
        from .processors.indices import calculate_indices, SpectralIndices

        bands = self._load_bands(scene)
        indices = calculate_indices(bands, self._indices_to_calculate)

        analysis = {
            'scene_id': scene.get('scene_id', ''),
            'collection': scene.get('collection', ''),
            'date': scene.get('date', ''),
            'indices': {},
        }

        if 'ndvi' in indices:
            ndvi = indices['ndvi']
            analysis['indices']['NDVI'] = {
                'mean': float(np.mean(ndvi)),
                'std': float(np.std(ndvi)),
                'min': float(np.min(ndvi)),
                'max': float(np.max(ndvi)),
                'classification': SpectralIndices.interpret_ndvi(float(np.mean(ndvi))),
            }
            seg_result = self._vegetation_segmentator.segment(bands.get('nir'), bands.get('red'))
            analysis['vegetation_segmentation'] = seg_result['statistics']

        if 'ndwi' in indices:
            ndwi = indices['ndwi']
            analysis['indices']['NDWI'] = {
                'mean': float(np.mean(ndwi)),
                'std': float(np.std(ndwi)),
                'min': float(np.min(ndwi)),
                'max': float(np.max(ndwi)),
                'classification': SpectralIndices.interpret_ndwi(float(np.mean(ndwi))),
            }
            if 'green' in bands and 'nir' in bands:
                water_result = self._water_segmentator.segment(bands['green'], bands['nir'])
                analysis['water_segmentation'] = water_result['statistics']

        if 'evi' in indices:
            evi = indices['evi']
            analysis['indices']['EVI'] = {
                'mean': float(np.mean(evi)),
                'std': float(np.std(evi)),
            }

        return analysis

    def _load_bands(self, scene: dict) -> dict[str, np.ndarray]:
        from .processors.raster_io import read_multiband

        blob_url = scene.get('blob_url', '')
        if blob_url and blob_url.startswith('file://'):
            path = blob_url[7:]
            return read_multiband(path)

        mock_shape = (256, 256)
        return {
            'nir': np.random.rand(*mock_shape).astype(np.float32),
            'red': np.random.rand(*mock_shape).astype(np.float32),
            'green': np.random.rand(*mock_shape).astype(np.float32),
            'blue': np.random.rand(*mock_shape).astype(np.float32),
            'swir1': np.random.rand(*mock_shape).astype(np.float32),
        }
