import {
  CombeimaSeriesPoint,
  HistoricalAlertEntry,
  PipelineStageState,
  WatershedPreset,
} from "../types/hydrology";

const COMBEIMA_SAT_IMG =
  "/src/assets/images/combeima_river_satellite_1795411238077.jpg";
const ALLUVIAL_SAT_IMG =
  "/src/assets/images/alluvial_basin_satellite_1795411236249.jpg";

export const INITIAL_PIPELINE_STAGES: PipelineStageState[] = [
  {
    id: "AREA_DEFINED",
    label: "AREA_DEFINED",
    status: "completed",
    detail: "Polígono WGS84 validado",
  },
  {
    id: "DATA_INGESTED",
    label: "DATA_INGESTED",
    status: "completed",
    detail: "Serie Combeima 1969–2023",
  },
  {
    id: "ANALYSIS_COMPLETE",
    label: "ANALYSIS_COMPLETE",
    status: "completed",
    detail: "NDWI · NDVI · OpenCV",
  },
  {
    id: "PREDICTION_COMPLETE",
    label: "PREDICTION_COMPLETE",
    status: "completed",
    detail: "RNN gru_attention_h1",
  },
  {
    id: "REPORT_READY",
    label: "REPORT_READY",
    status: "completed",
    detail: "Dictamen JSON listo",
  },
];

// Historical trajectory 1969-2023 + 2024 forecast grounded in PROJECT_SPEC.md
export const COMBEIMA_HISTORICAL_SERIES: CombeimaSeriesPoint[] = [
  { year: "1969", ndwi: 0.06, ndvi: 0.72, channelWidthM: 32.4, dischargeM3s: 34.2 },
  { year: "1976", ndwi: 0.08, ndvi: 0.69, channelWidthM: 33.8, dischargeM3s: 36.1 },
  { year: "1983", ndwi: 0.11, ndvi: 0.65, channelWidthM: 35.1, dischargeM3s: 38.4 },
  { year: "1990", ndwi: 0.09, ndvi: 0.63, channelWidthM: 36.2, dischargeM3s: 37.0 },
  { year: "1997", ndwi: 0.15, ndvi: 0.59, channelWidthM: 38.7, dischargeM3s: 42.5 },
  { year: "2004", ndwi: 0.13, ndvi: 0.57, channelWidthM: 39.4, dischargeM3s: 40.8 },
  { year: "2011", ndwi: 0.24, ndvi: 0.53, channelWidthM: 44.6, dischargeM3s: 58.3 },
  { year: "2016", ndwi: 0.10, ndvi: 0.56, channelWidthM: 37.9, dischargeM3s: 35.6 },
  { year: "2020", ndwi: 0.19, ndvi: 0.54, channelWidthM: 41.8, dischargeM3s: 49.1 },
  { year: "2023", ndwi: 0.28, ndvi: 0.52, channelWidthM: 46.2, dischargeM3s: 68.5 },
  {
    year: "2024 (Pr.)",
    ndwi: 0.26,
    ndvi: 0.53,
    channelWidthM: 45.4,
    dischargeM3s: 64.2,
    isForecast: true,
  },
];

