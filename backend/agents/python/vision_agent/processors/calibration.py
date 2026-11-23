import numpy as np
import cv2


def calibrate_radiometric(image: np.ndarray, gain: float, offset: float) -> np.ndarray:
    return image.astype(np.float32) * gain + offset


def dark_object_subtraction(band: np.ndarray, dark_pixel_pct: float = 0.01) -> np.ndarray:
    band = band.astype(np.float32)
    hist, _ = np.histogram(band, bins=256, range=(0, np.max(band)))
    cumulative = np.cumsum(hist) / np.sum(hist)
    dark_value = np.searchsorted(cumulative, dark_pixel_pct) / 255.0
    corrected = band - dark_value * np.max(band)
    return np.clip(corrected, 0, np.max(band))


def land_toa_correction(band: np.ndarray, sun_elevation: float, esun: float, d: float) -> np.ndarray:
    band = band.astype(np.float32)
    cos_zenith = np.sin(np.radians(sun_elevation))
    return (band * np.pi * d ** 2) / (esun * cos_zenith + 1e-10)
