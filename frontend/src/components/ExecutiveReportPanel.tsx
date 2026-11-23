import React, { useState } from "react";
import {
  FileText,
  AlertTriangle,
  CheckCircle2,
  ShieldAlert,
  Play,
  Loader2,
  Copy,
  Check,
  Download,
  ListOrdered,
  Sparkles,
} from "lucide-react";
import { AlertLevel, HydrologicalReport } from "../types/hydrology";

interface ExecutiveReportPanelProps {
  report: HydrologicalReport;
  isAnalyzing: boolean;
  onExecuteAnalysis: () => void;
  areaName: string;
}

export function ExecutiveReportPanel({
  report,
  isAnalyzing,
  onExecuteAnalysis,
  areaName,
}: ExecutiveReportPanelProps) {
  const [activeTab, setActiveTab] = useState<"narrative" | "json">("narrative");
  const [copied, setCopied] = useState(false);

  const getBadgeStyle = (level: AlertLevel) => {
    switch (level) {
      case "CRITICA":
        return {
          bg: "bg-neon-rose/15 border-neon-rose text-neon-rose",
          label: "ALERTA CRÍTICA",
          icon: ShieldAlert,
          glow: "shadow-neon-rose/30",
        };
      case "PREVENTIVA":
        return {
          bg: "bg-neon-amber/15 border-neon-amber text-neon-amber",
          label: "ALERTA PREVENTIVA",
          icon: AlertTriangle,
          glow: "shadow-neon-amber/30",
        };
      case "NORMAL":
      default:
        return {
          bg: "bg-neon-green/15 border-neon-green text-neon-green",
          label: "CONDICIÓN NORMAL",
          icon: CheckCircle2,
          glow: "shadow-neon-green/30",
        };
    }
  };

  const badge = getBadgeStyle(report.alert_level);
  const BadgeIcon = badge.icon;
  const jsonString = JSON.stringify(report, null, 2);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(jsonString);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Ignorar bloqueo de portapapeles
    }
  };

  const handleDownload = () => {
    const blob = new Blob([jsonString], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `reporte-ia-${areaName.toLowerCase().replace(/\s+/g, "-")}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="p-4 rounded-xl bg-control-card border border-control-border flex flex-col h-full">
      {/* Cabecera del Reporte y Botón de Ejecutar Análisis */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 mb-3 border-b border-control-border">
        <div className="flex items-center gap-2">
          <FileText className="w-4 h-4 text-neon-cyan" />
          <h3 className="text-sm font-semibold text-slate-100">
            Reporte Ejecutivo de Inteligencia Artificial
          </h3>
        </div>

        <div className="flex items-center gap-2">
          {/* Selector de Pestaña */}
          <div className="flex items-center bg-control-bg p-0.5 rounded-lg border border-control-border text-xs">
            <button
              type="button"
              onClick={() => setActiveTab("narrative")}
              className={`px-2.5 py-1 rounded transition-colors ${
                activeTab === "narrative"
                  ? "bg-control-surface text-slate-100 font-semibold"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Dictamen
            </button>
            <button
              type="button"
              onClick={() => setActiveTab("json")}
              className={`px-2.5 py-1 rounded transition-colors ${
                activeTab === "json"
                  ? "bg-control-surface text-slate-100 font-semibold"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              JSON
            </button>
          </div>

          {/* Botón Principal de Ejecutar Análisis */}
          <button
            type="button"
            onClick={onExecuteAnalysis}
            disabled={isAnalyzing}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-neon-cyan text-control-bg font-bold text-xs hover:bg-[#38ccf9] transition-all disabled:opacity-60 disabled:cursor-not-allowed shadow-md shadow-neon-cyan/20 cursor-pointer"
          >
            {isAnalyzing ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                <span>Ejecutando...</span>
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 fill-current" />
                <span>Ejecutar Análisis</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Contenido según pestaña */}
      {activeTab === "narrative" ? (
        <div className="flex flex-col gap-3.5 flex-1 overflow-y-auto pr-1">
          {/* Insignia de Alerta */}
          <div className="flex items-center justify-between gap-2 p-3 rounded-lg bg-control-bg border border-control-border">
            <div className="flex items-center gap-2">
              <span
                className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold border ${badge.bg} shadow-sm ${badge.glow}`}
              >
                <BadgeIcon className="w-3.5 h-3.5" />
                {badge.label}
              </span>
              <span className="text-xs text-slate-400">Área: {areaName}</span>
            </div>
            <span className="text-[11px] font-mono text-slate-400 flex items-center gap-1">
              <Sparkles className="w-3 h-3 text-neon-cyan" />
              ReportingAgent
            </span>
          </div>

          {/* Titular */}
          <h4 className="text-sm font-semibold text-slate-200 leading-snug">
            {report.headline}
          </h4>

          {/* Narrativa en Lenguaje Natural */}
          <div className="p-3 rounded-lg bg-control-bg/60 border border-control-border text-xs text-slate-300 leading-relaxed space-y-2">
            <p>{report.narrative}</p>
          </div>

          {/* 3 Recomendaciones Operativas */}
          <div>
            <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1.5 mb-2">
              <ListOrdered className="w-3.5 h-3.5 text-neon-green" />
              Recomendaciones Operativas
            </span>
            <div className="space-y-2">
              {report.recommendations.map((rec, idx) => (
                <div
                  key={idx}
                  className="flex items-start gap-2.5 p-2 rounded-lg bg-control-bg border border-control-border text-xs text-slate-300"
                >
                  <span className="w-5 h-5 rounded-full bg-neon-green/15 text-neon-green border border-neon-green/40 flex items-center justify-center font-mono font-bold text-[10px] shrink-0 mt-0.5">
                    {idx + 1}
                  </span>
                  <span className="leading-tight">{rec}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : (
        <div className="flex flex-col flex-1 min-h-[220px]">
          <div className="flex items-center justify-end gap-2 mb-2">
            <button
              type="button"
              onClick={handleCopy}
              className="flex items-center gap-1 px-2.5 py-1 bg-control-bg border border-control-border rounded text-xs text-slate-300 hover:text-slate-100"
            >
              {copied ? (
                <>
                  <Check className="w-3.5 h-3.5 text-neon-green" />
                  <span>Copiado</span>
                </>
              ) : (
                <>
                  <Copy className="w-3.5 h-3.5" />
                  <span>Copiar</span>
                </>
              )}
            </button>
            <button
              type="button"
              onClick={handleDownload}
              className="flex items-center gap-1 px-2.5 py-1 bg-control-bg border border-control-border rounded text-xs text-slate-300 hover:text-slate-100"
            >
              <Download className="w-3.5 h-3.5 text-neon-cyan" />
              <span>Descargar .json</span>
            </button>
          </div>
          <pre className="flex-1 p-3 bg-control-bg border border-control-border rounded-lg text-[11px] font-mono text-neon-cyan/90 overflow-auto">
            {jsonString}
          </pre>
        </div>
      )}
    </div>
  );
}
