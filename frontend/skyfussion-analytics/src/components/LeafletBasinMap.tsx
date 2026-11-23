import { useEffect, useRef, useState } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { Check, Compass, Crosshair, Pencil, RotateCcw, X } from "lucide-react";
import { AlertLevel, BasinMetrics, ThemeMode } from "../types/hydrology";
import { buildParsedResult, ParsedGeoResult } from "../utils/geoParser";

interface LeafletBasinMapProps {
  metrics: BasinMetrics;
  polygonRing: [number, number][]; // [lon, lat][]
  alertLevel?: AlertLevel;
  theme: ThemeMode;
  isDrawing: boolean;
  onToggleDrawing: (drawing: boolean) => void;
  onPolygonCommitted: (parsed: ParsedGeoResult) => void;
}

export function LeafletBasinMap({
  metrics,
  polygonRing,
  alertLevel = "PREVENTIVA",
  theme,
  isDrawing,
  onToggleDrawing,
  onPolygonCommitted,
}: LeafletBasinMapProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<L.Map | null>(null);
  const tileLayerRef = useRef<L.TileLayer | null>(null);
  const polygonLayerRef = useRef<L.Polygon | null>(null);
  const markersLayerRef = useRef<L.LayerGroup | null>(null);
  const drawLayerRef = useRef<L.LayerGroup | null>(null);

  const [baseStyle, setBaseStyle] = useState<"satellite" | "topo">("satellite");
  const [draftPoints, setDraftPoints] = useState<[number, number][]>([]);
  const [cursorLatLon, setCursorLatLon] = useState<[number, number] | null>(
    null
  );

  const strokeColor =
    alertLevel === "CRITICA"
      ? "#F72585"
      : alertLevel === "PREVENTIVA"
        ? "#FFB703"
        : "#00F5D4";

  // Initialize Leaflet map once
  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const map = L.map(containerRef.current, {
      center: [4.481, -75.1995],
      zoom: 12,
      zoomControl: true,
      attributionControl: true,
    });

    const markersGroup = L.layerGroup().addTo(map);
    const drawGroup = L.layerGroup().addTo(map);

    mapRef.current = map;
    markersLayerRef.current = markersGroup;
    drawLayerRef.current = drawGroup;

    map.on("mousemove", (e: L.LeafletMouseEvent) => {
      setCursorLatLon([
        Number(e.latlng.lat.toFixed(5)),
        Number(e.latlng.lng.toFixed(5)),
      ]);
    });

    map.on("mouseout", () => {
      setCursorLatLon(null);
    });

    return () => {
      map.remove();
      mapRef.current = null;
      tileLayerRef.current = null;
      polygonLayerRef.current = null;
      markersLayerRef.current = null;
      drawLayerRef.current = null;
    };
  }, []);

  // Switch tile provider cleanly
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    if (tileLayerRef.current) {
      map.removeLayer(tileLayerRef.current);
    }

    const tileUrl =
      baseStyle === "satellite"
        ? "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
        : "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png";

    const attribution =
      baseStyle === "satellite"
        ? "Esri World Imagery"
        : "&copy; OpenStreetMap";

    const layer = L.tileLayer(tileUrl, {
      maxZoom: 18,
      attribution,
    }).addTo(map);

    tileLayerRef.current = layer;
  }, [baseStyle, theme]);

  // Render active study polygon and monitoring stations
  useEffect(() => {
    const map = mapRef.current;
    const markersGroup = markersLayerRef.current;
    if (!map || !markersGroup || polygonRing.length < 3) return;

    if (polygonLayerRef.current) {
      map.removeLayer(polygonLayerRef.current);
    }
    markersGroup.clearLayers();

    const latLngs: L.LatLngTuple[] = polygonRing.map(([lon, lat]) => [
      lat,
      lon,
    ]);

    const poly = L.polygon(latLngs, {
      color: strokeColor,
      weight: 2.2,
      fillColor: "#00BBF9",
      fillOpacity: 0.16,
    }).addTo(map);

    polygonLayerRef.current = poly;

    const bounds = poly.getBounds();
    if (bounds.isValid()) {
      map.fitBounds(bounds, { padding: [34, 34], maxZoom: 13 });
    }

    // Add centroid + Combeima reference stations if within Tolima or generic centroid
    const center = bounds.getCenter();
    L.circleMarker(center, {
      radius: 6,
      color: "#00F5D4",
      weight: 2,
      fillColor: "#0B1229",
      fillOpacity: 0.9,
    })
      .bindTooltip(`${metrics.basinName} (Centroide)`, { direction: "top" })
      .addTo(markersGroup);

    if (metrics.basinId === "combeima-ibague") {
      const stations: { name: string; lat: number; lon: number }[] = [
        { name: "Estación Poblado (1,480 msnm)", lat: 4.481, lon: -75.1995 },
        { name: "Bocatoma Ibagué (1,210 msnm)", lat: 4.454, lon: -75.174 },
        { name: "Cabecera Juntas (2,150 msnm)", lat: 4.512, lon: -75.235 },
      ];
      stations.forEach((st) => {
        L.circleMarker([st.lat, st.lon], {
          radius: 5,
          color: "#00BBF9",
          weight: 2,
          fillColor: "#FFFFFF",
          fillOpacity: 0.95,
        })
          .bindTooltip(st.name, { direction: "top" })
          .addTo(markersGroup);
      });
    }
  }, [polygonRing, strokeColor, metrics.basinId, metrics.basinName]);

  // Handle interactive polygon vertex clicking in draw mode
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    const handleClick = (e: L.LeafletMouseEvent) => {
      if (!isDrawing) return;
      setDraftPoints((prev) => [
        ...prev,
        [Number(e.latlng.lng.toFixed(5)), Number(e.latlng.lat.toFixed(5))],
      ]);
    };

    map.on("click", handleClick);
    return () => {
      map.off("click", handleClick);
    };
  }, [isDrawing]);

  // Render draft polygon vertices
  useEffect(() => {
    const drawGroup = drawLayerRef.current;
    if (!drawGroup) return;
    drawGroup.clearLayers();

    if (draftPoints.length === 0) return;

    const latLngs: L.LatLngTuple[] = draftPoints.map(([lon, lat]) => [
      lat,
      lon,
    ]);

    if (latLngs.length >= 2) {
      L.polyline(latLngs, {
        color: "#00F5D4",
        weight: 2,
        dashArray: "5 4",
      }).addTo(drawGroup);
    }

    latLngs.forEach((pt, idx) => {
      L.circleMarker(pt, {
        radius: 5,
        color: "#00F5D4",
        weight: 2,
        fillColor: idx === 0 ? "#FFB703" : "#0B1229",
        fillOpacity: 1,
      }).addTo(drawGroup);
    });
  }, [draftPoints]);

  const handleFinishDrawing = () => {
    if (draftPoints.length < 3) return;
    const parsed = buildParsedResult("Polígono dibujado en mapa", draftPoints);
    setDraftPoints([]);
    onToggleDrawing(false);
    onPolygonCommitted(parsed);
  };

  const handleCancelDrawing = () => {
    setDraftPoints([]);
    onToggleDrawing(false);
  };

  const handleRecenter = () => {
    const map = mapRef.current;
    const poly = polygonLayerRef.current;
    if (map && poly && poly.getBounds().isValid()) {
      map.fitBounds(poly.getBounds(), { padding: [34, 34], maxZoom: 13 });
    }
  };

  return (
    <div className="relative flex-1 min-h-[380px] lg:min-h-[450px] bg-[#060D24]">
      {/* Leaflet Mount Container */}
      <div
        ref={containerRef}
        className={`w-full h-full min-h-[380px] lg:min-h-[450px] z-0 ${
          isDrawing ? "cursor-crosshair" : ""
        }`}
      />

      {/* Top-Left Map Controls: Base Layer & Draw Polygon */}
      <div className="absolute top-3 left-14 z-[400] flex flex-wrap items-center gap-2">
        <div className="flex items-center gap-1 p-1 rounded bg-[#FFFFFF]/92 dark:bg-[#101A36]/90 backdrop-blur-md border border-[#CBD5E1] dark:border-[#1E2D5A]">
          <button
            type="button"
            onClick={() => setBaseStyle("satellite")}
            className={`px-2 py-1 rounded text-[11px] font-medium cursor-pointer transition-colors ${
              baseStyle === "satellite"
                ? "bg-[#0284C7] dark:bg-[#00BBF9] text-white dark:text-[#0A1128]"
                : "text-[#334155] dark:text-[#BCC8D1]"
            }`}
          >
            Satelital
          </button>
          <button
            type="button"
            onClick={() => setBaseStyle("topo")}
            className={`px-2 py-1 rounded text-[11px] font-medium cursor-pointer transition-colors ${
              baseStyle === "topo"
                ? "bg-[#0284C7] dark:bg-[#00BBF9] text-white dark:text-[#0A1128]"
                : "text-[#334155] dark:text-[#BCC8D1]"
            }`}
          >
            Topográfico
          </button>
        </div>

        {!isDrawing ? (
          <button
            type="button"
            onClick={() => {
              setDraftPoints([]);
              onToggleDrawing(true);
            }}
            className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded text-[11px] font-medium bg-[#FFFFFF]/92 dark:bg-[#101A36]/90 backdrop-blur-md border border-[#CBD5E1] dark:border-[#1E2D5A] text-[#0F172A] dark:text-[#DCE1FF] hover:border-[#0284C7] dark:hover:border-[#00BBF9] cursor-pointer"
          >
            <Pencil className="w-3.5 h-3.5 text-[#0284C7] dark:text-[#00BBF9]" />
            <span>Dibujar Polígono</span>
          </button>
        ) : (
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#0A1128]/92 border border-[#00F5D4]/60 text-[#DCE1FF]">
            <span className="text-[11px] font-mono-tabular text-[#00F5D4]">
              Clic en mapa ({draftPoints.length} vértices)
            </span>
            <button
              type="button"
              onClick={handleFinishDrawing}
              disabled={draftPoints.length < 3}
              className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-[#00F5D4] text-[#0A1128] text-[11px] font-semibold disabled:opacity-45 cursor-pointer"
            >
              <Check className="w-3 h-3" />
              <span>Cerrar</span>
            </button>
            <button
              type="button"
              onClick={handleCancelDrawing}
              className="inline-flex items-center gap-1 px-2 py-0.5 rounded border border-[#8E9AB8]/40 text-[#BCC8D1] text-[11px] cursor-pointer"
            >
              <X className="w-3 h-3" />
              <span>Cancelar</span>
            </button>
          </div>
        )}

        <button
          type="button"
          onClick={handleRecenter}
          title="Centrar polígono activo"
          className="inline-flex items-center gap-1 px-2 py-1.5 rounded text-[11px] font-medium bg-[#FFFFFF]/92 dark:bg-[#101A36]/90 backdrop-blur-md border border-[#CBD5E1] dark:border-[#1E2D5A] text-[#334155] dark:text-[#BCC8D1] hover:text-[#0284C7] dark:hover:text-[#00BBF9] cursor-pointer"
        >
          <Crosshair className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">Encuadrar</span>
        </button>

        {draftPoints.length > 0 && isDrawing && (
          <button
            type="button"
            onClick={() => setDraftPoints((p) => p.slice(0, -1))}
            title="Deshacer último vértice"
            className="inline-flex items-center gap-1 px-2 py-1.5 rounded text-[11px] bg-[#0A1128]/90 border border-[#1E2D5A] text-[#BCC8D1] cursor-pointer"
          >
            <RotateCcw className="w-3 h-3" />
            <span>Deshacer</span>
          </button>
        )}
      </div>

      {/* Top-Right Coordinate HUD */}
      <div className="hidden md:flex items-center gap-2 absolute top-3 right-3 z-[400] px-3 py-1.5 rounded bg-[#FFFFFF]/92 dark:bg-[#0A1128]/88 backdrop-blur-md border border-[#CBD5E1] dark:border-[#1E2D5A] text-[11px] font-mono-tabular text-[#0F172A] dark:text-[#DCE1FF] pointer-events-none">
        <Compass className="w-3.5 h-3.5 text-[#0284C7] dark:text-[#00BBF9]" />
        <span>
          {cursorLatLon
            ? `Lat ${cursorLatLon[0]} · Lon ${cursorLatLon[1]}`
            : `WGS84 · ${metrics.coordinates}`}
        </span>
      </div>
    </div>
  );
}
