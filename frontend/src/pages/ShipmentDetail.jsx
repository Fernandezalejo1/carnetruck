import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  api,
  ESTADO_LABELS,
  ESTADO_STYLES,
  SEVERIDAD_STYLES,
  TIPO_LABELS,
  fmtTemp,
  fmtTs,
} from "../api/client";
import AlertBanner from "../components/AlertBanner";
import LiveMap from "../components/LiveMap";
import TemperatureChart from "../components/TemperatureChart";

export default function ShipmentDetail() {
  const { id } = useParams();
  const [shipment, setShipment] = useState(null);
  const [readings, setReadings] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [certificate, setCertificate] = useState(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [verify, setVerify] = useState(null);

  const load = useCallback(async () => {
    try {
      const [s, r, a] = await Promise.all([
        api(`/shipments/${id}`),
        api(`/shipments/${id}/readings`, { params: { limit: 2000 } }),
        api(`/shipments/${id}/alerts`, { params: { limit: 100 } }),
      ]);
      setShipment(s);
      setReadings(r.items);
      setAlerts(a);
      setError("");
    } catch (err) {
      setError(err.message);
    }
  }, [id]);

  const loadCertificate = useCallback(async () => {
    try {
      const certs = await api("/certificates", { params: { shipment_id: id } });
      setCertificate(certs[0] || null);
    } catch {
      setCertificate(null);
    }
  }, [id]);

  useEffect(() => {
    load();
    loadCertificate();
    const timer = setInterval(load, 30000);
    return () => clearInterval(timer);
  }, [load, loadCertificate]);

  async function finalizar(estado) {
    try {
      await api(`/shipments/${id}/finalizar`, { method: "POST", body: { estado } });
      setNotice(`Embarque marcado como ${estado}.`);
      await load();
      await loadCertificate();
    } catch (err) {
      setError(err.message);
    }
  }

  async function generarCertificado(regenerate = false) {
    try {
      const cert = await api(`/shipments/${id}/certificate`, {
        method: "POST",
        params: { regenerate },
      });
      setCertificate(cert);
      setNotice(regenerate ? "Certificado regenerado." : "Certificado generado.");
    } catch (err) {
      setError(err.message);
    }
  }

  async function verificar() {
    if (!certificate) return;
    try {
      setVerify(await api(`/certificates/${certificate.id}/verify`));
    } catch (err) {
      setError(err.message);
    }
  }

  async function resolver(alertId) {
    try {
      await api(`/shipments/${id}/alerts/${alertId}/resolve`, { method: "POST" });
      await load();
    } catch (err) {
      setError(err.message);
    }
  }

  if (error && !shipment) {
    return (
      <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
        {error} — <Link to="/" className="underline">volver al dashboard</Link>
      </div>
    );
  }
  if (!shipment) return <p className="text-slate-400">Cargando…</p>;

  const points = readings.map((r) => ({ lat: r.lat, lng: r.lng, timestamp: r.timestamp }));
  const pendingAlerts = alerts.filter((a) => !a.resuelta);

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold">{shipment.numero_contenedor}</h1>
          <p className="text-sm text-slate-500">
            {shipment.destino_pais} ({shipment.mercado}) · {shipment.tipo_producto}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className={`rounded-full border px-3 py-1 text-xs font-medium ${ESTADO_STYLES[shipment.estado]}`}>
            {ESTADO_LABELS[shipment.estado]}
          </span>
          {shipment.estado === "en_transito" && (
            <>
              <button
                onClick={() => finalizar("entregado")}
                className="rounded-md bg-green-600 px-3 py-1.5 text-sm text-white hover:bg-green-700"
              >
                Marcar entregado
              </button>
              <button
                onClick={() => finalizar("rechazado")}
                className="rounded-md border border-red-300 px-3 py-1.5 text-sm text-red-700 hover:bg-red-50"
              >
                Marcar rechazado
              </button>
            </>
          )}
        </div>
      </div>

      {error && (
        <div className="mb-4 rounded-md border border-red-200 bg-red-50 px-4 py-2 text-sm text-red-700">{error}</div>
      )}
      {notice && (
        <div className="mb-4 rounded-md border border-green-200 bg-green-50 px-4 py-2 text-sm text-green-700">{notice}</div>
      )}

      <div className="mb-6 grid grid-cols-2 gap-4 rounded-xl border border-slate-200 bg-white p-5 text-sm shadow-sm lg:grid-cols-5">
        <div>
          <div className="text-xs uppercase text-slate-400">Rango</div>
          <div className="font-medium">{fmtTemp(shipment.temp_min)} a {fmtTemp(shipment.temp_max)}</div>
        </div>
        <div>
          <div className="text-xs uppercase text-slate-400">Temp actual</div>
          <div className="font-medium">{fmtTemp(shipment.latest_reading?.temperatura)}</div>
        </div>
        <div>
          <div className="text-xs uppercase text-slate-400">Salida</div>
          <div className="font-medium">{fmtTs(shipment.fecha_salida)}</div>
        </div>
        <div>
          <div className="text-xs uppercase text-slate-400">Llegada est.</div>
          <div className="font-medium">{fmtTs(shipment.fecha_llegada_estimada)}</div>
        </div>
        <div>
          <div className="text-xs uppercase text-slate-400">Lecturas</div>
          <div className="font-medium">{readings.length}</div>
        </div>
      </div>

      {pendingAlerts.length > 0 && (
        <div className="mb-6">
          <AlertBanner alerts={pendingAlerts} />
        </div>
      )}

      <div className="mb-6 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="mb-3 text-sm font-semibold text-slate-700">Temperatura</h2>
        <TemperatureChart readings={readings} tempMin={shipment.temp_min} tempMax={shipment.temp_max} />
      </div>

      <div className="mb-6 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="mb-3 text-sm font-semibold text-slate-700">Ubicación en vivo</h2>
        <LiveMap points={points} />
      </div>

      <div className="mb-6 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-slate-700">Certificado de cadena de frío</h2>
          <div className="flex gap-2">
            {certificate ? (
              <>
                <a
                  href={`/api/v1/certificates/${certificate.id}/pdf`}
                  target="_blank"
                  rel="noreferrer"
                  className="rounded-md bg-blue-600 px-3 py-1.5 text-sm text-white hover:bg-blue-700"
                >
                  Descargar PDF
                </a>
                <button
                  onClick={() => generarCertificado(true)}
                  className="rounded-md border border-slate-300 px-3 py-1.5 text-sm hover:bg-slate-50"
                >
                  Regenerar
                </button>
                <button
                  onClick={verificar}
                  className="rounded-md border border-slate-300 px-3 py-1.5 text-sm hover:bg-slate-50"
                >
                  Verificar integridad
                </button>
              </>
            ) : (
              <button
                onClick={() => generarCertificado(false)}
                className="rounded-md bg-blue-600 px-3 py-1.5 text-sm text-white hover:bg-blue-700"
              >
                Generar certificado
              </button>
            )}
          </div>
        </div>
        {certificate ? (
          <div className="grid grid-cols-2 gap-4 text-sm lg:grid-cols-5">
            <div>
              <div className="text-xs uppercase text-slate-400">Generado</div>
              <div>{fmtTs(certificate.generado_en)}</div>
            </div>
            <div>
              <div className="text-xs uppercase text-slate-400">Mín / Máx / Prom</div>
              <div>
                {fmtTemp(certificate.temp_min_registrada)} / {fmtTemp(certificate.temp_max_registrada)} /{" "}
                {fmtTemp(certificate.temp_promedio)}
              </div>
            </div>
            <div>
              <div className="text-xs uppercase text-slate-400">Alertas</div>
              <div>{certificate.cantidad_alertas}</div>
            </div>
            <div>
              <div className="text-xs uppercase text-slate-400">Lecturas</div>
              <div>{certificate.cantidad_lecturas}</div>
            </div>
            <div>
              <div className="text-xs uppercase text-slate-400">Hash</div>
              <div className="break-all font-mono text-xs">{certificate.hash_documento.slice(0, 24)}…</div>
            </div>
          </div>
        ) : (
          <p className="text-sm text-slate-400">Aún no se generó un certificado para este embarque.</p>
        )}
        {verify && (
          <div
            className={`mt-3 rounded-md border px-3 py-2 text-sm ${
              verify.valid
                ? "border-green-200 bg-green-50 text-green-700"
                : "border-red-200 bg-red-50 text-red-700"
            }`}
          >
            {verify.detail}
            <div className="mt-1 font-mono text-xs break-all">
              {verify.stored_hash} {verify.valid ? "" : `≠ ${verify.recomputed_hash}`}
            </div>
          </div>
        )}
      </div>

      <div className="mb-6 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="mb-3 text-sm font-semibold text-slate-700">Alertas del embarque</h2>
        {alerts.length === 0 ? (
          <p className="text-sm text-slate-400">Sin alertas registradas.</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-left text-xs uppercase text-slate-400">
                <th className="py-2 pr-4">Fecha</th>
                <th className="py-2 pr-4">Tipo</th>
                <th className="py-2 pr-4">Severidad</th>
                <th className="py-2 pr-4">Mensaje</th>
                <th className="py-2">Acción</th>
              </tr>
            </thead>
            <tbody>
              {alerts.map((a) => (
                <tr key={a.id} className="border-b border-slate-100 last:border-0">
                  <td className="py-2 pr-4 text-slate-500">{fmtTs(a.timestamp)}</td>
                  <td className="py-2 pr-4 font-medium">{TIPO_LABELS[a.tipo] || a.tipo}</td>
                  <td className="py-2 pr-4">
                    <span className={`rounded-full border px-2 py-0.5 text-xs ${SEVERIDAD_STYLES[a.severidad] || SEVERIDAD_STYLES.baja}`}>
                      {a.severidad}
                    </span>
                  </td>
                  <td className="py-2 pr-4 text-slate-600">{a.mensaje}</td>
                  <td className="py-2">
                    {a.resuelta ? (
                      <span className="text-xs text-slate-400">
                        Resuelta{a.resuelto_por ? ` por ${a.resuelto_por}` : ""}
                      </span>
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
            </tbody>
          </table>
        )}
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="mb-3 text-sm font-semibold text-slate-700">Últimas lecturas</h2>
        <div className="max-h-72 overflow-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-left text-xs uppercase text-slate-400">
                <th className="py-2 pr-4">Timestamp</th>
                <th className="py-2 pr-4">Temp</th>
                <th className="py-2 pr-4">Humedad</th>
                <th className="py-2 pr-4">Batería</th>
                <th className="py-2 pr-4">Puerta</th>
                <th className="py-2">Fuente</th>
              </tr>
            </thead>
            <tbody>
              {[...readings]
                .reverse()
                .slice(0, 20)
                .map((r) => (
                  <tr key={r.id} className="border-b border-slate-100 last:border-0">
                    <td className="py-2 pr-4 text-slate-500">{fmtTs(r.timestamp)}</td>
                    <td className="py-2 pr-4 font-medium">{fmtTemp(r.temperatura)}</td>
                    <td className="py-2 pr-4 text-slate-500">
                      {r.humedad !== null ? `${r.humedad}%` : "—"}
                    </td>
                    <td className="py-2 pr-4 text-slate-500">
                      {r.bateria !== null ? `${r.bateria}%` : "—"}
                    </td>
                    <td className="py-2 pr-4 text-slate-500">{r.puerta_abierta ? "Abierta" : "Cerrada"}</td>
                    <td className="py-2 text-slate-500 uppercase">{r.fuente}</td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
