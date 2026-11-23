const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

export interface EnvMetrics {
  ndvi: number;
  ndwi: number;
  temperature: number;
  humidity: number;
  precipitation: number;
  flow_rate: number;
  alert_level: string;
  timestamp: string;
}

export interface SeriesPoint {
  label: string;
  ndvi: number;
}

interface ApiEnvelope<T> {
  success: boolean;
  data: T;
}

async function get<T>(path: string): Promise<T> {
  const response = await fetch(`${API_URL}${path}`);
  if (!response.ok) {
    throw new Error(`Error ${response.status} al consultar ${path}`);
  }
  const body = (await response.json()) as ApiEnvelope<T>;
  return body.data;
}

export const getMetrics = () => get<EnvMetrics>('/api/v1/demo/metrics');
export const getSeries = () => get<SeriesPoint[]>('/api/v1/series/demo');
