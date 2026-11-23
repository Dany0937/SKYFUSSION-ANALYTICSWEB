import { CheckCircle2, Circle, Loader2, ShieldAlert } from "lucide-react";
import { PipelineStageState } from "../types/hydrology";

interface EventPipelineBarProps {
  stages: PipelineStageState[];
}

export function EventPipelineBar({ stages }: EventPipelineBarProps) {
  return (
    <section
      aria-label="Pipeline de eventos del sistema"
      className="bg-[#FFFFFF] dark:bg-[#101A36] border border-[#E2E8F0] dark:border-[#1E2D5A] rounded-lg px-4 py-3"
    >
      <div className="flex flex-wrap items-center justify-between gap-2 pb-2.5 mb-3 border-b border-[#E2E8F0] dark:border-[#1E2D5A]">
        <h2 className="font-display text-xs font-semibold text-[#0F172A] dark:text-[#DCE1FF]">
          Trazabilidad de Eventos del Pipeline
        </h2>
        <span className="font-mono-tabular text-[11px] text-[#64748B] dark:text-[#8E9AB8]">
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
              className={`flex flex-col gap-1 px-3 py-2 rounded border text-xs transition-colors ${
                isError
                  ? "border-[#BA1A1A]/40 dark:border-[#F72585]/45 bg-[#FFDAD6]/30 dark:bg-[#F72585]/10"
                  : isRunning
                    ? "border-[#0284C7] dark:border-[#00BBF9] bg-[#0284C7]/8 dark:bg-[#00BBF9]/10"
                    : isCompleted
                      ? "border-[#E2E8F0] dark:border-[#1E2D5A] bg-[#F8FAFC] dark:bg-[#0A1128]"
                      : "border-[#E2E8F0] dark:border-[#1E2D5A] opacity-65"
              }`}
            >
              <div className="flex items-center justify-between gap-2">
                <span className="font-mono-tabular text-[10px] font-semibold text-[#64748B] dark:text-[#8E9AB8]">
                  0{idx + 1}
                </span>
                {isCompleted ? (
                  <CheckCircle2
                    className="w-3.5 h-3.5 text-[#059669] dark:text-[#00F5D4] shrink-0"
                    aria-hidden="true"
                  />
                ) : isRunning ? (
                  <Loader2
                    className="w-3.5 h-3.5 text-[#0284C7] dark:text-[#00BBF9] animate-spin shrink-0"
                    aria-hidden="true"
                  />
                ) : isError ? (
                  <ShieldAlert
                    className="w-3.5 h-3.5 text-[#BA1A1A] dark:text-[#F72585] shrink-0"
                    aria-hidden="true"
                  />
                ) : (
                  <Circle
                    className="w-3.5 h-3.5 text-[#94A3B8] dark:text-[#64748B] shrink-0"
                    aria-hidden="true"
                  />
                )}
              </div>

              <p className="font-mono-tabular text-[11px] font-semibold text-[#0F172A] dark:text-[#DCE1FF] truncate">
                {stage.id}
              </p>

              <p className="text-[11px] text-[#64748B] dark:text-[#8E9AB8] truncate">
                {stage.detail ||
                  (isCompleted
                    ? "Completado"
                    : isRunning
                      ? "Procesando..."
                      : isError
                        ? "Error"
                        : "En espera")}
              </p>
            </div>
          );
        })}
      </div>
    </section>
  );
}
