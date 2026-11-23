export type AlertLevel = "NORMAL" | "PREVENTIVA" | "CRITICA";

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
  detail: string;
  timestamp?: string;
}

export interface BasinMetrics {
  basinId: string;
  basinName: string;
  municipality: string;
  coordinates: string;
  ndwi: number; // [-1, 1]
  ndvi: number; // [-1, 1]
  channelWidthChangePct: number; // %
  predictedDischargeM3s: number; // m3/s
  baselineDischargeM3s: number;
}

export interface ModelPrecisionMetrics {
  rmse: number; // 0.0712
  r2: number; // 0.0775
  classificationMacroF1Plan: number; // 0.66
  classificationMacroF1Artifact: number; // 0.5328
  modelArchitecture: string; // "RNN gru_attention_h1"
  source: string; // "GEE Reales (1969–2023)"
}

export interface CombeimaSeriesPoint {
  year: string;
  ndwi: number;
  ndvi: number;
  channelWidthM: number;
  dischargeM3s: number;
  confidenceLower?: number;
  confidenceUpper?: number;
  isForecast?: boolean;
}

export interface HydrologicalReport {
  alert_level: AlertLevel;
  headline: string;
  narrative: string;
  recommendations: string[];
}

export interface WatershedPreset {
  id: string;
  name: string;
  sector: "ALTA" | "MEDIA" | "BAJA" | "TOTAL";
  description: string;
  centroid: [number, number]; // [lat, lon]
  polygon: [number, number][]; // [lon, lat][]
  metrics: BasinMetrics;
}

export interface AnalyzeRequest {
  area_name: string;
  geometry: {
    type: "Polygon" | "MultiPolygon";
    coordinates: [number, number][][];
  };
  years: [number, number]; // e.g. [1969, 2023]
}

export interface AnalyzeResponseData {
  metrics: {
    ndwi_mean: number;
    ndvi_mean: number;
    channel_width_change_pct: number;
  };
  forecast: {
    dates: string[];
    caudal_m3s: number[];
    rmse: number;
    r2: number;
  };
  report: {
    alert_level: "normal" | "watch" | "alert" | "critical";
    narrative: string;
    recommendations: string[];
  };
}

export type ActiveMapLayer = "none" | "ndwi" | "ndvi" | "morphology";
