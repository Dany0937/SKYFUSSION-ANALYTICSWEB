export function metersToDegrees(meters, latitude) {
  const earthRadius = 6371000;
  return meters / (earthRadius * Math.cos(latitude * Math.PI / 180)) * (180 / Math.PI);
}

export function degreesToMeters(degrees, latitude) {
  const earthRadius = 6371000;
  return degrees * Math.PI / 180 * earthRadius * Math.cos(latitude * Math.PI / 180);
}

export function calculateDistance(coord1, coord2) {
  const [lon1, lat1] = coord1;
  const [lon2, lat2] = coord2;
  
  const R = 6371000;
  const phi1 = lat1 * Math.PI / 180;
  const phi2 = lat2 * Math.PI / 180;
  const deltaPhi = (lat2 - lat1) * Math.PI / 180;
  const deltaLambda = (lon2 - lon1) * Math.PI / 180;

  const a = Math.sin(deltaPhi / 2) * Math.sin(deltaPhi / 2) +
            Math.cos(phi1) * Math.cos(phi2) *
            Math.sin(deltaLambda / 2) * Math.sin(deltaLambda / 2);
  
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

  return R * c;
}

export function getBoundingBox(coordinates) {
  let minLon = Infinity, minLat = Infinity;
  let maxLon = -Infinity, maxLat = -Infinity;

  const processCoords = (coords) => {
    for (const coord of coords) {
      if (Array.isArray(coord[0])) {
        processCoords(coord);
      } else {
        const [lon, lat] = coord;
        minLon = Math.min(minLon, lon);
        minLat = Math.min(minLat, lat);
        maxLon = Math.max(maxLon, lon);
        maxLat = Math.max(maxLat, lat);
      }
    }
  };

  processCoords(coordinates);

  return [minLon, minLat, maxLon, maxLat];
}

export function formatCoordinate(coord, precision = 6) {
  return {
    lon: parseFloat(coord[0].toFixed(precision)),
    lat: parseFloat(coord[1].toFixed(precision))
  };
}
