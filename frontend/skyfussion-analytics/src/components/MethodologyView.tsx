export function MethodologyView() {
  return (
    <div className="max-w-4xl mx-auto flex flex-col gap-6">
      <section className="bg-[#FFFFFF] dark:bg-[#101A36] border border-[#E2E8F0] dark:border-[#1E2D5A] rounded-lg p-6">
        <h1 className="font-display text-2xl font-bold text-[#0F172A] dark:text-[#DCE1FF] [text-wrap:balance]">
          Metodología Espectral, Morfometría OpenCV y Contrato del Agente
        </h1>
        <p className="mt-2 text-sm leading-relaxed text-[#334155] dark:text-[#BCC8D1]">
          Skyfussion Analytics integra escenas multiespectrales Sentinel-2
          (10/20 m) y Landsat (1969–2023), segmentación morfológica fluvial con
          OpenCV y modelado predictivo CRISP-DM sobre la cuenca del río Combeima
          (Ibagué, Tolima) y cuencas prioritarias.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6 pt-6 border-t border-[#E2E8F0] dark:border-[#1E2D5A]">
          <div>
            <h2 className="font-display text-sm font-semibold text-[#0284C7] dark:text-[#00BBF9]">
              01. NDWI — Índice Diferencial de Agua Normalizado
            </h2>
            <p className="mt-1.5 text-sm leading-relaxed text-[#334155] dark:text-[#BCC8D1]">
              Calculado como <span className="font-mono-tabular">(B3 − B8) / (B3 + B8)</span>.
              Valores entre <span className="font-mono-tabular">0.00</span> y{" "}
              <span className="font-mono-tabular">0.30</span> indican humedad moderada;
              por encima de <span className="font-mono-tabular">+0.30</span>{" "}
              confirman cuerpo de agua superficial o saturación ribereña.
            </p>
          </div>

          <div>
            <h2 className="font-display text-sm font-semibold text-[#059669] dark:text-[#00F5D4]">
              02. NDVI — Vigor de Cobertura Vegetal Riparia
            </h2>
            <p className="mt-1.5 text-sm leading-relaxed text-[#334155] dark:text-[#BCC8D1]">
              Calculado con bandas <span className="font-mono-tabular">(B8 − B4) / (B8 + B4)</span>.
              Valores menores a <span className="font-mono-tabular">0.30</span>{" "}
              revelan vegetación escasa o suelo desnudo vulnerable a deslizamientos
              (zona de riesgo K-Means Z1).
            </p>
          </div>

          <div>
            <h2 className="font-display text-sm font-semibold text-[#0F172A] dark:text-[#DCE1FF]">
              03. Pipeline Morfológico OpenCV (1969–2023)
            </h2>
            <p className="mt-1.5 text-sm leading-relaxed text-[#334155] dark:text-[#BCC8D1]">
              Aplica limpieza <span className="font-mono-tabular">MORPH_OPEN / CLOSE</span>{" "}
              (kernel elíptico 5×5), detección de bordes{" "}
              <span className="font-mono-tabular">Canny(50, 150)</span>, esqueletización
              para la línea central y transectos perpendiculares para cuantificar
              erosión (<span className="font-mono-tabular">M1 ∩ ¬M2</span>) vs. deposición.
            </p>
          </div>

          <div>
            <h2 className="font-display text-sm font-semibold text-[#0F172A] dark:text-[#DCE1FF]">
              04. Trazabilidad Estadística (Nivel A)
            </h2>
            <p className="mt-1.5 text-sm leading-relaxed text-[#334155] dark:text-[#BCC8D1]">
              Clasificación de cobertura: KNN test{" "}
              <span className="font-mono-tabular">macro-F1 0.5938</span> y Árbol
              explicable <span className="font-mono-tabular">macro-F1 0.5328</span>{" "}
              (0.66 en plan). Serie temporal RNN real{" "}
              <span className="font-mono-tabular">gru_attention_h1</span>:{" "}
              <span className="font-mono-tabular">RMSE = 0.0712 · R² = 0.0775</span>{" "}
              (alerta asistida por humano).
            </p>
          </div>
        </div>
      </section>

      <section className="bg-[#FFFFFF] dark:bg-[#101A36] border border-[#E2E8F0] dark:border-[#1E2D5A] rounded-lg p-6">
        <h2 className="font-display text-base font-semibold text-[#0F172A] dark:text-[#DCE1FF]">
          Instrucción Activa y Estructura JSON del Agente
        </h2>
        <p className="mt-1 text-xs text-[#64748B] dark:text-[#8E9AB8]">
          Esquema validado en servidor para interoperabilidad con alcaldías y sistemas de alerta temprana.
        </p>
        <p className="mt-3 p-3.5 rounded bg-[#F8FAFC] dark:bg-[#060D24] border border-[#E2E8F0] dark:border-[#1E2D5A] text-xs leading-relaxed text-[#334155] dark:text-[#BCC8D1]">
          &ldquo;Eres el Agente de Reportes Hidrológicos de Skyfussion Analytics.
          Recibirás métricas técnicas (NDWI, NDVI, cambio porcentual del ancho
          del cauce y predicción de caudal en m³/s) de una cuenca hidrográfica.
          Responde EXCLUSIVAMENTE en formato JSON válido con las claves:
          alert_level (&apos;NORMAL&apos; | &apos;PREVENTIVA&apos; |
          &apos;CRITICA&apos;), headline (máximo 12 palabras), narrative
          (párrafo ejecutivo de 3 líneas comprensible para alcaldías y
          autoridades ambientales) y recommendations (lista de 3 acciones
          concretas).&rdquo;
        </p>
        <pre className="mt-4 p-4 rounded bg-[#F8FAFC] dark:bg-[#060D24] border border-[#E2E8F0] dark:border-[#1E2D5A] text-xs font-mono-tabular text-[#0F172A] dark:text-[#00F5D4] overflow-x-auto leading-relaxed">
{`{
  "alert_level": "NORMAL | PREVENTIVA | CRITICA",
  "headline": "Titular ejecutivo conciso (máximo 12 palabras)",
  "narrative": "Párrafo ejecutivo de 3 líneas para alcaldías y autoridades ambientales",
  "recommendations": [
    "Acción concreta 1",
    "Acción concreta 2",
    "Acción concreta 3"
  ]
}`}
        </pre>
      </section>
    </div>
  );
}
