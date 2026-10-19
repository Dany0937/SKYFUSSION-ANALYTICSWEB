# Batch Processing Script for Spectral Indices

"""
Módulo de procesamiento por lotes para índices espectrales.
Diseñado para procesamiento paralelo de múltiples zonas geográficas
en el contexto de minería de datos ambientales.

Utiliza el patrón de procesamiento paralelo para escalar el análisis
de datos satelitales en clusters Docker/Kubernetes.
"""

import numpy as np
from typing import List, Dict, Tuple
from .ndvi import SpectralIndices


class BatchProcessor:
    """
    Procesa múltiples geometrias/zonas en paralelo.
    Ideal para minería de datos históricos y series temporales.
    """

    def __init__(self, indices_class=SpectralIndices, max_concurrent: int = 10):
        self.indices_class = indices_class
        self.max_concurrent = max_concurrent
        self.indices_calculator = indices_class()

    def process_batch_ndvi(
        self,
        nir_bands: List[np.ndarray],
        red_bands: List[np.ndarray],
        geometries: List[str] = None
    ) -> Dict[str, np.ndarray]:
        """
        Calcula NDVI para múltiples bandas en lote.

        Args:
            nir_bands: Lista de arrays de banda NIR
            red_bands: Lista de arrays de banda Red
            geometries: Lista opcional de nombres de geometrías

        Returns:
            Diccionario con resultados NDVI por índice
        """
        results = {
            'ndvi_arrays': [],
            'mean_values': [],
            'std_values': []
        }

        for i, (nir, red) in enumerate(zip(nir_bands, red_bands)):
            ndvi = self.indices_calculator.calculate_ndvi(nir, red)

            # Estadísticas del lote
            valid_mask = ndvi > -1
            mean_ndvi = np.mean(ndvi[valid_mask]) if np.any(valid_mask) else 0
            std_ndvi = np.std(ndvi[valid_mask]) if np.any(valid_mask) else 0

            results['ndvi_arrays'].append(ndvi)
            results['mean_values'].append(mean_ndvi)
            results['std_values'].append(std_ndvi)

        return results

    def process_batch_ndwi(
        self,
        green_bands: List[np.ndarray],
        nir_bands: List[np.ndarray]
    ) -> Dict[str, np.ndarray]:
        """
        Calcula NDWI para múltiples bandas en lote.

        Args:
            green_bands: Lista de arrays de banda Green
            nir_bands: Lista de arrays de banda NIR

        Returns:
            Diccionario con resultados NDWI por índice
        """
        results = {
            'ndwi_arrays': [],
            'mean_values': [],
            'water_percentage': []
        }

        for green, nir in zip(green_bands, nir_bands):
            ndwi = self.indices_calculator.calculate_ndwi(green, nir)

            # Estadísticas del lote
            valid_mask = ndwi > -1
            mean_ndwi = np.mean(ndwi[valid_mask]) if np.any(valid_mask) else 0
            water_px = np.sum(valid_mask)
            total_px = ndwi.size
            water_pct = (water_px / total_px * 100) if total_px > 0 else 0

            results['ndwi_arrays'].append(ndwi)
            results['mean_values'].append(mean_ndwi)
            results['water_percentage'].append(water_pct)

        return results

    def generate_summary_report(self, batch_results: Dict) -> str:
        """
        Genera un reporte resumido de los resultados del lote.
        Útil para dashboards y monitoreo.

        Args:
            batch_results: Resultados de process_batch_ndvi o process_batch_ndwi

        Returns:
            Reporte formateado como string
        """
        lines = [
            "=" * 60,
            "📊 REPORTE DE PROCESAMIENTO EN LOTE",
            "=" * 60
        ]

        if 'mean_values' in batch_results and batch_results['mean_values']:
            lines.append(f"\nEstadísticas NDVI:")
            for i, (mean, std) in enumerate(zip(batch_results['mean_values'],
                                                  batch_results['std_values'])):
                lines.append(f"  Zona {i+1}: Mean={mean:.4f}, Std={std:.4f}")

        if 'water_percentage' in batch_results and batch_results['water_percentage']:
            lines.append(f"\nEstadísticas NDWI:")
            for i, pct in enumerate(batch_results['water_percentage']):
                lines.append(f"  Zona {i+1}: Agua={pct:.2f}%")

        lines.extend([
            "\n" + "=" * 60,
            "Fin del reporte de lote",
            "=" * 60
        ])

        return "\n".join(lines)


def main():
    """Función de ejemplo de uso."""
    processor = BatchProcessor(max_concurrent=5)

    # Simular datos de ejemplo (bandas sintéticas para 3 zonas)
    nir_samples = [np.random.rand(100, 100) for _ in range(3)]
    red_samples = [np.random.rand(100, 100) for _ in range(3)]
    green_samples = [np.random.rand(100, 100) for _ in range(3)]

    # Procesar NDVI en lote
    ndvi_results = processor.process_batch_ndvi(nir_samples, red_samples)
    print(processor.generate_summary_report({
        'mean_values': ndvi_results['mean_values'],
        'std_values': ndvi_results['std_values']
    }))

    # Procesar NDWI en lote
    ndwi_results = processor.process_batch_ndwi(green_samples, nir_samples)
    print(processor.generate_summary_report({
        'water_percentage': ndwi_results['water_percentage']
    }))


if __name__ == "__main__":
    main()