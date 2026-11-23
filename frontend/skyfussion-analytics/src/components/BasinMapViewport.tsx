import React, { useMemo, useRef, useState } from "react";
import {
  Compass,
  Layers,
  LocateFixed,
  Map as MapIcon,
  SplitSquareHorizontal,
} from "lucide-react";
import {
  AlertLevel,
  BasinMetrics,
  MapEngineMode,
  MapLayer,
  ThemeMode,
  WatershedPreset,
} from "../types/hydrology";
import { ParsedGeoResult } from "../utils/geoParser";
import { LeafletBasinMap } from "./LeafletBasinMap";

interface BasinMapViewportProps {
  preset: WatershedPreset;
  metrics: BasinMetrics;
  activeLayer: MapLayer;
  onChangeLayer: (layer: MapLayer) => void;
  mapEngine: MapEngineMode;
  onChangeMapEngine: (mode: MapEngineMode) => void;
  polygonRing: [number, number][];
  alertLevel?: AlertLevel;
  theme: ThemeMode;
  isDrawing: boolean;
  onToggleDrawing: (drawing: boolean) => void;
  onPolygonCommitted: (parsed: ParsedGeoResult) => void;
}

interface MonitoringNode {
  id: string;
  label: string;
  x: number;
  y: number;
  sector: string;
  elevationM: number;
  ndwiOffset: number;
  ndviOffset: number;
}

const LAYER_OPTIONS: { id: MapLayer; label: string }[] = [
  { id: "composite", label: "Satélite RGB" },
  { id: "ndwi", label: "NDWI Agua" },
  { id: "ndvi", label: "NDVI Cobertura" },
  { id: "channel", label: "Morfología OpenCV" },
  { id: "kmeans", label: "Zonas K-Means" },
];

const EPOCHS = [1969, 1985, 2005, 2016, 2023] as const;

