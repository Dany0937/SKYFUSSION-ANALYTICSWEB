"""
Ejemplo de uso del módulo River Morphology Analyzer
===============================================

Este script demuestra cómo usar el módulo de análisis morfológico
para comparar imágenes satelitales del río Combeima entre dos épocas.

Uso:
    python example_usage.py
"""

import numpy as np
import cv2 as cv
from river_morphology import (
    RiverMorphologyAnalyzer,
    load_satellite_bands,
    MorphologicalAnalysisResult,
    MorphologicalComparison
)


def simulate_satellite_bands(
    height: int = 500,
    width: int = 1000,
    river_width: int = 50,
    seed: int = 42
) -> tuple:
    """
    Simula bandas satelitales para pruebas.
    
    En producción, usar load_satellite_bands() con archivos TIF reales.
    """
    np.random.seed(seed)
    
    green_base = np.random.randint(20, 80, (height, width), dtype=np.uint8)
    nir_base = np.random.randint(40, 120, (height, width), dtype=np.uint8)
    
    river_mask = np.zeros((height, width), dtype=np.uint8)
    center_y = height // 2
    for i in range(height):
        row_variation = int(10 * np.sin(i * 0.02))
        river_mask[i, :] = 0
        river_mask[
            i,
            max(0, width//2 - river_width//2 + row_variation):
            min(width, width//2 + river_width//2 + row_variation)
        ] = 1
    
    green_simulated = np.where(
        river_mask == 1,
        np.clip(green_base + 60, 0, 255).astype(np.uint8),
        green_base
    )
    
    nir_simulated = np.where(
        river_mask == 1,
        np.clip(nir_base - 30, 0, 255).astype(np.uint8),
        nir_base
    )
    
    return green_simulated, nir_simulated


def visualize_results(
    epoch_1: MorphologicalAnalysisResult,
    epoch_2: MorphologicalAnalysisResult,
    comparison: MorphologicalComparison
) -> None:
    """Visualiza los resultados del análisis."""
    
    print("\n" + "=" * 60)
    print("RESULTADOS DEL ANÁLISIS MORFOLÓGICO")
    print("=" * 60)
    
    print(f"\n📊 ÉPOCA 1 (1969):")
    print(f"   Ancho medio: {epoch_1.mean_width_pixels:.2f} px")
    print(f"   Cobertura agua: {epoch_1.water_coverage_percent:.4f}%")
    print(f"   Píxeles agua: {epoch_1.water_pixels:,}")
    
    print(f"\n📊 ÉPOCA 2 (2023):")
    print(f"   Ancho medio: {epoch_2.mean_width_pixels:.2f} px")
    print(f"   Cobertura agua: {epoch_2.water_coverage_percent:.4f}%")
    print(f"   Píxeles agua: {epoch_2.water_pixels:,}")
    
    print(f"\n📈 CAMBIOS DETECTADOS:")
    print(f"   Cambio medio ancho: {comparison.mean_width_change_pixels:.2f} px")
    print(f"   Incremento ancho: {comparison.width_increase_percent:.2f}%")
    print(f"   Disminución ancho: {comparison.width_decrease_percent:.2f}%")
    print(f"   Cambio cobertura: {comparison.water_coverage_change_percent:.4f}%")
    print(f"   Área erosión: {comparison.erosion_area_pixels:,} px")
    print(f"   Área sedimentación: {comparison.deposition_area_pixels:,} px")


def main() -> None:
    """Función principal de demostración."""
    
    print("\n🔄 Generando datos simulados para demostración...")
    
    green_1969, nir_1969 = simulate_satellite_bands(
        height=500,
        width=1000,
        river_width=45,
        seed=1969
    )
    
    green_2023, nir_2023 = simulate_satellite_bands(
        height=500,
        width=1000,
        river_width=38,
        seed=2023
    )
    
    print("✅ Datos simulados generados")
    print(f"   Dimensiones: {green_1969.shape[0]}x{green_1969.shape[1]} píxeles")
    
    analyzer = RiverMorphologyAnalyzer(
        ndwi_threshold=0.1,
        canny_low=50,
        canny_high=150,
        morphology_kernel=5
    )
    
    print("\n🔍 Analizando época 1969...")
    try:
        epoch_1_result = analyzer.analyze_epoch(green_1969, nir_1969)
        print("   ✓ Análisis completado")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return
    
    print("🔍 Analizando época 2023...")
    try:
        epoch_2_result = analyzer.analyze_epoch(green_2023, nir_2023)
        print("   ✓ Análisis completado")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return
    
    print("\n⚖️  Comparando épocas...")
    try:
        comparison = analyzer.compare_epochs(epoch_1_result, epoch_2_result)
        print("   ✓ Comparación completada")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return
    
    visualize_results(epoch_1_result, epoch_2_result, comparison)
    
    report = analyzer.generate_report(
        comparison,
        epoch_1_label="1969",
        epoch_2_label="2023"
    )
    
    print("\n📝 REPORTE INTERPRETADO:")
    print("-" * 60)
    print(report["interpretacion"])
    print("-" * 60)
    
    print("\n✨ Análisis completado exitosamente!")


if __name__ == "__main__":
    main()
