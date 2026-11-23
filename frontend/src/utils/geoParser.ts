export interface GeoPolygon {
  type: "Polygon";
  coordinates: [number, number][][];
}

export interface ParsedGeoResult {
  areaName: string;
  geometry: GeoPolygon;
  areaHa: number;
  centroid: [number, number]; // [lon, lat]
  formattedCoords: string;
}

function toDMS(deg: number, isLat: boolean): string {
  const abs = Math.abs(deg);
  const d = Math.floor(abs);
  const mFloat = (abs - d) * 60;
  const m = Math.floor(mFloat);
  const s = Math.round((mFloat - m) * 60);
  const dir = isLat ? (deg >= 0 ? "N" : "S") : deg >= 0 ? "E" : "O";
  return `${String(d).padStart(2, "0")}°${String(m).padStart(2, "0")}'${String(s).padStart(2, "0")}"${dir}`;
}

export function formatCoordPair(lon: number, lat: number): string {
  return `${toDMS(lat, true)} ${toDMS(lon, false)}`;
}

export function closeRing(ring: [number, number][]): [number, number][] {
  if (ring.length === 0) return ring;
  const first = ring[0];
  const last = ring[ring.length - 1];
  if (first[0] === last[0] && first[1] === last[1]) {
    return ring;
  }
  return [...ring, [first[0], first[1]]];
}

export function computePolygonAreaHa(ring: [number, number][]): number {
  if (ring.length < 3) return 0;
  const meanLatRad =
    (ring.reduce((sum, p) => sum + p[1], 0) / ring.length) * (Math.PI / 180);
  const metersPerDegLat = 111132.92;
  const metersPerDegLon = 111412.84 * Math.cos(meanLatRad);

  let areaM2 = 0;
  for (let i = 0; i < ring.length - 1; i++) {
    const x1 = ring[i][0] * metersPerDegLon;
    const y1 = ring[i][1] * metersPerDegLat;
    const x2 = ring[i + 1][0] * metersPerDegLon;
    const y2 = ring[i + 1][1] * metersPerDegLat;
    areaM2 += x1 * y2 - x2 * y1;
  }
  return Math.max(0.1, Math.round((Math.abs(areaM2) / 2 / 10000) * 100) / 100);
}

export function computeCentroid(ring: [number, number][]): [number, number] {
  const unique =
    ring.length > 1 &&
    ring[0][0] === ring[ring.length - 1][0] &&
    ring[0][1] === ring[ring.length - 1][1]
      ? ring.slice(0, -1)
      : ring;
  if (unique.length === 0) return [-75.22, 4.48];
  const lon = unique.reduce((s, p) => s + p[0], 0) / unique.length;
  const lat = unique.reduce((s, p) => s + p[1], 0) / unique.length;
  return [Number(lon.toFixed(5)), Number(lat.toFixed(5))];
}

function validateRingCoords(ring: [number, number][]): void {
  if (ring.length < 4) {
    throw new Error(
      "El polígono requiere al menos 3 vértices distintos (4 posiciones con anillo cerrado)."
    );
  }
  for (const [lon, lat] of ring) {
    if (
      !Number.isFinite(lon) ||
      !Number.isFinite(lat) ||
      lon < -180 ||
      lon > 180 ||
      lat < -90 ||
      lat > 90
    ) {
      throw new Error(
        `Coordenada WGS84 fuera de rango: [${lon}, ${lat}]. Usa formato [longitud, latitud].`
      );
    }
  }
}

export function buildParsedResult(
  areaName: string,
  rawRing: [number, number][]
): ParsedGeoResult {
  const closed = closeRing(rawRing);
  validateRingCoords(closed);
  const centroid = computeCentroid(closed);
  return {
    areaName: areaName.trim() || "Área definida",
    geometry: {
      type: "Polygon",
      coordinates: [closed],
    },
    areaHa: computePolygonAreaHa(closed),
    centroid,
    formattedCoords: formatCoordPair(centroid[0], centroid[1]),
  };
}

