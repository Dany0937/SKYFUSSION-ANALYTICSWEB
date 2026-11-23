import React, { useMemo } from "react";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  ChartOptions,
  ChartData,
} from "chart.js";
import { Line } from "react-chartjs-2";
import { CombeimaSeriesPoint } from "../types/hydrology";
import { TrendingUp, ShieldCheck } from "lucide-react";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

interface DischargeChartProps {
  series: CombeimaSeriesPoint[];
}

export function DischargeChart({ series }: DischargeChartProps) {
  const chartData: ChartData<"line"> = useMemo(() => {
    const labels = series.map((s) => s.year);

    // Separar datos históricos y proyectados
    const historicalDischarge = series.map((s) => (!s.isForecast ? s.dischargeM3s : null));
    const forecastDischarge = series.map((s, idx) => {
      // Conectar con el último punto histórico para continuidad visual
      if (s.isForecast) return s.dischargeM3s;
      if (idx < series.length - 1 && series[idx + 1].isForecast) return s.dischargeM3s;
      return null;
    });

    // Banda de confianza superior e inferior
    const confidenceUpper = series.map((s) => s.confidenceUpper ?? s.dischargeM3s * 1.1);
    const confidenceLower = series.map((s) => s.confidenceLower ?? s.dischargeM3s * 0.9);

    return {
      labels,
      datasets: [
        // Banda de confianza superior (rellena hacia la inferior)
        {
          label: "Banda Confianza Sup (95%)",
          data: confidenceUpper,
          borderColor: "transparent",
          backgroundColor: "rgba(0, 187, 249, 0.12)",
          fill: "+1",
          pointRadius: 0,
          tension: 0.28,
        },
        // Banda de confianza inferior
        {
          label: "Banda Confianza Inf (95%)",
          data: confidenceLower,
          borderColor: "transparent",
          backgroundColor: "transparent",
          fill: false,
          pointRadius: 0,
          tension: 0.28,
        },
        // Serie histórica observada (1969–2023)
        {
          label: "Caudal Histórico Observado (m³/s)",
          data: historicalDischarge,
          borderColor: "#00bbf9",
          backgroundColor: "#00bbf9",
          borderWidth: 2.5,
          pointRadius: 4,
          pointHoverRadius: 6,
          pointBackgroundColor: "#00bbf9",
          pointBorderColor: "#0a1128",
          pointBorderWidth: 2,
          tension: 0.28,
          fill: false,
        },
        // Proyección de la red neuronal (2024–2025)
        {
          label: "Proyección RNN gru_attention_h1 (m³/s)",
          data: forecastDischarge,
          borderColor: "#00f5d4",
          backgroundColor: "#00f5d4",
          borderWidth: 2.5,
          borderDash: [6, 4],
          pointRadius: 5,
          pointHoverRadius: 7,
          pointBackgroundColor: "#00f5d4",
          pointBorderColor: "#0a1128",
          pointBorderWidth: 2,
          tension: 0.28,
          fill: false,
        },
      ],
    };
  }, [series]);

  const options: ChartOptions<"line"> = useMemo(() => {
    return {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: "index",
        intersect: false,
      },
      plugins: {
        legend: {
          position: "top",
          align: "end",
          labels: {
            boxWidth: 12,
            boxHeight: 12,
            usePointStyle: true,
            color: "#94a3b8",
            font: {
              size: 11,
              family: "system-ui",
            },
            filter: (legendItem) => {
              // Ocultar las etiquetas de las bandas de confianza para no saturar
              return !legendItem.text.includes("Banda");
            },
          },
        },
        tooltip: {
          backgroundColor: "#101a36",
          borderColor: "#1e2d5a",
          borderWidth: 1,
          titleColor: "#f1f5f9",
          bodyColor: "#cbd5e1",
          padding: 10,
          cornerRadius: 8,
          callbacks: {
            label: (context) => {
              const val = context.parsed.y;
              if (val === null || val === undefined) return "";
              if (context.dataset.label?.includes("Banda")) {
                return `${context.dataset.label}: ${val.toFixed(1)} m³/s`;
              }
              return `${context.dataset.label}: ${val.toFixed(1)} m³/s`;
            },
          },
        },
      },
      scales: {
        x: {
          grid: {
            color: "rgba(30, 45, 90, 0.4)",
          },
          ticks: {
            color: "#94a3b8",
            font: {
              size: 11,
            },
          },
        },
        y: {
          title: {
            display: true,
            text: "Caudal (m³/s)",
            color: "#94a3b8",
            font: {
              size: 11,
              weight: "bold",
            },
          },
          grid: {
            color: "rgba(30, 45, 90, 0.4)",
          },
          ticks: {
            color: "#94a3b8",
            font: {
              size: 11,
            },
          },
          min: 20,
          max: 90,
        },
      },
    };
  }, []);

  return (
    <div className="p-4 rounded-xl bg-control-card border border-control-border flex flex-col h-[380px]">
      <div className="flex flex-wrap items-center justify-between gap-2 mb-3 pb-2 border-b border-control-border">
        <div className="flex items-center gap-2">
          <TrendingUp className="w-4 h-4 text-neon-cyan" />
          <h3 className="text-sm font-semibold text-slate-100">
            Serie Temporal de Caudal (1969–2023) vs. Proyección RNN
          </h3>
        </div>
        <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
          <ShieldCheck className="w-3.5 h-3.5 text-neon-green" />
          <span>Banda de Incertidumbre ±95%</span>
        </div>
      </div>
      <div className="relative flex-1 w-full min-h-0">
        <Line data={chartData} options={options} />
      </div>
    </div>
  );
}
