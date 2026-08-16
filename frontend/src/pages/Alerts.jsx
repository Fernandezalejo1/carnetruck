import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  api,
  SEVERIDAD_STYLES,
  TIPO_LABELS,
  fmtTs,
} from "../api/client";

export default function Alerts() {
  const [alerts, setAlerts] = useState([]);
  const [tipo, setTipo] = useState("");
  const [resuelta, setResuelta] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const params = { limit: 300 };
        if (tipo) params.tipo = tipo;
        if (resuelta !== "") params.resuelta = resuelta === "true";
        const data = await api("/alerts", { params });
        if (!cancelled) setAlerts(data);
      } catch (err) {
        if (!cancelled) setError(err.message);
      }
    }
    load();
    const timer = setInterval(load, 30000);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, [tipo, resuelta]);

  async function resolver(alertId) {
    try {
      const a = alerts.find((x) => x.id === alertId);
      await api(`/shipments/${a.shipment_id}/alerts/${alertId}/resolve`, { method: "POST" });
      setAlerts(alerts.map((x) => (x.id === alertId ? { ...x, resuelta: true } : x)));
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div>
      <h1 className="mb-4 text-xl font-semibold">Alertas</h1>

      <div className="mb-4 flex flex-wrap gap-3">
        <select
          value={tipo}
          onChange={(e) => setTipo(e.target.value)}
          className="rounded-md border border-slate-300 px-3 py-1.5 text-sm"
        >
          <option value="">Todos los tipos</option>
          {Object.entries(TIPO_LABELS).map(([k, v]) => (
            <option key={k} value={k}>{v}</option>
          ))}
        </select>
        <select
          value={resuelta}
          onChange={(e) => setResuelta(e.target.value)}
          className="rounded-md border border-slate-300 px-3 py-1.5 text-sm"
        >
          <option value="">Todas</option>
          <option value="false">Sin resolver</option>
          <option value="true">Resueltas</option>
        </select>
      </div>

      {error && (
        <div className="mb-4 rounded-md border border-red-200 bg-red-50 px-4 py-2 text-sm text-red-700">{error}</div>
      )}

      <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-200 text-left text-xs uppercase text-slate-400">
              <th className="px-5 py-2">Fecha</th>
              <th className="px-5 py-2">Tipo</th>
              <th className="px-5 py-2">Severidad</th>
              <th className="px-5 py-2">Mensaje</th>
              <th className="px-5 py-2">Embarque</th>
              <th className="px-5 py-2">Acción</th>
            </tr>
          </thead>
          <tbody>
            {alerts.map((a) => (
              <tr key={a.id} className="border-b border-slate-100 last:border-0 hover:bg-slate-50">
                <td className="px-5 py-2.5 text-slate-500">{fmtTs(a.timestamp)}</td>
                <td className="px-5 py-2.5 font-medium">{TIPO_LABELS[a.tipo] || a.tipo}</td>
                <td className="px-5 py-2.5">
                  <span className={`rounded-full border px-2 py-0.5 text-xs ${SEVERIDAD_STYLES[a.severidad] || SEVERIDAD_STYLES.baja}`}>
                    {a.severidad}
                  </span>
                </td>
                <td className="px-5 py-2.5 text-slate-600">{a.mensaje}</td>
                <td className="px-5 py-2.5">
                  <Link to={`/shipments/${a.shipment_id}`} className="text-blue-700 underline">
                    Ver
                  </Link>
                </td>
                <td className="px-5 py-2.5">
                  {a.resuelta ? (
                    <span className="text-xs text-slate-400">Resuelta</span>
                  ) : (
                    <button
                      onClick={() => resolver(a.id)}
                      className="rounded-md border border-slate-300 px-2 py-1 text-xs hover:bg-slate-50"
                    >
                      Resolver
                    </button>
                  )}
                </td>
              </tr>
            ))}
            {alerts.length === 0 && (
              <tr>
                <td colSpan={6} className="px-5 py-8 text-center text-slate-400">
                  Sin alertas con esos filtros
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