export const WATERSHED_PRESETS: WatershedPreset[] = [
  {
    basinId: "combeima-ibague",
    basinName: "Cuenca del Río Combeima",
    municipality: "Alcaldía de Ibagué · CORTOLIMA",
    coordinates: "04°28'51\"N 75°11'58\"O",
    region: "Tolima · Cordillera Central",
    areaKm2: 124.5,
    elevationRangeM: "800 – 4,200 m",
    stationCode: "EST-POBLADO-01",
    summary:
      "Aporta ~80% del agua potable de Ibagué. Alta pendiente andina sensible a avenidas torrenciales y pérdida de cobertura.",
    ndwi: 0.28,
    ndvi: 0.52,
    channelWidthChangePct: 19.4,
    predictedDischargeM3s: 68.5,
    baselineDischargeM3s: 39.8,
    geometryVariant: "combeima",
    satelliteImage: COMBEIMA_SAT_IMG,
    latBounds: [4.433, 4.529],
    lonBounds: [-75.257, -75.142],
    defaultPolygon: [
      [
        [-75.257, 4.433],
        [-75.142, 4.433],
        [-75.142, 4.529],
        [-75.257, 4.529],
        [-75.257, 4.433],
      ],
    ],
  },
  {
    basinId: "magdalena-medio",
    basinName: "Cuenca Río Magdalena Medio",
    municipality: "Alcaldía de Barrancabermeja · CORANTIOQUIA",
    coordinates: "07°03'55\"N 73°51'14\"O",
    region: "Valle del Magdalena",
    areaKm2: 1420,
    elevationRangeM: "75 – 640 m",
    stationCode: "HID-MAG-042",
    summary:
      "Llanura aluvial con meandros amplios, alta sensibilidad a crecientes súbitas y desbordamientos laterales.",
    ndwi: 0.46,
    ndvi: 0.34,
    channelWidthChangePct: 38.5,
    predictedDischargeM3s: 2480,
    baselineDischargeM3s: 1320,
    geometryVariant: "alluvial",
    satelliteImage: ALLUVIAL_SAT_IMG,
    latBounds: [6.98, 7.14],
    lonBounds: [-73.94, -73.76],
    defaultPolygon: [
      [
        [-73.92, 7.01],
        [-73.79, 7.01],
        [-73.79, 7.12],
        [-73.92, 7.12],
        [-73.92, 7.01],
      ],
    ],
  },
  {
    basinId: "sinu-alto",
    basinName: "Cuenca Río Sinú — Sector Tierralta",
    municipality: "Alcaldía de Tierralta · CVS Córdoba",
    coordinates: "08°10'18\"N 76°03'42\"O",
    region: "Caribe Húmedo",
    areaKm2: 980,
    elevationRangeM: "48 – 890 m",
    stationCode: "HID-SIN-019",
    summary:
      "Tramo regulado con incremento progresivo de humedad edáfica y saturación de riberas.",
    ndwi: 0.24,
    ndvi: 0.56,
    channelWidthChangePct: 14.2,
    predictedDischargeM3s: 790,
    baselineDischargeM3s: 520,
    geometryVariant: "alluvial",
    satelliteImage: ALLUVIAL_SAT_IMG,
    latBounds: [8.11, 8.24],
    lonBounds: [-76.12, -75.98],
    defaultPolygon: [
      [
        [-76.11, 8.12],
        [-75.99, 8.12],
        [-75.99, 8.23],
        [-76.11, 8.23],
        [-76.11, 8.12],
      ],
    ],
  },
  {
    basinId: "cauca-alto",
    basinName: "Cuenca Alta del Río Cauca",
    municipality: "Alcaldía de Popayán · CRC Cauca",
    coordinates: "02°26'41\"N 76°36'23\"O",
    region: "Macizo Andino",
    areaKm2: 765,
    elevationRangeM: "1,680 – 3,120 m",
    stationCode: "HID-CAU-108",
    summary:
      "Cuenca de montaña con cobertura riparia densa y comportamiento hidráulico estable.",
    ndwi: 0.04,
    ndvi: 0.74,
    channelWidthChangePct: 3.4,
    predictedDischargeM3s: 215,
    baselineDischargeM3s: 198,
    geometryVariant: "canyon",
    satelliteImage: COMBEIMA_SAT_IMG,
    latBounds: [2.39, 2.51],
    lonBounds: [-76.68, -76.54],
    defaultPolygon: [
      [
        [-76.66, 2.40],
        [-76.56, 2.40],
        [-76.56, 2.49],
        [-76.66, 2.49],
        [-76.66, 2.40],
      ],
    ],
  },
];

