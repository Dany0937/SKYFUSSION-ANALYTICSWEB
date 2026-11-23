import { ActiveView } from "../types/hydrology";

interface TopBarProps {
  activeView: ActiveView;
  onChangeView: (view: ActiveView) => void;
  onGenerateReport: () => void;
  isGenerating: boolean;
}

const NAV_ITEMS: { id: ActiveView; label: string }[] = [
  { id: "console", label: "Consola" },
  { id: "history", label: "Historial" },
  { id: "methodology", label: "Metodología" },
];

export function TopBar({
  activeView,
  onChangeView,
  onGenerateReport,
  isGenerating,
}: TopBarProps) {
  return (
    <header className="w-full border-b border-[#E2E8F0] dark:border-[#1E2D5A] bg-[#FFFFFF] dark:bg-[#0B1229]">
      <div className="max-w-[1600px] mx-auto px-4 md:px-6 h-14 flex items-center justify-between gap-8">
        {/* Zone 1: Brand wordmark (single line, no descriptor/pill) */}
        <button
          type="button"
          onClick={() => onChangeView("console")}
          className="font-display text-lg font-bold tracking-tight text-[#0F172A] dark:text-[#DCE1FF] whitespace-nowrap shrink-0 cursor-pointer focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-[#0284C7] dark:focus-visible:outline-[#00BBF9]"
        >
          Skyfussion Analytics
        </button>

        {/* Zone 2: Clean text navigation links */}
        <nav
          aria-label="Navegación principal"
          className="hidden sm:flex items-center gap-6"
        >
          {NAV_ITEMS.map((item) => {
            const isActive = activeView === item.id;
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => onChangeView(item.id)}
                className={`relative py-1 text-sm font-medium whitespace-nowrap shrink-0 transition-colors duration-150 cursor-pointer focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-[#0284C7] dark:focus-visible:outline-[#00BBF9] ${
                  isActive
                    ? "text-[#0284C7] dark:text-[#00BBF9]"
                    : "text-[#334155] dark:text-[#BCC8D1] hover:text-[#0F172A] dark:hover:text-[#DCE1FF]"
                }`}
              >
                {item.label}
                {isActive && (
                  <span
                    aria-hidden="true"
                    className="absolute inset-x-0 -bottom-[17px] h-[2px] bg-[#0284C7] dark:bg-[#00BBF9]"
                  />
                )}
              </button>
            );
          })}
        </nav>

        {/* Zone 3: Single primary action */}
        <div className="flex items-center shrink-0">
          <button
            type="button"
            onClick={onGenerateReport}
            disabled={isGenerating}
            className="px-4 py-2 rounded text-xs font-display font-semibold tracking-tight whitespace-nowrap shrink-0 transition-all duration-150 cursor-pointer disabled:opacity-60 disabled:cursor-not-allowed bg-[#0284C7] hover:bg-[#0EA5E9] text-white dark:bg-[#00BBF9] dark:hover:bg-[#38CCF9] dark:text-[#0A1128] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#0284C7] dark:focus-visible:outline-[#00BBF9]"
          >
            {isGenerating ? "Analizando cuenca..." : "Generar Reporte"}
          </button>
        </div>
      </div>

      {/* Mobile navigation strip */}
      <nav
        aria-label="Navegación móvil"
        className="flex sm:hidden items-center gap-4 px-4 py-2 border-t border-[#E2E8F0] dark:border-[#1E2D5A] bg-[#F8FAFC] dark:bg-[#101A36] overflow-x-auto"
      >
        {NAV_ITEMS.map((item) => {
          const isActive = activeView === item.id;
          return (
            <button
              key={item.id}
              type="button"
              onClick={() => onChangeView(item.id)}
              className={`text-xs font-medium whitespace-nowrap shrink-0 py-1 ${
                isActive
                  ? "text-[#0284C7] dark:text-[#00BBF9] font-semibold"
                  : "text-[#64748B] dark:text-[#8E9AB8]"
              }`}
            >
              {item.label}
            </button>
          );
        })}
      </nav>
    </header>
  );
}
