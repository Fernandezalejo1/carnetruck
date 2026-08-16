import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, fmtTemp, fmtTs } from "../api/client";

export default function Certificates() {
  const [certs, setCerts] = useState([]);
  const [error, setError] = useState("");
  const [verify, setVerify] = useState({});

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const data = await api("/certificates", { params: { limit: 100 } });
        if (!cancelled) setCerts(data);
      } catch (err) {
        if (!cancelled) setError(err.message);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, []);

  async function verificar(certId) {
    try {
      const result = await api(`/certificates/${certId}/verify`);
      setVerify((v) => ({ ...v, [certId]: result }));
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div>
      <h1 className="mb-4 text-xl font-semibold">Certificados</h1>

      {error && (
        <div className="mb-4 rounded-md border border-red-200 bg-red-50 px-4 py-2 text-sm text-red-700">{error}</div>
      )}

      <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-200 text-left text-xs uppercase text-slate-400">
              <th className="px-5 py-2">Contenedor</th>
              <th className="px-5 py-2">Generado</th>
              <th className="px-5 py-2">Mín / Máx / Prom</th>
              <th className="px-5 py-2">Alertas</th>
              <th className="px-5 py-2">Lecturas</th>
              <th className="px-5 py-2">Acciones</th>
            </tr>
          </thead>
          <tbody>
            {certs.map((c) => (
              <tr key={c.id} className="border-b border-slate-100 last:border-0 hover:bg-slate-50">
                <td className="px-5 py-2.5 font-medium">
                  <Link to={`/shipments/${c.shipment_id}`} className="text-blue-700">
                    {c.numero_contenedor || `Embarque #${c.shipment_id}`}
                  </Link>
                </td>
                <td className="px-5 py-2.5 text-slate-500">{fmtTs(c.generado_en)}</td>
                <td className="px-5 py-2.5">
                  {fmtTemp(c.temp_min_registrada)} / {fmtTemp(c.temp_max_registrada)} / {fmtTemp(c.temp_promedio)}
                </td>
                <td className="px-5 py-2.5">{c.cantidad_alertas}</td>
                <td className="px-5 py-2.5">{c.cantidad_lecturas}</td>
                <td className="px-5 py-2.5">
                  <div className="flex gap-2">
                    <a
                      href={`/api/v1/certificates/${c.id}/pdf`}
                      target="_blank"
                      rel="noreferrer"
                      className="rounded-md bg-blue-600 px-2.5 py-1 text-xs text-white hover:bg-blue-700"
                    >
                      PDF
                    </a>
                    <button
                      onClick={() => verificar(c.id)}
                      className="rounded-md border border-slate-300 px-2.5 py-1 text-xs hover:bg-slate-50"
                    >
                      Verificar
                    </button>
                  </div>
                  {verify[c.id] && (
                    <div
                      className={`mt-1 text-xs ${verify[c.id].valid ? "text-green-700" : "text-red-700"}`}
                    >
                      {verify[c.id].valid ? "✓ Íntegro" : "✗ ¡Alterado!"}
                    </div>
                  )}
                </td>
              </tr>
            ))}
            {certs.length === 0 && (
              <tr>
                <td colSpan={6} className="px-5 py-8 text-center text-slate-400">
                  Todavía no hay certificados
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