export function createCirclePolygon(
  lat: number,
  lon: number,
  radiusKm: number,
  points = 32
): ParsedGeoResult {
  if (!Number.isFinite(lat) || !Number.isFinite(lon) || !Number.isFinite(radiusKm) || radiusKm <= 0) {
    throw new Error("Parámetros de latitud, longitud o radio inválidos.");
  }
  const ring: [number, number][] = [];
  const kmPerDegLat = 111.132;
  const kmPerDegLon = 111.412 * Math.cos((lat * Math.PI) / 180);

  for (let i = 0; i < points; i++) {
    const angle = (i * 2 * Math.PI) / points;
    const dLat = (radiusKm * Math.sin(angle)) / kmPerDegLat;
    const dLon = (radiusKm * Math.cos(angle)) / kmPerDegLon;
    ring.push([Number((lon + dLon).toFixed(6)), Number((lat + dLat).toFixed(6))]);
  }

  return buildParsedResult(
    `Área Circular (r=${radiusKm}km)`,
    ring
  );
}

export function parseGeoJsonText(
  raw: string,
  fallbackName = "Polígono GeoJSON"
): ParsedGeoResult {
  let json: Record<string, unknown>;
  try {
    json = JSON.parse(raw);
  } catch {
    throw new Error("El archivo GeoJSON no contiene JSON válido.");
  }

  let geometry: Record<string, unknown> | undefined;
  let name = fallbackName;

  if (json.type === "FeatureCollection" && Array.isArray(json.features)) {
    const feat = json.features.find(
      (f: Record<string, unknown>) =>
        f?.geometry &&
        ((f.geometry as Record<string, unknown>).type === "Polygon" ||
          (f.geometry as Record<string, unknown>).type === "MultiPolygon")
    ) as Record<string, unknown> | undefined;

    if (!feat) {
      throw new Error(
        "El FeatureCollection no contiene ninguna geometría Polygon o MultiPolygon."
      );
    }
    geometry = feat.geometry as Record<string, unknown>;
    const props = feat.properties as Record<string, unknown> | undefined;
    if (typeof props?.nombre === "string") name = props.nombre;
    else if (typeof props?.name === "string") name = props.name;
  } else if (json.type === "Feature" && json.geometry) {
    geometry = json.geometry as Record<string, unknown>;
    const props = json.properties as Record<string, unknown> | undefined;
    if (typeof props?.nombre === "string") name = props.nombre;
    else if (typeof props?.name === "string") name = props.name;
  } else if (json.type === "Polygon" || json.type === "MultiPolygon") {
    geometry = json;
  }

  if (!geometry) {
    throw new Error("Formato GeoJSON no reconocido. Se esperaba Polygon, Feature o FeatureCollection.");
  }

  let ring: [number, number][] = [];
  if (geometry.type === "Polygon" && Array.isArray(geometry.coordinates)) {
    const outer = geometry.coordinates[0] as unknown[];
    if (Array.isArray(outer)) {
      ring = outer.map((pt) => {
        const arr = pt as number[];
        return [Number(arr[0]), Number(arr[1])];
      });
    }
  } else if (
    geometry.type === "MultiPolygon" &&
    Array.isArray(geometry.coordinates)
  ) {
    const firstPoly = geometry.coordinates[0] as unknown[];
    const outer = Array.isArray(firstPoly) ? (firstPoly[0] as unknown[]) : [];
    ring = outer.map((pt) => {
      const arr = pt as number[];
      return [Number(arr[0]), Number(arr[1])];
    });
  } else {
    throw new Error(`Tipo de geometría no soportado: ${String(geometry.type)}.`);
  }

  return buildParsedResult(name, ring);
}

export function parseKmlText(
  raw: string,
  fallbackName = "Polígono KML"
): ParsedGeoResult {
  const parser = new DOMParser();
  const doc = parser.parseFromString(raw, "application/xml");
  const parseError = doc.querySelector("parsererror");
  if (parseError) {
    throw new Error("El archivo KML no es XML válido.");
  }

  const nameEl = doc.querySelector("Placemark > name, Document > name");
  const areaName = nameEl?.textContent?.trim() || fallbackName;

  const coordsEl = doc.querySelector(
    "Polygon outerBoundaryIs LinearRing coordinates, LinearRing coordinates, LineString coordinates"
  );
  const coordsText = coordsEl?.textContent?.trim();
  if (!coordsText) {
    throw new Error("No se encontraron etiquetas <coordinates> con un polígono en el KML.");
  }

  const ring: [number, number][] = coordsText
    .split(/\s+/)
    .map((tuple) => tuple.trim())
    .filter(Boolean)
    .map((tuple) => {
      const [lonStr, latStr] = tuple.split(",");
      return [Number(lonStr), Number(latStr)] as [number, number];
    });

  return buildParsedResult(areaName, ring);
}
