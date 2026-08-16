import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";

const empty = {
  device_id: "",
  numero_contenedor: "",
  destino_pais: "",
  mercado: "CN",
  tipo_producto: "congelado",
  temp_min: "",
  temp_max: "",
  fecha_salida: "",
  fecha_llegada_estimada: "",
};

export default function NewShipment() {
  const navigate = useNavigate();
  const [devices, setDevices] = useState([]);
  const [form, setForm] = useState(empty);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api("/devices", { params: { limit: 200 } })
      .then((d) => setDevices(d))
      .catch((err) => setError(err.message));
  }, []);

  function set(field) {
    return (e) => setForm((f) => ({ ...f, [field]: e.target.value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      const body = {
        device_id: Number(form.device_id),
        numero_contenedor: form.numero_contenedor,
        destino_pais: form.destino_pais,
        mercado: form.mercado,
        tipo_producto: form.tipo_producto,
        temp_min: form.temp_min === "" ? null : Number(form.temp_min),
        temp_max: form.temp_max === "" ? null : Number(form.temp_max),
        fecha_salida: form.fecha_salida ? new Date(form.fecha_salida).toISOString() : null,
        fecha_llegada_estimada: form.fecha_llegada_estimada
          ? new Date(form.fecha_llegada_estimada).toISOString()
          : null,
      };
      const s = await api("/shipments", { method: "POST", body });
      navigate(`/shipments/${s.id}`);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  const activeDevices = devices.filter((d) => d.estado === "activo");

  return (
    <div className="max-w-2xl">
      <h1 className="mb-4 text-xl font-semibold">Nuevo embarque</h1>

      {error && (
        <div className="mb-4 rounded-md border border-red-200 bg-red-50 px-4 py-2 text-sm text-red-700">{error}</div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label className="mb-1 block text-sm font-medium">Dispositivo (sensor)</label>
            <select required value={form.device_id} onChange={set("device_id")} className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm">
              <option value="">Seleccionar…</option>
              {activeDevices.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.alias || d.imei} ({d.imei})
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">N° de contenedor</label>
            <input required value={form.numero_contenedor} onChange={set("numero_contenedor")} className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="MSKU1234567" />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">País de destino</label>
            <input required value={form.destino_pais} onChange={set("destino_pais")} className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="China" />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">Mercado</label>
            <select value={form.mercado} onChange={set("mercado")} className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm">
              <option value="CN">China (GACC)</option>
              <option value="EU">Unión Europea</option>
              <option value="US">EE.UU. (USDA-FSIS)</option>
            </select>
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">Tipo de producto</label>
            <select value={form.tipo_producto} onChange={set("tipo_producto")} className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm">
              <option value="congelado">Congelado</option>
              <option value="fresco">Fresco</option>
            </select>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1 block text-sm font-medium">Temp mín (°C)</label>
              <input type="number" step="0.1" value={form.temp_min} onChange={set("temp_min")} className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="-20" />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium">Temp máx (°C)</label>
              <input type="number" step="0.1" value={form.temp_max} onChange={set("temp_max")} className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="-15" />
            </div>
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">Fecha de salida</label>
            <input type="datetime-local" value={form.fecha_salida} onChange={set("fecha_salida")} className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm" />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">Llegada estimada</label>
            <input type="datetime-local" value={form.fecha_llegada_estimada} onChange={set("fecha_llegada_estimada")} className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm" />
          </div>
        </div>
        <button type="submit" disabled={busy} className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50">
          {busy ? "Creando…" : "Crear embarque"}
        </button>
      </form>
    </div>
  );
}
