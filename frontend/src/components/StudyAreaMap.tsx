import React, { useEffect, useRef, useState } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import {
  Layers,
  MapPin,
  Upload,
  Compass,
  Sliders,
  Eye,
  CheckCircle,
  AlertCircle,
  Maximize2,
} from "lucide-react";
import { ActiveMapLayer, AlertLevel, WatershedPreset } from "../types/hydrology";
import { COMBEIMA_PRESETS } from "../data/watersheds";
import {
  buildParsedResult,
  computePolygonAreaHa,
  createCirclePolygon,
  parseGeoJsonText,
  parseKmlText,
  ParsedGeoResult,
} from "../utils/geoParser";

interface StudyAreaMapProps {
  currentPolygon: [number, number][]; // [lon, lat][]
  alertLevel: AlertLevel;
  activeLayer: ActiveMapLayer;
  onLayerChange: (layer: ActiveMapLayer) => void;
  onAreaChanged: (parsed: ParsedGeoResult) => void;
}

export function StudyAreaMap({
  currentPolygon,
  alertLevel,
  activeLayer,
  onLayerChange,
  onAreaChanged,
}: StudyAreaMapProps) {
  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<L.Map | null>(null);
  const polygonLayerRef = useRef<L.Polygon | null>(null);
  const overlaysGroupRef = useRef<L.LayerGroup | null>(null);

  // Modo de definición de área
  const [definitionMode, setDefinitionMode] = useState<"presets" | "manual" | "file">("presets");
  const [selectedPresetId, setSelectedPresetId] = useState<string>("combeima-total");

  // Entrada manual
  const [manualLat, setManualLat] = useState<string>("4.4810");
  const [manualLon, setManualLon] = useState<string>("-75.1995");
  const [manualRadiusKm, setManualRadiusKm] = useState<string>("4.0");

  // Subida de archivos
  const [fileError, setFileError] = useState<string | null>(null);
  const [uploadedFileName, setUploadedFileName] = useState<string | null>(null);

  // Inicializar mapa Leaflet centrado en el Río Combeima
  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) return;

    const map = L.map(mapContainerRef.current, {
      center: [4.481, -75.1995],
      zoom: 12,
      zoomControl: false,
    });

    L.control.zoom({ position: "bottomright" }).addTo(map);

    // Capa satelital de fondo
    L.tileLayer(
      "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
      {
        attribution: "Esri World Imagery",
        maxZoom: 18,
      }
    ).addTo(map);

    const overlays = L.layerGroup().addTo(map);
    overlaysGroupRef.current = overlays;
    mapRef.current = map;

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // Actualizar el polígono principal en el mapa
  useEffect(() => {
    const map = mapRef.current;
    if (!map || currentPolygon.length < 3) return;

    if (polygonLayerRef.current) {
      map.removeLayer(polygonLayerRef.current);
    }

    // Convertir de [lon, lat] a [lat, lon] para Leaflet
    const latLngs = currentPolygon.map(([lon, lat]) => [lat, lon] as [number, number]);

    const strokeColor =
      alertLevel === "CRITICA"
        ? "#ff3864"
        : alertLevel === "PREVENTIVA"
        ? "#ffd166"
        : "#00f5d4";

    const polygon = L.polygon(latLngs, {
      color: strokeColor,
      weight: 2.5,
      opacity: 0.9,
      fillColor: strokeColor,
      fillOpacity: 0.15,
      dashArray: undefined,
    }).addTo(map);

    polygonLayerRef.current = polygon;

    // Ajustar bounds si el polígono es válido
    try {
      const bounds = polygon.getBounds();
      if (bounds.isValid()) {
        map.fitBounds(bounds, { padding: [35, 35], maxZoom: 14 });
      }
    } catch {
      // Ignorar bounds no inicializados
    }
  }, [currentPolygon, alertLevel]);

  // Actualizar capas visuales simuladas (NDWI, NDVI, Morfología)
  useEffect(() => {
    const map = mapRef.current;
    const group = overlaysGroupRef.current;
    if (!map || !group) return;

    group.clearLayers();
    if (activeLayer === "none") return;

    if (activeLayer === "ndwi") {
      // Capa de cuerpos hídricos y humedad (Cian brillante)
      const riverWaterCoords: [number, number][] = [
        [4.542, -75.310],
        [4.520, -75.285],
        [4.495, -75.255],
        [4.470, -75.220],
        [4.445, -75.185],
        [4.425, -75.155],
      ];
      L.polyline(riverWaterCoords, {
        color: "#00bbf9",
        weight: 6,
        opacity: 0.85,
      }).addTo(group);

      // Lagunas de alta montaña / zonas de alta humedad
      L.circle([4.535, -75.295], {
        radius: 450,
        color: "#00bbf9",
        fillColor: "#00bbf9",
        fillOpacity: 0.45,
        weight: 2,
      }).addTo(group);
      L.circle([4.485, -75.240], {
        radius: 380,
        color: "#00bbf9",
        fillColor: "#00bbf9",
        fillOpacity: 0.4,
        weight: 2,
      }).addTo(group);
    } else if (activeLayer === "ndvi") {
      // Capa de vegetación y biomasa (Verde neón translúcido)
      const forestPolys: [number, number][][] = [
        [
          [4.550, -75.330],
          [4.530, -75.290],
          [4.510, -75.320],
          [4.535, -75.350],
        ],
        [
          [4.500, -75.280],
          [4.475, -75.245],
          [4.460, -75.275],
          [4.485, -75.305],
        ],
      ];
      forestPolys.forEach((coords) => {
        L.polygon(coords, {
          color: "#00f5d4",
          fillColor: "#00f5d4",
          fillOpacity: 0.3,
          weight: 1.5,
        }).addTo(group);
      });
    } else if (activeLayer === "morphology") {
      // Morfología de cauce: histórico 1969 vs 2023 con zonas de erosión
      const bank1969: [number, number][] = [
        [4.540, -75.305],
        [4.518, -75.280],
        [4.492, -75.250],
        [4.468, -75.215],
        [4.422, -75.150],
      ];
      const bank2023: [number, number][] = [
        [4.540, -75.312],
        [4.522, -75.288],
        [4.497, -75.258],
        [4.472, -75.225],
        [4.428, -75.160],
      ];

      // Eje fluvial 1969 (cian punteado)
      L.polyline(bank1969, {
        color: "#00bbf9",
        weight: 2,
        dashArray: "4, 6",
        opacity: 0.7,
      }).addTo(group);

      // Eje fluvial 2023 ampliado (amarillo preventivo)
      L.polyline(bank2023, {
        color: "#ffd166",
        weight: 3,
        opacity: 0.9,
      }).addTo(group);

      // Puntos críticos de socavación lateral
      const erosionHotspots: [number, number][] = [
        [4.510, -75.270],
        [4.485, -75.235],
        [4.450, -75.195],
      ];
      erosionHotspots.forEach((pt) => {
        L.circleMarker(pt, {
          radius: 7,
          color: "#ff3864",
          fillColor: "#ff3864",
          fillOpacity: 0.8,
          weight: 2,
        }).addTo(group);
      });
    }
  }, [activeLayer]);

  // Manejar cambio de preajuste
  const handleSelectPreset = (preset: WatershedPreset) => {
    setSelectedPresetId(preset.id);
    const parsed = buildParsedResult(preset.name, preset.polygon);
    onAreaChanged(parsed);
  };

  // Manejar entrada manual (lat, lon, radio km)
  const handleApplyManual = (e: React.FormEvent) => {
    e.preventDefault();
    const lat = parseFloat(manualLat);
    const lon = parseFloat(manualLon);
    const rad = parseFloat(manualRadiusKm);

    if (isNaN(lat) || isNaN(lon) || isNaN(rad)) {
      setFileError("Por favor ingresa valores numéricos válidos.");
      return;
    }
    try {
      const parsed = createCirclePolygon(lat, lon, rad);
      setFileError(null);
      onAreaChanged(parsed);
    } catch (err: unknown) {
      setFileError(err instanceof Error ? err.message : "Error al procesar área circular.");
    }
  };

  // Manejar carga de archivo (.geojson o .kml)
  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploadedFileName(file.name);
    setFileError(null);

    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const text = event.target?.result as string;
        let parsed: ParsedGeoResult;
        if (file.name.toLowerCase().endsWith(".kml")) {
          parsed = parseKmlText(text, file.name);
        } else {
          parsed = parseGeoJsonText(text, file.name);
        }
        onAreaChanged(parsed);
      } catch (err: unknown) {
        setFileError(
          err instanceof Error
            ? err.message
            : "No fue posible leer el archivo espacial. Comprueba que sea GeoJSON o KML válido."
        );
      }
    };
    reader.readAsText(file);
  };

  const currentAreaHa = computePolygonAreaHa(currentPolygon);

  return (
    <div className="relative w-full h-[520px] rounded-xl overflow-hidden border border-control-border bg-control-card flex flex-col">
      {/* Barra superior de controles del área y capas */}
      <div className="z-[1000] bg-control-card/95 backdrop-blur-md px-4 py-2.5 border-b border-control-border flex flex-wrap items-center justify-between gap-3 text-xs">
        {/* Selector de modo de definición */}
        <div className="flex items-center gap-1.5 bg-control-bg p-1 rounded-lg border border-control-border">
          <button
            type="button"
            onClick={() => setDefinitionMode("presets")}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded font-medium transition-all ${
              definitionMode === "presets"
                ? "bg-neon-cyan/20 text-neon-cyan border border-neon-cyan/40"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <MapPin className="w-3.5 h-3.5" />
            <span>Preajustes Combeima</span>
          </button>
          <button
            type="button"
            onClick={() => setDefinitionMode("manual")}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded font-medium transition-all ${
              definitionMode === "manual"
                ? "bg-neon-cyan/20 text-neon-cyan border border-neon-cyan/40"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Sliders className="w-3.5 h-3.5" />
            <span>Manual (Lat/Lon + Radio)</span>
          </button>
          <button
            type="button"
            onClick={() => setDefinitionMode("file")}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded font-medium transition-all ${
              definitionMode === "file"
                ? "bg-neon-cyan/20 text-neon-cyan border border-neon-cyan/40"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Upload className="w-3.5 h-3.5" />
            <span>Cargar GeoJSON / KML</span>
          </button>
        </div>

        {/* Conmutador de Capas Visuales */}
        <div className="flex items-center gap-2">
          <span className="text-slate-400 font-medium flex items-center gap-1">
            <Layers className="w-3.5 h-3.5 text-neon-cyan" />
            Capas:
          </span>
          <div className="flex items-center gap-1 bg-control-bg p-1 rounded-lg border border-control-border">
            <button
              type="button"
              onClick={() => onLayerChange("none")}
              className={`px-2 py-0.5 rounded transition-colors ${
                activeLayer === "none"
                  ? "bg-control-surface text-slate-200 font-semibold"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Base
            </button>
            <button
              type="button"
              onClick={() => onLayerChange("ndwi")}
              className={`px-2 py-0.5 rounded transition-colors ${
                activeLayer === "ndwi"
                  ? "bg-neon-cyan/25 text-neon-cyan font-semibold border border-neon-cyan/50"
                  : "text-slate-400 hover:text-neon-cyan"
              }`}
            >
              NDWI (Agua)
            </button>
            <button
              type="button"
              onClick={() => onLayerChange("ndvi")}
              className={`px-2 py-0.5 rounded transition-colors ${
                activeLayer === "ndvi"
                  ? "bg-neon-green/25 text-neon-green font-semibold border border-neon-green/50"
                  : "text-slate-400 hover:text-neon-green"
              }`}
            >
              NDVI (Vegetación)
            </button>
            <button
              type="button"
              onClick={() => onLayerChange("morphology")}
              className={`px-2 py-0.5 rounded transition-colors ${
                activeLayer === "morphology"
                  ? "bg-neon-amber/25 text-neon-amber font-semibold border border-neon-amber/50"
                  : "text-slate-400 hover:text-neon-amber"
              }`}
            >
              Morfología de Cauce
            </button>
          </div>
        </div>
      </div>

      {/* Sub-barra contextual según modo activo */}
      <div className="z-[999] bg-control-bg/90 backdrop-blur-sm px-4 py-2 border-b border-control-border text-xs flex flex-wrap items-center justify-between gap-3">
        {definitionMode === "presets" && (
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-slate-400">Seleccionar sector:</span>
            {COMBEIMA_PRESETS.map((preset) => {
              const isSelected = selectedPresetId === preset.id;
              return (
                <button
                  key={preset.id}
                  type="button"
                  onClick={() => handleSelectPreset(preset)}
                  className={`px-2.5 py-1 rounded transition-all text-xs font-medium cursor-pointer ${
                    isSelected
                      ? "bg-neon-cyan text-control-bg font-bold shadow-sm shadow-neon-cyan/40"
                      : "bg-control-card border border-control-border text-slate-300 hover:border-neon-cyan/60"
                  }`}
                >
                  {preset.name}
                </button>
              );
            })}
          </div>
        )}

        {definitionMode === "manual" && (
          <form onSubmit={handleApplyManual} className="flex items-center gap-3 flex-wrap">
            <div className="flex items-center gap-1.5">
              <label htmlFor="manualLat" className="text-slate-400">Lat:</label>
              <input
                id="manualLat"
                type="text"
                value={manualLat}
                onChange={(e) => setManualLat(e.target.value)}
                className="w-20 px-2 py-1 bg-control-card border border-control-border rounded text-slate-100 focus:outline-none focus:border-neon-cyan font-mono"
              />
            </div>
            <div className="flex items-center gap-1.5">
              <label htmlFor="manualLon" className="text-slate-400">Lon:</label>
              <input
                id="manualLon"
                type="text"
                value={manualLon}
                onChange={(e) => setManualLon(e.target.value)}
                className="w-20 px-2 py-1 bg-control-card border border-control-border rounded text-slate-100 focus:outline-none focus:border-neon-cyan font-mono"
              />
            </div>
            <div className="flex items-center gap-1.5">
              <label htmlFor="manualRadiusKm" className="text-slate-400">Radio (km):</label>
              <input
                id="manualRadiusKm"
                type="text"
                value={manualRadiusKm}
                onChange={(e) => setManualRadiusKm(e.target.value)}
                className="w-16 px-2 py-1 bg-control-card border border-control-border rounded text-slate-100 focus:outline-none focus:border-neon-cyan font-mono"
              />
            </div>
            <button
              type="submit"
              className="px-3 py-1 bg-neon-cyan/20 border border-neon-cyan text-neon-cyan font-semibold rounded hover:bg-neon-cyan hover:text-control-bg transition-colors"
            >
              Trazar Radio
            </button>
          </form>
        )}

        {definitionMode === "file" && (
          <div className="flex items-center gap-3 flex-wrap">
            <label className="flex items-center gap-2 px-3 py-1 bg-control-card border border-neon-cyan/50 rounded cursor-pointer text-slate-200 hover:bg-control-surface">
              <Upload className="w-3.5 h-3.5 text-neon-cyan" />
              <span>{uploadedFileName || "Seleccionar .geojson o .kml"}</span>
              <input
                type="file"
                accept=".geojson,.json,.kml"
                onChange={handleFileUpload}
                className="hidden"
              />
            </label>
            {uploadedFileName && (
              <span className="text-neon-green flex items-center gap-1">
                <CheckCircle className="w-3.5 h-3.5" /> Archivo procesado
              </span>
            )}
          </div>
        )}

        {/* Métrica de área calculada */}
        <div className="ml-auto text-slate-300 font-mono flex items-center gap-2">
          <span className="text-slate-500">Área Polígono:</span>
          <span className="text-neon-cyan font-bold">{currentAreaHa.toLocaleString("es-CO")} ha</span>
        </div>
      </div>

      {/* Mensaje de error si falla archivo o entrada manual */}
      {fileError && (
        <div className="z-[998] bg-neon-rose/20 border-b border-neon-rose/50 px-4 py-1.5 text-xs text-neon-rose flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{fileError}</span>
        </div>
      )}

      {/* Contenedor del Mapa Leaflet */}
      <div className="relative flex-1 w-full h-full" ref={mapContainerRef}>
        {/* Indicador de coordenadas y centro */}
        <div className="absolute bottom-3 left-3 z-[990] bg-control-card/85 backdrop-blur-sm border border-control-border px-3 py-1.5 rounded-lg text-[11px] text-slate-300 flex items-center gap-2">
          <Compass className="w-3.5 h-3.5 text-neon-cyan" />
          <span>Cuenca Río Combeima (Ibagué, Tolima · WGS84)</span>
        </div>
      </div>
    </div>
  );
}
