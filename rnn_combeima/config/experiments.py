"""
Configuración de Experimentos RNA — Río Combeima, Tolima
==========================================================

Define la matriz completa de experimentos para la red neuronal
recurrente (RNA) que predice NDVI/EVI a partir de series
multitemporales multisensor del área del río Combeima.

Permite ejecutar:
- Grid de configuraciones por arquitectura (GRU/LSTM/Bi-GRU/Attention/TCN)
- Comparación por horizonte de predicción (1, 4, 8 pasos)
- Comparación por zona (cuenca Combeima — por ahora 1 zona)
- Validación espacio-temporal (evita data leakage)

Estructura de un experimento:
    {
        "id":            "compileable y único",
        "arquitectura":  uno de AMBIENTES_RNN,
        "config":        {hiperparámetros de capa},
        "horizonte":     pasos hacia adelante a predecir,
        "zona":          nombre de la zona/cuenca,
        "seed":          semilla determinista,
    }
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any
from copy import deepcopy
import hashlib
import json

# --------------------------------------------------------------------------- #
# Catálogo de arquitecturas RNN disponibles
# --------------------------------------------------------------------------- #

ARQUITECTURAS_RNN = {
    "gru": {
        "descripcion": "Gated Recurrent Unit. Eficiente y robusto para series NDVI.",
        "capas_recurrentes": 2,
    },
    "lstm": {
        "descripcion": "Long Short-Term Memory. Contexto largo (importa en 10 años).",
        "capas_recurrentes": 2,
    },
    "bigru": {
        "descripcion": "GRU Bidireccional. Captura contexto antes/después del paso.",
        "capas_recurrentes": 2,
    },
    "gru_attention": {
        "descripcion": "GRU + mecanismo de atención sobre los timesteps.",
        "capas_recurrentes": 2,
    },
    "tcn": {
        "descripcion": "Temporal Convolutional Network (convoluciones dilatas).",
        "capas_recurrentes": 0,
    },
}

# --------------------------------------------------------------------------- #
# Zonas / cuencas de estudio.
# El usuario confirmó "Solo río Combeima". Se deja extensible por si después
# se agregan cuencas vecinas (Cucuana, Anaime, etc.).
# --------------------------------------------------------------------------- #

ZONAS = {
    "combeima": {
        "nombre": "Cuenca del río Combeima (Ibagué, Tolima)",
        "bbox": [-75.6560, 4.3950, -75.2130, 4.6500],  # [lon_min, lat_min, lon_max, lat_max]
        "buffer_km": 2.0,
        "descripcion": (
            "Cuenca entre el páramo y el río Combeima hasta la confluencia "
            "con la quebrada del municipio de Ibagué. Región andina."
        ),
    },
}

# --------------------------------------------------------------------------- #
# Sensores multisensor y sus bandas / índices
# --------------------------------------------------------------------------- #

SENSORES = {
    "modis": {
        "coleccion": "MODIS/061/MOD13A2",
        "escala": 1000,
        "frecuencia_dias": 16,
        "indices": ["NDVI", "EVI"],
        # QA real de MOD13A2: SummaryQA (0=good,1=marginal,2=snow,3=cloudy)
        # NO existe banda 'QA_PIXEL' en este producto.
        "qa": "SummaryQA",
        "factor_escala": 0.0001,      # NDVI/EVI vienen como int16 (-2000..10000)
        "factor_offset": 0.0,
        "bandas": ["NDVI", "EVI", "SummaryQA"],
        "desde": "2015-01-01",
        "hasta": "2024-12-31",
    },
    "sentinel2": {
        "coleccion": "COPERNICUS/S2_SR_HARMONIZED",
        "escala": 10,
        "frecuencia_dias": 5,
        "indices": ["NDVI", "NDWI"],
        # QA de Sentinel-2 L2A: banda SCL (1-11, 0=sin datos) y QA60 (nubes)
        "qa": "SCL",
        "factor_escala": 0.0001,      # SR uint16 * 0.0001
        "factor_offset": 0.0,
        "bandas": ["B3", "B4", "B8", "B8A", "SCL"],
        # La colección S2_SR no tiene cobertura global hasta 2017 (confirmado en catálogo)
        "desde": "2017-01-01",
        "hasta": "2024-12-31",
    },
    "landsat": {
        "coleccion": "LANDSAT/LC08/C02/T1_L2",
        "escala": 30,
        "frecuencia_dias": 16,
        "indices": ["NDVI"],
        "qa": "QA_PIXEL",
        "factor_escala": 0.0000275,   # SR de Landsat C2 L2 = DN*0.0000275 - 0.2
        "factor_offset": -0.2,
        "bandas": ["SR_B4", "SR_B5", "QA_PIXEL"],
        "desde": "2015-01-01",
        "hasta": "2024-12-31",
    },
}

# --------------------------------------------------------------------------- #
# Proyecto Google Cloud / Earth Engine.
# Las cuentas de GEE creadas tras abril 2023 REQUIEREN un proyecto Cloud con
# la Earth Engine API habilitada. Completa aqui con tu PROJECT_ID de GCP.
# --------------------------------------------------------------------------- #

GEE_CONFIG = {
    "proyecto_id": "",          # ej: "slyfusion-analytics" o "ee-nombre-usuario"
    "rastrear_tareas": True,    # monitorear export tasks en segundo plano
}

# --------------------------------------------------------------------------- #
# Grid de hiperparámetros por arquitectura (se itera cartesianamente)
# --------------------------------------------------------------------------- #

GRID_CONFIGS = {
    # unidades_recurrentes por capa, dropout, lr, batch_size
    "grid_pequeno": [
        {"unidades": [32, 64], "dropout": 0.3, "lr": 1e-3, "batch_size": 32},
        {"unidades": [64, 32], "dropout": 0.3, "lr": 1e-3, "batch_size": 32},
    ],
    "grid_medio": [
        {"unidades": [64, 64], "dropout": 0.3, "lr": 1e-3, "batch_size": 32},
        {"unidades": [128, 64], "dropout": 0.3, "lr": 1e-3, "batch_size": 32},
        {"unidades": [128, 64], "dropout": 0.2, "lr": 5e-4, "batch_size": 64},
        {"unidades": [128, 64], "dropout": 0.4, "lr": 1e-3, "batch_size": 32},
    ],
    "grid_amplio": [
        {"unidades": [32, 32], "dropout": 0.3, "lr": 1e-3, "batch_size": 32},
        {"unidades": [64, 64], "dropout": 0.3, "lr": 1e-3, "batch_size": 32},
        {"unidades": [128, 64], "dropout": 0.3, "lr": 1e-3, "batch_size": 32},
        {"unidades": [128, 64], "dropout": 0.2, "lr": 5e-4, "batch_size": 64},
        {"unidades": [128, 128], "dropout": 0.3, "lr": 1e-3, "batch_size": 32},
        {"unidades": [256, 128], "dropout": 0.3, "lr": 1e-3, "batch_size": 32},
        {"unidades": [128, 64, 32], "dropout": 0.3, "lr": 1e-3, "batch_size": 32},
        {"unidades": [64], "dropout": 0.2, "lr": 1e-3, "batch_size": 64},
    ],
}

# --------------------------------------------------------------------------- #
# Horizontes de predicción (en pasos de 16 días MODIS)
# --------------------------------------------------------------------------- #

HORIZONTES_PASOS = {
    1: {"descripcion": "1 paso (~16 días) — pronóstico inmediato"},
    4: {"descripcion": "4 pasos (~2.5 meses) — pronóstico estacional corto"},
    8: {"descripcion": "8 pasos (~5 meses) — pronóstico estacional largo"},
}

# --------------------------------------------------------------------------- #
# Lotes de experimentos predefinidos
# --------------------------------------------------------------------------- #

LOTES = {
    "smoke": {
        "descripcion": "Prueba rápida (2 configs × 1 arquitectura × 1 horizonte)",
        "arquitecturas": ["gru"],
        "grid": "grid_pequeno",
        "horizontes": [1],
        "zonas": ["combeima"],
        "epochs": 5,
    },
    "basico": {
        "descripcion": "Comparación de arquitecturas (1 config c/u) × horizonte 1",
        "arquitecturas": list(ARQUITECTURAS_RNN.keys()),
        "grid": "grid_pequeno",
        "horizontes": [1],
        "zonas": ["combeima"],
        "epochs": 15,
    },
    "completo": {
        "descripcion": "Matriz completa: 3 arquitecturas × grid medio × 3 horizontes",
        "arquitecturas": ["gru", "lstm", "gru_attention"],
        "grid": "grid_medio",
        "horizontes": [1, 4, 8],
        "zonas": ["combeima"],
        "epochs": 30,
    },
    "todos": {
        "descripcion": "Todos los experimentos: todas las arquitecturas × grid amplio × horizontes",
        "arquitecturas": list(ARQUITECTURAS_RNN.keys()),
        "grid": "grid_amplio",
        "horizontes": [1, 4, 8],
        "zonas": ["combeima"],
        "epochs": 25,
    },
}


# --------------------------------------------------------------------------- #
# Dataclasses y expansión de experimentos
# --------------------------------------------------------------------------- #

@dataclass
class Experimento:
    id: str
    arquitectura: str
    config: Dict[str, Any]
    horizonte: int
    zona: str
    seed: int
    epochs: int
    treinar_per_zona: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def generar_id(arquitectura: str, config: Dict[str, Any], horizonte: int,
               zona: str, seed: int) -> str:
    """Genera un ID determinista y único para el experimento."""
    sobrenombre = f"{arquitectura}_h{horizonte}"
    clave = json.dumps({
        "arquitectura": arquitectura,
        "config": config,
        "horizonte": horizonte,
        "zona": zona,
        "seed": seed,
    }, sort_keys=True)
    digest = hashlib.sha1(clave.encode("utf-8")).hexdigest()[:8]
    return f"{sobrenombre}_{digest}"


def expandir_lote(nombre_lote: str, epochs_override: int = None,
                  semilla: int = 42) -> List[Experimento]:
    """
    Expande un lote predefinido en la lista concreta de experimentos,
    iterando cartesianamente sobre arquitecturas × grid × horizontes × zonas.
    """
    if nombre_lote not in LOTES:
        raise ValueError(f"Lote '{nombre_lote}' no existe. Opciones: {list(LOTES.keys())}")

    lote = LOTES[nombre_lote]
    grid = GRID_CONFIGS[lote["grid"]]
    epochs = epochs_override or lote["epochs"]

    experimentos: List[Experimento] = []

    for arquitectura in lote["arquitecturas"]:
        if arquitectura not in ARQUITECTURAS_RNN:
            raise ValueError(f"Arquitectura '{arquitectura}' desconocida.")

        # Para TCN, transformar la grid (usa kernel/filters en vez de unidades)
        if arquitectura == "tcn":
            grid_arq = [transformar_grid_a_tcn(c) for c in grid]
        else:
            grid_arq = grid

        for config in grid_arq:
            for horizonte in lote["horizontes"]:
                if horizonte not in HORIZONTES_PASOS:
                    raise ValueError(f"Horizonte {horizonte} fuera de rango.")
                for zona in lote["zonas"]:
                    if zona not in ZONAS:
                        raise ValueError(f"Zona '{zona}' desconocida.")
                    exp_id = generar_id(arquitectura, config, horizonte, zona, semilla)
                    experimentos.append(
                        Experimento(
                            id=exp_id,
                            arquitectura=arquitectura,
                            config=config,
                            horizonte=horizonte,
                            zona=zona,
                            seed=semilla,
                            epochs=epochs,
                        )
                    )
    return experimentos


def transformar_grid_a_tcn(config: Dict[str, Any]) -> Dict[str, Any]:
    """Convierte una config de capa recurrente a params equivalentes de TCN."""
    unidades = config["unidades"]
    if isinstance(unidades, (list, tuple)):
        unidades = unidades[0]
    # kernel 3 ≈ contexto de 3 timesteps por capa
    return {
        "filters": int(unidades * 1.5),
        "kernel_size": 3,
        "dilations": [1, 2, 4, 8],
        "dropout": config["dropout"],
        "lr": config["lr"],
        "batch_size": config["batch_size"],
    }


if __name__ == "__main__":
    import sys
    lote = sys.argv[1] if len(sys.argv) > 1 else "smoke"
    exps = expandir_lote(lote)
    print(f"Lote '{lote}' → {len(exps)} experimentos")
    for e in exps:
        print(f"  - {e.id} | {e.arquitectura:15s} | h={e.horizonte} | cfg={e.config}")
