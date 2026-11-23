# Frontend — Skyfussion Analytics

React + Vite + TypeScript + Tailwind CSS + Leaflet + Chart.js. Despliegue objetivo: **Vercel** (Root Directory = `frontend/`).

## Desarrollo

```bash
npm install
npm run dev
```

La URL del backend se configura con `VITE_API_URL` (por defecto `http://localhost:8000`).

```bash
VITE_API_URL=https://tu-backend.onrender.com npm run build
```

## Estructura

- `src/lib/api.ts` — contratos y llamadas a la API.
- `src/components/MapView.tsx` — mapa Leaflet de la cuenca.
- `src/components/TimeSeriesChart.tsx` — serie NDVI con Chart.js.
- `src/components/MetricCard.tsx` — tarjetas de métricas.

> Las cifras y su jerarquía de evidencia están definidas en `../PROJECT_SPEC.md`.
