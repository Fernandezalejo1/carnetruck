import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, ESTADO_LABELS, ESTADO_STYLES, fmtTemp, fmtTs } from "../api/client";
import AlertBanner from "../components/AlertBanner";

export default function Dashboard() {
  const [shipments, setShipments] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const [s, a] = await Promise.all([
          api("/shipments", { params: { limit: 100 } }),
          api("/alerts", { params: { resuelta: false, limit: 8 } }),
        ]);
        if (cancelled) return;
        setShipments(s);
        setAlerts(a);
        setError("");
      } catch (err) {
        if (!cancelled) setError(err.message);
      }
    }
    load();
    const timer = setInterval(load, 30000); // polling 30s
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, []);

  const activos = shipments.filter((s) => s.estado === "en_transito");
  const entregados = shipments.filter((s) => s.estado === "entregado");
  const rechazados = shipments.filter((s) => s.estado === "rechazado");
  const pendientes = shipments.reduce((acc, s) => acc + (s.alertas_sin_resolver || 0), 0);

  const cards = [
    { label: "Embarques en tránsito", value: activos.length, color: "text-blue-700" },
    { label: "Entregados", value: entregados.length, color: "text-green-700" },
    { label: "Rechazados", value: rechazados.length, color: "text-red-700" },
    { label: "Alertas sin resolver", value: pendientes, color: "text-amber-600" },
  ];

  return (
    <div>
      <h1 className="mb-4 text-xl font-semibold">Dashboard</h1>

      {error && (
        <div className="mb-4 rounded-md border border-red-200 bg-red-50 px-4 py-2 text-sm text-red-700">
          {error}
        </div>
      )}

      <div className="mb-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
        {cards.map((c) => (
          <div key={c.label} className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
            <div className={`text-2xl font-bold ${c.color}`}>{c.value}</div>
            <div className="mt-1 text-sm text-slate-500">{c.label}</div>
          </div>
        ))}
      </div>

      <AlertBanner alerts={alerts} />

      <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
        <div className="border-b border-slate-200 px-5 py-3 font-semibold">Embarques</div>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-200 text-left text-xs uppercase text-slate-400">
              <th className="px-5 py-2">Contenedor</th>
              <th className="px-5 py-2">Destino</th>
              <th className="px-5 py-2">Producto</th>
              <th className="px-5 py-2">Temp actual</th>
              <th className="px-5 py-2">Rango</th>
              <th className="px-5 py-2">Última lectura</th>
              <th className="px-5 py-2">Estado</th>
            </tr>
          </thead>
          <tbody>
            {shipments.map((s) => {
              const temp = s.latest_reading?.temperatura;
              const fuera =
                temp !== null &&
                temp !== undefined &&
                s.temp_min !== null &&
                s.temp_max !== null &&
                (temp < s.temp_min || temp > s.temp_max);
              return (
                <tr key={s.id} className="border-b border-slate-100 last:border-0 hover:bg-slate-50">
                  <td className="px-5 py-2.5 font-medium text-blue-700">
                    <Link to={`/shipments/${s.id}`}>{s.numero_contenedor}</Link>
                  </td>
                  <td className="px-5 py-2.5">
                    {s.destino_pais} <span className="text-xs text-slate-400">({s.mercado})</span>
                  </td>
                  <td className="px-5 py-2.5 capitalize">{s.tipo_producto}</td>
                  <td className={`px-5 py-2.5 font-semibold ${fuera ? "text-red-600" : ""}`}>
                    {fmtTemp(temp)}
                  </td>
                  <td className="px-5 py-2.5 text-slate-500">
                    {s.temp_min !== null ? `${s.temp_min} a ${s.temp_max}°C` : "—"}
                  </td>
                  <td className="px-5 py-2.5 text-slate-500">{fmtTs(s.latest_reading?.timestamp)}</td>
                  <td className="px-5 py-2.5">
                    <span
                      className={`rounded-full border px-2.5 py-0.5 text-xs font-medium ${ESTADO_STYLES[s.estado]}`}
                    >
                      {ESTADO_LABELS[s.estado]}
                    </span>
                    {s.alertas_sin_resolver > 0 && (
                      <span className="ml-2 rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-700">
                        {s.alertas_sin_resolver}
                      </span>
                    )}
                  </td>
                </tr>
              );
            })}
            {shipments.length === 0 && (
              <tr>
                <td colSpan={7} className="px-5 py-8 text-center text-slate-400">
                  Sin embarques todavía
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
