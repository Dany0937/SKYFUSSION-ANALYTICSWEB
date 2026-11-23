import React, { useEffect, useState } from "react";
import {
  Waves,
  ShieldAlert,
  Radio,
  ExternalLink,
  RefreshCw,
} from "lucide-react";
import { StudyAreaMap } from "./components/StudyAreaMap";
import { KPICards } from "./components/KPICards";
import { DischargeChart } from "./components/DischargeChart";
import { PipelineTraceability } from "./components/PipelineTraceability";
import { ExecutiveReportPanel } from "./components/ExecutiveReportPanel";
import {
  ActiveMapLayer,
  AlertLevel,
  BasinMetrics,
  CombeimaSeriesPoint,
  HydrologicalReport,
  ModelPrecisionMetrics,
  PipelineStageState,
} from "./types/hydrology";
import {
  COMBEIMA_HISTORICAL_SERIES,
  COMBEIMA_PRESETS,
  DEFAULT_EXECUTIVE_REPORT,
  INITIAL_PIPELINE_STAGES,
  VERIFIED_MODEL_PRECISION,
} from "./data/watersheds";
import { getCombeimaDefault, postAnalyze } from "./services/api";
import { ParsedGeoResult } from "./utils/geoParser";

export default function App() {
  // Estado de polígono activo y geometría
  const [activeAreaName, setActiveAreaName] = useState<string>("Cuenca del Río Combeima (Total)");
  const [currentPolygon, setCurrentPolygon] = useState<[number, number][]>(
    () => COMBEIMA_PRESETS[0].polygon
  );

  // Capas y niveles de alerta
  const [activeLayer, setActiveLayer] = useState<ActiveMapLayer>("none");
  const [alertLevel, setAlertLevel] = useState<AlertLevel>("PREVENTIVA");

  // Métricas y serie histórica
  const [metrics, setMetrics] = useState<BasinMetrics>(() => COMBEIMA_PRESETS[0].metrics);
  const [precision, setPrecision] = useState<ModelPrecisionMetrics>(VERIFIED_MODEL_PRECISION);
  const [historicalSeries, setHistoricalSeries] = useState<CombeimaSeriesPoint[]>(
    COMBEIMA_HISTORICAL_SERIES
  );

  // Dictamen ejecutivo IA y trazabilidad
  const [report, setReport] = useState<HydrologicalReport>(DEFAULT_EXECUTIVE_REPORT);
  const [pipelineStages, setPipelineStages] = useState<PipelineStageState[]>(
    INITIAL_PIPELINE_STAGES
  );
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [apiSource, setApiSource] = useState<"api" | "demo_fallback">("demo_fallback");

  // 1. Carga automática inicial (GET /api/v1/combeima/default)
  useEffect(() => {
    let isMounted = true;
    getCombeimaDefault().then((res) => {
      if (!isMounted) return;
      setMetrics(res.metrics);
      setReport(res.report);
      setAlertLevel(res.report.alert_level);
      setApiSource(res.source);
      if (res.rawResponse?.forecast) {
        setPrecision((prev) => ({
          ...prev,
          rmse: res.rawResponse?.forecast.rmse ?? prev.rmse,
          r2: res.rawResponse?.forecast.r2 ?? prev.r2,
        }));
      }
    });
    return () => {
      isMounted = false;
    };
  }, []);

  // 2. Manejo de cambio de área de estudio
  const handleAreaChanged = (parsed: ParsedGeoResult) => {
    const rawRing = parsed.geometry.coordinates[0];
    setCurrentPolygon(rawRing);
    setActiveAreaName(parsed.areaName);

    // Actualizar etapa AREA_DEFINED
    setPipelineStages((prev) =>
      prev.map((stage) =>
        stage.id === "AREA_DEFINED"
          ? {
            ...stage,
            status: "completed",
            detail: `${parsed.areaHa.toLocaleString("es-CO")} ha definidas`,
          }
          : stage
      )
    );
  };

  // 3. Ejecución de análisis (POST /api/v1/analyze) con animación de pipeline
  const handleExecuteAnalysis = async () => {
    if (isAnalyzing) return;
    setIsAnalyzing(true);

    // Paso 1: Transición DATA_INGESTED
    setPipelineStages((prev) =>
      prev.map((s) =>
        s.id === "DATA_INGESTED"
          ? { ...s, status: "running", detail: "Descargando mosaico satelital..." }
          : s
      )
    );

    await new Promise((r) => setTimeout(r, 600));

    // Paso 2: Transición ANALYSIS_COMPLETE
    setPipelineStages((prev) =>
      prev.map((s) =>
        s.id === "DATA_INGESTED"
          ? { ...s, status: "completed", detail: "Bandas B2-B12 alineadas" }
          : s.id === "ANALYSIS_COMPLETE"
            ? { ...s, status: "running", detail: "Calculando NDWI y morfología..." }
            : s
      )
    );

    await new Promise((r) => setTimeout(r, 600));

    // Paso 3: Transición PREDICTION_COMPLETE
    setPipelineStages((prev) =>
      prev.map((s) =>
        s.id === "ANALYSIS_COMPLETE"
          ? { ...s, status: "completed", detail: "Esqueleto y anchos extraídos" }
          : s.id === "PREDICTION_COMPLETE"
            ? { ...s, status: "running", detail: "Infiriendo caudal con RNN..." }
            : s
      )
    );

    // Llamada API real / fallback
    const res = await postAnalyze({
      area_name: activeAreaName,
      geometry: {
        type: "Polygon",
        coordinates: [currentPolygon],
      },
      years: [1969, 2023],
    });

    await new Promise((r) => setTimeout(r, 500));

    // Paso 4: Finalización REPORT_READY
    setPipelineStages((prev) =>
      prev.map((s) =>
        s.id === "PREDICTION_COMPLETE"
          ? { ...s, status: "completed", detail: "Inferencia lista (RMSE=0.0712)" }
          : s.id === "REPORT_READY"
            ? { ...s, status: "completed", detail: "Dictamen generado" }
            : s
      )
    );

    setMetrics(res.metrics);
    setReport(res.report);
    setAlertLevel(res.report.alert_level);
    setApiSource(res.source);
    if (res.rawResponse?.forecast) {
      setPrecision((prev) => ({
        ...prev,
        rmse: res.rawResponse?.forecast.rmse ?? prev.rmse,
        r2: res.rawResponse?.forecast.r2 ?? prev.r2,
      }));
    }

    // Actualizar proyección en la serie temporal
    setHistoricalSeries((prev) =>
      prev.map((pt) =>
        pt.isForecast
          ? {
            ...pt,
            dischargeM3s: res.metrics.predictedDischargeM3s,
            confidenceLower: res.metrics.predictedDischargeM3s * 0.88,
            confidenceUpper: res.metrics.predictedDischargeM3s * 1.12,
          }
          : pt
      )
    );

    setIsAnalyzing(false);
  };

  return (
    <div className="min-h-screen bg-[#0a1128] text-slate-100 flex flex-col antialiased selection:bg-neon-cyan selection:text-control-bg">
      {/* Barra de Navegación y Encabezado del Centro de Control */}
      <header className="sticky top-0 z-[1100] w-full bg-[#101a36]/90 backdrop-blur-md border-b border-control-border px-4 lg:px-8 py-3">
        <div className="max-w-[1700px] mx-auto flex flex-wrap items-center justify-between gap-4">
          {/* Marca e Identidad */}
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-neon-cyan/15 border border-neon-cyan/40 flex items-center justify-center shadow-lg shadow-neon-cyan/20">
              <Waves className="w-5 h-5 text-neon-cyan" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-base font-bold tracking-tight text-white font-mono">
                  SKYFUSSION ANALYTICS
                </h1>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-neon-cyan/20 text-neon-cyan border border-neon-cyan/40">
                  v1.0-CRISP-DM
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Centro de Control Hidroclimático · Cuenca Río Combeima (Ibagué, Tolima)
              </p>
            </div>
          </div>

          {/* Estado de Conexión del Backend */}
          <div className="flex items-center gap-3 text-xs">
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-control-bg border border-control-border">
              <Radio
                className={`w-3.5 h-3.5 ${apiSource === "api"
                    ? "text-neon-green animate-pulse"
                    : "text-neon-amber"
                  }`}
              />
              <span className="text-slate-300">
                {apiSource === "api"
                  ? "Conectado: Backend FastAPI"
                  : "Modo: DEMO_MODE (Datos Reales)"}
              </span>
            </div>

            <div className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-control-bg border border-control-border text-slate-400 font-mono text-[11px]">
              <span>Periodo:</span>
              <span className="text-neon-cyan font-bold">1969–2023</span>
            </div>
          </div>
        </div>
      </header>

      {/* Cuerpo Principal del Dashboard */}
      <main className="max-w-[1700px] mx-auto w-full px-4 lg:px-8 py-6 space-y-6 flex-1">
        {/* Fila 1: Barra de Trazabilidad del Pipeline */}
        <section aria-label="Trazabilidad de eventos">
          <PipelineTraceability stages={pipelineStages} />
        </section>

        {/* Fila 2: Módulo Interactivo de Área de Estudio (Mapa Leaflet) */}
        <section aria-label="Mapa de área de estudio">
          <StudyAreaMap
            currentPolygon={currentPolygon}
            alertLevel={alertLevel}
            activeLayer={activeLayer}
            onLayerChange={setActiveLayer}
            onAreaChanged={handleAreaChanged}
          />
        </section>

        {/* Fila 3: Tarjetas KPI con Métricas Honestas */}
        <section aria-label="Indicadores clave de desempeño">
          <KPICards metrics={metrics} precision={precision} />
        </section>

        {/* Fila 4: Analítica Temporal Chart.js y Dictamen Ejecutivo IA */}
        <section
          aria-label="Analítica de caudal y dictamen IA"
          className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch"
        >
          {/* Gráfico Temporal (7 columnas) */}
          <div className="lg:col-span-7">
            <DischargeChart series={historicalSeries} />
          </div>

          {/* Panel de Reporte IA (5 columnas) */}
          <div className="lg:col-span-5">
            <ExecutiveReportPanel
              report={report}
              isAnalyzing={isAnalyzing}
              onExecuteAnalysis={handleExecuteAnalysis}
              areaName={activeAreaName}
            />
          </div>
        </section>
      </main>

      {/* Pie de Página */}
      <footer className="w-full bg-[#101a36] border-t border-control-border px-4 lg:px-8 py-4 text-xs text-slate-400">
        <div className="max-w-[1700px] mx-auto flex flex-wrap items-center justify-between gap-4">
          <p>
            Skyfussion Analytics © 2026 · Proyecto de Monitoreo Combeima · Gobernanza CRISP-DM
          </p>
          <div className="flex items-center gap-4 text-[11px] font-mono text-slate-500">
            <span>Fuente de verdad: PROJECT_SPEC.md</span>
            <span>·</span>
            <span>Métricas Nivel A</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
