import React, { useState } from "react";
import {
  FileUp,
  MapPin,
  Pencil,
  RotateCcw,
  SlidersHorizontal,
} from "lucide-react";
import { BasinMetrics, WatershedPreset } from "../types/hydrology";
import {
  ParsedGeoResult,
  parseGeoJsonText,
  parseKmlText,
  parseManualCoordinates,
} from "../utils/geoParser";

interface MetricsControlPanelProps {
  presets: WatershedPreset[];
  activePreset: WatershedPreset;
  metrics: BasinMetrics;
  activePolygonAreaHa: number;
  onSelectPreset: (preset: WatershedPreset) => void;
  onChangeMetric: (field: keyof BasinMetrics, value: number | string) => void;
  onResetToPreset: () => void;
  onGenerateReport: () => void;
  onPolygonParsed: (parsed: ParsedGeoResult, runAnalyze: boolean) => void;
  onStartDrawOnMap: () => void;
  isGenerating: boolean;
}

const SAMPLE_COMBEIMA_COORDS = `-75.257, 4.433
-75.142, 4.433
-75.142, 4.529
-75.257, 4.529`;

export function MetricsControlPanel({
  presets,
  activePreset,
  metrics,
  activePolygonAreaHa,
  onSelectPreset,
  onChangeMetric,
  onResetToPreset,
  onGenerateReport,
  onPolygonParsed,
  onStartDrawOnMap,
  isGenerating,
}: MetricsControlPanelProps) {
  const [panelTab, setPanelTab] = useState<"metrics" | "geometry">("metrics");
  const [customAreaName, setCustomAreaName] = useState<string>(
    "Subcuenca Alta Combeima"
  );
  const [coordsInput, setCoordsInput] = useState<string>(SAMPLE_COMBEIMA_COORDS);
  const [geoError, setGeoError] = useState<string | null>(null);
  const [geoSuccess, setGeoSuccess] = useState<string | null>(null);

  const applyScenarioQuick = (scenario: "normal" | "preventiva" | "critica") => {
    if (scenario === "normal") {
      onChangeMetric("ndwi", 0.05);
      onChangeMetric("ndvi", 0.72);
      onChangeMetric("channelWidthChangePct", 3.5);
      onChangeMetric(
        "predictedDischargeM3s",
        Math.round(activePreset.baselineDischargeM3s * 1.05)
      );
    } else if (scenario === "preventiva") {
      onChangeMetric("ndwi", 0.25);
      onChangeMetric("ndvi", 0.54);
      onChangeMetric("channelWidthChangePct", 18.0);
      onChangeMetric(
        "predictedDischargeM3s",
        Math.round(activePreset.baselineDischargeM3s * 1.52)
      );
    } else {
      onChangeMetric("ndwi", 0.48);
      onChangeMetric("ndvi", 0.31);
      onChangeMetric("channelWidthChangePct", 41.0);
      onChangeMetric(
        "predictedDischargeM3s",
        Math.round(activePreset.baselineDischargeM3s * 2.15)
      );
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setGeoError(null);
    setGeoSuccess(null);

    try {
      const content = await file.text();
      const lower = file.name.toLowerCase();
      const parsed = lower.endsWith(".kml")
        ? parseKmlText(content, file.name.replace(/\.kml$/i, ""))
        : parseGeoJsonText(content, file.name.replace(/\.(geo)?json$/i, ""));

      setCustomAreaName(parsed.areaName);
      setCoordsInput(
        parsed.geometry.coordinates[0]
          .slice(0, -1)
          .map(([lon, lat]) => `${lon}, ${lat}`)
          .join("\n")
      );
      setGeoSuccess(
        `Archivo cargado: ${parsed.areaName} (${parsed.areaHa.toLocaleString("es-CO")} ha)`
      );
      onPolygonParsed(parsed, true);
    } catch (err: unknown) {
      setGeoError(
        err instanceof Error
          ? err.message
          : "No fue posible procesar el archivo vectorial."
      );
    } finally {
      e.target.value = "";
    }
  };

  const handleApplyManualCoords = (runAnalyze: boolean) => {
    setGeoError(null);
    setGeoSuccess(null);
    try {
      const parsed = parseManualCoordinates(coordsInput, customAreaName);
      setGeoSuccess(
        `Polígono validado: ${parsed.areaHa.toLocaleString("es-CO")} ha`
      );
      onPolygonParsed(parsed, runAnalyze);
    } catch (err: unknown) {
      setGeoError(
        err instanceof Error ? err.message : "Coordenadas inválidas."
      );
    }
  };

  return (
    <aside className="w-full lg:w-[340px] xl:w-[360px] shrink-0 flex flex-col gap-4 bg-[#FFFFFF] dark:bg-[#101A36] border border-[#E2E8F0] dark:border-[#1E2D5A] rounded-lg p-4">
      {/* Header + Tabs */}
      <div className="flex flex-col gap-3 pb-3 border-b border-[#E2E8F0] dark:border-[#1E2D5A]">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <SlidersHorizontal
              className="w-4 h-4 text-[#0284C7] dark:text-[#00BBF9]"
              aria-hidden="true"
            />
            <h2 className="font-display text-sm font-semibold text-[#0F172A] dark:text-[#DCE1FF]">
              Control de Cuenca
            </h2>
          </div>
          <button
            type="button"
            onClick={onResetToPreset}
            title="Restablecer métricas del preset"
            className="inline-flex items-center gap-1.5 text-xs font-medium text-[#64748B] dark:text-[#8E9AB8] hover:text-[#0284C7] dark:hover:text-[#00BBF9] transition-colors cursor-pointer"
          >
            <RotateCcw className="w-3.5 h-3.5" aria-hidden="true" />
            <span>Restablecer</span>
          </button>
        </div>

        <div
          role="group"
          aria-label="Modo de entrada de datos"
          className="grid grid-cols-2 gap-1 p-1 rounded bg-[#F1F5F9] dark:bg-[#0A1128] border border-[#E2E8F0] dark:border-[#1E2D5A]"
        >
          <button
            type="button"
            onClick={() => setPanelTab("metrics")}
            className={`px-2 py-1 rounded text-xs font-medium cursor-pointer transition-colors ${
              panelTab === "metrics"
                ? "bg-[#FFFFFF] dark:bg-[#181E36] text-[#0284C7] dark:text-[#00BBF9]"
                : "text-[#64748B] dark:text-[#8E9AB8]"
            }`}
          >
            Parámetros
          </button>
          <button
            type="button"
            onClick={() => setPanelTab("geometry")}
            className={`px-2 py-1 rounded text-xs font-medium cursor-pointer transition-colors ${
              panelTab === "geometry"
                ? "bg-[#FFFFFF] dark:bg-[#181E36] text-[#0284C7] dark:text-[#00BBF9]"
                : "text-[#64748B] dark:text-[#8E9AB8]"
            }`}
          >
            GeoJSON / KML
          </button>
        </div>
      </div>

      {panelTab === "metrics" ? (
        <>
          {/* Watershed Preset Selector */}
          <div className="flex flex-col gap-1.5">
            <label
              htmlFor="watershed-preset-select"
              className="text-xs font-medium text-[#334155] dark:text-[#BCC8D1]"
            >
              Cuenca hidrográfica monitoreada
            </label>
            <select
              id="watershed-preset-select"
              value={activePreset.basinId}
              onChange={(e) => {
                const found = presets.find((p) => p.basinId === e.target.value);
                if (found) onSelectPreset(found);
              }}
              className="w-full rounded px-3 py-2 text-sm bg-[#F8FAFC] dark:bg-[#0A1128] border border-[#CBD5E1] dark:border-[#1E2D5A] text-[#0F172A] dark:text-[#DCE1FF] focus:outline-none focus:border-[#0284C7] dark:focus:border-[#00BBF9]"
            >
              {presets.map((preset) => (
                <option key={preset.basinId} value={preset.basinId}>
                  {preset.basinName}
                </option>
              ))}
            </select>

            <div className="pt-1 text-xs text-[#64748B] dark:text-[#8E9AB8] leading-relaxed">
              <span className="font-mono-tabular text-[#0284C7] dark:text-[#00BBF9]">
                {activePreset.stationCode}
              </span>
              <span className="mx-1.5" aria-hidden="true">
                ·
              </span>
              <span>{activePolygonAreaHa.toLocaleString("es-CO")} ha</span>
              <span className="mx-1.5" aria-hidden="true">
                ·
              </span>
              <span>{activePreset.elevationRangeM}</span>
            </div>
            <p className="text-xs text-[#334155] dark:text-[#BCC8D1] leading-snug">
              {metrics.municipality}
            </p>
          </div>

          {/* Quick calibration scenarios */}
          <div className="flex flex-col gap-1.5 pt-2 border-t border-[#E2E8F0] dark:border-[#1E2D5A]">
            <span className="text-xs font-medium text-[#334155] dark:text-[#BCC8D1]">
              Simulación rápida de escenario
            </span>
            <div className="grid grid-cols-3 gap-1.5">
              <button
                type="button"
                onClick={() => applyScenarioQuick("normal")}
                className="px-2 py-1.5 rounded text-xs font-medium border border-[#CBD5E1] dark:border-[#1E2D5A] bg-[#F8FAFC] dark:bg-[#0A1128] text-[#059669] dark:text-[#00F5D4] hover:border-[#059669] dark:hover:border-[#00F5D4] transition-colors cursor-pointer whitespace-nowrap"
              >
                Normal
              </button>
              <button
                type="button"
                onClick={() => applyScenarioQuick("preventiva")}
                className="px-2 py-1.5 rounded text-xs font-medium border border-[#CBD5E1] dark:border-[#1E2D5A] bg-[#F8FAFC] dark:bg-[#0A1128] text-[#D97706] dark:text-[#FFB703] hover:border-[#D97706] dark:hover:border-[#FFB703] transition-colors cursor-pointer whitespace-nowrap"
              >
                Preventiva
              </button>
              <button
                type="button"
                onClick={() => applyScenarioQuick("critica")}
                className="px-2 py-1.5 rounded text-xs font-medium border border-[#CBD5E1] dark:border-[#1E2D5A] bg-[#F8FAFC] dark:bg-[#0A1128] text-[#BA1A1A] dark:text-[#F72585] hover:border-[#BA1A1A] dark:hover:border-[#F72585] transition-colors cursor-pointer whitespace-nowrap"
              >
                Crítica
              </button>
            </div>
          </div>

          {/* Sliders & direct numeric inputs */}
          <div className="flex flex-col gap-4 pt-2 border-t border-[#E2E8F0] dark:border-[#1E2D5A]">
            {/* NDWI */}
            <div className="flex flex-col gap-1.5">
              <div className="flex items-center justify-between gap-2">
                <label
                  htmlFor="slider-ndwi"
                  className="text-xs font-medium text-[#334155] dark:text-[#BCC8D1]"
                >
                  Índice de Agua (NDWI)
                </label>
                <input
                  type="number"
                  aria-label="Valor numérico NDWI"
                  min={-1}
                  max={1}
                  step={0.01}
                  value={metrics.ndwi}
                  onChange={(e) => {
                    const v = Number(e.target.value);
                    if (Number.isFinite(v)) {
                      onChangeMetric("ndwi", Math.max(-1, Math.min(1, v)));
                    }
                  }}
                  className="w-20 text-right px-1.5 py-0.5 rounded bg-[#F8FAFC] dark:bg-[#0A1128] border border-[#E2E8F0] dark:border-[#1E2D5A] font-mono-tabular text-xs font-semibold text-[#0284C7] dark:text-[#00BBF9] focus:outline-none focus:border-[#0284C7] dark:focus:border-[#00BBF9]"
                />
              </div>
              <input
                id="slider-ndwi"
                type="range"
                min={-0.6}
                max={0.8}
                step={0.01}
                value={Math.max(-0.6, Math.min(0.8, metrics.ndwi))}
                onChange={(e) => onChangeMetric("ndwi", Number(e.target.value))}
                className="telemetry-slider w-full bg-[#E2E8F0] dark:bg-[#1E2D5A]"
              />
              <div className="flex justify-between text-[11px] font-mono-tabular text-[#64748B] dark:text-[#8E9AB8]">
                <span>-0.60 Seco</span>
                <span>0.00</span>
                <span>+0.80 Saturado</span>
              </div>
            </div>

            {/* NDVI */}
            <div className="flex flex-col gap-1.5">
              <div className="flex items-center justify-between gap-2">
                <label
                  htmlFor="slider-ndvi"
                  className="text-xs font-medium text-[#334155] dark:text-[#BCC8D1]"
                >
                  Vigor Vegetal (NDVI)
                </label>
                <input
                  type="number"
                  aria-label="Valor numérico NDVI"
                  min={-1}
                  max={1}
                  step={0.01}
                  value={metrics.ndvi}
                  onChange={(e) => {
                    const v = Number(e.target.value);
                    if (Number.isFinite(v)) {
                      onChangeMetric("ndvi", Math.max(-1, Math.min(1, v)));
                    }
                  }}
                  className="w-20 text-right px-1.5 py-0.5 rounded bg-[#F8FAFC] dark:bg-[#0A1128] border border-[#E2E8F0] dark:border-[#1E2D5A] font-mono-tabular text-xs font-semibold text-[#059669] dark:text-[#00F5D4] focus:outline-none focus:border-[#0284C7] dark:focus:border-[#00BBF9]"
                />
              </div>
              <input
                id="slider-ndvi"
                type="range"
                min={-0.2}
                max={0.9}
                step={0.01}
                value={Math.max(-0.2, Math.min(0.9, metrics.ndvi))}
                onChange={(e) => onChangeMetric("ndvi", Number(e.target.value))}
                className="telemetry-slider w-full bg-[#E2E8F0] dark:bg-[#1E2D5A]"
              />
              <div className="flex justify-between text-[11px] font-mono-tabular text-[#64748B] dark:text-[#8E9AB8]">
                <span>-0.20 Suelo desnudo</span>
                <span>+0.90 Denso</span>
              </div>
            </div>

            {/* Channel width % */}
            <div className="flex flex-col gap-1.5">
              <div className="flex items-center justify-between gap-2">
                <label
                  htmlFor="slider-width"
                  className="text-xs font-medium text-[#334155] dark:text-[#BCC8D1]"
                >
                  Cambio Ancho del Cauce
                </label>
                <div className="flex items-center gap-1">
                  <input
                    type="number"
                    aria-label="Porcentaje cambio ancho del cauce"
                    min={-50}
                    max={200}
                    step={0.5}
                    value={metrics.channelWidthChangePct}
                    onChange={(e) => {
                      const v = Number(e.target.value);
                      if (Number.isFinite(v)) {
                        onChangeMetric(
                          "channelWidthChangePct",
                          Math.max(-50, Math.min(200, v))
                        );
                      }
                    }}
                    className="w-18 text-right px-1.5 py-0.5 rounded bg-[#F8FAFC] dark:bg-[#0A1128] border border-[#E2E8F0] dark:border-[#1E2D5A] font-mono-tabular text-xs font-semibold text-[#0F172A] dark:text-[#DCE1FF] focus:outline-none focus:border-[#0284C7] dark:focus:border-[#00BBF9]"
                  />
                  <span className="font-mono-tabular text-xs text-[#64748B] dark:text-[#8E9AB8]">
                    %
                  </span>
                </div>
              </div>
              <input
                id="slider-width"
                type="range"
                min={-15}
                max={75}
                step={0.5}
                value={Math.max(-15, Math.min(75, metrics.channelWidthChangePct))}
                onChange={(e) =>
                  onChangeMetric("channelWidthChangePct", Number(e.target.value))
                }
                className="telemetry-slider w-full bg-[#E2E8F0] dark:bg-[#1E2D5A]"
              />
              <div className="flex justify-between text-[11px] font-mono-tabular text-[#64748B] dark:text-[#8E9AB8]">
                <span>-15% Estiaje</span>
                <span>0%</span>
                <span>+75% Desborde</span>
              </div>
            </div>

            {/* Discharge m3/s */}
            <div className="flex flex-col gap-1.5">
              <div className="flex items-center justify-between gap-2">
                <label
                  htmlFor="slider-discharge"
                  className="text-xs font-medium text-[#334155] dark:text-[#BCC8D1]"
                >
                  Predicción de Caudal
                </label>
                <div className="flex items-center gap-1">
                  <input
                    type="number"
                    aria-label="Predicción de caudal en m3/s"
                    min={0}
                    max={20000}
                    step={5}
                    value={metrics.predictedDischargeM3s}
                    onChange={(e) => {
                      const v = Number(e.target.value);
                      if (Number.isFinite(v)) {
                        onChangeMetric(
                          "predictedDischargeM3s",
                          Math.max(0, Math.min(20000, v))
                        );
                      }
                    }}
                    className="w-20 text-right px-1.5 py-0.5 rounded bg-[#F8FAFC] dark:bg-[#0A1128] border border-[#E2E8F0] dark:border-[#1E2D5A] font-mono-tabular text-xs font-semibold text-[#0F172A] dark:text-[#DCE1FF] focus:outline-none focus:border-[#0284C7] dark:focus:border-[#00BBF9]"
                  />
                  <span className="font-mono-tabular text-xs text-[#64748B] dark:text-[#8E9AB8]">
                    m³/s
                  </span>
                </div>
              </div>
              <input
                id="slider-discharge"
                type="range"
                min={10}
                max={4500}
                step={5}
                value={Math.max(10, Math.min(4500, metrics.predictedDischargeM3s))}
                onChange={(e) =>
                  onChangeMetric("predictedDischargeM3s", Number(e.target.value))
                }
                className="telemetry-slider w-full bg-[#E2E8F0] dark:bg-[#1E2D5A]"
              />
              <div className="flex justify-between text-[11px] font-mono-tabular text-[#64748B] dark:text-[#8E9AB8]">
                <span>10 m³/s</span>
                <span>Base: {activePreset.baselineDischargeM3s} m³/s</span>
                <span>4,500 m³/s</span>
              </div>
            </div>
          </div>

          <div className="pt-2 border-t border-[#E2E8F0] dark:border-[#1E2D5A]">
            <button
              type="button"
              onClick={onGenerateReport}
              disabled={isGenerating}
              className="w-full py-2.5 px-4 rounded font-display text-sm font-semibold transition-all duration-150 cursor-pointer disabled:opacity-60 disabled:cursor-not-allowed bg-[#0284C7] hover:bg-[#0EA5E9] text-white dark:bg-[#00BBF9] dark:hover:bg-[#38CCF9] dark:text-[#0A1128]"
            >
              {isGenerating
                ? "Consultando Agente Skyfussion..."
                : "Generar Reporte Hidrológico"}
            </button>
          </div>
        </>
      ) : (
        <div className="flex flex-col gap-3.5">
          {/* File Upload GeoJSON / KML */}
          <div className="flex flex-col gap-1.5">
            <span className="text-xs font-medium text-[#334155] dark:text-[#BCC8D1]">
              Cargar archivo vectorial (.geojson / .kml)
            </span>
            <label className="flex flex-col items-center justify-center gap-1.5 p-3.5 rounded border border-dashed border-[#CBD5E1] dark:border-[#1E2D5A] bg-[#F8FAFC] dark:bg-[#0A1128] hover:border-[#0284C7] dark:hover:border-[#00BBF9] transition-colors cursor-pointer text-center">
              <FileUp className="w-4 h-4 text-[#0284C7] dark:text-[#00BBF9]" />
              <span className="text-xs font-medium text-[#0F172A] dark:text-[#DCE1FF]">
                Seleccionar .geojson, .json o .kml
              </span>
              <span className="text-[11px] text-[#64748B] dark:text-[#8E9AB8]">
                WGS84 (EPSG:4326) · Polygon / MultiPolygon
              </span>
              <input
                type="file"
                accept=".geojson,.json,.kml"
                onChange={handleFileUpload}
                className="sr-only"
              />
            </label>
          </div>

          {/* Draw directly on Leaflet */}
          <button
            type="button"
            onClick={onStartDrawOnMap}
            className="w-full inline-flex items-center justify-center gap-2 py-2 px-3 rounded border border-[#CBD5E1] dark:border-[#1E2D5A] bg-[#F8FAFC] dark:bg-[#0A1128] hover:border-[#0284C7] dark:hover:border-[#00BBF9] text-xs font-medium text-[#0F172A] dark:text-[#DCE1FF] cursor-pointer transition-colors"
          >
            <Pencil className="w-3.5 h-3.5 text-[#0284C7] dark:text-[#00BBF9]" />
            <span>Dibujar polígono directo en mapa Leaflet</span>
          </button>

          {/* Manual coordinates */}
          <div className="flex flex-col gap-1.5 pt-2 border-t border-[#E2E8F0] dark:border-[#1E2D5A]">
            <label
              htmlFor="custom-area-name"
              className="text-xs font-medium text-[#334155] dark:text-[#BCC8D1]"
            >
              Nombre del área de estudio
            </label>
            <input
              id="custom-area-name"
              type="text"
              value={customAreaName}
              onChange={(e) => setCustomAreaName(e.target.value)}
              className="w-full rounded px-2.5 py-1.5 text-xs bg-[#F8FAFC] dark:bg-[#0A1128] border border-[#CBD5E1] dark:border-[#1E2D5A] text-[#0F172A] dark:text-[#DCE1FF] focus:outline-none focus:border-[#0284C7] dark:focus:border-[#00BBF9]"
            />

            <div className="flex items-center justify-between mt-1">
              <label
                htmlFor="manual-coords-input"
                className="text-xs font-medium text-[#334155] dark:text-[#BCC8D1]"
              >
                Vértices manuales (lon, lat)
              </label>
              <button
                type="button"
                onClick={() => setCoordsInput(SAMPLE_COMBEIMA_COORDS)}
                className="text-[11px] text-[#0284C7] dark:text-[#00BBF9] hover:underline cursor-pointer"
              >
                Ejemplo Combeima
              </button>
            </div>
            <textarea
              id="manual-coords-input"
              rows={4}
              value={coordsInput}
              onChange={(e) => setCoordsInput(e.target.value)}
              className="w-full rounded p-2 text-xs font-mono-tabular bg-[#F8FAFC] dark:bg-[#0A1128] border border-[#CBD5E1] dark:border-[#1E2D5A] text-[#0F172A] dark:text-[#DCE1FF] focus:outline-none focus:border-[#0284C7] dark:focus:border-[#00BBF9]"
            />
          </div>

          {geoError && (
            <p className="text-xs text-[#BA1A1A] dark:text-[#F72585]">
              {geoError}
            </p>
          )}
          {geoSuccess && (
            <p className="text-xs text-[#059669] dark:text-[#00F5D4] flex items-center gap-1.5">
              <MapPin className="w-3.5 h-3.5 shrink-0" />
              <span>{geoSuccess}</span>
            </p>
          )}

          <div className="grid grid-cols-2 gap-2 pt-1">
            <button
              type="button"
              onClick={() => handleApplyManualCoords(false)}
              className="py-2 px-3 rounded border border-[#CBD5E1] dark:border-[#1E2D5A] text-xs font-medium text-[#0F172A] dark:text-[#DCE1FF] hover:border-[#0284C7] dark:hover:border-[#00BBF9] cursor-pointer"
            >
              Solo ubicar
            </button>
            <button
              type="button"
              onClick={() => handleApplyManualCoords(true)}
              disabled={isGenerating}
              className="py-2 px-3 rounded font-display text-xs font-semibold bg-[#0284C7] hover:bg-[#0EA5E9] text-white dark:bg-[#00BBF9] dark:hover:bg-[#38CCF9] dark:text-[#0A1128] disabled:opacity-60 cursor-pointer"
            >
              Analizar área
            </button>
          </div>
        </div>
      )}
    </aside>
  );
}
