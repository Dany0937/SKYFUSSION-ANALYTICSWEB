import { useMemo, useState } from "react";
import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  GitCompare,
  Search,
  ShieldAlert,
  Trash2,
} from "lucide-react";
import { AlertLevel, HistoricalAlertEntry } from "../types/hydrology";

interface HistoryComparisonViewProps {
  entries: HistoricalAlertEntry[];
  onLoadToConsole: (entry: HistoricalAlertEntry) => void;
  onDeleteEntry: (id: string) => void;
}

function AlertTag({ level }: { level: AlertLevel }) {
  if (level === "CRITICA") {
    return (
      <span className="inline-flex items-center gap-1.5 font-mono-tabular text-xs font-semibold text-[#BA1A1A] dark:text-[#F72585]">
        <ShieldAlert className="w-3.5 h-3.5 shrink-0" aria-hidden="true" />
        <span>CRÍTICA</span>
      </span>
    );
  }
  if (level === "PREVENTIVA") {
    return (
      <span className="inline-flex items-center gap-1.5 font-mono-tabular text-xs font-semibold text-[#B45309] dark:text-[#FFB703]">
        <AlertTriangle className="w-3.5 h-3.5 shrink-0" aria-hidden="true" />
        <span>PREVENTIVA</span>
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1.5 font-mono-tabular text-xs font-semibold text-[#059669] dark:text-[#00F5D4]">
      <CheckCircle2 className="w-3.5 h-3.5 shrink-0" aria-hidden="true" />
      <span>NORMAL</span>
    </span>
  );
}

function formatDelta(val: number, decimals = 2, suffix = "") {
  const sign = val > 0 ? "+" : "";
  return `${sign}${val.toFixed(decimals)}${suffix}`;
}

export function HistoryComparisonView({
  entries,
  onLoadToConsole,
  onDeleteEntry,
}: HistoryComparisonViewProps) {
  const [filterLevel, setFilterLevel] = useState<"ALL" | AlertLevel>("ALL");
  const [searchQuery, setSearchQuery] = useState("");
  const [compareAId, setCompareAId] = useState<string>(entries[1]?.id ?? entries[0]?.id ?? "");
  const [compareBId, setCompareBId] = useState<string>(entries[0]?.id ?? "");

  const filteredEntries = useMemo(() => {
    return entries.filter((entry) => {
      const matchesLevel =
        filterLevel === "ALL" || entry.report.alert_level === filterLevel;
      const q = searchQuery.trim().toLowerCase();
      const matchesSearch =
        !q ||
        entry.metrics.basinName.toLowerCase().includes(q) ||
        entry.metrics.municipality.toLowerCase().includes(q) ||
        entry.report.headline.toLowerCase().includes(q);
      return matchesLevel && matchesSearch;
    });
  }, [entries, filterLevel, searchQuery]);

  const entryA = entries.find((e) => e.id === compareAId) ?? entries[1] ?? entries[0];
  const entryB = entries.find((e) => e.id === compareBId) ?? entries[0];

  return (
    <div className="flex flex-col gap-6">
      {/* Side-by-side comparison studio */}
      {entryA && entryB && (
        <section className="bg-[#FFFFFF] dark:bg-[#101A36] border border-[#E2E8F0] dark:border-[#1E2D5A] rounded-lg p-5">
          <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-[#E2E8F0] dark:border-[#1E2D5A]">
            <div className="flex items-center gap-2">
              <GitCompare
                className="w-4 h-4 text-[#0284C7] dark:text-[#00BBF9]"
                aria-hidden="true"
              />
              <h2 className="font-display text-base font-semibold text-[#0F172A] dark:text-[#DCE1FF]">
                Comparativa Hidrológica Lado a Lado
              </h2>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <div className="flex items-center gap-2">
                <label
                  htmlFor="compare-select-a"
                  className="text-xs font-mono-tabular text-[#64748B] dark:text-[#8E9AB8]"
                >
                  Lectura A:
                </label>
                <select
                  id="compare-select-a"
                  value={entryA.id}
                  onChange={(e) => setCompareAId(e.target.value)}
                  className="rounded px-2.5 py-1.5 text-xs bg-[#F8FAFC] dark:bg-[#0A1128] border border-[#CBD5E1] dark:border-[#1E2D5A] text-[#0F172A] dark:text-[#DCE1FF]"
                >
                  {entries.map((entry) => (
                    <option key={entry.id} value={entry.id}>
                      {entry.metrics.basinName} (
                      {new Date(entry.timestamp).toLocaleDateString("es-CO")})
                    </option>
                  ))}
                </select>
              </div>

              <ArrowRight
                className="w-4 h-4 text-[#64748B] dark:text-[#8E9AB8]"
                aria-hidden="true"
              />

              <div className="flex items-center gap-2">
                <label
                  htmlFor="compare-select-b"
                  className="text-xs font-mono-tabular text-[#64748B] dark:text-[#8E9AB8]"
                >
                  Lectura B:
                </label>
                <select
                  id="compare-select-b"
                  value={entryB.id}
                  onChange={(e) => setCompareBId(e.target.value)}
                  className="rounded px-2.5 py-1.5 text-xs bg-[#F8FAFC] dark:bg-[#0A1128] border border-[#CBD5E1] dark:border-[#1E2D5A] text-[#0F172A] dark:text-[#DCE1FF]"
                >
                  {entries.map((entry) => (
                    <option key={entry.id} value={entry.id}>
                      {entry.metrics.basinName} (
                      {new Date(entry.timestamp).toLocaleDateString("es-CO")})
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Metric Deltas Strip */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 py-4 border-b border-[#E2E8F0] dark:border-[#1E2D5A]">
            <div>
              <span className="text-xs text-[#64748B] dark:text-[#8E9AB8]">
                Variación NDWI (B vs A)
              </span>
              <p className="font-mono-tabular text-lg font-semibold text-[#0284C7] dark:text-[#00BBF9] mt-0.5">
                {formatDelta(entryB.metrics.ndwi - entryA.metrics.ndwi, 2)}
              </p>
              <span className="font-mono-tabular text-[11px] text-[#64748B] dark:text-[#8E9AB8]">
                {entryA.metrics.ndwi.toFixed(2)} → {entryB.metrics.ndwi.toFixed(2)}
              </span>
            </div>

            <div>
              <span className="text-xs text-[#64748B] dark:text-[#8E9AB8]">
                Variación NDVI (B vs A)
              </span>
              <p className="font-mono-tabular text-lg font-semibold text-[#059669] dark:text-[#00F5D4] mt-0.5">
                {formatDelta(entryB.metrics.ndvi - entryA.metrics.ndvi, 2)}
              </p>
              <span className="font-mono-tabular text-[11px] text-[#64748B] dark:text-[#8E9AB8]">
                {entryA.metrics.ndvi.toFixed(2)} → {entryB.metrics.ndvi.toFixed(2)}
              </span>
            </div>

            <div>
              <span className="text-xs text-[#64748B] dark:text-[#8E9AB8]">
                Delta Ancho del Cauce
              </span>
              <p className="font-mono-tabular text-lg font-semibold text-[#0F172A] dark:text-[#DCE1FF] mt-0.5">
                {formatDelta(
                  entryB.metrics.channelWidthChangePct -
                    entryA.metrics.channelWidthChangePct,
                  1,
                  " pp"
                )}
              </p>
              <span className="font-mono-tabular text-[11px] text-[#64748B] dark:text-[#8E9AB8]">
                {entryA.metrics.channelWidthChangePct.toFixed(1)}% →{" "}
                {entryB.metrics.channelWidthChangePct.toFixed(1)}%
              </span>
            </div>

            <div>
              <span className="text-xs text-[#64748B] dark:text-[#8E9AB8]">
                Delta Caudal Proyectado
              </span>
              <p className="font-mono-tabular text-lg font-semibold text-[#0F172A] dark:text-[#DCE1FF] mt-0.5">
                {formatDelta(
                  entryB.metrics.predictedDischargeM3s -
                    entryA.metrics.predictedDischargeM3s,
                  0,
                  " m³/s"
                )}
              </p>
              <span className="font-mono-tabular text-[11px] text-[#64748B] dark:text-[#8E9AB8]">
                {entryA.metrics.predictedDischargeM3s.toLocaleString("es-CO")} →{" "}
                {entryB.metrics.predictedDischargeM3s.toLocaleString("es-CO")} m³/s
              </span>
            </div>
          </div>

          {/* Narratives Comparison */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4">
            {[
              { label: "Lectura A", item: entryA },
              { label: "Lectura B", item: entryB },
            ].map(({ label, item }) => (
              <div key={label} className="flex flex-col gap-2">
                <div className="flex items-center justify-between gap-2">
                  <span className="font-mono-tabular text-xs font-semibold text-[#64748B] dark:text-[#8E9AB8]">
                    {label} ·{" "}
                    {new Date(item.timestamp).toLocaleString("es-CO", {
                      dateStyle: "short",
                      timeStyle: "short",
                    })}
                  </span>
                  <AlertTag level={item.report.alert_level} />
                </div>
                <h3 className="font-display text-sm font-semibold text-[#0F172A] dark:text-[#DCE1FF]">
                  {item.metrics.basinName}
                </h3>
                <p className="text-sm font-medium text-[#0284C7] dark:text-[#00BBF9]">
                  {item.report.headline}
                </p>
                <p className="text-xs leading-relaxed text-[#334155] dark:text-[#BCC8D1]">
                  {item.report.narrative}
                </p>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Historical Log Table */}
      <section className="bg-[#FFFFFF] dark:bg-[#101A36] border border-[#E2E8F0] dark:border-[#1E2D5A] rounded-lg overflow-hidden">
        <div className="flex flex-wrap items-center justify-between gap-4 px-5 py-4 border-b border-[#E2E8F0] dark:border-[#1E2D5A]">
          <div>
            <h2 className="font-display text-base font-semibold text-[#0F172A] dark:text-[#DCE1FF]">
              Registro Histórico de Alertas Hidrológicas
            </h2>
            <p className="text-xs text-[#64748B] dark:text-[#8E9AB8] mt-0.5">
              {filteredEntries.length} de {entries.length} dictámenes registrados
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {/* Search */}
            <div className="relative">
              <Search
                className="w-3.5 h-3.5 text-[#64748B] dark:text-[#8E9AB8] absolute left-3 top-1/2 -translate-y-1/2"
                aria-hidden="true"
              />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Buscar cuenca o alcaldía..."
                className="pl-8 pr-3 py-1.5 rounded text-xs bg-[#F8FAFC] dark:bg-[#0A1128] border border-[#CBD5E1] dark:border-[#1E2D5A] text-[#0F172A] dark:text-[#DCE1FF] placeholder:text-[#64748B] dark:placeholder:text-[#8E9AB8] focus:outline-none focus:border-[#0284C7] dark:focus:border-[#00BBF9]"
              />
            </div>

            {/* Alert Level Filter */}
            <div
              role="group"
              aria-label="Filtrar por nivel de alerta"
              className="flex items-center gap-1 p-1 rounded bg-[#F1F5F9] dark:bg-[#0A1128] border border-[#E2E8F0] dark:border-[#1E2D5A]"
            >
              {(["ALL", "NORMAL", "PREVENTIVA", "CRITICA"] as const).map((lvl) => (
                <button
                  key={lvl}
                  type="button"
                  onClick={() => setFilterLevel(lvl)}
                  className={`px-2.5 py-1 rounded text-xs font-medium cursor-pointer transition-colors ${
                    filterLevel === lvl
                      ? "bg-[#FFFFFF] dark:bg-[#181E36] text-[#0284C7] dark:text-[#00BBF9]"
                      : "text-[#64748B] dark:text-[#8E9AB8] hover:text-[#0F172A] dark:hover:text-[#DCE1FF]"
                  }`}
                >
                  {lvl === "ALL" ? "Todas" : lvl}
                </button>
              ))}
            </div>
          </div>
        </div>

        {filteredEntries.length === 0 ? (
          <div className="py-12 text-center px-4">
            <p className="text-sm text-[#334155] dark:text-[#BCC8D1]">
              No hay registros que coincidan con el filtro aplicado.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-[#F1F5F9] dark:bg-[#141A32] border-b border-[#CBD5E1] dark:border-[#1E2D5A] text-[11px] font-mono-tabular uppercase tracking-wider text-[#334155] dark:text-[#BCC8D1]">
                  <th className="py-3 px-4 font-semibold">Fecha / Origen</th>
                  <th className="py-3 px-4 font-semibold">Cuenca y Titular</th>
                  <th className="py-3 px-4 font-semibold">Severidad</th>
                  <th className="py-3 px-4 font-semibold text-right">NDWI</th>
                  <th className="py-3 px-4 font-semibold text-right">NDVI</th>
                  <th className="py-3 px-4 font-semibold text-right">Cauce</th>
                  <th className="py-3 px-4 font-semibold text-right">Caudal</th>
                  <th className="py-3 px-4 font-semibold text-right">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E2E8F0] dark:divide-[#1E2D5A] text-xs">
                {filteredEntries.map((entry) => (
                  <tr
                    key={entry.id}
                    className="hover:bg-[#F8FAFC] dark:hover:bg-[#141A32]/70 transition-colors"
                  >
                    <td className="py-3 px-4 whitespace-nowrap font-mono-tabular text-[#64748B] dark:text-[#8E9AB8]">
                      <div>
                        {new Date(entry.timestamp).toLocaleDateString("es-CO", {
                          day: "2-digit",
                          month: "short",
                          year: "numeric",
                        })}
                      </div>
                      <div className="text-[11px]">
                        {entry.source === "ia" ? "Agente IA" : "Línea base"}
                      </div>
                    </td>
                    <td className="py-3 px-4 max-w-md">
                      <div className="font-semibold text-[#0F172A] dark:text-[#DCE1FF]">
                        {entry.metrics.basinName}
                      </div>
                      <div className="text-[#334155] dark:text-[#BCC8D1] mt-0.5 line-clamp-1">
                        {entry.report.headline}
                      </div>
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap">
                      <AlertTag level={entry.report.alert_level} />
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap text-right font-mono-tabular text-[#0284C7] dark:text-[#00BBF9]">
                      {entry.metrics.ndwi.toFixed(2)}
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap text-right font-mono-tabular text-[#059669] dark:text-[#00F5D4]">
                      {entry.metrics.ndvi.toFixed(2)}
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap text-right font-mono-tabular text-[#0F172A] dark:text-[#DCE1FF]">
                      {entry.metrics.channelWidthChangePct >= 0 ? "+" : ""}
                      {entry.metrics.channelWidthChangePct.toFixed(1)}%
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap text-right font-mono-tabular text-[#0F172A] dark:text-[#DCE1FF]">
                      {entry.metrics.predictedDischargeM3s.toLocaleString("es-CO")} m³/s
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap text-right">
                      <div className="inline-flex items-center gap-1.5">
                        <button
                          type="button"
                          onClick={() => setCompareAId(entry.id)}
                          className={`px-2 py-1 rounded text-[11px] font-mono-tabular border cursor-pointer ${
                            compareAId === entry.id
                              ? "border-[#0284C7] dark:border-[#00BBF9] text-[#0284C7] dark:text-[#00BBF9]"
                              : "border-[#CBD5E1] dark:border-[#1E2D5A] text-[#64748B] dark:text-[#8E9AB8]"
                          }`}
                        >
                          Fijar A
                        </button>
                        <button
                          type="button"
                          onClick={() => setCompareBId(entry.id)}
                          className={`px-2 py-1 rounded text-[11px] font-mono-tabular border cursor-pointer ${
                            compareBId === entry.id
                              ? "border-[#0284C7] dark:border-[#00BBF9] text-[#0284C7] dark:text-[#00BBF9]"
                              : "border-[#CBD5E1] dark:border-[#1E2D5A] text-[#64748B] dark:text-[#8E9AB8]"
                          }`}
                        >
                          Fijar B
                        </button>
                        <button
                          type="button"
                          onClick={() => onLoadToConsole(entry)}
                          className="px-2 py-1 rounded text-[11px] font-medium border border-[#CBD5E1] dark:border-[#1E2D5A] text-[#0F172A] dark:text-[#DCE1FF] hover:border-[#0284C7] dark:hover:border-[#00BBF9] cursor-pointer"
                        >
                          Cargar
                        </button>
                        {entries.length > 2 && (
                          <button
                            type="button"
                            onClick={() => onDeleteEntry(entry.id)}
                            title="Eliminar registro"
                            className="p-1 rounded text-[#64748B] hover:text-[#BA1A1A] dark:hover:text-[#F72585] cursor-pointer"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