export const INITIAL_HISTORICAL_ALERTS: HistoricalAlertEntry[] = [
  {
    id: "hist-20261122-combeima",
    timestamp: "2026-11-22T18:40:00-05:00",
    metrics: {
      basinId: "combeima-ibague",
      basinName: "Cuenca del Río Combeima",
      municipality: "Alcaldía de Ibagué · CORTOLIMA",
      coordinates: "04°28'51\"N 75°11'58\"O",
      ndwi: 0.28,
      ndvi: 0.52,
      channelWidthChangePct: 19.4,
      predictedDischargeM3s: 68.5,
    },
    report: {
      alert_level: "PREVENTIVA",
      headline:
        "Ensanchamiento del cauce en Combeima exige vigilancia sobre bocatoma Ibagué",
      narrative:
        "Las escenas Sentinel-2 sobre la cuenca del río Combeima registran un NDWI de 0.28 y un ensanchamiento activo del cauce del 19.4%, con caudal proyectado de 68.5 m³/s en la estación Poblado. Aunque la cobertura vegetal media (NDVI 0.52) conserva estabilidad en laderas altas, el tramo urbano-desnudo (zona Z1) presenta mayor arrastre de sedimentos. Se recomienda activar alistamiento preventivo en la bocatoma municipal y puntos críticos de ribera.",
      recommendations: [
        "Activar monitoreo horario en la estación Poblado y verificar turbidez en la captación de acueducto de Ibagué.",
        "Inspeccionar taludes y zonas de suelo desnudo en el corredor ribereño ante posible incremento de avenidas torrenciales.",
        "Emitir boletín preventivo a juntas comunitarias de Juntas, Pastales y Villarrestrepo sobre variación del cauce.",
      ],
    },
    source: "referencia",
  },
  {
    id: "hist-20261121-magdalena",
    timestamp: "2026-11-21T14:15:00-05:00",
    metrics: {
      basinId: "magdalena-medio",
      basinName: "Cuenca Río Magdalena Medio",
      municipality: "Alcaldía de Barrancabermeja · CORANTIOQUIA",
      coordinates: "07°03'55\"N 73°51'14\"O",
      ndwi: 0.46,
      ndvi: 0.34,
      channelWidthChangePct: 38.5,
      predictedDischargeM3s: 2480,
    },
    report: {
      alert_level: "CRITICA",
      headline:
        "Expansión severa del cauce exige evacuación preventiva en riberas",
      narrative:
        "El incremento del 38.5% en el ancho del cauce y un índice NDWI de 0.46 confirman saturación extrema en la llanura aluvial. Con un caudal proyectado de 2,480 m³/s y reducción de cobertura vegetal riparia, existe riesgo inminente de desbordamiento sobre sectores bajos. Se requiere activación inmediata de los comités municipales de gestión del riesgo y protección de infraestructura crítica.",
      recommendations: [
        "Activar alerta roja municipal y evacuar de forma preventiva viviendas en la cota de inundación ribereña.",
        "Habilitar albergues temporales y desplegar brigadas de cierre en vías terciarias paralelas al margen derecho.",
        "Realizar monitoreo horario de miras limnimétricas y restringir toda navegación menor en el tramo medio.",
      ],
    },
    source: "referencia",
  },
  {
    id: "hist-20261120-cauca",
    timestamp: "2026-11-20T09:30:00-05:00",
    metrics: {
      basinId: "cauca-alto",
      basinName: "Cuenca Alta del Río Cauca",
      municipality: "Alcaldía de Popayán · CRC Cauca",
      coordinates: "02°26'41\"N 76°36'23\"O",
      ndwi: 0.04,
      ndvi: 0.74,
      channelWidthChangePct: 3.4,
      predictedDischargeM3s: 215,
    },
    report: {
      alert_level: "NORMAL",
      headline: "Cuenca estable con cobertura vegetal densa y caudal controlado",
      narrative:
        "La subcuenca alta presenta condiciones hidráulicas dentro de los rangos históricos esperados, con una variación mínima del cauce (+3.4%) y un caudal estimado de 215 m³/s. El alto vigor vegetal (NDVI 0.74) amortigua eficazmente la escorrentía superficial y reduce la carga de sedimentos. No se registran amenazas inmediatas para centros poblados ni infraestructura.",
      recommendations: [
        "Mantener el esquema rutinario de seguimiento satelital semanal y control de estaciones base.",
        "Continuar los programas de conservación de franjas forestales protectoras en nacimientos tributarios.",
        "Actualizar el inventario de obras de captación aprovechando la ventana de estabilidad hidráulica.",
      ],
    },
    source: "referencia",
  },
  {
    id: "hist-20261119-combeima-base",
    timestamp: "2026-11-19T16:50:00-05:00",
    metrics: {
      basinId: "combeima-ibague",
      basinName: "Cuenca del Río Combeima",
      municipality: "Alcaldía de Ibagué · CORTOLIMA",
      coordinates: "04°28'51\"N 75°11'58\"O",
      ndwi: 0.12,
      ndvi: 0.58,
      channelWidthChangePct: -8.4,
      predictedDischargeM3s: 41.2,
    },
    report: {
      alert_level: "NORMAL",
      headline:
        "Caudal estable en Combeima con estrechamiento moderado en estiaje",
      narrative:
        "Las métricas satelitales muestran un NDWI medio de 0.12, NDVI de 0.58 y una contracción del ancho del cauce del -8.4% respecto a la referencia histórica, con caudal proyectado de 41.2 m³/s. El sistema hídrico abastece con normalidad la demanda de Ibagué sin señales de avenida torrencial ni estrés severo. Se aconseja seguimiento rutinario durante la transición climática.",
      recommendations: [
        "Sostener el registro diario de caudal en Estación Poblado y validación quincenal de imágenes Sentinel-2.",
        "Verificar las reservas de regulación en bocatoma ante la ligera contracción estacional del espejo de agua.",
        "Consolidar la serie temporal de NDVI y NDWI para recalibrar umbrales de estiaje en época seca.",
      ],
    },
    source: "referencia",
  },
];
