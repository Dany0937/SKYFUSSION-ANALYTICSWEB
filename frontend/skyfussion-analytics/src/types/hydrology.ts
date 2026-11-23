export type AlertLevel = "NORMAL" | "PREVENTIVA" | "CRITICA";

export type MapLayer = "composite" | "ndwi" | "ndvi" | "channel" | "kmeans";

export type MapEngineMode = "leaflet" | "spectral";

export type ActiveView = "console" | "history" | "methodology";

export type ThemeMode = "dark" | "light";

export type PipelineStageId =
  | "AREA_DEFINED"
  | "DATA_INGESTED"
  | "ANALYSIS_COMPLETE"
  | "PREDICTION_COMPLETE"
  | "REPORT_READY";

export type PipelineStageStatus = "pending" | "running" | "completed" | "error";

export interface PipelineStageState {
  id: PipelineStageId;
  label: string;
  status: PipelineStageStatus;
  timestamp?: string;
  detail?: string;
}

export interface BasinMetrics {
  basinId: string;
  basinName: string;
  municipality: string;
  coordinates: string;
  ndwi: number;
  ndvi: number;
  channelWidthChangePct: number;
  predictedDischargeM3s: number;
}

export interface HydrologicalReport {
  alert_level: AlertLevel;
  headline: string;
  narrative: string;
  recommendations: [string, string, string];
}

export interface WatershedPreset extends BasinMetrics {
  region: string;
  areaKm2: number;
  elevationRangeM: string;
  stationCode: string;
  summary: string;
  baselineDischargeM3s: number;
  geometryVariant: "combeima" | "alluvial" | "canyon" | "delta";
  satelliteImage: string;
  latBounds: [number, number];
  lonBounds: [number, number];
  defaultPolygon: [number, number][][];
}

export interface CombeimaSeriesPoint {
  year: string;
  ndwi: number;
  ndvi: number;
  channelWidthM: number;
  dischargeM3s: number;
  isForecast?: boolean;
}

export interface HistoricalAlertEntry {
  id: string;
  timestamp: string;
  metrics: BasinMetrics;
  report: HydrologicalReport;
  source: "ia" | "referencia";
}
