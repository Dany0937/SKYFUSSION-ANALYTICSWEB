"""
River Morphology Analysis Module for Skyfusion Analytics
======================================================
Análisis de Variabilidad y Alteraciones Morfológicas del Río Combeima (1969-2023)

Este módulo proporciona herramientas para:
- Detección de cauces fluviales mediante umbralización y detección de bordes
- Cálculo de índices espectrales (NDWI)
- Comparación morfológica entre épocas históricas
"""

import numpy as np
import cv2 as cv
from dataclasses import dataclass
from typing import Optional, Tuple, List, Dict, Any


@dataclass
class MorphologicalAnalysisResult:
    """Resultado del análisis morfológico del río."""
    ndwi_image: np.ndarray
    binary_mask: np.ndarray
    river_centerline: np.ndarray
    width_profile: np.ndarray
    mean_width_pixels: float
    std_width_pixels: float
    min_width_pixels: float
    max_width_pixels: float
    water_pixels: int
    total_pixels: int
    water_coverage_percent: float


@dataclass
class MorphologicalComparison:
    """Comparación morfológica entre dos épocas."""
    epoch_1_result: MorphologicalAnalysisResult
    epoch_2_result: MorphologicalAnalysisResult
    width_difference_map: np.ndarray
    mean_width_change_pixels: float
    width_increase_percent: float
    width_decrease_percent: float
    water_coverage_change_percent: float
    erosion_area_pixels: int
    deposition_area_pixels: int


