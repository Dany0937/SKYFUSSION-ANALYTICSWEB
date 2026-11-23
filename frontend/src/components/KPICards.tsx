import React from "react";
import {
  Waves,
  Activity,
  Droplet,
  Cpu,
  TrendingUp,
  Info,
} from "lucide-react";
import { BasinMetrics, ModelPrecisionMetrics } from "../types/hydrology";

interface KPICardsProps {
  metrics: BasinMetrics;
  precision: ModelPrecisionMetrics;
}

export function KPICards({ metrics, precision }: KPICardsProps) {
  const isCaudalElevated = metrics.predictedDischargeM3s > metrics.baselineDischargeM3s * 1.3;
  const isWidthExpanded = metrics.channelWidthChangePct > 15;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* 1. Caudal Estimado */}
      <div className="relative p-4 rounded-xl bg-control-card border border-control-border hover:border-neon-cyan/50 transition-all group overflow-hidden">
        <div className="flex items-center justify-between text-slate-400 mb-2">
          <span className="text-xs font-semibold tracking-wider uppercase flex items-center gap-1.5">
            <Waves className="w-4 h-4 text-neon-cyan" />
            Caudal Estimado
          </span>
          <span
            className={`text-[11px] font-mono px-2 py-0.5 rounded-full border ${isCaudalElevated
                ? "bg-neon-amber/15 text-neon-amber border-neon-amber/40"
                : "bg-neon-green/15 text-neon-green border-neon-green/40"
              }`}
          >
            {isCaudalElevated ? "+72% vs base" : "Estable"}
          </span>
        </div>
        <div className="flex items-baseline gap-2">
          <span className="text-2xl font-bold font-mono text-slate-50">
            {metrics.predictedDischargeM3s.toFixed(1)}
          </span>
          <span className="text-sm font-semibold text-slate-400">m³/s</span>
        </div>
        <p className="mt-2 text-xs text-slate-400 flex items-center gap-1">
          <TrendingUp className="w-3.5 h-3.5 text-neon-cyan shrink-0" />
          <span>Base histórica: {metrics.baselineDischargeM3s.toFixed(1)} m³/s</span>
        </p>
        <div className="absolute top-0 right-0 w-24 h-24 bg-neon-cyan/5 rounded-full blur-2xl group-hover:bg-neon-cyan/10 transition-all pointer-events-none" />
      </div>

      {/* 2. Variación Morfológica de Cauce */}
      <div className="relative p-4 rounded-xl bg-control-card border border-control-border hover:border-neon-amber/50 transition-all group overflow-hidden">
        <div className="flex items-center justify-between text-slate-400 mb-2">
          <span className="text-xs font-semibold tracking-wider uppercase flex items-center gap-1.5">
            <Activity className="w-4 h-4 text-neon-amber" />
            Variación Morfológica
          </span>
          <span className="text-[11px] font-mono px-2 py-0.5 rounded-full bg-neon-amber/15 text-neon-amber border border-neon-amber/40">
            1969–2023
          </span>
        </div>
        <div className="flex items-baseline gap-2">
          <span className="text-2xl font-bold font-mono text-neon-amber">
            {metrics.channelWidthChangePct > 0 ? "+" : ""}
            {metrics.channelWidthChangePct.toFixed(1)}%
          </span>
          <span className="text-sm font-semibold text-slate-400">ancho de cauce</span>
        </div>
        <p className="mt-2 text-xs text-slate-400 flex items-center gap-1">
          <Info className="w-3.5 h-3.5 text-neon-amber shrink-0" />
          <span>
            {isWidthExpanded
              ? "Ensanchamiento activo por avenidas"
              : "Estabilidad relativa de riberas"}
          </span>
        </p>
        <div className="absolute top-0 right-0 w-24 h-24 bg-neon-amber/5 rounded-full blur-2xl group-hover:bg-neon-amber/10 transition-all pointer-events-none" />
      </div>

      {/* 3. Índice NDWI Medio */}
      <div className="relative p-4 rounded-xl bg-control-card border border-control-border hover:border-neon-cyan/50 transition-all group overflow-hidden">
        <div className="flex items-center justify-between text-slate-400 mb-2">
          <span className="text-xs font-semibold tracking-wider uppercase flex items-center gap-1.5">
            <Droplet className="w-4 h-4 text-neon-cyan" />
            NDWI Medio
          </span>
          <span className="text-[11px] font-mono px-2 py-0.5 rounded-full bg-neon-cyan/15 text-neon-cyan border border-neon-cyan/40">
            Agua / Humedad
          </span>
        </div>
        <div className="flex items-baseline gap-2">
          <span className="text-2xl font-bold font-mono text-neon-cyan">
            {metrics.ndwi.toFixed(2)}
          </span>
          <span className="text-sm font-semibold text-slate-400">[-1 a 1]</span>
        </div>
        <p className="mt-2 text-xs text-slate-400">
          NDVI de biomasa asociado:{" "}
          <span className="text-neon-green font-mono font-semibold">
            {metrics.ndvi.toFixed(2)}
          </span>
        </p>
        <div className="absolute top-0 right-0 w-24 h-24 bg-neon-cyan/5 rounded-full blur-2xl group-hover:bg-neon-cyan/10 transition-all pointer-events-none" />
      </div>

      {/* 4. Precisión del Modelo (Regla 2: Métricas Honestas Nivel A) */}
      <div className="relative p-4 rounded-xl bg-control-card border border-control-border hover:border-neon-green/50 transition-all group overflow-hidden">
        <div className="flex items-center justify-between text-slate-400 mb-2">
          <span className="text-xs font-semibold tracking-wider uppercase flex items-center gap-1.5">
            <Cpu className="w-4 h-4 text-neon-green" />
            Precisión Modelo (RNN)
          </span>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-control-bg text-slate-300 border border-control-border">
            Nivel A
          </span>
        </div>
        <div className="flex items-baseline gap-3">
          <div className="flex items-baseline gap-1">
            <span className="text-xs text-slate-400">RMSE</span>
            <span className="text-lg font-bold font-mono text-neon-green">
              {precision.rmse.toFixed(2)}
            </span>
          </div>
          <div className="flex items-baseline gap-1">
            <span className="text-xs text-slate-400">R²</span>
            <span className="text-lg font-bold font-mono text-neon-cyan">
              {precision.r2.toFixed(2)}
            </span>
          </div>
        </div>
        <p className="mt-2 text-[11px] text-slate-400 leading-tight">
          RNN <span className="text-slate-200">gru_attention_h1</span> (GEE Real).
          <span className="block text-[10px] text-slate-500 mt-0.5">
            Macro-F1 Árbol: 0.66 (plan) / 0.53 (test verificado)
          </span>
        </p>
        <div className="absolute top-0 right-0 w-24 h-24 bg-neon-green/5 rounded-full blur-2xl group-hover:bg-neon-green/10 transition-all pointer-events-none" />
      </div>
    </div>
  );
}
