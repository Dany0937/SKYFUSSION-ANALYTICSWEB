import numpy as np
from typing import Any


class SpectralIndices:
    @staticmethod
    def ndvi(nir: np.ndarray, red: np.ndarray, scale: bool = False) -> np.ndarray:
        nir = nir.astype(np.float32)
        red = red.astype(np.float32)
        denominator = nir + red + 1e-10
        ndvi = (nir - red) / denominator
        ndvi = np.clip(ndvi, -1, 1)
        if scale:
            return ((ndvi + 1) * 127.5).astype(np.uint8)
        return ndvi

    @staticmethod
    def ndwi(green: np.ndarray, nir: np.ndarray, scale: bool = False) -> np.ndarray:
        green = green.astype(np.float32)
        nir = nir.astype(np.float32)
        denominator = green + nir + 1e-10
        ndwi = (green - nir) / denominator
        ndwi = np.clip(ndwi, -1, 1)
        if scale:
            return ((ndwi + 1) * 127.5).astype(np.uint8)
        return ndwi

    @staticmethod
    def evi(
        nir: np.ndarray, red: np.ndarray, blue: np.ndarray,
        g: float = 2.5, c1: float = 6.0, c2: float = 7.5, l: float = 1.0,
    ) -> np.ndarray:
        nir = nir.astype(np.float32)
        red = red.astype(np.float32)
        blue = blue.astype(np.float32)
        denominator = nir + c1 * red - c2 * blue + l + 1e-10
        evi = g * (nir - red) / denominator
        return np.clip(evi, -1, 1)

    @staticmethod
    def ndbi(swir1: np.ndarray, nir: np.ndarray) -> np.ndarray:
        swir1 = swir1.astype(np.float32)
        nir = nir.astype(np.float32)
        denominator = swir1 + nir + 1e-10
        ndbi = (swir1 - nir) / denominator
        return np.clip(ndbi, -1, 1)

    @staticmethod
    def mndwi(green: np.ndarray, swir1: np.ndarray) -> np.ndarray:
        green = green.astype(np.float32)
        swir1 = swir1.astype(np.float32)
        denominator = green + swir1 + 1e-10
        mndwi = (green - swir1) / denominator
        return np.clip(mndwi, -1, 1)

    @staticmethod
    def interpret_ndvi(value: float) -> dict:
        if value < 0.1:
            return {'category': 'suelo_desnudo', 'color': '#8B4513', 'vegetation': 'Ninguna'}
        elif value < 0.3:
            return {'category': 'vegetacion_escasa', 'color': '#CD853F', 'vegetation': 'Baja'}
        elif value < 0.6:
            return {'category': 'vegetacion_moderada', 'color': '#228B22', 'vegetation': 'Moderada'}
        else:
            return {'category': 'vegetacion_densa', 'color': '#006400', 'vegetation': 'Alta'}

    @staticmethod
    def interpret_ndwi(value: float) -> dict:
        if value < -0.3:
            return {'category': 'suelo_seco', 'color': '#8B4513', 'water': 'Ninguna'}
        elif value < 0.0:
            return {'category': 'humedad_baja', 'color': '#CD853F', 'water': 'Baja'}
        elif value < 0.3:
            return {'category': 'humedad_moderada', 'color': '#4169E1', 'water': 'Moderada'}
        else:
            return {'category': 'cuerpo_agua', 'color': '#0000FF', 'water': 'Alta'}


def calculate_indices(bands: dict[str, np.ndarray], indices: list[str]) -> dict[str, np.ndarray]:
    results = {}
    for index in indices:
        match index.upper():
            case 'NDVI':
                if 'nir' in bands and 'red' in bands:
                    results['ndvi'] = SpectralIndices.ndvi(bands['nir'], bands['red'])
            case 'NDWI':
                if 'green' in bands and 'nir' in bands:
                    results['ndwi'] = SpectralIndices.ndwi(bands['green'], bands['nir'])
            case 'EVI':
                if all(b in bands for b in ['nir', 'red', 'blue']):
                    results['evi'] = SpectralIndices.evi(bands['nir'], bands['red'], bands['blue'])
            case 'NDBI':
                if 'swir1' in bands and 'nir' in bands:
                    results['ndbi'] = SpectralIndices.ndbi(bands['swir1'], bands['nir'])
            case 'MNDWI':
                if 'green' in bands and 'swir1' in bands:
                    results['mndwi'] = SpectralIndices.mndwi(bands['green'], bands['swir1'])
    return results
