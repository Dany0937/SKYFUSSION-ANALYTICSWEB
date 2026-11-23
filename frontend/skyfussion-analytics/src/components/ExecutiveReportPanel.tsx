import { useState } from "react";
import {
  AlertTriangle,
  Check,
  CheckCircle2,
  Code2,
  Copy,
  Download,
  FileText,
  RefreshCw,
  ShieldAlert,
} from "lucide-react";
import { AlertLevel, BasinMetrics, HydrologicalReport } from "../types/hydrology";

interface ExecutiveReportPanelProps {
  metrics: BasinMetrics;
  report: HydrologicalReport | null;
  generatedAt: string | null;
  isGenerating: boolean;
  error: string | null;
  onRetry: () => void;
}

function getAlertMeta(level: AlertLevel) {
  switch (level) {
    case "CRITICA":
      return {
        label: "CRÍTICA",
        subtitle: "Acción municipal inmediata",
        Icon: ShieldAlert,
        badgeClass:
          "text-[#BA1A1A] dark:text-[#F72585] border-[#BA1A1A]/35 dark:border-[#F72585]/45 bg-[#FFDAD6]/45 dark:bg-[#F72585]/12",
      };
    case "PREVENTIVA":
      return {
        label: "PREVENTIVA",
        subtitle: "Vigilancia y alistamiento",
        Icon: AlertTriangle,
        badgeClass:
          "text-[#B45309] dark:text-[#FFB703] border-[#D97706]/35 dark:border-[#FFB703]/45 bg-[#FEF3C7]/60 dark:bg-[#FFB703]/12",
      };
    case "NORMAL":
    default:
      return {
        label: "NORMAL",
        subtitle: "Condición hidráulica estable",
        Icon: CheckCircle2,
        badgeClass:
          "text-[#059669] dark:text-[#00F5D4] border-[#059669]/35 dark:border-[#00F5D4]/45 bg-[#D1FAE5]/50 dark:bg-[#00F5D4]/10",
      };
  }
}

