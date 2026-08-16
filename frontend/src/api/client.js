const API_BASE = "/api/v1";

let token = localStorage.getItem("token") || null;

export function setToken(t) {
  token = t;
  if (t) localStorage.setItem("token", t);
  else localStorage.removeItem("token");
}

export function getToken() {
  return token;
}

export async function api(path, { method = "GET", body, params } = {}) {
  const url = new URL(API_BASE + path, window.location.origin);
  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== "") url.searchParams.set(k, v);
    });
  }
  const headers = { "Content-Type": "application/json" };
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(url, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (res.status === 401) {
    setToken(null);
    window.dispatchEvent(new Event("auth-expired"));
    throw new Error("Sesión expirada");
  }
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const data = await res.json();
      if (typeof data.detail === "string") detail = data.detail;
      else if (Array.isArray(data.detail) && data.detail[0]?.msg) detail = data.detail[0].msg;
    } catch {
      /* sin cuerpo JSON */
    }
    throw new Error(detail);
  }
  const ct = res.headers.get("content-type") || "";
  if (ct.includes("application/json")) return res.json();
  return res;
}

export function fmtTs(value) {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return "—";
  return d.toLocaleString("es-AR", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function fmtTemp(value, decimals = 1) {
  return value === null || value === undefined ? "—" : `${Number(value).toFixed(decimals)}°C`;
}

export const TIPO_LABELS = {
  temp_fuera_rango: "Temp fuera de rango",
  puerta_abierta: "Puerta abierta",
  tamper: "Manipulación",
  sin_señal: "Sin señal",
  bateria_baja: "Batería baja",
};

export const SEVERIDAD_STYLES = {
  critica: "bg-red-100 text-red-700 border-red-200",
  media: "bg-amber-100 text-amber-700 border-amber-200",
  baja: "bg-slate-100 text-slate-600 border-slate-200",
};

export const ESTADO_STYLES = {
  en_transito: "bg-blue-100 text-blue-700 border-blue-200",
  entregado: "bg-green-100 text-green-700 border-green-200",
  rechazado: "bg-red-100 text-red-700 border-red-200",
};

export const ESTADO_LABELS = {
  en_transito: "En tránsito",
  entregado: "Entregado",
  rechazado: "Rechazado",
};
