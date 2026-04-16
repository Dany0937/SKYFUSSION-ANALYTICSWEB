export function validateGeoJSON(geojson) {
  const errors = [];

  if (!geojson || typeof geojson !== 'object') {
    return { valid: false, errors: ['Invalid GeoJSON object'] };
  }

  if (!geojson.type) {
    errors.push('Missing "type" property');
  }

  const validTypes = ['FeatureCollection', 'Feature', 'Point', 'LineString', 'Polygon', 'MultiPoint', 'MultiLineString', 'MultiPolygon'];
  if (geojson.type && !validTypes.includes(geojson.type)) {
    errors.push(`Invalid type: ${geojson.type}`);
  }

  if (geojson.type === 'FeatureCollection') {
    if (!Array.isArray(geojson.features)) {
      errors.push('FeatureCollection must have "features" array');
    }
  }

  if (geojson.features) {
    geojson.features.forEach((feature, index) => {
      if (!feature.geometry) {
        errors.push(`Feature ${index}: Missing geometry`);
      }
    });
  }

  if (geojson.crs?.properties?.name?.includes('EPSG')) {
    const match = geojson.crs.properties.name.match(/EPSG::(\d+)/);
    if (match) {
      const epsg = parseInt(match[1]);
      if (epsg !== 4326 && epsg !== 32618) {
        errors.push(`Unsupported CRS: EPSG:${epsg}. Use EPSG:4326 (WGS84)`);
      }
    }
  }

  return {
    valid: errors.length === 0,
    errors
  };
}

export function validateCoordinates(lon, lat) {
  if (typeof lon !== 'number' || typeof lat !== 'number') {
    return { valid: false, error: 'Coordinates must be numbers' };
  }

  if (lon < -180 || lon > 180) {
    return { valid: false, error: 'Longitude out of range (-180 to 180)' };
  }

  if (lat < -90 || lat > 90) {
    return { valid: false, error: 'Latitude out of range (-90 to 90)' };
  }

  return { valid: true };
}

export function isPointInColombia(lon, lat) {
  return lon >= -79 && lon <= -66 && lat >= -4.2 && lat <= 13;
}

export function validateBbox(bbox) {
  if (!Array.isArray(bbox) || bbox.length !== 4) {
    return { valid: false, error: 'Bounding box must have 4 coordinates' };
  }

  const [minLon, minLat, maxLon, maxLat] = bbox;

  if (minLon >= maxLon || minLat >= maxLat) {
    return { valid: false, error: 'Invalid bounding box coordinates' };
  }

  return { valid: true };
}
