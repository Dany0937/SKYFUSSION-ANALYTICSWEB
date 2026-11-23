import { useEffect, useState } from "react";
import { ArrowUpRight, Moon, Sun } from "lucide-react";
import { BasinMapViewport } from "./components/BasinMapViewport";
import { EventPipelineBar } from "./components/EventPipelineBar";
import { ExecutiveReportPanel } from "./components/ExecutiveReportPanel";
import { HistoryComparisonView } from "./components/HistoryComparisonView";
import { MethodologyView } from "./components/MethodologyView";
import { MetricsControlPanel } from "./components/MetricsControlPanel";
import { TimeSeriesCharts } from "./components/TimeSeriesCharts";
import { TopBar } from "./components/TopBar";
import {
  INITIAL_HISTORICAL_ALERTS,
  INITIAL_PIPELINE_STAGES,
  WATERSHED_PRESETS,
} from "./data/watersheds";
import {
  ActiveView,
  BasinMetrics,
  HistoricalAlertEntry,
  HydrologicalReport,
  MapEngineMode,
  MapLayer,
  PipelineStageState,
  ThemeMode,
  WatershedPreset,
} from "./types/hydrology";
import { computePolygonAreaHa, ParsedGeoResult } from "./utils/geoParser";

const HISTORY_STORAGE_KEY = "skyfussion_alert_history_v2";
const THEME_STORAGE_KEY = "skyfussion_theme_mode_v1";

function toMetrics(preset: WatershedPreset): BasinMetrics {
  return {
    basinId: preset.basinId,
    basinName: preset.basinName,
    municipality: preset.municipality,
    coordinates: preset.coordinates,
    ndwi: preset.ndwi,
    ndvi: preset.ndvi,
    channelWidthChangePct: preset.channelWidthChangePct,
    predictedDischargeM3s: preset.predictedDischargeM3s,
  };
}