export function ExecutiveReportPanel({
  metrics,
  report,
  generatedAt,
  isGenerating,
  error,
  onRetry,
}: ExecutiveReportPanelProps) {
  const [tab, setTab] = useState<"executive" | "json">("executive");
  const [copied, setCopied] = useState(false);

  const formattedJson = report ? JSON.stringify(report, null, 2) : "";

  const handleCopyJson = async () => {
    if (!formattedJson) return;
    try {
      await navigator.clipboard.writeText(formattedJson);
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    } catch {
      // Clipboard blocked in restricted context
    }
  };

  const handleDownloadJson = () => {
    if (!formattedJson) return;
    const blob = new Blob([formattedJson], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `skyfussion-reporte-${metrics.basinId}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const formattedTimestamp = generatedAt
    ? new Date(generatedAt).toLocaleString("es-CO", {
        dateStyle: "medium",
        timeStyle: "short",
      })
    : "Lectura de referencia";

  return (
    <aside className="w-full lg:w-[390px] xl:w-[420px] shrink-0 flex flex-col bg-[#FFFFFF] dark:bg-[#101A36] border border-[#E2E8F0] dark:border-[#1E2D5A] rounded-lg overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between gap-3 px-4 py-3 border-b border-[#E2E8F0] dark:border-[#1E2D5A]">
        <div className="flex items-center gap-2 min-w-0">
          <FileText
            className="w-4 h-4 text-[#0284C7] dark:text-[#00BBF9] shrink-0"
            aria-hidden="true"
          />
          <h2 className="font-display text-sm font-semibold text-[#0F172A] dark:text-[#DCE1FF] truncate">
            Dictamen Ejecutivo
          </h2>
        </div>

        <div
          role="group"
          aria-label="Modo de visualización del reporte"
          className="flex items-center gap-1 p-0.5 rounded bg-[#F1F5F9] dark:bg-[#0A1128] border border-[#E2E8F0] dark:border-[#1E2D5A]"
        >
          <button
            type="button"
            onClick={() => setTab("executive")}
            className={`px-2 py-1 rounded text-xs font-medium cursor-pointer transition-colors ${
              tab === "executive"
                ? "bg-[#FFFFFF] dark:bg-[#181E36] text-[#0F172A] dark:text-[#DCE1FF]"
                : "text-[#64748B] dark:text-[#8E9AB8]"
            }`}
          >
            Ejecutivo
          </button>
          <button
            type="button"
            onClick={() => setTab("json")}
            className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium cursor-pointer transition-colors ${
              tab === "json"
                ? "bg-[#FFFFFF] dark:bg-[#181E36] text-[#0284C7] dark:text-[#00BBF9]"
                : "text-[#64748B] dark:text-[#8E9AB8]"
            }`}
          >
            <Code2 className="w-3.5 h-3.5" aria-hidden="true" />
            <span>JSON</span>
          </button>
        </div>
      </div>

      {/* Body */}
      <div className="flex-1 p-4 flex flex-col justify-between gap-4">
        {isGenerating ? (
          <div className="flex flex-col gap-4 py-2" aria-busy="true">
            <div className="h-8 w-40 rounded bg-[#E2E8F0] dark:bg-[#1E2D5A]" />
            <div className="h-6 w-full rounded bg-[#E2E8F0] dark:bg-[#1E2D5A]" />
            <div className="h-6 w-4/5 rounded bg-[#E2E8F0] dark:bg-[#1E2D5A]" />
            <div className="space-y-2 pt-2">
              <div className="h-4 w-full rounded bg-[#F1F5F9] dark:bg-[#181E36]" />
              <div className="h-4 w-full rounded bg-[#F1F5F9] dark:bg-[#181E36]" />
              <div className="h-4 w-5/6 rounded bg-[#F1F5F9] dark:bg-[#181E36]" />
            </div>
            <div className="space-y-2 pt-3 border-t border-[#E2E8F0] dark:border-[#1E2D5A]">
              <div className="h-10 w-full rounded bg-[#F1F5F9] dark:bg-[#181E36]" />
              <div className="h-10 w-full rounded bg-[#F1F5F9] dark:bg-[#181E36]" />
              <div className="h-10 w-full rounded bg-[#F1F5F9] dark:bg-[#181E36]" />
            </div>
          </div>
        ) : error ? (
          <div className="rounded border border-[#BA1A1A]/40 dark:border-[#F72585]/50 bg-[#FFDAD6]/35 dark:bg-[#F72585]/10 p-4 flex flex-col gap-3">
            <div className="flex items-center gap-2 text-sm font-semibold text-[#BA1A1A] dark:text-[#F72585]">
              <ShieldAlert className="w-4 h-4 shrink-0" aria-hidden="true" />
              <span>No fue posible generar el dictamen</span>
            </div>
            <p className="text-xs leading-relaxed text-[#334155] dark:text-[#BCC8D1]">
              {error}
            </p>
            <div>
              <button
                type="button"
                onClick={onRetry}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium border border-[#BA1A1A]/40 dark:border-[#F72585]/50 text-[#BA1A1A] dark:text-[#F72585] hover:bg-[#FFFFFF] dark:hover:bg-[#0A1128] transition-colors cursor-pointer"
              >
                <RefreshCw className="w-3.5 h-3.5" aria-hidden="true" />
                <span>Reintentar análisis</span>
              </button>
            </div>
          </div>
        ) : !report ? (
          <div className="py-10 text-center flex flex-col items-center gap-3">
            <p className="text-sm text-[#334155] dark:text-[#BCC8D1] max-w-xs">
              Ajusta las métricas técnicas de la cuenca y ejecuta{" "}
              <strong>Generar Reporte</strong> para recibir el dictamen oficial
              del Agente Hidrológico.
            </p>
          </div>
        ) : tab === "json" ? (
          <div className="flex flex-col gap-3 h-full">
            <pre className="flex-1 p-3.5 rounded bg-[#F8FAFC] dark:bg-[#060D24] border border-[#E2E8F0] dark:border-[#1E2D5A] text-xs font-mono-tabular text-[#0F172A] dark:text-[#00F5D4] overflow-x-auto leading-relaxed whitespace-pre-wrap break-words">
              {formattedJson}
            </pre>
          </div>
        ) : (
          (() => {
            const meta = getAlertMeta(report.alert_level);
            const Icon = meta.Icon;
            return (
              <div className="flex flex-col gap-4">
                {/* Alert classification + metadata */}
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div
                    className={`inline-flex items-center gap-2 px-3 py-1.5 rounded border text-xs font-mono-tabular font-semibold ${meta.badgeClass}`}
                  >
                    <Icon className="w-4 h-4 shrink-0" aria-hidden="true" />
                    <span>ALERTA {meta.label}</span>
                  </div>
                  <span className="text-xs text-[#64748B] dark:text-[#8E9AB8]">
                    {meta.subtitle}
                  </span>
                </div>

                {/* Headline */}
                <div>
                  <h3 className="font-display text-lg font-semibold leading-snug text-[#0F172A] dark:text-[#DCE1FF] [text-wrap:balance]">
                    {report.headline}
                  </h3>
                  <p className="mt-1.5 text-xs text-[#64748B] dark:text-[#8E9AB8]">
                    {metrics.municipality} · {formattedTimestamp}
                  </p>
                </div>

                {/* Executive 3-line narrative */}
                <div className="pt-3 border-t border-[#E2E8F0] dark:border-[#1E2D5A]">
                  <p className="text-xs font-medium text-[#64748B] dark:text-[#8E9AB8] mb-1.5">
                    Síntesis ejecutiva para autoridades
                  </p>
                  <p className="text-sm leading-relaxed text-[#334155] dark:text-[#BCC8D1]">
                    {report.narrative}
                  </p>
                </div>

                {/* 3 Concrete recommendations */}
                <div className="pt-3 border-t border-[#E2E8F0] dark:border-[#1E2D5A]">
                  <p className="text-xs font-medium text-[#64748B] dark:text-[#8E9AB8] mb-2.5">
                    Acciones concretas recomendadas
                  </p>
                  <ol className="flex flex-col gap-2.5">
                    {report.recommendations.map((rec, index) => (
                      <li
                        key={index}
                        className="flex items-start gap-2.5 text-sm leading-snug text-[#0F172A] dark:text-[#DCE1FF]"
                      >
                        <span className="font-mono-tabular text-xs font-semibold text-[#0284C7] dark:text-[#00BBF9] pt-0.5 shrink-0">
                          0{index + 1}.
                        </span>
                        <span>{rec}</span>
                      </li>
                    ))}
                  </ol>
                </div>
              </div>
            );
          })()
        )}

        {/* Footer Actions when report is available */}
        {report && !isGenerating && (
          <div className="pt-3 border-t border-[#E2E8F0] dark:border-[#1E2D5A] flex items-center justify-between gap-2">
            <button
              type="button"
              onClick={handleCopyJson}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium border border-[#CBD5E1] dark:border-[#1E2D5A] text-[#334155] dark:text-[#BCC8D1] hover:border-[#0284C7] dark:hover:border-[#00BBF9] hover:text-[#0284C7] dark:hover:text-[#00BBF9] transition-colors cursor-pointer"
            >
              {copied ? (
                <>
                  <Check className="w-3.5 h-3.5 text-[#059669] dark:text-[#00F5D4]" />
                  <span>JSON copiado</span>
                </>
              ) : (
                <>
                  <Copy className="w-3.5 h-3.5" />
                  <span>Copiar JSON</span>
                </>
              )}
            </button>

            <button
              type="button"
              onClick={handleDownloadJson}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium border border-[#CBD5E1] dark:border-[#1E2D5A] text-[#334155] dark:text-[#BCC8D1] hover:border-[#0284C7] dark:hover:border-[#00BBF9] hover:text-[#0284C7] dark:hover:text-[#00BBF9] transition-colors cursor-pointer"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Exportar dictamen</span>
            </button>
          </div>
        )}
      </div>
    </aside>
  );
}