class RiverMorphologyAnalyzer:
    """
    Analizador de morfología fluvial para imágenes satelitales multitemporales.
    
    Utiliza técnicas de procesamiento de imágenes para detectar cauces fluviales,
    calcular índices espectrales y analizar cambios morfológicos entre épocas.
    
    Attributes:
        ndwi_threshold: Umbral para binarizar la imagen NDWI (default: 0.0)
        canny_low: Umbral bajo para el detector Canny (default: 50)
        canny_high: Umbral alto para el detector Canny (default: 150)
        morphology_kernel: Tamaño del kernel para operaciones morfológicas
    """

    def __init__(
        self,
        ndwi_threshold: float = 0.0,
        canny_low: int = 50,
        canny_high: int = 150,
        morphology_kernel: int = 5
    ) -> None:
        """
        Inicializa el analizador de morfología fluvial.
        
        Args:
            ndwi_threshold: Umbral NDWI para detección de agua [0.0 a 1.0]
            canny_low: Umbral bajo de Canny
            canny_high: Umbral alto de Canny
            morphology_kernel: Tamaño del kernel morfológico (debe ser impar > 0)
        """
        if not 0.0 <= ndwi_threshold <= 1.0:
            raise ValueError("ndwi_threshold debe estar entre 0.0 y 1.0")
        if canny_low < 0 or canny_high < 0:
            raise ValueError("Los umbrales de Canny no pueden ser negativos")
        if canny_low >= canny_high:
            raise ValueError("canny_low debe ser menor que canny_high")
        if morphology_kernel % 2 == 0:
            raise ValueError("morphology_kernel debe ser un número impar")
            
        self.ndwi_threshold = ndwi_threshold
        self.canny_low = canny_low
        self.canny_high = canny_high
        self.morphology_kernel = morphology_kernel

    def calculate_ndwi(
        self,
        green_band: np.ndarray,
        nir_band: np.ndarray
    ) -> np.ndarray:
        """
        Calcula el Índice de Diferencia Normalizada de Agua (NDWI).
        
        NDWI = (Green - NIR) / (Green + NIR)
        
        El NDWI es efectivo para realzar cuerpos de agua abiertos:
        - Valores > 0 typically indican agua
        - Valores <= 0 typically indican no-agua (vegetación, suelo, etc.)
        
        Args:
            green_band: Banda verde del espectro electromagnético (shape: HxW)
            nir_band: Banda infrarroja cercana del espectro (shape: HxW)
            
        Returns:
            Array 2D con valores NDWI normalizados en [-1, 1]
            
        Raises:
            ValueError: Si las bandas no tienen las mismas dimensiones
            TypeError: Si las bandas no son arrays de NumPy
        """
        if not isinstance(green_band, np.ndarray) or not isinstance(nir_band, np.ndarray):
            raise TypeError("Las bandas deben ser arrays de NumPy")
            
        if green_band.shape != nir_band.shape:
            raise ValueError(
                f"Las bandas deben tener la misma forma. "
                f"Green: {green_band.shape}, NIR: {nir_band.shape}"
            )
        
        try:
            green = green_band.astype(np.float64)
            nir = nir_band.astype(np.float64)
            
            denominator = green + nir
            
            safe_denominator = np.where(
                np.abs(denominator) < 1e-10,
                1e-10,
                denominator
            )
            
            ndwi = (green - nir) / safe_denominator
            
            return np.clip(ndwi, -1.0, 1.0)
            
        except Exception as e:
            raise RuntimeError(f"Error calculando NDWI: {str(e)}")

    def segment_water(
        self,
        ndwi_image: np.ndarray
    ) -> np.ndarray:
        """
        Segmenta cuerpos de agua aplicando umbralización al NDWI.
        
        Args:
            ndwi_image: Imagen NDWI normalizada en [-1, 1]
            
        Returns:
            Máscara binaria donde 1 = agua, 0 = no-agua
        """
        if not isinstance(ndwi_image, np.ndarray):
            raise TypeError("ndwi_image debe ser un array de NumPy")
            
        binary_mask = (ndwi_image > self.ndwi_threshold).astype(np.uint8)
        
        kernel = np.ones(
            (self.morphology_kernel, self.morphology_kernel),
            np.uint8
        )
        
        binary_mask = cv.morphologyEx(
            binary_mask,
            cv.MORPH_OPEN,
            kernel,
            iterations=1
        )
        
        binary_mask = cv.morphologyEx(
            binary_mask,
            cv.MORPH_CLOSE,
            kernel,
            iterations=1
        )
        
        return binary_mask

    def detect_river_edges(
        self,
        ndwi_image: np.ndarray
    ) -> np.ndarray:
        """
        Detecta bordes del río usando el algoritmo Canny.
        
        Args:
            ndwi_image: Imagen NDWI normalizada
            
        Returns:
            Imagen binaria con bordes detectados
        """
        try:
            blurred = cv.GaussianBlur(
                ndwi_image.astype(np.float32),
                (5, 5),
                0
            )
            
            edges = cv.Canny(
                (blurred * 255).astype(np.uint8),
                self.canny_low,
                self.canny_high
            )
            
            return edges
            
        except Exception as e:
            raise RuntimeError(f"Error en detección de bordes Canny: {str(e)}")

    def extract_centerline(
        self,
        binary_mask: np.ndarray
    ) -> np.ndarray:
        """
        Extrae la línea central del río mediante skeletonization.
        
        Args:
            binary_mask: Máscara binaria del cauce
            
        Returns:
            Línea central del río como array binario
        """
        try:
            skeleton = np.zeros_like(binary_mask)
            
            element = cv.getStructuringElement(
                cv.MORPH_CROSS,
                (3, 3)
            )
            
            temp = binary_mask.copy()
            while cv.countNonZero(temp) > 0:
                eroded = cv.erode(temp, element)
                opened = cv.dilate(eroded, element)
                skeleton_bit = cv.subtract(temp, opened)
                skeleton = cv.bitwise_or(skeleton, skeleton_bit)
                temp = eroded.copy()
            
            return skeleton
            
        except Exception as e:
            raise RuntimeError(f"Error extrayendo línea central: {str(e)}")

    def calculate_width_profile(
        self,
        binary_mask: np.ndarray,
        centerline: np.ndarray
    ) -> np.ndarray:
        """
        Calcula el perfil de ancho del río a lo largo de su longitud.
        
        Args:
            binary_mask: Máscara binaria del agua
            centerline: Línea central del río
            
        Returns:
            Array 1D con anchos en píxeles para cada punto de la línea central
        """
        try:
            height, width = binary_mask.shape
            width_profile: List[float] = []
            
            center_points = np.argwhere(centerline > 0)
            
            if len(center_points) == 0:
                return np.array([])
            
            sorted_indices = np.lexsort((center_points[:, 1], center_points[:, 0]))
            sorted_points = center_points[sorted_indices]
            
            for point in sorted_points:
                row, col = point
                
                row_profile = binary_mask[row, :]
                col_profile = binary_mask[:, col]
                
                left_edge = col
                for c in range(col, -1, -1):
                    if row_profile[c] == 0:
                        left_edge = c
                        break
                        
                right_edge = col
                for c in range(col, width):
                    if row_profile[c] == 0:
                        right_edge = c
                        break
                
                row_width = max(right_edge - left_edge, 1)
                width_profile.append(row_width)
            
            return np.array(width_profile)
            
        except Exception as e:
            raise RuntimeError(f"Error calculando perfil de anchos: {str(e)}")

    def analyze_epoch(
        self,
        green_band: np.ndarray,
        nir_band: np.ndarray,
        metadata: Optional[Dict[str, Any]] = None
    ) -> MorphologicalAnalysisResult:
        """
        Realiza el análisis morfológico completo de una época.
        
        Args:
            green_band: Banda verde
            nir_band: Banda NIR
            metadata: Metadatos opcionales (año, satélite, etc.)
            
        Returns:
            Resultado del análisis morfológico
        """
        try:
            ndwi_image = self.calculate_ndwi(green_band, nir_band)
            binary_mask = self.segment_water(ndwi_image)
            centerline = self.extract_centerline(binary_mask)
            width_profile = self.calculate_width_profile(binary_mask, centerline)
            
            water_pixels = np.sum(binary_mask > 0)
            total_pixels = binary_mask.size
            water_coverage = (water_pixels / total_pixels) * 100
            
            return MorphologicalAnalysisResult(
                ndwi_image=ndwi_image,
                binary_mask=binary_mask,
                river_centerline=centerline,
                width_profile=width_profile,
                mean_width_pixels=float(np.mean(width_profile)) if len(width_profile) > 0 else 0.0,
                std_width_pixels=float(np.std(width_profile)) if len(width_profile) > 0 else 0.0,
                min_width_pixels=float(np.min(width_profile)) if len(width_profile) > 0 else 0.0,
                max_width_pixels=float(np.max(width_profile)) if len(width_profile) > 0 else 0.0,
                water_pixels=water_pixels,
                total_pixels=total_pixels,
                water_coverage_percent=water_coverage
            )
            
        except Exception as e:
            raise RuntimeError(f"Error en análisis de época: {str(e)}")

    def compare_epochs(
        self,
        epoch_1_result: MorphologicalAnalysisResult,
        epoch_2_result: MorphologicalAnalysisResult
    ) -> MorphologicalComparison:
        """
        Compara los resultados de dos épocas para detectar cambios morfológicos.
        
        Args:
            epoch_1_result: Resultado de la época más antigua
            epoch_2_result: Resultado de la época más reciente
            
        Returns:
            Comparación morfológica detallada
        """
        try:
            height, width = epoch_1_result.binary_mask.shape
            
            aligned_mask1 = epoch_1_result.binary_mask
            aligned_mask2 = epoch_2_result.binary_mask
            
            if epoch_2_result.binary_mask.shape != aligned_mask1.shape:
                aligned_mask2 = cv.resize(
                    epoch_2_result.binary_mask,
                    (width, height),
                    interpolation=cv.INTER_NEAREST
                )
            
            erosion = (aligned_mask1 > 0) & (aligned_mask2 == 0)
            deposition = (aligned_mask1 == 0) & (aligned_mask2 > 0)
            
            width_change = epoch_2_result.width_profile - epoch_1_result.width_profile
            
            mean_width_change = float(np.mean(width_change)) if len(width_change) > 0 else 0.0
            
            width_increase = width_change[width_change > 0]
            width_decrease = width_change[width_change < 0]
            
            increase_percent = float(
                (len(width_increase) / len(width_change) * 100)
                if len(width_change) > 0 else 0.0
            )
            
            decrease_percent = float(
                (len(width_decrease) / len(width_change) * 100)
                if len(width_change) > 0 else 0.0
            )
            
            coverage_change = (
                epoch_2_result.water_coverage_percent -
                epoch_1_result.water_coverage_percent
            )
            
            return MorphologicalComparison(
                epoch_1_result=epoch_1_result,
                epoch_2_result=epoch_2_result,
                width_difference_map=width_change,
                mean_width_change_pixels=mean_width_change,
                width_increase_percent=increase_percent,
                width_decrease_percent=decrease_percent,
                water_coverage_change_percent=coverage_change,
                erosion_area_pixels=int(np.sum(erosion)),
                deposition_area_pixels=int(np.sum(deposition))
            )
            
        except Exception as e:
            raise RuntimeError(f"Error comparando épocas: {str(e)}")

    def generate_report(
        self,
        comparison: MorphologicalComparison,
        epoch_1_label: str = "Época 1",
        epoch_2_label: str = "Época 2"
    ) -> Dict[str, Any]:
        """
        Genera un reporte de análisis comparativo.
        
        Args:
            comparison: Resultado de la comparación
            epoch_1_label: Etiqueta para época 1
            epoch_2_label: Etiqueta para época 2
            
        Returns:
            Diccionario con el reporte completo
        """
        r1 = comparison.epoch_1_result
        r2 = comparison.epoch_2_result
        
        return {
            "analisis_morfologico": {
                epoch_1_label: {
                    "ancho_medio_px": round(r1.mean_width_pixels, 2),
                    "ancho_std_px": round(r1.std_width_pixels, 2),
                    "ancho_min_px": round(r1.min_width_pixels, 2),
                    "ancho_max_px": round(r1.max_width_pixels, 2),
                    "cobertura_agua_porcentaje": round(r1.water_coverage_percent, 4),
                    "pixeles_agua": r1.water_pixels
                },
                epoch_2_label: {
                    "ancho_medio_px": round(r2.mean_width_pixels, 2),
                    "ancho_std_px": round(r2.std_width_pixels, 2),
                    "ancho_min_px": round(r2.min_width_pixels, 2),
                    "ancho_max_px": round(r2.max_width_pixels, 2),
                    "cobertura_agua_porcentaje": round(r2.water_coverage_percent, 4),
                    "pixeles_agua": r2.water_pixels
                }
            },
            "cambios_detectados": {
                "cambio_medio_ancho_px": round(comparison.mean_width_change_pixels, 2),
                "porcentaje_incremento_ancho": round(comparison.width_increase_percent, 2),
                "porcentaje_disminucion_ancho": round(comparison.width_decrease_percent, 2),
                "cambio_cobertura_agua_porcentaje": round(
                    comparison.water_coverage_change_percent, 4
                ),
                "area_erosion_pixeles": comparison.erosion_area_pixels,
                "area_deposicion_pixeles": comparison.deposition_area_pixels
            },
            "interpretacion": self._interpret_results(comparison)
        }

    def _interpret_results(
        self,
        comparison: MorphologicalComparison
    ) -> str:
        """Genera interpretación de los resultados."""
        interpretations: List[str] = []
        
        if comparison.water_coverage_change_percent < -5:
            interpretations.append(
                "ALERTA: Reducción significativa en la cobertura de agua, "
                "posiblemente relacionada con procesos de sequía o intervención antrópica."
            )
        elif comparison.water_coverage_change_percent > 5:
            interpretations.append(
                "Cambio positivo en cobertura hídrica. Posible recuperación "
                "o condiciones de mayor precipitación."
            )
        else:
            interpretations.append(
                "Estabilidad en la cobertura de agua dentro de rangos esperados."
            )
        
        if comparison.erosion_area_pixels > comparison.deposition_area_pixels * 1.5:
            interpretations.append(
                "Tendencia a la INCICIÓN (erosión) domina el sistema fluvial. "
                "El río está ganando capacidad erosiva."
            )
        elif comparison.deposition_area_pixels > comparison.erosion_area_pixels * 1.5:
            interpretations.append(
                "Tendencia a la SEDIMENTACIÓN domina el sistema fluvial. "
                "Posible reducción de pendiente o carga sedimentaria."
            )
        
        return " ".join(interpretations)


