"""Módulo de análisis de visión por computador e índices espectrales para Skyfussion Analytics.

Calcula índices espectrales NDWI y NDVI, y la variación porcentual del ancho del cauce
del río utilizando NumPy y OpenCV (headless) mediante morfología matemática y skeletonization.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

try:
    import cv2 as cv
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False


@dataclass
class VisionMetrics:
    ndwi_mean: float
    ndvi_mean: float
    channel_width_change_pct: float
    initial_mean_width_px: float
    final_mean_width_px: float
    water_coverage_initial_pct: float
    water_coverage_final_pct: float
    details: Dict[str, Any]


def calculate_ndwi(green_band: np.ndarray, nir_band: np.ndarray) -> np.ndarray:
    """Calcula el Normalized Difference Water Index (NDWI).

    NDWI = (Green - NIR) / (Green + NIR + 1e-10)
    Rango resultante: [-1.0, 1.0]
    """
    green = green_band.astype(np.float64)
    nir = nir_band.astype(np.float64)
    denom = green + nir + 1e-10
    ndwi = (green - nir) / denom
    return np.clip(ndwi, -1.0, 1.0)


def calculate_ndvi(red_band: np.ndarray, nir_band: np.ndarray) -> np.ndarray:
    """Calcula el Normalized Difference Vegetation Index (NDVI).

    NDVI = (NIR - Red) / (NIR + Red + 1e-10)
    Rango resultante: [-1.0, 1.0]
    """
    red = red_band.astype(np.float64)
    nir = nir_band.astype(np.float64)
    denom = nir + red + 1e-10
    ndvi = (nir - red) / denom
    return np.clip(ndvi, -1.0, 1.0)


def segment_water_mask(ndwi_image: np.ndarray, threshold: float = 0.0, kernel_size: int = 5) -> np.ndarray:
    """Genera máscara binaria de agua aplicando umbralización y operaciones morfológicas."""
    binary_mask = (ndwi_image > threshold).astype(np.uint8)
    if HAS_OPENCV:
        kernel = cv.getStructuringElement(cv.MORPH_ELLIPSE, (kernel_size, kernel_size))
        opened = cv.morphologyEx(binary_mask, cv.MORPH_OPEN, kernel, iterations=1)
        closed = cv.morphologyEx(opened, cv.MORPH_CLOSE, kernel, iterations=1)
        return closed
    return binary_mask


def extract_centerline_skeleton(binary_mask: np.ndarray) -> np.ndarray:
    """Extrae la línea central del cauce mediante skeletonization iterativa."""
    if not HAS_OPENCV:
        # Fallback NumPy: extraer punto medio de cada fila donde hay agua
        skeleton = np.zeros_like(binary_mask)
        for r in range(binary_mask.shape[0]):
            cols = np.where(binary_mask[r] > 0)[0]
            if len(cols) > 0:
                mid_c = cols[len(cols) // 2]
                skeleton[r, mid_c] = 1
        return skeleton

    skeleton = np.zeros_like(binary_mask)
    element = cv.getStructuringElement(cv.MORPH_CROSS, (3, 3))
    temp = binary_mask.copy()

    while cv.countNonZero(temp) > 0:
        eroded = cv.erode(temp, element)
        opened = cv.dilate(eroded, element)
        skeleton_bit = cv.subtract(temp, opened)
        skeleton = cv.bitwise_or(skeleton, skeleton_bit)
        temp = eroded.copy()

    return skeleton


def compute_channel_widths(binary_mask: np.ndarray, centerline: np.ndarray) -> List[float]:
    """Calcula el perfil de anchos transversales a lo largo de la línea central."""
    h, w = binary_mask.shape
    center_points = np.argwhere(centerline > 0)
    if len(center_points) == 0:
        return [0.0]

    widths: List[float] = []
    # Muestreo a lo largo del eje del río
    for row, col in center_points:
        row_slice = binary_mask[row, :]
        left_idx = col
        while left_idx >= 0 and row_slice[left_idx] > 0:
            left_idx -= 1
        right_idx = col
        while right_idx < w and row_slice[right_idx] > 0:
            right_idx += 1
        width_px = max(1.0, float(right_idx - left_idx - 1))
        widths.append(width_px)

    return widths if widths else [1.0]


def synthesize_basin_bands(
    year: int,
    height: int = 120,
    width: int = 120,
    river_intensity: float = 1.0
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Sintetiza bandas espectrales representativas del Río Combeima (Green, Red, NIR).

    Modela la morfología meándrica del río y variaciones antropogénicas e históricas (1969-2023).
    """
    rng = np.random.default_rng(seed=1969 + year)
    y, x = np.ogrid[:height, :width]

    # Trayectoria sinusoidal del cauce del río Combeima
    center_curve = width / 2.0 + (width / 5.0) * np.sin(2.0 * np.pi * y / (height * 0.8))
    
    # Ancho del río modulado históricamente: mayor en 1969, reducción por presión antrópica hacia 2023
    trend_decay = 1.0 - 0.12 * ((year - 1969) / 54.0)  # ~12% reducción tendencia base
    base_channel_width = 8.0 * river_intensity * trend_decay
    dist_to_river = np.abs(x - center_curve)

    is_river = dist_to_river < (base_channel_width / 2.0)
    is_bank = (dist_to_river >= (base_channel_width / 2.0)) & (dist_to_river < (base_channel_width * 1.5))

    # Banda Verde (B3): Alta en agua
    green = np.where(is_river, rng.uniform(0.45, 0.65, (height, width)), rng.uniform(0.10, 0.25, (height, width)))

    # Banda Roja (B4): Baja en agua, alta en vegetación/suelo
    red = np.where(is_river, rng.uniform(0.05, 0.15, (height, width)), rng.uniform(0.12, 0.35, (height, width)))

    # Banda NIR (B8): Muy baja en agua (absorción), muy alta en vegetación
    nir = np.where(is_river, rng.uniform(0.02, 0.08, (height, width)), rng.uniform(0.45, 0.80, (height, width)))

    # Ruido atmosférico suave
    green += rng.normal(0, 0.02, (height, width))
    red += rng.normal(0, 0.02, (height, width))
    nir += rng.normal(0, 0.02, (height, width))

    return np.clip(green, 0.0, 1.0), np.clip(red, 0.0, 1.0), np.clip(nir, 0.0, 1.0)


