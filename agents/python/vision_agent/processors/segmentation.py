import numpy as np
import cv2
from .morphology import opening, closing, filter_by_area


class WaterBodySegmentator:
    def __init__(self, config: dict | None = None):
        self.config = config or {
            'ndwi_threshold': 0.0,
            'kernel_size': 5,
            'min_area_px': 100,
        }

    def segment(self, green_band: np.ndarray, nir_band: np.ndarray) -> dict:
        from .indices import SpectralIndices
        ndwi = SpectralIndices.ndwi(green_band, nir_band)
        mask = (ndwi > self.config['ndwi_threshold']).astype(np.uint8)
        mask = opening(mask, self.config['kernel_size'])
        mask = closing(mask, self.config['kernel_size'])
        mask = filter_by_area(mask, self.config['min_area_px'])

        water_pixels = np.sum(mask == 1)
        total_pixels = mask.size

        return {
            'mask': mask,
            'ndwi': ndwi,
            'statistics': {
                'water_pixels': int(water_pixels),
                'water_percentage': float(water_pixels / total_pixels * 100),
                'mean_ndwi': float(np.mean(ndwi[mask > 0])) if water_pixels > 0 else 0,
            },
        }


class VegetationSegmentator:
    def __init__(self, config: dict | None = None):
        self.config = config or {
            'ndvi_threshold': 0.3,
            'kernel_size': 3,
            'min_area_px': 50,
        }

    def segment(self, nir_band: np.ndarray, red_band: np.ndarray) -> dict:
        from .indices import SpectralIndices
        ndvi = SpectralIndices.ndvi(nir_band, red_band)
        mask = (ndvi > self.config['ndvi_threshold']).astype(np.uint8)
        mask = opening(mask, self.config['kernel_size'])
        mask = closing(mask, self.config['kernel_size'])

        veg_pixels = np.sum(mask == 1)
        total_pixels = mask.size

        return {
            'mask': mask,
            'ndvi': ndvi,
            'statistics': {
                'vegetation_pixels': int(veg_pixels),
                'vegetation_percentage': float(veg_pixels / total_pixels * 100),
                'mean_ndvi': float(np.mean(ndvi[mask > 0])) if veg_pixels > 0 else 0,
                'ndvi_classification': self._classify_ndvi_zones(ndvi),
            },
        }

    def _classify_ndvi_zones(self, ndvi: np.ndarray) -> dict:
        categories = {
            'suelo_desnudo': float(np.sum((ndvi >= -1) & (ndvi < 0.1))),
            'vegetacion_escasa': float(np.sum((ndvi >= 0.1) & (ndvi < 0.3))),
            'vegetacion_moderada': float(np.sum((ndvi >= 0.3) & (ndvi < 0.6))),
            'vegetacion_densa': float(np.sum(ndvi >= 0.6)),
        }
        total = sum(categories.values())
        if total > 0:
            for k in categories:
                categories[k] = round(categories[k] / total * 100, 2)
        return categories