export default function App() {
  const [theme, setTheme] = useState<ThemeMode>(() => {
    try {
      const saved = localStorage.getItem(THEME_STORAGE_KEY);
      return saved === "light" ? "light" : "dark";
    } catch {
      return "dark";
    }
  });

  const [activeView, setActiveView] = useState<ActiveView>("console");
  const [mapEngine, setMapEngine] = useState<MapEngineMode>("leaflet");
  const [activeLayer, setActiveLayer] = useState<MapLayer>("composite");
  const [isDrawing, setIsDrawing] = useState(false);

  const [activePreset, setActivePreset] = useState<WatershedPreset>(
    WATERSHED_PRESETS[0]
  );
  const [metrics, setMetrics] = useState<BasinMetrics>(() =>
    toMetrics(WATERSHED_PRESETS[0])
  );
  const [polygonRing, setPolygonRing] = useState<[number, number][]>(
    () => WATERSHED_PRESETS[0].defaultPolygon[0]
  );
  const [activePolygonAreaHa, setActivePolygonAreaHa] = useState<number>(() =>
    computePolygonAreaHa(WATERSHED_PRESETS[0].defaultPolygon[0])
  );

  const [pipelineStages, setPipelineStages] = useState<PipelineStageState[]>(
    INITIAL_PIPELINE_STAGES
  );

  const [history, setHistory] = useState<HistoricalAlertEntry[]>(() => {
    try {
      const raw = localStorage.getItem(HISTORY_STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw);
        if (Array.isArray(parsed) && parsed.length > 0) {
          return parsed as HistoricalAlertEntry[];
        }
      }
    } catch {
      // Fallback to initial seeded records
    }
    return INITIAL_HISTORICAL_ALERTS;
  });

  const [currentReport, setCurrentReport] = useState<HydrologicalReport | null>(
    INITIAL_HISTORICAL_ALERTS[0].report
  );
  const [reportGeneratedAt, setReportGeneratedAt] = useState<string | null>(
    INITIAL_HISTORICAL_ALERTS[0].timestamp
  );
  const [isGenerating, setIsGenerating] = useState(false);
  const [reportError, setReportError] = useState<string | null>(null);

  // Sync theme class on <html>
  useEffect(() => {
    const root = document.documentElement;
    if (theme === "dark") {
      root.classList.add("dark");
    } else {
      root.classList.remove("dark");
    }
    try {
      localStorage.setItem(THEME_STORAGE_KEY, theme);
    } catch {
      // Ignore storage errors
    }
  }, [theme]);

  // Persist alert history
  useEffect(() => {
    try {
      localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(history));
    } catch {
      // Ignore storage errors
    }
  }, [history]);

  const handleSelectPreset = (preset: WatershedPreset) => {
    setActivePreset(preset);
    setMetrics(toMetrics(preset));
    setPolygonRing(preset.defaultPolygon[0]);
    setActivePolygonAreaHa(computePolygonAreaHa(preset.defaultPolygon[0]));
    setIsDrawing(false);
    setReportError(null);
    const matchingHistory = history.find(
      (entry) => entry.metrics.basinId === preset.basinId
    );
    if (matchingHistory) {
      setCurrentReport(matchingHistory.report);
      setReportGeneratedAt(matchingHistory.timestamp);
    }
    setPipelineStages(INITIAL_PIPELINE_STAGES);
  };

  const handleResetToPreset = () => {
    setMetrics(toMetrics(activePreset));
    setPolygonRing(activePreset.defaultPolygon[0]);
    setActivePolygonAreaHa(
      computePolygonAreaHa(activePreset.defaultPolygon[0])
    );
    setReportError(null);
  };

  const handleChangeMetric = (
    field: keyof BasinMetrics,
    value: number | string
  ) => {
    setMetrics((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const setPipelineRunning = (areaLabel: string) => {
    setPipelineStages([
      {
        id: "AREA_DEFINED",
        label: "AREA_DEFINED",
        status: "completed",
        detail: areaLabel,
      },
      {
        id: "DATA_INGESTED",
        label: "DATA_INGESTED",
        status: "completed",
        detail: "Sentinel-2 + 1969–2023",
      },
      {
        id: "ANALYSIS_COMPLETE",
        label: "ANALYSIS_COMPLETE",
        status: "running",
        detail: "Calculando NDWI/NDVI",
      },
      {
        id: "PREDICTION_COMPLETE",
        label: "PREDICTION_COMPLETE",
        status: "pending",
        detail: "En espera",
      },
      {
        id: "REPORT_READY",
        label: "REPORT_READY",
        status: "pending",
        detail: "En espera",
      },
    ]);
  };

  const setPipelineCompleted = (alertLevel: string) => {
    setPipelineStages([
      {
        id: "AREA_DEFINED",
        label: "AREA_DEFINED",
        status: "completed",
        detail: "Geometría validada",
      },
      {
        id: "DATA_INGESTED",
        label: "DATA_INGESTED",
        status: "completed",
        detail: "Serie temporal lista",
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
        detail: "Caudal proyectado",
      },
      {
        id: "REPORT_READY",
        label: "REPORT_READY",
        status: "completed",
        detail: `Alerta ${alertLevel}`,
      },
    ]);
  };

  const setPipelineFailed = () => {
    setPipelineStages((prev) =>
      prev.map((s) =>
        s.status === "running" || s.status === "pending"
          ? { ...s, status: "error", detail: "Interrumpido" }
          : s
      )
    );
  };

  const handleGenerateReport = async () => {
    setActiveView("console");
    setIsGenerating(true);
    setReportError(null);
    setPipelineRunning(metrics.basinName);

    try {
      const response = await fetch("/api/report", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(metrics),
      });

      const payload = await response.json();
      if (!response.ok) {
        throw new Error(
          payload?.error ||
            "El servicio hidrológico respondió con un error inesperado."
        );
      }

      const nextReport = payload.report as HydrologicalReport;
      const timestamp = payload.generatedAt || new Date().toISOString();

      setCurrentReport(nextReport);
      setReportGeneratedAt(timestamp);
      setPipelineCompleted(nextReport.alert_level);

      const newEntry: HistoricalAlertEntry = {
        id: `hist-${Date.now()}`,
        timestamp,
        metrics: { ...metrics },
        report: nextReport,
        source: "ia",
      };
      setHistory((prev) => [newEntry, ...prev]);
    } catch (err: unknown) {
      const message =
        err instanceof Error
          ? err.message
          : "No se pudo conectar con el servidor de Skyfussion Analytics.";
      setReportError(message);
      setPipelineFailed();
    } finally {
      setIsGenerating(false);
    }
  };

  const handlePolygonWorkflow = async (
    parsed: ParsedGeoResult,
    runAnalyze: boolean
  ) => {
    const outerRing = parsed.geometry.coordinates[0];
    setPolygonRing(outerRing);
    setActivePolygonAreaHa(parsed.areaHa);
    setMetrics((prev) => ({
      ...prev,
      basinName: parsed.areaName,
      coordinates: parsed.formattedCoords,
    }));
    setMapEngine("leaflet");

    if (!runAnalyze) {
      setPipelineStages([
        {
          id: "AREA_DEFINED",
          label: "AREA_DEFINED",
          status: "completed",
          detail: `${parsed.areaHa.toLocaleString("es-CO")} ha`,
        },
        {
          id: "DATA_INGESTED",
          label: "DATA_INGESTED",
          status: "pending",
          detail: "Listo para analizar",
        },
        {
          id: "ANALYSIS_COMPLETE",
          label: "ANALYSIS_COMPLETE",
          status: "pending",
          detail: "En espera",
        },
        {
          id: "PREDICTION_COMPLETE",
          label: "PREDICTION_COMPLETE",
          status: "pending",
          detail: "En espera",
        },
        {
          id: "REPORT_READY",
          label: "REPORT_READY",
          status: "pending",
          detail: "En espera",
        },
      ]);
      return;
    }

    setIsGenerating(true);
    setReportError(null);
    setPipelineRunning(`${parsed.areaHa.toLocaleString("es-CO")} ha`);

    try {
      const response = await fetch("/api/v1/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          area_name: parsed.areaName,
          geometry: parsed.geometry,
          years: [1969, 2023],
        }),
      });

      const payload = await response.json();
      if (!response.ok || !payload?.success) {
        throw new Error(
          payload?.detail ||
            payload?.error ||
            "Error al analizar la geometría recibida."
        );
      }

      const data = payload.data;
      const updatedMetrics: BasinMetrics = {
        basinId: `custom-${Date.now()}`,
        basinName: data.area_name,
        municipality: "Alcaldía Local · Polígono Personalizado",
        coordinates: parsed.formattedCoords,
        ndwi: data.metrics.ndwi_mean,
        ndvi: data.metrics.ndvi_mean,
        channelWidthChangePct: data.metrics.channel_width_change_pct,
        predictedDischargeM3s: data.forecast.caudal_m3s[0],
      };

      const nextReport = data.report as HydrologicalReport;
      const timestamp = new Date().toISOString();

      setMetrics(updatedMetrics);
      setCurrentReport(nextReport);
      setReportGeneratedAt(timestamp);
      setPipelineCompleted(nextReport.alert_level);

      setHistory((prev) => [
        {
          id: `hist-${Date.now()}`,
          timestamp,
          metrics: updatedMetrics,
          report: nextReport,
          source: "ia",
        },
        ...prev,
      ]);
    } catch (err: unknown) {
      const message =
        err instanceof Error
          ? err.message
          : "Error ejecutando POST /api/v1/analyze.";
      setReportError(message);
      setPipelineFailed();
    } finally {
      setIsGenerating(false);
    }
  };

  const handleLoadHistoryEntry = (entry: HistoricalAlertEntry) => {
    const matchedPreset =
      WATERSHED_PRESETS.find((p) => p.basinId === entry.metrics.basinId) ??
      WATERSHED_PRESETS[0];
    setActivePreset(matchedPreset);
    setMetrics({ ...entry.metrics });
    setPolygonRing(matchedPreset.defaultPolygon[0]);
    setActivePolygonAreaHa(
      computePolygonAreaHa(matchedPreset.defaultPolygon[0])
    );
    setCurrentReport(entry.report);
    setReportGeneratedAt(entry.timestamp);
    setReportError(null);
    setPipelineCompleted(entry.report.alert_level);
    setActiveView("console");
  };

  const handleDeleteEntry = (id: string) => {
    setHistory((prev) => prev.filter((item) => item.id !== id));
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#FAF8FF] dark:bg-[#0B1229] text-[#0F172A] dark:text-[#DCE1FF] transition-colors duration-150">
      <TopBar
        activeView={activeView}
        onChangeView={setActiveView}
        onGenerateReport={handleGenerateReport}
        isGenerating={isGenerating}
      />

      <main className="flex-1 w-full max-w-[1600px] mx-auto px-4 md:px-6 py-5 flex flex-col gap-5">
        {/* Workspace Toolbar (Theme switcher + active basin context) */}
        <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-[#E2E8F0] dark:border-[#1E2D5A]">
          <div className="min-w-0">
            <h1 className="font-display text-xl md:text-2xl font-bold tracking-tight text-[#0F172A] dark:text-[#DCE1FF]">
              {activeView === "console"
                ? metrics.basinName
                : activeView === "history"
                  ? "Historial y Comparativa de Cuencas"
                  : "Base Técnica del Agente Hidrológico"}
            </h1>
            <p className="text-xs text-[#64748B] dark:text-[#8E9AB8] mt-0.5">
              {activePreset.region} · {metrics.municipality} · Área{" "}
              <span className="font-mono-tabular">
                {activePolygonAreaHa.toLocaleString("es-CO")} ha
              </span>
            </p>
          </div>

          {/* Dual-Theme Toggle (Orbital Dark / Oceanic Light) */}
          <div
            role="group"
            aria-label="Selector de modo visual"
            className="flex items-center gap-1 p-1 rounded bg-[#F1F5F9] dark:bg-[#101A36] border border-[#E2E8F0] dark:border-[#1E2D5A]"
          >
            <button
              type="button"
              onClick={() => setTheme("dark")}
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium whitespace-nowrap cursor-pointer transition-colors ${
                theme === "dark"
                  ? "bg-[#181E36] text-[#00BBF9] border border-[#1E2D5A]"
                  : "text-[#64748B] hover:text-[#0F172A] border border-transparent"
              }`}
            >
              <Moon className="w-3.5 h-3.5" aria-hidden="true" />
              <span>Orbital Oscuro</span>
            </button>
            <button
              type="button"
              onClick={() => setTheme("light")}
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium whitespace-nowrap cursor-pointer transition-colors ${
                theme === "light"
                  ? "bg-[#FFFFFF] text-[#0284C7] border border-[#CBD5E1]"
                  : "text-[#8E9AB8] hover:text-[#DCE1FF] border border-transparent"
              }`}
            >
              <Sun className="w-3.5 h-3.5" aria-hidden="true" />
              <span>Oceánico Claro</span>
            </button>
          </div>
        </div>

        {activeView === "console" && (
          <>
            {/* 5-Stage Event Pipeline Tracker */}
            <EventPipelineBar stages={pipelineStages} />

            {/* Asymmetric Split Console */}
            <div className="flex flex-col lg:flex-row items-stretch gap-4">
              <MetricsControlPanel
                presets={WATERSHED_PRESETS}
                activePreset={activePreset}
                metrics={metrics}
                activePolygonAreaHa={activePolygonAreaHa}
                onSelectPreset={handleSelectPreset}
                onChangeMetric={handleChangeMetric}
                onResetToPreset={handleResetToPreset}
                onGenerateReport={handleGenerateReport}
                onPolygonParsed={handlePolygonWorkflow}
                onStartDrawOnMap={() => {
                  setMapEngine("leaflet");
                  setIsDrawing(true);
                }}
                isGenerating={isGenerating}
              />

              <BasinMapViewport
                preset={activePreset}
                metrics={metrics}
                activeLayer={activeLayer}
                onChangeLayer={setActiveLayer}
                mapEngine={mapEngine}
                onChangeMapEngine={setMapEngine}
                polygonRing={polygonRing}
                alertLevel={currentReport?.alert_level}
                theme={theme}
                isDrawing={isDrawing}
                onToggleDrawing={setIsDrawing}
                onPolygonCommitted={(parsed) =>
                  handlePolygonWorkflow(parsed, true)
                }
              />

              <ExecutiveReportPanel
                metrics={metrics}
                report={currentReport}
                generatedAt={reportGeneratedAt}
                isGenerating={isGenerating}
                error={reportError}
                onRetry={handleGenerateReport}
              />
            </div>

            {/* Chart.js 1969-2023 Time-Series Section */}
            <TimeSeriesCharts metrics={metrics} theme={theme} />

            {/* Bottom Historical Quick Strip */}
            <section className="bg-[#FFFFFF] dark:bg-[#101A36] border border-[#E2E8F0] dark:border-[#1E2D5A] rounded-lg p-4">
              <div className="flex items-center justify-between gap-4 pb-3 border-b border-[#E2E8F0] dark:border-[#1E2D5A]">
                <h2 className="font-display text-sm font-semibold text-[#0F172A] dark:text-[#DCE1FF]">
                  Últimos Boletines Hidrológicos Emitidos
                </h2>
                <button
                  type="button"
                  onClick={() => setActiveView("history")}
                  className="inline-flex items-center gap-1 text-xs font-medium text-[#0284C7] dark:text-[#00BBF9] hover:underline cursor-pointer"
                >
                  <span>Abrir comparativa completa</span>
                  <ArrowUpRight className="w-3.5 h-3.5" aria-hidden="true" />
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4 pt-3">
                {history.slice(0, 4).map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => handleLoadHistoryEntry(item)}
                    className="text-left p-3 rounded border border-[#E2E8F0] dark:border-[#1E2D5A] bg-[#F8FAFC] dark:bg-[#0A1128] hover:border-[#0284C7] dark:hover:border-[#00BBF9] transition-colors cursor-pointer flex flex-col gap-1.5"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span
                        className={`font-mono-tabular text-[11px] font-semibold ${
                          item.report.alert_level === "CRITICA"
                            ? "text-[#BA1A1A] dark:text-[#F72585]"
                            : item.report.alert_level === "PREVENTIVA"
                              ? "text-[#B45309] dark:text-[#FFB703]"
                              : "text-[#059669] dark:text-[#00F5D4]"
                        }`}
                      >
                        {item.report.alert_level}
                      </span>
                      <span className="font-mono-tabular text-[11px] text-[#64748B] dark:text-[#8E9AB8]">
                        {item.metrics.predictedDischargeM3s.toLocaleString("es-CO")} m³/s
                      </span>
                    </div>
                    <p className="text-xs font-semibold text-[#0F172A] dark:text-[#DCE1FF] line-clamp-1">
                      {item.metrics.basinName}
                    </p>
                    <p className="text-xs text-[#334155] dark:text-[#BCC8D1] line-clamp-2 leading-snug">
                      {item.report.headline}
                    </p>
                  </button>
                ))}
              </div>
            </section>
          </>
        )}

        {activeView === "history" && (
          <HistoryComparisonView
            entries={history}
            onLoadToConsole={handleLoadHistoryEntry}
            onDeleteEntry={handleDeleteEntry}
          />
        )}

        {activeView === "methodology" && <MethodologyView />}
      </main>

      <footer className="w-full border-t border-[#E2E8F0] dark:border-[#1E2D5A] py-4 px-4 md:px-6 text-xs text-[#64748B] dark:text-[#8E9AB8]">
        <div className="max-w-[1600px] mx-auto flex flex-wrap items-center justify-between gap-2">
          <span>Skyfussion Analytics · Monitoreo Hidrológico Satelital</span>
          <span>Reportes estructurados para alcaldías y autoridades ambientales</span>
        </div>
      </footer>
    </div>
  );
}
