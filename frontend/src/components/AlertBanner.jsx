import { Link } from "react-router-dom";
import { SEVERIDAD_STYLES, TIPO_LABELS, fmtTs } from "../api/client";

export default function AlertBanner({ alerts }) {
  if (!alerts || alerts.length === 0) return null;
  return (
    <div className="mb-6 space-y-2">
      <h2 className="text-sm font-semibold text-slate-700">Alertas sin resolver</h2>
      {alerts.map((a) => (
        <div
          key={a.id}
          className={`flex items-center justify-between rounded-md border px-4 py-2 text-sm ${SEVERIDAD_STYLES[a.severidad] || SEVERIDAD_STYLES.baja}`}
        >
          <div className="min-w-0">
            <span className="font-medium">{TIPO_LABELS[a.tipo] || a.tipo}</span>
            <span className="ml-2 text-slate-600">{a.mensaje}</span>
          </div>
          <div className="flex shrink-0 items-center gap-3 text-xs text-slate-500">
            <span>{fmtTs(a.timestamp)}</span>
            <Link to={`/shipments/${a.shipment_id}`} className="text-blue-700 underline">
              Embarque
            </Link>
          </div>
        </div>
      ))}
    </div>
  );
}