def analyze_multitemporal_vision(
    years: List[int] = [1969, 2023],
    river_intensity: float = 1.0
) -> VisionMetrics:
    """Ejecuta el análisis multitemporal completo entre el año inicial y final.

    Calcula NDWI, NDVI, máscaras de agua morfológicas y variación porcentual del cauce.
    """
    year_start = min(years)
    year_end = max(years)

    # 1. Época Inicial (year_start)
    g1, r1, n1 = synthesize_basin_bands(year_start, river_intensity=river_intensity)
    ndwi1 = calculate_ndwi(g1, n1)
    ndvi1 = calculate_ndvi(r1, n1)
    mask1 = segment_water_mask(ndwi1)
    skel1 = extract_centerline_skeleton(mask1)
    widths1 = compute_channel_widths(mask1, skel1)
    mean_w1 = float(np.mean(widths1))
    water_cov1 = float((np.sum(mask1 > 0) / mask1.size) * 100.0)

    # 2. Época Final (year_end)
    g2, r2, n2 = synthesize_basin_bands(year_end, river_intensity=river_intensity)
    ndwi2 = calculate_ndwi(g2, n2)
    ndvi2 = calculate_ndvi(r2, n2)
    mask2 = segment_water_mask(ndwi2)
    skel2 = extract_centerline_skeleton(mask2)
    widths2 = compute_channel_widths(mask2, skel2)
    mean_w2 = float(np.mean(widths2))
    water_cov2 = float((np.sum(mask2 > 0) / mask2.size) * 100.0)

    # Variación porcentual del ancho del cauce: ((w2 - w1) / w1) * 100
    if mean_w1 > 0:
        width_change_pct = ((mean_w2 - mean_w1) / mean_w1) * 100.0
    else:
        width_change_pct = 0.0

    # Promedios espaciales consolidados para el reporte
    ndwi_mean = float(np.mean(ndwi2))
    ndvi_mean = float(np.mean(ndvi2))

    return VisionMetrics(
        ndwi_mean=round(ndwi_mean, 4),
        ndvi_mean=round(ndvi_mean, 4),
        channel_width_change_pct=round(width_change_pct, 2),
        initial_mean_width_px=round(mean_w1, 2),
        final_mean_width_px=round(mean_w2, 2),
        water_coverage_initial_pct=round(water_cov1, 2),
        water_coverage_final_pct=round(water_cov2, 2),
        details={
            "initial_year": year_start,
            "final_year": year_end,
            "erosion_deposition_ratio": round(water_cov2 / max(water_cov1, 0.001), 3),
        }
    )
