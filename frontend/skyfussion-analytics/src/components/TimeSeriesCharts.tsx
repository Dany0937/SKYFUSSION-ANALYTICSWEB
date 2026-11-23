import { useEffect, useRef } from "react";
import {
  Chart,
  Filler,
  Legend,
  LinearScale,
  LineController,
  LineElement,
  PointElement,
  CategoryScale,
  Tooltip,
} from "chart.js";
import { COMBEIMA_HISTORICAL_SERIES } from "../data/watersheds";
import { BasinMetrics, ThemeMode } from "../types/hydrology";

Chart.register(
  LineController,
  LineElement,
  PointElement,
  LinearScale,
  CategoryScale,
  Tooltip,
  Legend,
  Filler
);

interface TimeSeriesChartsProps {
  metrics: BasinMetrics;
  theme: ThemeMode;
}

export function TimeSeriesCharts({ metrics, theme }: TimeSeriesChartsProps) {
  const spectralCanvasRef = useRef<HTMLCanvasElement | null>(null);
  const dischargeCanvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const isDark = theme === "dark";
    const gridColor = isDark
      ? "rgba(30, 45, 90, 0.7)"
      : "rgba(203, 213, 225, 0.65)";
    const textColor = isDark ? "#BCC8D1" : "#334155";
    const cyanColor = isDark ? "#00BBF9" : "#0284C7";
    const emeraldColor = isDark ? "#00F5D4" : "#059669";
    const amberColor = isDark ? "#FFB703" : "#D97706";

    const series = COMBEIMA_HISTORICAL_SERIES.map((pt, index) => {
      if (index === COMBEIMA_HISTORICAL_SERIES.length - 1) {
        return {
          ...pt,
          ndwi: metrics.ndwi,
          ndvi: metrics.ndvi,
          channelWidthM: Number(
            (38.8 * (1 + metrics.channelWidthChangePct / 100)).toFixed(1)
          ),
          dischargeM3s: metrics.predictedDischargeM3s,
        };
      }
      return pt;
    });

    const labels = series.map((s) => s.year);

    let spectralChart: Chart | null = null;
    let dischargeChart: Chart | null = null;

    if (spectralCanvasRef.current) {
      spectralChart = new Chart(spectralCanvasRef.current, {
        type: "line",
        data: {
          labels,
          datasets: [
            {
              label: "NDWI (Agua)",
              data: series.map((s) => s.ndwi),
              borderColor: cyanColor,
              backgroundColor: cyanColor,
              yAxisID: "y",
              tension: 0.28,
              borderWidth: 2,
              pointRadius: 3,
            },
            {
              label: "NDVI (Vegetación)",
              data: series.map((s) => s.ndvi),
              borderColor: emeraldColor,
              backgroundColor: emeraldColor,
              yAxisID: "y",
              tension: 0.28,
              borderWidth: 2,
              pointRadius: 3,
            },
            {
              label: "Ancho Cauce (m)",
              data: series.map((s) => s.channelWidthM),
              borderColor: amberColor,
              backgroundColor: amberColor,
              borderDash: [5, 4],
              yAxisID: "y1",
              tension: 0.28,
              borderWidth: 2,
              pointRadius: 2.5,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          interaction: { mode: "index", intersect: false },
          plugins: {
            legend: {
              labels: {
                color: textColor,
                font: { family: "JetBrains Mono", size: 11 },
                boxWidth: 12,
              },
            },
          },
          scales: {
            x: {
              ticks: {
                color: textColor,
                font: { family: "JetBrains Mono", size: 10 },
              },
              grid: { color: gridColor },
            },
            y: {
              type: "linear",
              position: "left",
              min: -0.2,
              max: 0.9,
              ticks: {
                color: textColor,
                font: { family: "JetBrains Mono", size: 10 },
              },
              grid: { color: gridColor },
            },
            y1: {
              type: "linear",
              position: "right",
              min: 20,
              max: 70,
              ticks: {
                color: amberColor,
                font: { family: "JetBrains Mono", size: 10 },
              },
              grid: { drawOnChartArea: false },
            },
          },
        },
      });
    }

    if (dischargeCanvasRef.current) {
      dischargeChart = new Chart(dischargeCanvasRef.current, {
        type: "line",
        data: {
          labels,
          datasets: [
            {
              label: "Caudal Proyectado (m³/s)",
              data: series.map((s) => s.dischargeM3s),
              borderColor: cyanColor,
              backgroundColor: isDark
                ? "rgba(0, 187, 249, 0.14)"
                : "rgba(2, 132, 199, 0.12)",
              fill: true,
              tension: 0.3,
              borderWidth: 2.2,
              pointRadius: 3.5,
              pointBackgroundColor: series.map((s) =>
                s.isForecast ? amberColor : cyanColor
              ),
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          interaction: { mode: "index", intersect: false },
          plugins: {
            legend: {
              labels: {
                color: textColor,
                font: { family: "JetBrains Mono", size: 11 },
                boxWidth: 12,
              },
            },
          },
          scales: {
            x: {
              ticks: {
                color: textColor,
                font: { family: "JetBrains Mono", size: 10 },
              },
              grid: { color: gridColor },
            },
            y: {
              beginAtZero: true,
              ticks: {
                color: textColor,
                font: { family: "JetBrains Mono", size: 10 },
              },
              grid: { color: gridColor },
            },
          },
        },
      });
    }

    return () => {
      spectralChart?.destroy();
      dischargeChart?.destroy();
    };
  }, [
    theme,
    metrics.ndwi,
    metrics.ndvi,
    metrics.channelWidthChangePct,
    metrics.predictedDischargeM3s,
  ]);

  return (
    <section className="bg-[#FFFFFF] dark:bg-[#101A36] border border-[#E2E8F0] dark:border-[#1E2D5A] rounded-lg p-4">
      <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-[#E2E8F0] dark:border-[#1E2D5A]">
        <div>
          <h2 className="font-display text-sm font-semibold text-[#0F172A] dark:text-[#DCE1FF]">
            Series Temporales Multianuales (1969–2023) y Pronóstico
          </h2>
          <p className="text-xs text-[#64748B] dark:text-[#8E9AB8] mt-0.5">
            Referencia Combeima (Nivel A): RNN gru_attention_h1 RMSE = 0.0712 · R² = 0.0775 · Clasificación macro-F1 = 0.53 (artefacto) / 0.66 (plan) · Alerta asistida por humano
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 pt-4">
        <div className="flex flex-col gap-2">
          <span className="text-xs font-medium text-[#334155] dark:text-[#BCC8D1]">
            Evolución NDWI, NDVI y Ancho del Cauce (m)
          </span>
          <div className="h-[230px] w-full">
            <canvas ref={spectralCanvasRef} />
          </div>
        </div>

        <div className="flex flex-col gap-2">
          <span className="text-xs font-medium text-[#334155] dark:text-[#BCC8D1]">
            Hidrograma Histórico y Punto Proyectado (m³/s)
          </span>
          <div className="h-[230px] w-full">
            <canvas ref={dischargeCanvasRef} />
          </div>
        </div>
      </div>
    </section>
  );
}
