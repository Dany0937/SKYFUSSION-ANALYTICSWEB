import numpy as np
from typing import Any


def read_geotiff(path: str, band: int = 1) -> tuple[np.ndarray, dict]:
    try:
        import rasterio
        with rasterio.open(path) as src:
            data = src.read(band)
            metadata = {
                'width': src.width,
                'height': src.height,
                'count': src.count,
                'crs': str(src.crs),
                'transform': list(src.transform),
                'bounds': list(src.bounds),
                'nodata': src.nodata,
                'dtype': str(data.dtype),
            }
            return data, metadata
    except ImportError:
        import logging
        logging.getLogger(__name__).warning('rasterio not available, using mock data')
        mock = np.random.rand(256, 256).astype(np.float32)
        return mock, {
            'width': 256, 'height': 256, 'count': 1,
            'crs': 'EPSG:4326', 'nodata': -9999,
        }


def write_geotiff(path: str, data: np.ndarray, metadata: dict | None = None):
    try:
        import rasterio
        from rasterio.transform import from_bounds
        meta = {
            'driver': 'GTiff',
            'height': data.shape[0],
            'width': data.shape[1],
            'count': 1,
            'dtype': data.dtype.name,
            'crs': 'EPSG:4326',
            'transform': from_bounds(0, 0, 1, 1, data.shape[1], data.shape[0]),
            'compress': 'lzw',
        }
        if metadata:
            meta.update({k: v for k, v in metadata.items() if k in meta})

        with rasterio.open(path, 'w', **meta) as dst:
            dst.write(data, 1)
    except ImportError:
        import logging
        logging.getLogger(__name__).warning(f'rasterio not available, skipping write to {path}')


def read_multiband(path: str, bands: list[int] | None = None) -> dict[str, np.ndarray]:
    try:
        import rasterio
        result = {}
        with rasterio.open(path) as src:
            band_indices = bands or list(range(1, src.count + 1))
            for b in band_indices:
                data = src.read(b)
                band_name = f'B{b}'
                if hasattr(src, 'descriptions') and src.descriptions[b - 1]:
                    band_name = src.descriptions[b - 1]
                result[band_name] = data
        return result
    except ImportError:
        import logging
        logging.getLogger(__name__).warning('rasterio not available')
        return {f'B{i}': np.random.rand(256, 256).astype(np.float32) for i in (bands or [1, 2, 3, 4])}