export function BasinMapViewport({
  preset,
  metrics,
  activeLayer,
  onChangeLayer,
  mapEngine,
  onChangeMapEngine,
  polygonRing,
  alertLevel,
  theme,
  isDrawing,
  onToggleDrawing,
  onPolygonCommitted,
}: BasinMapViewportProps) {
  const [selectedNodeId, setSelectedNodeId] = useState<string>("E-02");
  const [selectedEpoch, setSelectedEpoch] = useState<number>(2023);
  const [overlayOpacity, setOverlayOpacity] = useState<number>(0.82);
  const [splitCompare, setSplitCompare] = useState<boolean>(false);
  const [splitPct, setSplitPct] = useState<number>(48);
  const [imageError, setImageError] = useState<boolean>(false);
  const [probe, setProbe] = useState<{
    x: number;
    y: number;
    lat: string;
    lon: string;
    elevationM: number;
    localNdwi: number;
    localNdvi: number;
  } | null>(null);

  const stageRef = useRef<HTMLDivElement | null>(null);
  const isDraggingSplit = useRef<boolean>(false);

  const isCombeimaVariant =
    preset.geometryVariant === "combeima" ||
    preset.geometryVariant === "canyon";

  const nodes: MonitoringNode[] = useMemo(() => {
    if (isCombeimaVariant) {
      return [
        {
          id: "E-01",
          label: "Cabecera Nevado",
          x: 92,
          y: 112,
          sector: "Tramo Alto (Z0)",
          elevationM: 2840,
          ndwiOffset: -0.06,
          ndviOffset: 0.11,
        },
        {
          id: "E-02",
          label: "Estación Poblado",
          x: 412,
          y: 252,
          sector: "Corredor Urbano (Z1)",
          elevationM: 1480,
          ndwiOffset: 0.04,
          ndviOffset: -0.07,
        },
        {
          id: "E-03",
          label: "Bocatoma Ibagué",
          x: 690,
          y: 382,
          sector: "Descarga Baja (Z2)",
          elevationM: 940,
          ndwiOffset: 0.1,
          ndviOffset: -0.09,
        },
      ];
    }
    return [
      {
        id: "E-01",
        label: "Cabecera Meandro",
        x: 155,
        y: 122,
        sector: "Tramo Alto (Z0)",
        elevationM: 210,
        ndwiOffset: -0.04,
        ndviOffset: 0.08,
      },
      {
        id: "E-02",
        label: "Estación Central",
        x: 382,
        y: 274,
        sector: "Llanura Media (Z2)",
        elevationM: 112,
        ndwiOffset: 0.05,
        ndviOffset: -0.04,
      },
      {
        id: "E-03",
        label: "Salida Aluvial",
        x: 682,
        y: 236,
        sector: "Madrevieja Baja (Z2)",
        elevationM: 64,
        ndwiOffset: 0.12,
        ndviOffset: -0.08,
      },
    ];
  }, [isCombeimaVariant]);

  const geometry = useMemo(() => {
    if (isCombeimaVariant) {
      return {
        // Traces the winding turquoise river in combeima_river_satellite_1795411238077.jpg
        main: "M 0 156 Q 55 142 88 112 Q 130 142 158 205 Q 202 268 258 232 Q 315 208 386 178 Q 422 258 478 304 Q 535 282 585 250 Q 645 278 688 388 Q 748 415 800 282",
        braid:
          "M 235 245 Q 292 248 355 212 Q 392 195 415 218 M 560 264 Q 625 225 675 305",
        tributaryA: "M 135 12 Q 165 92 215 178 L 258 232",
        tributaryB: "M 690 25 Q 675 140 612 225 L 585 250",
        transects: [
          { x1: 76, y1: 94, x2: 102, y2: 128, label: "34 m" },
          { x1: 238, y1: 212, x2: 266, y2: 256, label: "58 m" },
          { x1: 398, y1: 212, x2: 432, y2: 266, label: "49 m" },
          { x1: 570, y1: 228, x2: 604, y2: 274, label: "44 m" },
          { x1: 672, y1: 356, x2: 710, y2: 402, label: "62 m" },
        ],
        urbanZone: "M 340 235 L 445 245 L 468 335 L 355 340 Z",
        vegZoneA: "M 35 190 L 210 215 L 250 385 L 25 415 Z",
        vegZoneB: "M 475 30 L 765 35 L 775 210 L 495 195 Z",
      };
    }
    return {
      // Traces the sweeping meander river in alluvial_basin_satellite_1795411236249.jpg
      main: "M 0 245 Q 85 175 155 120 Q 225 148 295 255 Q 355 310 432 238 Q 492 162 530 120 Q 565 182 565 285 Q 620 220 685 235 Q 745 285 800 315",
      braid:
        "M 118 238 Q 165 335 268 308 Q 345 370 432 332 M 345 148 Q 418 195 478 135",
      tributaryA: "M 255 15 Q 285 95 310 175 L 295 255",
      tributaryB: "M 515 435 Q 545 360 565 285",
      transects: [
        { x1: 138, y1: 96, x2: 174, y2: 144, label: "112 m" },
        { x1: 278, y1: 228, x2: 318, y2: 282, label: "145 m" },
        { x1: 508, y1: 104, x2: 552, y2: 140, label: "128 m" },
        { x1: 542, y1: 268, x2: 590, y2: 304, label: "136 m" },
        { x1: 668, y1: 208, x2: 706, y2: 264, label: "152 m" },
      ],
      urbanZone: "M 295 32 L 420 35 L 430 118 L 285 112 Z",
      vegZoneA: "M 25 275 L 250 325 L 245 430 L 20 430 Z",
      vegZoneB: "M 605 28 L 785 32 L 785 185 L 620 170 Z",
    };
  }, [isCombeimaVariant]);

  const epochFactor = (selectedEpoch - 1969) / (2023 - 1969); // 0 in 1969 -> 1 in 2023
  const effectiveWidthPct = metrics.channelWidthChangePct * (0.25 + 0.75 * epochFactor);

  const baseChannelPx = isCombeimaVariant ? 10 : 14;
  const activeChannelPx = Math.max(
    6,
    baseChannelPx * (1 + effectiveWidthPct / 100)
  );
  const erosionMarginPx = activeChannelPx + Math.max(4, Math.abs(effectiveWidthPct) * 0.45);

  const ndwiAlpha = Math.min(0.88, Math.max(0.18, (metrics.ndwi + 0.6) / 1.4));
  const ndviAlpha = Math.min(0.85, Math.max(0.18, (metrics.ndvi + 0.2) / 1.1));

  const isErosionAlert =
    metrics.channelWidthChangePct >= 22 || metrics.ndwi >= 0.35;

  const selectedNode = nodes.find((n) => n.id === selectedNodeId) ?? nodes[1];

  // Satellite CSS color grading per spectral mode
  const satelliteFilterClass = useMemo(() => {
    switch (activeLayer) {
      case "ndwi":
        return "saturate-150 hue-rotate-[155deg] contrast-115 brightness-90";
      case "ndvi":
        return "saturate-[1.65] contrast-115 brightness-95";
      case "channel":
        return "grayscale contrast-125 brightness-75";
      case "kmeans":
        return "saturate-75 contrast-110 brightness-90";
      case "composite":
      default:
        return "saturate-110 contrast-105 brightness-95";
    }
  }, [activeLayer]);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!stageRef.current) return;
    const rect = stageRef.current.getBoundingClientRect();
    const normX = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
    const normY = Math.max(0, Math.min(1, (e.clientY - rect.top) / rect.height));

    if (isDraggingSplit.current && splitCompare) {
      setSplitPct(Math.round(Math.max(10, Math.min(90, normX * 100))));
    }

    const svgX = Math.round(normX * 800);
    const svgY = Math.round(normY * 450);

    const [latMin, latMax] = preset.latBounds;
    const [lonMin, lonMax] = preset.lonBounds;
    const lat = (latMax - normY * (latMax - latMin)).toFixed(4);
    const lon = (lonMin + normX * (lonMax - lonMin)).toFixed(4);
    const elev = isCombeimaVariant
      ? Math.round(2950 - normX * 1850 + Math.sin(normY * 4) * 140)
      : Math.round(180 - normX * 95 + Math.cos(normY * 3) * 24);
    const wave = Math.sin(normX * 6) * 0.06 + Math.cos(normY * 5) * 0.04;

    setProbe({
      x: svgX,
      y: svgY,
      lat: `${lat}° N`,
      lon: `${lon}° O`,
      elevationM: elev,
      localNdwi: Math.max(-1, Math.min(1, metrics.ndwi + wave)),
      localNdvi: Math.max(-1, Math.min(1, metrics.ndvi - wave * 0.8)),
    });
  };

  // Water level height in hydraulic cross-section (0..1)
  const dischargeFillRatio = Math.min(
    0.94,
    Math.max(
      0.2,
      metrics.predictedDischargeM3s / (preset.baselineDischargeM3s * 2.2)
    )
  );

  const renderVectorOverlay = (isHistorical1969: boolean) => (
    <svg
      viewBox="0 0 800 450"
      preserveAspectRatio="xMidYMid slice"
      className="w-full h-full block pointer-events-none select-none"
    >
      <defs>
        <pattern
          id={isHistorical1969 ? "satGrid1969" : "satGrid2023"}
          width="80"
          height="80"
          patternUnits="userSpaceOnUse"
        >
          <path
            d="M 80 0 L 0 0 0 80"
            fill="none"
            stroke="#FFFFFF"
            strokeWidth="0.45"
            strokeOpacity="0.22"
          />
        </pattern>
      </defs>

      {/* Coordinate Sub-Grid */}
      <rect
        width="800"
        height="450"
        fill={`url(#${isHistorical1969 ? "satGrid1969" : "satGrid2023"})`}
      />

      {/* K-Means Cluster Zones (when kmeans or composite subtle) */}
      {!isHistorical1969 && activeLayer === "kmeans" && (
        <g opacity={overlayOpacity * 0.85}>
          <path
            d={geometry.vegZoneA}
            fill="#10B981"
            fillOpacity="0.28"
            stroke="#00F5D4"
            strokeWidth="1.5"
            strokeDasharray="4 3"
          />
          <path
            d={geometry.vegZoneB}
            fill="#10B981"
            fillOpacity="0.28"
            stroke="#00F5D4"
            strokeWidth="1.5"
            strokeDasharray="4 3"
          />
          <path
            d={geometry.urbanZone}
            fill="#FFB703"
            fillOpacity="0.34"
            stroke="#FFB703"
            strokeWidth="1.8"
          />
          <text
            x="60"
            y="365"
            className="text-[11px] font-mono-tabular font-semibold fill-white"
          >
            Z0 · Vegetación mixta (58%)
          </text>
          <text
            x={isCombeimaVariant ? 348 : 296}
            y={isCombeimaVariant ? 318 : 74}
            className="text-[11px] font-mono-tabular font-semibold fill-[#FEF3C7]"
          >
            Z1 · Suelo desnudo / urbano
          </text>
        </g>
      )}

      {/* Spectral NDVI tint */}
      {!isHistorical1969 && activeLayer === "ndvi" && (
        <g opacity={overlayOpacity * 0.72}>
          <rect
            width="800"
            height="450"
            fill={metrics.ndvi >= 0.45 ? "#059669" : "#D97706"}
            fillOpacity={0.18 + ndviAlpha * 0.25}
          />
        </g>
      )}

      {/* Spectral NDWI water highlight */}
      {!isHistorical1969 && (activeLayer === "ndwi" || activeLayer === "kmeans") && (
        <g opacity={overlayOpacity}>
          <path
            d={geometry.main}
            fill="none"
            stroke="#00BBF9"
            strokeWidth={activeChannelPx + 14}
            strokeLinecap="round"
            strokeLinejoin="round"
            opacity={0.22 + ndwiAlpha * 0.38}
          />
          <path
            d={geometry.braid}
            fill="none"
            stroke="#38BDF8"
            strokeWidth={8}
            strokeLinecap="round"
            opacity={0.25 + ndwiAlpha * 0.35}
          />
        </g>
      )}

      {/* Tributaries */}
      <path
        d={geometry.tributaryA}
        fill="none"
        stroke="#38BDF8"
        strokeWidth="2"
        strokeLinecap="round"
        opacity={isHistorical1969 ? 0.5 : 0.75 * overlayOpacity}
      />
      <path
        d={geometry.tributaryB}
        fill="none"
        stroke="#38BDF8"
        strokeWidth="2"
        strokeLinecap="round"
        opacity={isHistorical1969 ? 0.5 : 0.75 * overlayOpacity}
      />

      {/* OpenCV Erosion / Flood Expansion Envelope (2023 or active epoch) */}
      {!isHistorical1969 && (
        <path
          d={geometry.main}
          fill="none"
          stroke={isErosionAlert ? "#F72585" : "#00F5D4"}
          strokeWidth={erosionMarginPx}
          strokeLinecap="round"
          strokeLinejoin="round"
          opacity={
            activeLayer === "channel"
              ? 0.42 * overlayOpacity
              : metrics.channelWidthChangePct > 10
                ? 0.28 * overlayOpacity
                : 0.14 * overlayOpacity
          }
        />
      )}

      {/* Historical 1969 Baseline Channel Contours */}
      <path
        d={geometry.main}
        fill="none"
        stroke="#FFFFFF"
        strokeWidth={baseChannelPx + 2}
        strokeDasharray="4 4"
        strokeLinecap="round"
        opacity={isHistorical1969 ? 0.85 : activeLayer === "channel" ? 0.75 : 0.38}
      />

      {/* Canny Riverbank Edges + Active Water Mask */}
      {!isHistorical1969 && (
        <>
          <path
            d={geometry.main}
            fill="none"
            stroke={activeLayer === "channel" ? "#00BBF9" : "#38BDF8"}
            strokeWidth={activeChannelPx}
            strokeLinecap="round"
            strokeLinejoin="round"
            opacity={
              activeLayer === "composite"
                ? 0.35 * overlayOpacity
                : 0.72 * overlayOpacity
            }
          />
          {/* Braided sub-channels */}
          <path
            d={geometry.braid}
            fill="none"
            stroke="#00BBF9"
            strokeWidth={3.5}
            strokeLinecap="round"
            opacity={0.55 * overlayOpacity}
          />
        </>
      )}

      {/* Skeleton Medial Axis + Perpendicular Width Transects in Morphology / Composite */}
      {!isHistorical1969 &&
        (activeLayer === "channel" || activeLayer === "composite") && (
          <g opacity={activeLayer === "channel" ? 0.95 : 0.72}>
            <path
              d={geometry.main}
              fill="none"
              stroke="#00F5D4"
              strokeWidth="1.5"
              strokeDasharray="6 4"
            />
            {activeLayer === "channel" &&
              geometry.transects.map((t, idx) => {
                const dynamicMeters = Math.round(
                  parseInt(t.label, 10) * (1 + effectiveWidthPct / 100)
                );
                return (
                  <g key={idx}>
                    <line
                      x1={t.x1}
                      y1={t.y1}
                      x2={t.x2}
                      y2={t.y2}
                      stroke="#FFB703"
                      strokeWidth="1.8"
                    />
                    <text
                      x={t.x2 + 4}
                      y={t.y2 + 3}
                      className="text-[10px] font-mono-tabular font-semibold fill-[#FEF3C7]"
                      style={{ paintOrder: "stroke", stroke: "#060D24", strokeWidth: "2.5px" }}
                    >
                      {dynamicMeters} m
                    </text>
                  </g>
                );
              })}
          </g>
        )}

      {/* Monitoring Nodes */}
      {nodes.map((node) => {
        const isSelected = node.id === selectedNodeId;
        return (
          <g key={node.id} transform={`translate(${node.x}, ${node.y})`}>
            <circle
              r={isSelected ? 14 : 10}
              fill="#060D24"
              fillOpacity="0.55"
              stroke={isSelected ? "#00F5D4" : "#00BBF9"}
              strokeWidth={isSelected ? 2 : 1.3}
            />
            <circle r="3.5" fill={isSelected ? "#00F5D4" : "#00BBF9"} />
            <text
              x="14"
              y="-6"
              className="text-[10px] font-mono-tabular font-semibold fill-white"
              style={{
                paintOrder: "stroke",
                stroke: "#060D24",
                strokeWidth: "3px",
              }}
            >
              {node.id}
            </text>
          </g>
        );
      })}
    </svg>
  );

  return (
    <section className="flex-1 min-w-0 flex flex-col bg-[#FFFFFF] dark:bg-[#101A36] border border-[#E2E8F0] dark:border-[#1E2D5A] rounded-lg overflow-hidden">
      {/* Header & Map Engine + Layer Switcher */}
      <div className="flex flex-wrap items-center justify-between gap-2.5 px-4 py-3 border-b border-[#E2E8F0] dark:border-[#1E2D5A]">
        <div className="flex items-center gap-2 min-w-0">
          {mapEngine === "leaflet" ? (
            <MapIcon
              className="w-4 h-4 text-[#0284C7] dark:text-[#00BBF9] shrink-0"
              aria-hidden="true"
            />
          ) : (
            <Layers
              className="w-4 h-4 text-[#0284C7] dark:text-[#00BBF9] shrink-0"
              aria-hidden="true"
            />
          )}
          <h2 className="font-display text-sm font-semibold text-[#0F172A] dark:text-[#DCE1FF] truncate">
            {mapEngine === "leaflet"
              ? "Mapa Geográfico Leaflet"
              : "Visor Espectral Sentinel-2"}
          </h2>
          <span className="hidden xl:inline text-xs font-mono-tabular text-[#64748B] dark:text-[#8E9AB8]">
            · {metrics.coordinates}
          </span>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Primary Engine Switch: Leaflet GIS vs Sentinel-2 OpenCV */}
          <div
            role="group"
            aria-label="Modo del visor cartográfico"
            className="flex items-center gap-1 p-1 rounded bg-[#F1F5F9] dark:bg-[#0A1128] border border-[#E2E8F0] dark:border-[#1E2D5A]"
          >
            <button
              type="button"
              onClick={() => onChangeMapEngine("leaflet")}
              className={`px-2.5 py-1 rounded text-xs font-medium whitespace-nowrap cursor-pointer transition-colors ${
                mapEngine === "leaflet"
                  ? "bg-[#0284C7] dark:bg-[#00BBF9] text-white dark:text-[#0A1128] font-semibold"
                  : "text-[#64748B] dark:text-[#8E9AB8] hover:text-[#0F172A] dark:hover:text-[#DCE1FF]"
              }`}
            >
              Mapa Leaflet
            </button>
            <button
              type="button"
              onClick={() => onChangeMapEngine("spectral")}
              className={`px-2.5 py-1 rounded text-xs font-medium whitespace-nowrap cursor-pointer transition-colors ${
                mapEngine === "spectral"
                  ? "bg-[#0284C7] dark:bg-[#00BBF9] text-white dark:text-[#0A1128] font-semibold"
                  : "text-[#64748B] dark:text-[#8E9AB8] hover:text-[#0F172A] dark:hover:text-[#DCE1FF]"
              }`}
            >
              Espectral OpenCV
            </button>
          </div>
        </div>
      </div>

      {/* Spectral Layer & Epoch Controls (visible in spectral mode) */}
      {mapEngine === "spectral" && (
        <div className="flex flex-wrap items-center justify-between gap-2.5 px-4 py-2 border-b border-[#E2E8F0] dark:border-[#1E2D5A] bg-[#F8FAFC] dark:bg-[#0E1630] text-xs">
          <div
            role="group"
            aria-label="Capas espectrales del visor"
            className="flex items-center gap-1 overflow-x-auto max-w-full"
          >
            {LAYER_OPTIONS.map((layer) => {
              const active = activeLayer === layer.id;
              return (
                <button
                  key={layer.id}
                  type="button"
                  onClick={() => onChangeLayer(layer.id)}
                  className={`px-2 py-1 rounded text-[11px] font-medium whitespace-nowrap shrink-0 transition-colors cursor-pointer ${
                    active
                      ? "bg-[#FFFFFF] dark:bg-[#181E36] text-[#0284C7] dark:text-[#00F5D4] border border-[#CBD5E1] dark:border-[#00F5D4]/60"
                      : "text-[#64748B] dark:text-[#8E9AB8] hover:text-[#0F172A] dark:hover:text-[#DCE1FF] border border-transparent"
                  }`}
                >
                  {layer.label}
                </button>
              );
            })}
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <div className="flex items-center gap-1">
              {EPOCHS.map((yr) => (
                <button
                  key={yr}
                  type="button"
                  onClick={() => setSelectedEpoch(yr)}
                  className={`px-1.5 py-0.5 rounded font-mono-tabular text-[11px] cursor-pointer transition-colors ${
                    selectedEpoch === yr
                      ? "bg-[#0284C7] dark:bg-[#00BBF9] text-white dark:text-[#0A1128] font-semibold"
                      : "text-[#334155] dark:text-[#BCC8D1] hover:bg-[#E2E8F0] dark:hover:bg-[#181E36]"
                  }`}
                >
                  {yr}
                </button>
              ))}
            </div>

            <input
              type="range"
              aria-label="Opacidad capa vectorial"
              min={0.25}
              max={1}
              step={0.05}
              value={overlayOpacity}
              onChange={(e) => setOverlayOpacity(Number(e.target.value))}
              className="telemetry-slider w-16 bg-[#CBD5E1] dark:bg-[#1E2D5A] hidden sm:block"
            />

            <button
              type="button"
              onClick={() => setSplitCompare((prev) => !prev)}
              className={`inline-flex items-center gap-1 px-2 py-1 rounded text-[11px] font-medium border cursor-pointer transition-colors whitespace-nowrap ${
                splitCompare
                  ? "border-[#0284C7] dark:border-[#00F5D4] bg-[#0284C7]/10 dark:bg-[#00F5D4]/12 text-[#0284C7] dark:text-[#00F5D4]"
                  : "border-[#CBD5E1] dark:border-[#1E2D5A] text-[#334155] dark:text-[#BCC8D1] hover:border-[#0284C7] dark:hover:border-[#00BBF9]"
              }`}
            >
              <SplitSquareHorizontal className="w-3.5 h-3.5" aria-hidden="true" />
              <span>1969 | {selectedEpoch}</span>
            </button>
          </div>
        </div>
      )}

      {mapEngine === "leaflet" ? (
        <LeafletBasinMap
          metrics={metrics}
          polygonRing={polygonRing}
          alertLevel={alertLevel}
          theme={theme}
          isDrawing={isDrawing}
          onToggleDrawing={onToggleDrawing}
          onPolygonCommitted={onPolygonCommitted}
        />
      ) : (
        <>

      {/* Satellite + OpenCV Vector Stage */}
      <div
        ref={stageRef}
        onMouseMove={handleMouseMove}
        onMouseUp={() => {
          isDraggingSplit.current = false;
        }}
        onMouseLeave={() => {
          isDraggingSplit.current = false;
          setProbe(null);
        }}
        className="relative flex-1 min-h-[360px] lg:min-h-[430px] bg-[#060D24] overflow-hidden cursor-crosshair select-none"
      >
        {/* Active 2023 / Selected Spectral Layer */}
        <div className="absolute inset-0">
          {!imageError ? (
            <img
              src={preset.satelliteImage}
              alt={`Imagen satelital Sentinel-2 de ${metrics.basinName}`}
              referrerPolicy="no-referrer"
              onError={() => setImageError(true)}
              className={`w-full h-full object-cover transition-all duration-200 ${satelliteFilterClass}`}
            />
          ) : (
            <div className="w-full h-full bg-gradient-to-br from-[#0B1229] via-[#14284B] to-[#0A1F2C]" />
          )}
          <div className="absolute inset-0 bg-[#060D24]/18 pointer-events-none" />
          <div className="absolute inset-0">{renderVectorOverlay(false)}</div>
        </div>

        {/* Historical 1969 Left Curtain (when splitCompare enabled) */}
        {splitCompare && (
          <div
            className="absolute inset-0 pointer-events-none"
            style={{ clipPath: `inset(0 ${100 - splitPct}% 0 0)` }}
          >
            {!imageError ? (
              <img
                src={preset.satelliteImage}
                alt={`Referencia histórica 1969 de ${metrics.basinName}`}
                referrerPolicy="no-referrer"
                className="w-full h-full object-cover grayscale contrast-125 sepia-[0.22] brightness-85"
              />
            ) : (
              <div className="w-full h-full bg-[#1C2438]" />
            )}
            <div className="absolute inset-0">{renderVectorOverlay(true)}</div>
            <div className="absolute bottom-3 left-3 px-2 py-1 rounded bg-[#060D24]/85 border border-white/20 text-[11px] font-mono-tabular text-white">
              Línea base 1969
            </div>
          </div>
        )}

        {/* Draggable Split Handle */}
        {splitCompare && (
          <div
            role="slider"
            aria-label="Deslizador comparativo 1969 vs actual"
            aria-valuemin={10}
            aria-valuemax={90}
            aria-valuenow={splitPct}
            tabIndex={0}
            onMouseDown={() => {
              isDraggingSplit.current = true;
            }}
            onKeyDown={(e) => {
              if (e.key === "ArrowLeft") setSplitPct((p) => Math.max(10, p - 4));
              if (e.key === "ArrowRight") setSplitPct((p) => Math.min(90, p + 4));
            }}
            style={{ left: `${splitPct}%` }}
            className="absolute inset-y-0 w-0.5 bg-[#00F5D4] cursor-ew-resize z-20"
          >
            <div className="absolute top-1/2 -translate-x-1/2 -translate-y-1/2 w-7 h-7 rounded-full bg-[#0A1128]/95 border border-[#00F5D4] flex items-center justify-center text-[#00F5D4] shadow-md">
              <SplitSquareHorizontal className="w-3.5 h-3.5" aria-hidden="true" />
            </div>
          </div>
        )}

        {/* Clickable Station Hit Targets */}
        <svg
          viewBox="0 0 800 450"
          preserveAspectRatio="xMidYMid slice"
          className="absolute inset-0 w-full h-full pointer-events-none"
        >
          {nodes.map((node) => (
            <circle
              key={node.id}
              cx={node.x}
              cy={node.y}
              r={18}
              fill="transparent"
              className="pointer-events-auto cursor-pointer"
              onClick={() => setSelectedNodeId(node.id)}
            />
          ))}

          {/* Live Crosshair Reticle */}
          {probe && (
            <g pointerEvents="none">
              <line
                x1={probe.x}
                y1="0"
                x2={probe.x}
                y2="450"
                stroke="#00F5D4"
                strokeWidth="0.75"
                strokeDasharray="3 3"
                opacity="0.75"
              />
              <line
                x1="0"
                y1={probe.y}
                x2="800"
                y2={probe.y}
                stroke="#00F5D4"
                strokeWidth="0.75"
                strokeDasharray="3 3"
                opacity="0.75"
              />
              <circle
                cx={probe.x}
                cy={probe.y}
                r="5"
                fill="none"
                stroke="#00F5D4"
                strokeWidth="1.4"
              />
            </g>
          )}
        </svg>

        {/* Top-Left HUD: Active Monitoring Station */}
        <div className="absolute top-3 left-3 max-w-[260px] px-3 py-2 rounded bg-[#0A1128]/82 backdrop-blur-md border border-[#00BBF9]/30 text-[#DCE1FF] pointer-events-none z-10">
          <div className="flex items-center gap-1.5 text-[11px] font-mono-tabular text-[#00BBF9]">
            <LocateFixed className="w-3.5 h-3.5 shrink-0" aria-hidden="true" />
            <span>
              {selectedNode.id} · {selectedNode.sector}
            </span>
          </div>
          <p className="text-xs font-semibold text-white mt-0.5">
            {selectedNode.label} · {selectedNode.elevationM.toLocaleString("es-CO")} msnm
          </p>
          <div className="flex items-center gap-3 mt-1 text-[11px] font-mono-tabular text-[#BCC8D1]">
            <span>
              NDWI:{" "}
              {Math.max(-1, Math.min(1, metrics.ndwi + selectedNode.ndwiOffset)).toFixed(2)}
            </span>
            <span>
              NDVI:{" "}
              {Math.max(-1, Math.min(1, metrics.ndvi + selectedNode.ndviOffset)).toFixed(2)}
            </span>
          </div>
        </div>

        {/* Top-Right HUD: Coordinate & Elevation Probe */}
        <div className="absolute top-3 right-3 px-3 py-2 rounded bg-[#0A1128]/82 backdrop-blur-md border border-[#00BBF9]/30 text-[#DCE1FF] pointer-events-none z-10">
          <div className="flex items-center gap-1.5 text-[11px] font-mono-tabular text-[#DCE1FF]">
            <Compass className="w-3.5 h-3.5 text-[#00BBF9]" aria-hidden="true" />
            <span>
              {probe
                ? `${probe.lat} · ${probe.lon} · ${probe.elevationM} m`
                : "Sonda WGS84 · Mueve el cursor"}
            </span>
          </div>
          {probe && (
            <div className="flex items-center gap-3 mt-1 text-[11px] font-mono-tabular text-[#BCC8D1]">
              <span>NDWI: {probe.localNdwi.toFixed(2)}</span>
              <span>NDVI: {probe.localNdvi.toFixed(2)}</span>
            </div>
          )}
        </div>

        {/* Bottom-Right Compact Hydraulic Cross-Section Profile */}
        <div className="hidden sm:flex flex-col gap-1 absolute bottom-3 right-3 w-48 px-2.5 py-2 rounded bg-[#0A1128]/85 backdrop-blur-md border border-[#1E2D5A] text-[#DCE1FF] pointer-events-none z-10">
          <div className="flex items-center justify-between text-[10px] font-mono-tabular text-[#8E9AB8]">
            <span>SECCIÓN TRANSVERSAL</span>
            <span className="text-[#00BBF9]">
              {metrics.predictedDischargeM3s} m³/s
            </span>
          </div>
          <svg viewBox="0 0 160 44" className="w-full h-9">
            {/* Water fill */}
            <polygon
              points={`${22 - dischargeFillRatio * 10},${40 - dischargeFillRatio * 28} ${138 + dischargeFillRatio * 10},${40 - dischargeFillRatio * 28} 122,38 38,38`}
              fill={isErosionAlert ? "#F72585" : "#00BBF9"}
              fillOpacity="0.38"
            />
            {/* Water surface */}
            <line
              x1={20 - dischargeFillRatio * 10}
              y1={40 - dischargeFillRatio * 28}
              x2={140 + dischargeFillRatio * 10}
              y2={40 - dischargeFillRatio * 28}
              stroke={isErosionAlert ? "#F72585" : "#00F5D4"}
              strokeWidth="1.5"
            />
            {/* Riverbed topography */}
            <polyline
              points="4,8 28,22 38,38 122,38 132,22 156,8"
              fill="none"
              stroke="#94A3B8"
              strokeWidth="1.6"
            />
          </svg>
        </div>
      </div>
        </>
      )}

      {/* Calibrated Bottom Legend */}
      <div className="px-4 py-2.5 border-t border-[#E2E8F0] dark:border-[#1E2D5A] bg-[#F8FAFC] dark:bg-[#141A32] flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex flex-wrap items-center gap-4 text-[#334155] dark:text-[#BCC8D1]">
          <span className="inline-flex items-center gap-1.5">
            <span className="w-3 h-1.5 rounded-xs bg-[#00BBF9]" aria-hidden="true" />
            <span>Lámina de agua (NDWI)</span>
          </span>
          <span className="inline-flex items-center gap-1.5">
            <span className="w-3 h-1.5 rounded-xs bg-[#00F5D4]" aria-hidden="true" />
            <span>Esqueleto OpenCV</span>
          </span>
          <span className="inline-flex items-center gap-1.5">
            <span
              className={`w-3 h-1.5 rounded-xs ${
                isErosionAlert ? "bg-[#F72585]" : "bg-[#FFB703]"
              }`}
              aria-hidden="true"
            />
            <span>
              Margen erosión / expansión ({metrics.channelWidthChangePct >= 0 ? "+" : ""}
              {metrics.channelWidthChangePct.toFixed(1)}%)
            </span>
          </span>
        </div>

        <div className="font-mono-tabular text-[11px] text-[#64748B] dark:text-[#8E9AB8]">
          Época {selectedEpoch} · Caudal:{" "}
          <strong className="text-[#0F172A] dark:text-[#DCE1FF]">
            {metrics.predictedDischargeM3s.toLocaleString("es-CO")} m³/s
          </strong>
        </div>
      </div>
    </section>
  );
}