def load_satellite_bands(
    green_path: str,
    nir_path: str
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Carga bandas satelitales desde archivos TIF.
    
    Args:
        green_path: Ruta al archivo TIF de banda verde
        nir_path: Ruta al archivo TIF de banda NIR
        
    Returns:
        Tupla de arrays NumPy (green_band, nir_band)
    """
    try:
        import rasterio
        from rasterio.warp import reproject, Resampling
        
        with rasterio.open(green_path) as src:
            green_band = src.read(1)
            
        with rasterio.open(nir_path) as src:
            nir_band = src.read(1)
            
        return green_band, nir_band
        
    except ImportError:
        print("Advertencia: rasterio no está instalado. Usando cv2.imread代替.")
        green_band = cv.imread(green_path, cv.IMREAD_GRAYSCALE)
        nir_band = cv.imread(nir_path, cv.IMREAD_GRAYSCALE)
        
        if green_band is None or nir_band is None:
            raise FileNotFoundError("No se pudieron leer los archivos de imagen")
            
        return green_band, nir_band


if __name__ == "__main__":
    print("=" * 60)
    print("Skyfusion Analytics - River Morphology Analyzer")
    print("Módulo de Variabilidad y Alteraciones Morfológicas")
    print("Río Combeima, Ibagué, Colombia (1969-2023)")
    print("=" * 60)
    
    print("\n[INFO] Módulo cargado correctamente.")
    print("[INFO] Use: from river_morphology import RiverMorphologyAnalyzer")
