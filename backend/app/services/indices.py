"""Índices espectrales y morfología fluvial.

Las fórmulas replican `skills/vision_tools/river_morphology.py` y
`agents/python/vision_agent/processors/indices.py` para evitar divergencias.
"""

from __future__ import annotations

from typing import Iterable

import numpy as np

EPS = 1e-10


def ndvi(nir: np.ndarray, red: np.ndarray) -> np.ndarray:
    nir_f = np.asarray(nir, dtype=np.float32)
    red_f = np.asarray(red, dtype=np.float32)
    return np.clip((nir_f - red_f) / (nir_f + red_f + EPS), -1.0, 1.0)


def ndwi(green: np.ndarray, nir: np.ndarray) -> np.ndarray:
    green_f = np.asarray(green, dtype=np.float32)
    nir_f = np.asarray(nir, dtype=np.float32)
    return np.clip((green_f - nir_f) / (green_f + nir_f + EPS), -1.0, 1.0)


def summarize(values: Iterable[float]) -> dict[str, float]:
    array = np.asarray(list(values), dtype=np.float32)
    if array.size == 0:
        raise ValueError("La banda no contiene valores")
    return {
        "mean": float(np.mean(array)),
        "min": float(np.min(array)),
        "max": float(np.max(array)),
        "std": float(np.std(array)),
    }
