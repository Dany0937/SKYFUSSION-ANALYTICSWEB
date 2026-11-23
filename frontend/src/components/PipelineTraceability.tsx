import React from "react";
import { CheckCircle2, Circle, Loader2, ShieldAlert } from "lucide-react";
import { PipelineStageState } from "../types/hydrology";

interface PipelineTraceabilityProps {
  stages: PipelineStageState[];
}

export function PipelineTraceability({ stages }: PipelineStageStateProps) {
  return (
    <div className="p-3.5 rounded-xl bg-control-card border border-control-border">
      <div className="flex flex-wrap items-center justify-between gap-2 pb-2 mb-2.5 border-b border-control-border text-xs">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-neon-cyan animate-pulse" />
          <h3 className="font-semibold text-slate-100">
            Trazabilidad de Eventos del Pipeline Orientado a Eventos
          </h3>
        </div>
        <span className="font-mono text-[11px] text-slate-400">
          AREA_DEFINED → REPORT_READY
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-2.5">
        {stages.map((stage, idx) => {
          const isCompleted = stage.status === "completed";
          const isRunning = stage.status === "running";
          const isError = stage.status === "error";

          return (
            <div
              key={stage.id}
              className={`flex flex-col gap-1 px-3 py-2 rounded-lg border text-xs transition-all ${
                isError
                  ? "border-neon-rose/50 bg-neon-rose/10 text-neon-rose"
                  : isRunning
                  ? "border-neon-cyan/50 bg-neon-cyan/10 text-slate-100 shadow-sm shadow-neon-cyan/20"
                  : isCompleted
                  ? "border-control-border bg-control-surface/50 text-slate-200"
                  : "border-control-border/60 bg-control-bg/40 opacity-60 text-slate-400"
              }`}
            >
              <div className="flex items-center justify-between gap-1">
                <span className="font-mono text-[10px] text-slate-400">0{idx + 1}</span>
                {isCompleted ? (
                  <CheckCircle2 className="w-3.5 h-3.5 text-neon-green" />
                ) : isRunning ? (
                  <Loader2 className="w-3.5 h-3.5 text-neon-cyan animate-spin" />
                ) : isError ? (
                  <ShieldAlert className="w-3.5 h-3.5 text-neon-rose" />
                ) : (
                  <Circle className="w-3.5 h-3.5 text-slate-600" />
                )}
              </div>
              <span className="font-mono font-semibold text-[11px] truncate">
                {stage.id}
              </span>
              <span className="text-[10px] text-slate-400 truncate">
                {stage.detail}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
type PipelineStageStateProps = PipelineTraceabilityProps;
